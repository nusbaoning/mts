# fig.12 14 globalrank + quadrant
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
#pathDirCam = "/mnt/raid5/trace/MS-Cambridge/"
pathDirCam = "/home/trace/ms-cambridge/"

def getPath(traceID, typeID):
	if typeID == "cam":
		return pathDirCam + traceID + ".csv.req"

PERIODNUM = 10
PERIODLEN = 10 ** 5
logFilename = "/home/wcw/data/analysis.csv"

#logFilename = "/home/bn/data/analysis.csv"
SIZERATE = 0.1
reqDict = {}
updateDict = {}
reqRecordFinish = False


def ssd_init():
	global reqDict, updateDict
	# print("debug init")
	if not reqRecordFinish:
		reqDict = {}	
	updateDict = {}

def ssd_record(block):
	global reqDict
	if reqRecordFinish:
		return
	if block in reqDict:
		reqDict[block] += 1
	else:
		reqDict[block] = 1
def ssd_update(block):
	global updateDict
	if block == None:
		return
	if type(block) == type(1):
		if block in updateDict:
			updateDict[block] += 1
		else:
			updateDict[block] = 1
	else:
		for blk in block:
			if blk in updateDict:
				updateDict[blk] += 1
			else:
				updateDict[blk] = 1

'''
def ssd_update(block):
	global updateDict
	if block == None:
		if block in updateDict:
			updateDict[block] += 1
		else:
			updateDict[block] = 1
	return

	if type(block) == type(1):
		if block in updateDict:
			updateDict[block] += 1
		else:
			updateDict[block] = 1
	else:
		for blk in block:
			if blk in updateDict:
				updateDict[blk] += 1
			else:
				updateDict[blk] = 1
def ssd_hit(block):
	global updateDict
	if block in updateDict:
		updateDict[block] += 1
	else:
		updateDict[block]=1
'''
def ssd_finish(traceID, alg, ucln):
	global reqDict
	if not reqRecordFinish:		
		# get req and rank
		l = list(reqDict.items())
		l.sort(key=operator.itemgetter(1), reverse=True)
		# print(l)
		rank = 0
		subrank = 1
		lastreq = 0
		for (key, req) in l:

			if req != lastreq:
				lastreq = req
				rank += subrank
				subrank = 1
				reqDict[key] = (rank, req)
			else:
				subrank += 1
				reqDict[key] = (rank, req)
		# print(lastreq, rank, subrank, reqDict)
	# hot & not repeat, hot & repeat, cold & not repeat, cold & repeat
	fourdimension = [0]*4
	globalrank = (0,0,0)
	_, reqTh = l[int(0.2*ucln)]
	updateTh = 5
	for block,update in updateDict.items():
		repeat = 0
		hot = 0
		rank, req = reqDict[block]
		if update >= updateTh:
			repeat = 1
		if req >= reqTh:
			hot = 1
		r1, r2, r3 = globalrank
		globalrank = r1+rank, r2+req, r3+1
		fourdimension[2*(1-hot)+repeat] += 1
	logFile = open(logFilename, "a")
	print(traceID, alg, fourdimension[0], fourdimension[1], fourdimension[2], fourdimension[3], sum(fourdimension),1.0*fourdimension[0]/sum(fourdimension), 1.0*fourdimension[1]/sum(fourdimension), 1.0*fourdimension[2]/sum(fourdimension), 1.0*fourdimension[3]/sum(fourdimension),1.0*globalrank[0]/globalrank[2], 1.0*globalrank[1]/globalrank[2],sep='\t', file=logFile)

	logFile.close()

