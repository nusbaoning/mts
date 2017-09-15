import mts_cache_algorithm
import operator 
import time
import sys
import math

uclnDict = {"netfs":47949, "mix":195423,
"mds_0":	769376,
"hm_0":	488986,
"prn_0":	985474,
"proj_0":	462462,
"prxy_0":	79483,
"rsrch_0":	20855,
"src1_0":	31656826,
"usr_1":	171538746,
"src2_0":	104953,
"stg_0":	1608935,
"ts_0":	131140,
"wdev_0":	52111,
"web_0":	1887115
}
pathDirCam = "/mnt/raid5/trace/MS-Cambridge/"
pathDictHome = "/home/trace/"
# pathDict = {"usr_1": pathDirCam+"usr_1.csv.req","src1_0": pathDirCam+"src1_0.csv.req",
# "ts_0": pathDirCam+"ts_0.csv.req","prn0": pathDirCam+"prn0.csv.req",
# "netfs": pathDictHome+"netfs.csv.req","mix": pathDictHome+"mix.csv.req",
# "proj_0": pathDirCam+"proj_0.csv.req","rsrch_0": pathDirCam+"rsrch_0.csv.req",
# "prxy_0": pathDirCam+"prxy_0.csv.req","stg_0": pathDirCam+"stg_0.csv.req",
# "src2_0": pathDirCam+"src2_0.csv.req","mds_0": pathDirCam+"mds0.csv.req",
# "web_0": pathDirCam+"web_0.csv.req","hm_0": pathDirCam+"hm0.csv.req",
# "wdev_0": pathDirCam+"wdev_0.csv.req"
# }

def getPath(traceID, typeID):
	if typeID == "home":
		return pathDictHome + traceID + ".csv.req"
	if typeID == "cam":
		return pathDirCam + traceID + ".csv.req"
PERIODNUM = 10
PERIODLEN = 10 ** 4
logFilename = "/home/bn/data/result.csv"
SIZERATE = 0.1

# def load_file_dram(traceID):
# 	readReq = 0
# 	dram = mts_cache_algorithm.LRU(math.ceil(0.001*uclnDict[traceID]))
# 	ssd = mts_cache_algorithm.LRU(math.ceil(0.05*uclnDict[traceID]))
# 	fin = open(getPath(traceID, "cam"), 'r', encoding='utf-8', errors='ignore')
# 	lines = fin.readlines()
# 	# print("test", dram.hit, ssd.hit)
# 	for line in lines:
# 		items = line.split(' ')
# 		reqtype = int(items[0])
# 		block = int(items[2])
# 		if reqtype == 1:
# 			dram.delete_cache(block)
# 			ssd.delete_cache(block)
# 		else:
# 			readReq += 1
# 			if dram.is_hit(block):
# 				dram.update_cache(block)
# 			else:
# 				dram.update_cache(block)
# 				ssd.is_hit(block)
# 				ssd.update_cache(block)
# 	print("size", math.ceil(0.001*uclnDict[traceID]), math.ceil(0.05*uclnDict[traceID]))
# 	print("total hit rate", 1.0*(dram.hit+ssd.hit)/readReq, 1.0*ssd.hit/(readReq-dram.hit))

def load_file(traceID, alg):
	readReq = 0
	# print(traceID)
	size = math.ceil(SIZERATE*uclnDict[traceID])
	ssd = alg(size)
	fin = open(getPath(traceID, "cam"), 'r', encoding='utf-8', errors='ignore')
	lines = fin.readlines()
	for line in lines:
		items = line.split(' ')
		reqtype = int(items[0])
		block = int(items[2])
		if reqtype == 1:			
			ssd.delete_cache(block)
		else:			
			readReq += 1
			ssd.is_hit(block)				
			ssd.update_cache(block)
	fin.close()
	print("size", size)
	print("total hit rate", 1.0*ssd.hit/readReq)
	logFile = open(logFilename, "a")
	print(traceID, alg, size, 1.0*ssd.hit/readReq, ssd.update, sep=',', file=logFile)
	logFile.close()


def load_file_mt(traceID):
	readReq = 0
	size = math.ceil(SIZERATE*uclnDict[traceID])
	ssd = mts_cache_algorithm.MT(size)
	hisDict = mts_cache_algorithm.HistoryDict()
	PERIODLEN = size
	throt = int(0.1*size)
	potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
	fin = open(getPath(traceID, "cam"), 'r', encoding='utf-8', errors='ignore')
	lines = fin.readlines()
	periodSign = 0
	period = 1	
	sleepStart = 50
	sleepInterval = 30
	periodRecord = True
	# print("test", dram.hit, ssd.hit)
	for line in lines:		
		items = line.split(' ')
		reqtype = int(items[0])
		block = int(items[2])
		if reqtype == 1:			
			ssd.delete_cache(block)
		else:
			readReq += 1			
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
					ssd.update_cache_k(throt, potentialDict, hisDict, period)
					hisDict = mts_cache_algorithm.HistoryDict()
					potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
				elif (period-sleepStart) % sleepInterval == 0:
					ssd.update_cache_k(throt, potentialDict, hisDict, period)
					hisDict = mts_cache_algorithm.HistoryDict()
					potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
				periodSign = 0	
				period += 1
				sleepSign = (period-sleepStart) % sleepInterval
				if period > sleepStart and sleepSign >=  1 and sleepSign <= sleepInterval-10:
					periodRecord = False
					
	fin.close()
	print("size", size)
	print("total hit rate", 1.0*ssd.hit/readReq)
	print("write", ssd.update)
	logFile = open(logFilename, "a")
	print(traceID, "MT", size, 1.0*ssd.hit/readReq, ssd.update, sep=',', file=logFile)
	logFile.close()


