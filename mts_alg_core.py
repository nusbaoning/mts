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
"web_0":	1887115,

"bs24":	4155,
"bs39":	12190,
"dev5.3.7.19":	1873854,
"dev5.3.11.19":	1081695,
"live6.31":	30393264,
"live3.31":	6920465,
"mfs253":	2222973,
"mfs101":	1408158,
"msc116":	216158,
"msc651":	128895,
"dad807":	294190,
"dap812":	224019
}
pathDirCam = "/mnt/raid5/trace/MS-Cambridge/"
pathDictHome = "/home/trace/"

pathDict = {
"bs24":	"/mnt/raid5/trace/MS-production/BuildServer/Traces/24.hour.BuildServer.11-28-2007.07-24-PM.trace.csv.req",
"bs39":	"/mnt/raid5/trace/MS-production/BuildServer/Traces/24.hour.BuildServer.11-28-2007.07-39-PM.trace.csv.req",
"dev5.3.7.19":	"/home/bn/python/DevelopmentToolsRelease/Traces/DevDivRelease.03-05-2008.07-19-PM.trace.csv.req",
"dev5.3.11.19":	"/home/bn/python/DevelopmentToolsRelease/Traces/DevDivRelease.03-05-2008.11-19-PM.trace.csv.req",
"live6.31":	"/home/bn/python/LiveMapsBackEnd/Traces/LiveMapsBE.02-21-2008.06-31-PM.trace.csv.csv.req",
"live3.31":	"/home/bn/python/LiveMapsBackEnd/Traces/LiveMapsBE.02-21-2008.03-31-PM.trace.csv.csv.req",
"mfs253": "/home/bn/python/MSNStorageFileServer/Traces/MSNFS.2008-03-10.02-53.trace.csv.csv.req",
"mfs101": "/home/bn/python/MSNStorageFileServer/Traces/MSNFS.2008-03-10.01-01.trace.csv.csv.req",
"msc116": "/home/bn/python/MSNStorageCFS/Traces/CFS.2008-03-10.01-16.trace.csv.csv.req",
"msc651": "/home/bn/python/MSNStorageCFS/Traces/CFS.2008-03-10.06-51.trace.csv.csv.req",
"dad807": "/home/bn/python/DisplayAdsDataServer/Traces/DisplayAdsDataServer.2008-03-08.08-07.trace.csv.csv.req",
"dap812": "/home/bn/python/DisplayAdsPayload/Traces/DisplayAdsPayload.2008-03-08.08-12.trace.csv.csv.req",
}



def getPath(traceID, typeID):
	if typeID == "home":
		return pathDictHome + traceID + ".csv.req"
	if typeID == "cam":
		return pathDirCam + traceID + ".csv.req"
	if typeID == "production":
		return pathDict[traceID]
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

def load_file(traceID, typeID, alg):
	readReq = 0
	# print(traceID)
	size = math.ceil(SIZERATE*uclnDict[traceID])
	ssd = alg(size)
	fin = open(getPath(traceID, typeID), 'r', encoding='utf-8', errors='ignore')
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


def load_file_mt(traceID, typeID):
	readReq = 0
	size = math.ceil(SIZERATE*uclnDict[traceID])
	ssd = mts_cache_algorithm.MT(size)
	hisDict = mts_cache_algorithm.HistoryDict()
	PERIODLEN = size
	throt = int(0.1*size)
	potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
	fin = open(getPath(traceID, typeID), 'r', encoding='utf-8', errors='ignore')
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


def load_file_mt_time(traceID, typeID):
	readReq = 0
	size = math.ceil(SIZERATE*uclnDict[traceID])
	ssd = mts_cache_algorithm.MTtime(size)
	hisDict = mts_cache_algorithm.HistoryDict()
	PERIODLEN = size
	throt = int(0.1*size)
	potentialDict = mts_cache_algorithm.PLFU(PERIODLEN * PERIODNUM)
	fin = open(getPath(traceID, typeID), 'r', encoding='utf-8', errors='ignore')
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
# load_file(sys.argv[1], sys.argv[2], mts_cache_algorithm.LRU)
# end = time.clock()
# print("consumed ", end-start, "s")

# start = time.clock()
# load_file(sys.argv[1], sys.argv[2], mts_cache_algorithm.SieveStore)
# end = time.clock()
# print("consumed ", end-start, "s")

start = time.clock()
load_file_mt(sys.argv[1], sys.argv[2])
end = time.clock()
print("consumed ", end-start, "s")

# start = time.clock()
# load_file_mt_time(sys.argv[1])
# end = time.clock()
# print("consumed ", end-start, "s")