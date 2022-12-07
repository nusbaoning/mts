import mts_cache_algorithm
import operator 
import time
import sys
import math

uclnDict = {
"prn_0":	985474,
"proj_0":	462462,
"prxy_0":	79483,
"rsrch_0":	20855,
"src2_0":	104953,
"wdev_0":	52111,
"mds_0":	769376,
"ts_0":	131140,
"stg_0":	1608935,
"hm_0":	488986,
"web_2":	17610218,
"usr_20":	31968051	
}
pathDirCam = "/mnt/raid5/trace/MS-Cambridge/"

def getPath(traceID, typeID):
	if typeID == "cam":
		return pathDirCam + traceID + ".csv.req"

PERIODNUM = 10
PERIODLEN = 10 ** 5
logFilename = "/home/bn/data/analysis.csv"
SIZERATE = 0.1
ssdDict = {}
resultList = []
# evict, insert, update, ssd
logList = None

def ssd_init():
	global ssdDict, resultList, logList
	# print("debug init")
	resultList = []
	logList = None
	ssdDict = {}

def calculate_last_update(evict, insert, update):
	global resultList
	evictHit = 0
	updateHit = 0
	for block in evict:
		if block in ssdDict:
			evictHit += ssdDict[block]
	for block in insert:
		if block in ssdDict:
			updateHit += ssdDict[block]
	resultList.append((evictHit, updateHit, update))

def record_new_set(lastSsd, ssd, size):
	global logList
	ssdSet = set(ssd.get_top_n(size))
	# print(lastSsd, type(lastSsd), type(ssdSet))
	evict = lastSsd - ssdSet
	insert = ssdSet - lastSsd
	update = ssd.update
	logList = (evict, insert, update, ssdSet)


def ssd_analysis(ssd, size):
	global ssdDict, logList	
	if logList != None:		
		lastEvict, lastInsert, lastUpdate, lastSsd = logList
		calculate_last_update(lastEvict, lastInsert, ssd.update-lastUpdate)
		record_new_set(lastSsd, ssd, size)
	else:
		record_new_set(set([]), ssd, size)
	ssdDict = {}

def ssd_record(block):
	global ssdDict
	if block in ssdDict:
		ssdDict[block] += 1
	else:
		ssdDict[block] = 1
	

def analysis_finish(traceID, alg, size):
	logFile = open(logFilename, "a")
	# print(traceID, "LRU", size, 1.0*ssd.hit/readReq, ssd.update, sep=',', file=logFile)
	print(traceID, alg, size, 200000, sep=',', file=logFile)
	for result in resultList:
		evictHit, updateHit, update = result
		if update>0:			
			print(evictHit, updateHit, update, updateHit-evictHit, 1.0*(updateHit-evictHit)/update, sep=',', file=logFile)
	logFile.close()


def load_file(traceID, typeID, alg):
	global resultList
	ssd_init()
	readReq = 0
	# print(traceID)
	size = math.ceil(SIZERATE*uclnDict[traceID])
	ssd = alg(size)
	fin = open(getPath(traceID, typeID), 'r', encoding='utf-8', errors='ignore')
	lines = fin.readlines()
	print("load file finished")
	for line in lines:
		items = line.split(' ')
		reqtype = int(items[0])
		block = int(items[2])
		if reqtype == 1:			
			ssd.delete_cache(block)
		else:		
			if readReq > 1.2*size + 5000000:
				break
			if readReq > 1.2*size and readReq % (2*PERIODLEN) == 0:
				print(readReq)
				ssd_analysis(ssd, size)
				if len(resultList)>0:
					print(len(resultList), resultList[-1])
			ssd_record(block)
			readReq += 1
			ssd.is_hit(block)				
			ssd.update_cache(block)
	fin.close()
	analysis_finish(traceID, "LRU", size)
	

	
	


