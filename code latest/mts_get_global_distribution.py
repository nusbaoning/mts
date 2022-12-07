import mts_cache_algorithm
import operator 
import time
import sys
import math

# add trace workflow:
# add ucln
# add path

# run overflow:
# 

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
recordFinish = False
resultList = [0]*4
# resultList = [0]*11
logList = []

def ssd_init():
	global resultList
	# print("debug init")
	resultList = [0]*4
	logList = []

def __ssd_analysis(ssdList, ucln):
	# print("debug analysis")
	if ssdList == None:
		# print("debug ssd list none")
		return
	global ssdDict, resultList
	# print("debug", ucln)
	for key in ssdList:
		rank = ssdDict[key]
		# resultList[int(100*rank/ucln)]
		if rank <= 0.01*ucln:
			resultList[0] += 1
		elif rank <= 0.2*ucln:
			resultList[1] += 1
		else:
			resultList[2] += 1
	resultList[3] += 1
	# print("debug", resultList)

def ssd_analysis(ssd, size, ucln):
	global ssdDict, recordFinish
	ssdList = ssd.get_top_n(size)
	# if ssdList!=None:
	# 	print("debug ssd analysis", len(ssdList))
	# else:
	# 	print("None")
	if recordFinish and ssdList!=None:		
		__ssd_analysis(ssdList, ucln)
	elif ssdList!=None:
		# print("debug log list append", len(logList))
		logList.append(ssdList)

def ssd_record(block):
	global ssdDict, recordFinish
	if not recordFinish:
		if block in ssdDict:
			ssdDict[block] += 1
		else:
			ssdDict[block] = 1

def analysis_finish(ucln):
	global ssdDict, recordFinish
	if not recordFinish:
		l = list(ssdDict.items())
		l.sort(key=operator.itemgetter(1), reverse=True)
		print("highest freq", l[0], l[int(0.01*ucln)], l[int(0.2*ucln)])
		rank = 0
		for (key, _) in l:
			ssdDict[key] = rank
			rank += 1
		recordFinish = True
		for ssdList in logList:
			__ssd_analysis(ssdList, ucln)


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
			if readReq % 100000 == 0:
				print(readReq)
				ssd_analysis(ssd, size, uclnDict[traceID])
				print(resultList)
			ssd_record(block)
			readReq += 1
			ssd.is_hit(block)				
			ssd.update_cache(block)
	analysis_finish(uclnDict[traceID])

	fin.close()
	print("size", size)
	print("total hit rate", 1.0*ssd.hit/readReq)
	logFile = open(logFilename, "a")
	# print(traceID, "LRU", size, 1.0*ssd.hit/readReq, ssd.update, sep=',', file=logFile)
	print(traceID, "LRU", size, 1.0*resultList[0]/resultList[3], 1.0*resultList[1]/resultList[3], 
		1.0*resultList[2]/resultList[3], 1.0*resultList[0]/resultList[3]/size, 1.0*resultList[1]/resultList[3]/size, 
		1.0*resultList[2]/resultList[3]/size,sep=',', file=logFile)
	print(traceID, "LRU", size, 1.0*resultList[0]/resultList[3], 1.0*resultList[1]/resultList[3], 
		1.0*resultList[2]/resultList[3], 1.0*resultList[0]/resultList[3]/size, 1.0*resultList[1]/resultList[3]/size, 
		1.0*resultList[2]/resultList[3]/size,sep=',')
	logFile.close()


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
			if readReq % 3000000 == 0:
				print(readReq)
				ssd_analysis(ssd, size, uclnDict[traceID])
				print(resultList)
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
					
	analysis_finish(uclnDict[traceID])
	fin.close()
	print("size", size)
	print("total hit rate", 1.0*ssd.hit/readReq)
	print("write", ssd.update)
	logFile = open(logFilename, "a")
	# print(traceID, "MT", size, 1.0*ssd.hit/readReq, ssd.update, PERIODLEN, sign, sep=',', file=logFile)
	print(traceID, "MT", size, 1.0*resultList[0]/resultList[3], 1.0*resultList[1]/resultList[3], 
		1.0*resultList[2]/resultList[3], 1.0*resultList[0]/resultList[3]/size, 1.0*resultList[1]/resultList[3]/size, 
		1.0*resultList[2]/resultList[3]/size,sep=',', file=logFile)
	print(traceID, "MT", size, 1.0*resultList[0]/resultList[3], 1.0*resultList[1]/resultList[3], 
		1.0*resultList[2]/resultList[3], 1.0*resultList[0]/resultList[3]/size, 1.0*resultList[1]/resultList[3]/size, 
		1.0*resultList[2]/resultList[3]/size,sep=',')
	logFile.close()

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
			if readReq % 100000 == 0:
				print(readReq)
				ssd_analysis(ssd, size, uclnDict[traceID])
				print(resultList)
			ssd_record(block)			
			hit = ssd.is_hit(block)		
			periodSign += 1				
			ssd.update_cache(block, period)		

			if periodSign >= PERIODLEN:
				periodSign = 0	
				period += 1
				
	analysis_finish(uclnDict[traceID])
	fin.close()
	print("size", size)
	print("total hit rate", 1.0*ssd.hit/readReq)
	print("write", ssd.update)
	logFile = open(logFilename, "a")
	print(resultList)
	# print(traceID, "Sieve", size, 1.0*ssd.hit/readReq, ssd.update, PERIODLEN, t1, t2, sep=',', file=logFile)
	print(traceID, "Sieve", size, 1.0*resultList[0]/resultList[3], 1.0*resultList[1]/resultList[3], 
		1.0*resultList[2]/resultList[3], 1.0*resultList[0]/resultList[3]/size, 1.0*resultList[1]/resultList[3]/size, 
		1.0*resultList[2]/resultList[3]/size,sep=',', file=logFile)
	print(traceID, "Sieve", size, 1.0*resultList[0]/resultList[3], 1.0*resultList[1]/resultList[3], 
		1.0*resultList[2]/resultList[3], 1.0*resultList[0]/resultList[3]/size, 1.0*resultList[1]/resultList[3]/size, 
		1.0*resultList[2]/resultList[3]/size,sep=',')
	logFile.close()


start = time.clock()
load_file_mt(sys.argv[1], sys.argv[2])
end = time.clock()
print(sys.argv[1], sys.argv[2], "MT", "consumed ", end-start, "s")

start = time.clock()
load_file(sys.argv[1], sys.argv[2], mts_cache_algorithm.LRU)
end = time.clock()
print(sys.argv[1], sys.argv[2], "LRU", "consumed ", end-start, "s")

start = time.clock()
load_file_sieve_original(sys.argv[1], sys.argv[2])
end = time.clock()
print(sys.argv[1], sys.argv[2], "SS", "consumed ", end-start, "s")

start = time.clock()
load_file_sieve_original(sys.argv[1], sys.argv[2], 3, 1)
end = time.clock()
print(sys.argv[1], sys.argv[2], "SS", "consumed ", end-start, "s")

# ssd_init()
# ssdDict = {1:1, 2:2, 3:5, 4:4}
# ssd_record(5)
# # print(ssdDict)
# recordFinish = True
# # ssd_record(5)
# # print(ssdDict)
# print(resultList)
# __ssd_analysis([1,2], 4)
# print(resultList)