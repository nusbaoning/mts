import mts_cache_algorithm
import operator 
import time
import sys
trace = open("trace.result", "a")
# def load_file(filename, alg, periodSize=10**5, throt=500, watch=1, predict=5):
# 	i = 0
# 	readReq = 0
# 	period = 1
# 	status = "watch"
# 	watchDict = {}
# 	predictDict = {}
# 	ssd = alg(throt)
# 	fin = open(filename, 'r', encoding='utf-8', errors='ignore')
# 	lines = fin.readlines()
# 	lineNum = len(lines)
# 	print(filename, alg, periodSize, throt, watch, predict, file=trace)
	
# 	for line in lines:
# 		i += 1
# 		# print(readReq, period, watchDict, predictDict)
# 		items = line.split(' ')
# 		reqtype = int(items[0])
# 		block = int(items[2])

# 		if reqtype == 1:
# 			continue

# 		readReq += 1
# 		if status == "watch":
# 			ssd.update_cache(block)
# 			watchDict = recordReq(block, watchDict)
# 		else:
# 			predictDict = recordReq(block, predictDict)

# 		if readReq >= periodSize:
# 			# print("period increase", readReq, period)
# 			readReq = 0
# 			period += 1
# 			if status == "watch" and (period%(watch+predict)) > watch:
# 				status = "predict"
# 			elif status == "predict" and (period%(watch+predict)) == 1:
# 				outputResult(watchDict, predictDict, ssd, period-1)
# 				print(i, "************************************", file=trace)
# 				status = "watch"
# 				watchDict = {}
# 				predictDict = {}
# 				ssd = alg(throt)
# 			elif status == "predict":
# 				outputResult(watchDict, predictDict, ssd, period-1)
# 				predictDict = {}

# 	fin.close()

def init_predictSize(throt):
	predictSize = 100
	while predictSize < throt:
		predictSize = predictSize * 10
	return predictSize

def load_file_time_window(filename, alg, periodSize=10**5, throt=500):
	i = 0
	readReq = 0
	period = 1
	status = "watch"
	watchDict = {}
	predictDict = {}
	predictSize = init_predictSize(throt)
	ssd = alg(throt)
	fin = open(filename, 'r', encoding='utf-8', errors='ignore')
	lines = fin.readlines()
	lineNum = len(lines)
	print(filename, alg, periodSize, throt, file=trace)
	
	for line in lines:
		i += 1
		# print(readReq, period, watchDict, predictDict)
		items = line.split(' ')
		reqtype = int(items[0])
		block = int(items[2])

		if reqtype == 1:
			continue

		readReq += 1
		if status == "watch":
			ssd.update_cache(block)
			watchDict = recordReq(block, watchDict)
		else:
			predictDict = recordReq(block, predictDict)

		if readReq >= periodSize and status == "watch":
			# print("period increase", readReq, period)
			readReq = 0
			period += 1
			status = "predict"
		elif status == "predict" and readReq >= predictSize:
				outputResult(watchDict, predictDict, ssd, predictSize)
				if predictSize >= periodSize:
					print(i, "************************************", file=trace)
					readReq = 0
					period += 1
					status = "watch"
					watchDict = {}
					predictDict = {}
					ssd = alg(throt)
					predictSize = init_predictSize(throt)
				else:
					predictSize = 10*predictSize


	fin.close()

def recordReq(block, blockDict):
	if block in blockDict:
		blockDict[block] += 1
	else:
		blockDict[block] = 1
	return blockDict

def outputResult(watchDict, predictDict, ssd, period):
	ssdBlocks = list(ssd.get_top_n(len(ssd)))
	# print(ssdBlocks)
	# print("watchdict", watchDict)
	# print("predictdict", predictDict)
	req = 0
	for block in ssdBlocks:
		if block in predictDict:
			req += predictDict[block]


	l = list(predictDict.items())        
	l.sort(key=operator.itemgetter(1), reverse=True)
	i = 0
	j = 0
	reqIdeal = 0
	while i<len(ssd) and j<len(l):
		if l[j][0] in watchDict:
			reqIdeal += l[j][1]
			i+=1
			j+=1
		else:
			j+=1
	# print(watchDict)
	# print(predictDict)
	if reqIdeal != 0:		
		ratio = round(100*req/reqIdeal, 2)
		print(period, ratio, "%", req, reqIdeal, file=trace)
	else:
		print(period, req, reqIdeal, file=trace)

    

# load_file("/home/trace/spc-financial-150w-4K.req", mts_cache_algorithm.LRU, periodSize=50000, throt=10)
# load_file("/home/trace/spc-financial-150w-4K.req", mts_cache_algorithm.LFU, periodSize=50000, throt=10)
# load_file("/home/trace/spc-websearch1-500w-4K.req", mts_cache_algorithm.LRU, periodSize = 100000, throt=100)
# load_file("/home/trace/spc-websearch1-500w-4K.req", mts_cache_algorithm.LFU, periodSize = 100000, throt=100)
load_file_time_window("/home/trace/spc-websearch1-500w-4K.req", mts_cache_algorithm.LRU, periodSize = 10000, throt=100)
load_file_time_window("/home/trace/spc-websearch1-500w-4K.req", mts_cache_algorithm.LFU, periodSize = 10000, throt=100)
# load_file_time_window("/home/trace/spc-websearch1-500w-4K.req", mts_cache_algorithm.LRU, periodSize = 1000000, throt=100)
# load_file_time_window("/home/trace/spc-websearch1-500w-4K.req", mts_cache_algorithm.LFU, periodSize = 1000000, throt=100)
# load_file("/home/trace/metanode-hive-select-std.req", mts_cache_algorithm.LRU, periodSize=10000, throt=10)
# load_file("/home/trace/metanode-hive-select-std.req", mts_cache_algorithm.LFU, periodSize=10000, throt=10)
# load_file("/home/trace/metanode-hive-aggregation-std.req", mts_cache_algorithm.LRU, periodSize=10000, throt=10)
# load_file("/home/trace/metanode-hive-aggregation-std.req", mts_cache_algorithm.LFU, periodSize=10000, throt=10)

# load_file_time_window("trace.req", mts_cache_algorithm.LRU, periodSize=100, throt=1)
trace.close()
print("finished")