def ssd_statistics(traceID, alg, ucln, ssd):
	global reqDict
	tmpDict = []
	tmpDict = dict(reqDict)
	if not reqRecordFinish:
		# get req and rank
                l = list(tmpDict.items())
                l.sort(key=operator.itemgetter(1), reverse=True)
                # print(l)
                rank = 0
                subrank = 1
                lastreq = 0
                for (key, req) in l:

                        if req != lastreq:
                                lastreq = req
                                rank += subrank
                                subrank = 1
                                tmpDict[key] = (rank, req)
                        else:
                                subrank += 1
                                tmpDict[key] = (rank, req)
                # print(lastreq, rank, subrank, reqDict)
        # hot & not repeat, hot & repeat, cold & not repeat, cold & repeat
	globalrank = (0,0,0)
	if len(l) <= int(0.2*ucln):
		_,reqTh = l[-1]
	else:
		_, reqTh = l[int(0.2*ucln)]
	fourdimension = [0]*4
	updateTh = 5
	for block, _ in ssd.items():
		rank, req = tmpDict[block]
		# get rank of this block in cache
		r1, r2, r3 = globalrank
		globalrank = r1+rank, r2+req, r3+1
	
		repeat = 0
		hot = 0
		if block in updateDict:
			update = updateDict[block]
		else:
			update = 0
		if update >= updateTh:
			repeat = 1
		if req >= reqTh:
			hot = 1
		fourdimension[2*(1-hot)+repeat] += 1	
	logFile = open(logFilename, "a")
	print(traceID, alg, 'globalrank in cache', 1.0*globalrank[0]/globalrank[2], 1.0*globalrank[1]/globalrank[2],sep='\t', file=logFile)
	print(traceID, alg, fourdimension[0], fourdimension[1], fourdimension[2], fourdimension[3], sum(fourdimension),1.0*fourdimension[0]/sum(fourdimension), 1.0*fourdimension[1]/sum(fourdimension), 1.0*fourdimension[2]/sum(fourdimension), 1.0*fourdimension[3]/sum(fourdimension),sep='\t', file=logFile)
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
			ssd_record(block)
			readReq += 1
			if readReq % 100000 == 0:
                logFile = open(logFilename, "a")
                print(traceID, "LRU", readReq, sep='\t', file=logFile)
                logFile.close()
                ssd_statistics(traceID, alg, uclnDict[traceID],ssd.ssd)
			result = ssd.is_hit(block)
			blocks = ssd.update_cache(block)
			ssd_update(blocks)
	print("total hit rate", 1.0*ssd.hit/readReq)
	print('update: ',ssd.update)
	# ssd_finish(traceID, "LRU", uclnDict[traceID])
	ssd_statistics(traceID, alg, uclnDict[traceID],ssd.ssd)
	fin.close()

def load_file_filter(traceID, typeID, alg, sizerate=0.1):
	global resultList
	ssd_init()
	readReq = 0
	# print(traceID)
	size = math.ceil(sizerate*uclnDict[traceID])
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
			ssd_record(block)
			readReq += 1
			if readReq % 100000 == 0:
                logFile = open(logFilename, "a")
                print(traceID, "LRU", readReq, sep='\t', file=logFile)
                logFile.close()
                ssd_statistics(traceID, alg, uclnDict[traceID],ssd.ssd)
			ssd.is_hit(block)	
			if ssd.update < size:				
				ssd.warm_up(block)
				ssd_update(block)
				continue		
			if readReq % 1000000 == 0:
				print(readReq)
						
			blocks = ssd.update_cache(block)
			ssd_update(blocks)
	fin.close()
	print("size", size)
	print("total hit rate", 1.0*ssd.hit/readReq)
	print("write", ssd.update)
	ssd_statistics(traceID, alg, uclnDict[traceID],ssd.ssd)

def load_file_period(traceID, typeID, alg, sizerate=0.1):
	global resultList
	ssd_init()
	readReq = 0
	# print(traceID)
	size = math.ceil(sizerate*uclnDict[traceID])
	throt = int(0.1*size)
	ssd = mts_cache_algorithm.Period(size, throt, alg, True, 50, 30)
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
			ssd_record(block)
			readReq += 1
			if readReq % 100000 == 0:
                                logFile = open(logFilename, "a")
                                print(traceID, "periodLRU", readReq, sep='\t', file=logFile)
                                logFile.close()
                                ssd_statistics(traceID, "periodLRU", uclnDict[traceID], ssd.ssd.ssd)
			result = ssd.is_hit(block)				
			blocks = ssd.update_cache(block)
			ssd_update(blocks)
	print("total hit rate", 1.0*ssd.ssd.hit/readReq)
	print('update: ',ssd.ssd.update)
	ssd_statistics(traceID, "periodLRU", uclnDict[traceID], ssd.ssd.ssd)
	#ssd_finish(traceID, "periodLRU", uclnDict[traceID])
	fin.close()	