def load_file_mt_time(traceID):
	readReq = 0
	size = math.ceil(SIZERATE*uclnDict[traceID])
	ssd = mts_cache_algorithm.MTtime(size)
	hisDict = mts_cache_algorithm.HistoryDict()
	PERIODLEN = size
	throt = int(0.1*size)
	potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
	fin = open(getPath(traceID, "cam"), 'r', encoding='utf-8', errors='ignore')
	lines = fin.readlines()
	periodSign = 0
	period = 1	
	sleepStart = 50
	sleepInterval = 30
	periodRecord = True
	# print("test", dram.hit, ssd.hit)
	for line in lines:		
		items = line.split(' ')
		reqtype = int(items[0])
		block = int(items[2])
		if reqtype == 1:			
			ssd.delete_cache(block)
		else:
			readReq += 1			
			hit = ssd.is_hit(block)
			if ssd.update < size:				
				ssd.update_cache(block)
				continue			
			periodSign += 1
			if periodRecord:
				hisDict.access_data_time(block, period, readReq)			
				if not hit:
					potentialDict.update_cache(block)		
			if periodSign >= PERIODLEN:

				if period <= sleepStart:
					# print("bug 127", period, periodSign, warmup, test)
					ssd.update_cache_k(throt, potentialDict, hisDict, period)
					hisDict = mts_cache_algorithm.HistoryDict()
					potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
				elif (period-sleepStart) % sleepInterval == 0:
					ssd.update_cache_k(throt, potentialDict, hisDict, period)
					hisDict = mts_cache_algorithm.HistoryDict()
					potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
				periodSign = 0	
				period += 1
				sleepSign = (period-sleepStart) % sleepInterval
				if period > sleepStart and sleepSign >=  1 and sleepSign <= sleepInterval-10:
					periodRecord = False
					
	fin.close()
	print("size", size)
	print("total hit rate", 1.0*ssd.hit/readReq)
	print("write", ssd.update)
	logFile = open(logFilename, "a")
	print(traceID, "MT", size, 1.0*ssd.hit/readReq, ssd.update, sep=',', file=logFile)
	logFile.close()
# def load_file_mt_dram(traceID):
# 	readReq = 0
# 	dram = mts_cache_algorithm.LRU(math.ceil(0.001*uclnDict[traceID]))
# 	ssd = mts_cache_algorithm.MT(math.ceil(0.05*uclnDict[traceID]))
# 	hisDict = mts_cache_algorithm.HistoryDict()
# 	potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
# 	fin = open(getPath(traceID, "cam"), 'r', encoding='utf-8', errors='ignore')
# 	lines = fin.readlines()
# 	periodSign = 0
# 	period = 1
# 	warmup = True
# 	sleepStart = 50
# 	sleepInterval = 30
# 	# print("test", dram.hit, ssd.hit)
# 	for line in lines:
		
# 		items = line.split(' ')
# 		reqtype = int(items[0])
# 		block = int(items[2])
# 		if reqtype == 1:
# 			dram.delete_cache(block)
# 			ssd.delete_cache(block)
# 		else:
# 			readReq += 1
			
# 			if dram.is_hit(block):
# 				dram.update_cache(block)
# 			else:
# 				periodSign += 1
# 				dram.update_cache(block)
# 				hit = ssd.is_hit(block)
# 				if warmup:				
# 					ssd.update_cache(block)
# 				else:
# 					hisDict.access_data(block, period)
# 					if not hit:
# 						potentialDict.update_cache(block)
# 			if warmup and periodSign >= math.ceil(0.05*uclnDict[traceID]):
# 				print("warmup", ssd.update)
# 				warmup = False
# 				periodSign = 0
# 			elif periodSign >= PERIODLEN:
# 				periodSign = 0
# 				period += 1
# 				if period <= sleepStart:
# 					ssd.update_cache_k(1500, potentialDict, hisDict, period)
# 				elif (period-sleepStart) % sleepInterval == 0:
# 					ssd.update_cache_k(1500, potentialDict, hisDict, period)

# 	print("size", math.ceil(0.001*uclnDict[traceID]), math.ceil(0.05*uclnDict[traceID]))
# 	print("total hit rate", 1.0*(dram.hit+ssd.hit)/readReq, 1.0*ssd.hit/(readReq-dram.hit))
# 	print("write", ssd.update)
# for key in uclnDict.keys():
# 	load_file(key)
# load_file_mt_dram("netfs")
# load_file_mt_dram("mix")
# load_file_mt("netfs")
# def generateDict():
# 	for i in uclnDict:
# 		print("\"" + i + "\": pathDirCam+\"" + i + ".csv.req\"", end="," )


# generateDict()
# start = time.clock()
# load_file(sys.argv[1], mts_cache_algorithm.LRU)
# end = time.clock()
# print("consumed ", end-start, "s")

# start = time.clock()
# load_file(sys.argv[1], mts_cache_algorithm.SieveStore)
# end = time.clock()
# print("consumed ", end-start, "s")

# start = time.clock()
# load_file_mt(sys.argv[1])
# end = time.clock()
# print("consumed ", end-start, "s")

start = time.clock()
load_file_mt_time(sys.argv[1])
end = time.clock()
print("consumed ", end-start, "s")