import mts_cache_algorithm
import operator 
import time
import sys
trace = open("trace.result", "a")
def load_file(filename, alg, periodSize=10**5, throt=500, watch=1, predict=5):
	i = 0
	readReq = 0
	period = 1
	status = "watch"
	watchDict = {}
	predictDict = {}
	ssd = alg(throt)
	fin = open(filename, 'r', encoding='utf-8', errors='ignore')
	lines = fin.readlines()
	lineNum = len(lines)
	
	
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

		if readReq >= periodSize:
			# print("period increase", readReq, period)
			readReq = 0
			period += 1
			if status == "watch" and (period%(watch+predict)) > watch:
				status = "predict"
			elif status == "predict" and (period%(watch+predict)) == 1:
				outputResult(watchDict, predictDict, ssd, period-1)
				print(i, "************************************")
				status = "watch"
				watchDict = {}
				predictDict = {}
				ssd = alg(throt)
			elif status == "predict":
				outputResult(watchDict, predictDict, ssd, period-1)
				predictDict = {}

	fin.close()



def recordReq(block, blockDict):
	if block in blockDict:
		blockDict[block] += 1
	else:
		blockDict[block] = 1
	return blockDict

def outputResult(watchDict, predictDict, ssd, period):
	ssdBlocks = list(ssd.get_top_n(len(ssd)))
	print(ssdBlocks)
	print("watchdict", watchDict)
	print("predictdict", predictDict)
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

    

load_file("/mnt/raid5/zf/usr_0.csv.req", mts_cache_algorithm.LFU)
trace.close()
# load_file("trace.req", mts_cache_algorithm.LRU, periodSize=5, throt=1)