def load_file_mt(traceID, typeID, periodLen = 10**5, sizerate=0.1, throtrate=0.1, sleepInterval=30):
	readReq = 0
	ssd_init()		
	ucln = uclnDict[traceID]
	size = math.ceil(sizerate*ucln)
	ssd = mts_cache_algorithm.MT(size)
	hisDict = mts_cache_algorithm.HistoryDict()
	PERIODLEN = periodLen
	throt = int(throtrate*min(size, PERIODLEN))
	potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
	fin = open(getPath(traceID, typeID), 'r', encoding='utf-8', errors='ignore')
	lines = fin.readlines()
	periodSign = 0
	period = 1	
	sleepStart = 10000000
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
			if readReq % 100000 == 0:
                                logFile = open(logFilename, "a")
                                print(traceID, "MT", readReq, sep='\t', file=logFile)
                                logFile.close()
                                ssd_statistics(traceID, "MT", uclnDict[traceID], ssd.ssd)	
			ssd_record(block)
			hit = ssd.is_hit(block)
			if ssd.update < size:				
				result = ssd.update_cache(block)
				ssd_update(block)
				continue			
			periodSign += 1
			if periodRecord:
				hisDict.access_data(block, period)			
				if not hit:
					potentialDict.update_cache(block)		
			if periodSign >= PERIODLEN:

				if period <= sleepStart:
					# print("bug 127", period, periodSign, warmup, test)
					_,updateBlocks = ssd.update_cache_k(throt, potentialDict, hisDict, period)
					ssd_update(updateBlocks)
					hisDict = mts_cache_algorithm.HistoryDict()
					potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
				elif (period-sleepStart) % sleepInterval == 0:
					_,updateBlocks = ssd.update_cache_k(throt, potentialDict, hisDict, period)
					ssd_update(updateBlocks)
					hisDict = mts_cache_algorithm.HistoryDict()
					potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
				periodSign = 0	
				period += 1
				# sleepSign = (period-sleepStart) % sleepInterval
				# if period > sleepStart and sleepSign >=  1 and sleepSign <= sleepInterval-10:
				# 	periodRecord = False
				# if not periodRecord and sleepSign >= sleepInterval-10:
				# 	periodRecord = True
					
	fin.close()
	ssd_statistics(traceID, "MT", ucln, ssd.ssd)

def load_file_sieve_original(traceID, typeID, t1=3, t2=1):
	global resultList
	ssd_init()
	readReq = 0
	ucln = uclnDict[traceID]
	size = math.ceil(SIZERATE*ucln)
	ssd = mts_cache_algorithm.SieveStoreOriginal(size, 5, t1, t2)

	throt = int(0.1*size)
	fin = open(getPath(traceID, typeID), 'r', encoding='utf-8', errors='ignore')
	lines = fin.readlines()
	periodSign = 0
	period = 1	
	
	for line in lines:		
		items = line.split(' ')
		reqtype = int(items[0])
		block = int(items[2])
		if reqtype == 1:			
			ssd.delete_cache(block)
		else:
			readReq += 1
			if readReq % 100000 == 0:
                                # print(readReq)
                                # print(reqDict)
                                logFile = open(logFilename, "a")
                                print(traceID, "SS", readReq, sep='\t', file=logFile)
                                logFile.close()
                                ssd_statistics(traceID, "SS", uclnDict[traceID],ssd.lru.ssd)			
			ssd_record(block)			
			hit = ssd.is_hit(block)		
			periodSign += 1				
			updateBlock = ssd.update_cache(block, period)		
			ssd_update(updateBlock)
			if periodSign >= PERIODLEN:
				periodSign = 0	
				period += 1
				
	
	fin.close()
	ssd_statistics(traceID, "SS", uclnDict[traceID],ssd.lru.ssd)
start = time.clock()
load_file(sys.argv[1], sys.argv[2], mts_cache_algorithm.LRU)
end = time.clock()
print(sys.argv[1], sys.argv[2], "LRU", "consumed ", end-start, "s")

start = time.clock()
load_file_period(sys.argv[1], sys.argv[2], mts_cache_algorithm.LRU)
end = time.clock()
print(sys.argv[1], sys.argv[2], "periodLRU", "consumed ", end-start, "s")

start = time.clock()
load_file(sys.argv[1], sys.argv[2], mts_cache_algorithm.ARC)
end = time.clock()
print(sys.argv[1], sys.argv[2], "periodLRU", "consumed ", end-start, "s")


start = time.clock()
load_file_filter(sys.argv[1], sys.argv[2], mts_cache_algorithm.LARC)
end = time.clock()
print(sys.argv[1], sys.argv[2], "periodLRU", "consumed ", end-start, "s")


start = time.clock()
load_file_mt(sys.argv[1], sys.argv[2])
end = time.clock()
print(sys.argv[1], sys.argv[2], "MT", "consumed ", end-start, "s")
start = time.clock()
load_file_sieve_original(sys.argv[1], sys.argv[2])
end = time.clock()
print(sys.argv[1], sys.argv[2], "Sieve", "consumed ", end-start, "s")