def load_file_mt(traceID, typeID, periodLen = 10**5):
	global resultList
	ssd_init()
	readReq = 0
	size = math.ceil(SIZERATE*uclnDict[traceID])
	ssd = mts_cache_algorithm.MT(size)
	hisDict = mts_cache_algorithm.HistoryDict()
	PERIODLEN = periodLen
	throt = int(0.1*size)
	potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
	fin = open(getPath(traceID, typeID), 'r', encoding='utf-8', errors='ignore')
	lines = fin.readlines()
	periodSign = 0
	period = 1	
	sleepStart = 50
	sleepInterval = 30
	periodRecord = True
	sign = False
	# print("test", dram.hit, ssd.hit)
	for line in lines:		
		items = line.split(' ')
		reqtype = int(items[0])
		block = int(items[2])
		if reqtype == 1:			
			ssd.delete_cache(block)
		else:
			readReq += 1	
			if readReq > 1.2*size + 5000000:
				break	
			if readReq > 1.2*size and readReq % (2*PERIODLEN) == 0:
				print(readReq)
				ssd_analysis(ssd, size)
				if len(resultList)>0:
					print(len(resultList), resultList[-1])
				
			ssd_record(block)	
			hit = ssd.is_hit(block)
			if ssd.update < size:				
				ssd.update_cache(block)
				continue			
			periodSign += 1
			if periodRecord:
				hisDict.access_data(block, period)			
				if not hit:
					potentialDict.update_cache(block)		
			if periodSign >= PERIODLEN:

				if period <= sleepStart:
					# print("bug 127", period, periodSign, warmup, test)
					sign |= ssd.update_cache_k(throt, potentialDict, hisDict, period)
					hisDict = mts_cache_algorithm.HistoryDict()
					potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
				elif (period-sleepStart) % sleepInterval == 0:
					sign |= ssd.update_cache_k(throt, potentialDict, hisDict, period)
					hisDict = mts_cache_algorithm.HistoryDict()
					potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
				periodSign = 0	
				period += 1
				sleepSign = (period-sleepStart) % sleepInterval
				if period > sleepStart and sleepSign >=  1 and sleepSign <= sleepInterval-10:
					periodRecord = False
					
	fin.close()
	analysis_finish(traceID, "MT", size)
	
	

def load_file_sieve_original(traceID, typeID, t1=9, t2=4):
	global resultList
	ssd_init()
	readReq = 0
	size = math.ceil(SIZERATE*uclnDict[traceID])
	ssd = mts_cache_algorithm.SieveStoreOriginal(size, 5, t1, t2)
	# PERIODLEN = size
	throt = int(0.1*size)
	fin = open(getPath(traceID, typeID), 'r', encoding='utf-8', errors='ignore')
	lines = fin.readlines()
	periodSign = 0
	period = 1	
	# sleepStart = 50
	# sleepInterval = 30
	
	for line in lines:		
		items = line.split(' ')
		reqtype = int(items[0])
		block = int(items[2])
		if reqtype == 1:			
			ssd.delete_cache(block)
		else:
			readReq += 1	
			if readReq > 1.2*size + 5000000:
				break
			if readReq > 1.2*size and readReq % (2*PERIODLEN) == 0:
				print(readReq)
				ssd_analysis(ssd, size)
				if len(resultList)>0:
					print(len(resultList), resultList[-1])
			ssd_record(block)				
			hit = ssd.is_hit(block)		
			periodSign += 1				
			ssd.update_cache(block, period)		

			if periodSign >= PERIODLEN:
				periodSign = 0	
				period += 1
				
	fin.close()
	analysis_finish(traceID, "Sieve", size)
	


start = time.clock()
load_file_mt(sys.argv[1], sys.argv[2])
end = time.clock()
print(sys.argv[1], sys.argv[2], "MT", "consumed ", end-start, "s")

start = time.clock()
load_file(sys.argv[1], sys.argv[2], mts_cache_algorithm.LRU)
end = time.clock()
print(sys.argv[1], sys.argv[2], "LRU", "consumed ", end-start, "s")

start = time.clock()
load_file_sieve_original(sys.argv[1], sys.argv[2], 3, 1)
end = time.clock()
print(sys.argv[1], sys.argv[2], "SS", "consumed ", end-start, "s")

# test
# ssd_init()
# ssdDict = {1:2, 3:4, 5:6}
# calculate_last_update(set([1,2]), set([3,4]), 5)
# print(resultList)
# record_new_set(set([1,3,5,7,9,10]), set([2,3,4,5,6,7]))
# print(logList)