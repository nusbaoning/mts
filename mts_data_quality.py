import mts_cache_algorithm
import operator 
import time
import sys

TIME_WINDOW = 10 ** 4

readReq = 0
reqdict = {}
period = 0
sign = False
ssd = None
logFile = open("log", "a")
s = time.time()

def init():
    global readReq, reqdict, period, sign, ssd
    readReq = 0
    reqdict = {}
    period = 0
    sign = False
    ssd = None

def update_req_dict(key):
    global reqdict
    if key in reqdict:
        reqlist = reqdict[key]
        lastperiod, req = reqlist[-1]
        if lastperiod == period:
            reqlist[-1] = (lastperiod, req+1)
        else:
            reqlist.append((period,1))
    else:
        reqdict[key] = [(period,1)]

def load_file(filename, start, end):
    global period, ssd, readReq, sign, reqdict, s
    # try:
    fin = open(filename, 'r', encoding='utf-8', errors='ignore')
    lines = fin.readlines()
    lineNum = len(lines)
    i = 0
    for line in lines:
        i += 1
        if readReq % TIME_WINDOW == 0 and (not sign):            
            period+=1
            if period % 10 == 0:
                e = time.time()
                print(period, " period finished", int(100*i/lineNum), "%", (e-s), "time consumed")
                s = e
            sign = True
        if line[-1] == "\n":
            line = line[0:-1]
        items = line.split(' ')
        reqtype = int(items[0])
        block = int(items[2])
        if reqtype == 0:
            readReq += 1
            sign = False
            if period in range(start, end+1):
                ssd.update_cache(block)
            update_req_dict(block)
        else:
            if period in range(start, end+1):
                ssd.delete_cache(block)
    fin.close()

'''
return a dict [(key, rank)]
scope = "global" / (start, end)
test finished
'''
def cal_rank_dict(scope):
    rd = {}
    if scope == "global":
        for key in reqdict.keys():
            l = reqdict[key]
            rd[key] = sum(i for _, i in l)
    else:
        start, end = scope
        for key in reqdict.keys():
            l = reqdict[key]
            rd[key] = 0
            for item in l:
                per,req = item
                if per >= end:
                    break
                if per < start:
                    continue
                rd[key] += req
            # if rd[key] == 0:
            #     del rd[key]
    # print(rd)
    l = list(rd.items())        
    l.sort(key=operator.itemgetter(1), reverse=True)
    # print("sorted line", l, file=sys.stdout)
    # print("line76", l)
    i = 0
    pre = -1
    # the version for a list that the number of a specific value is counted
    # j = 1
    # for key,req in l:        
    #     if pre == req:
    #         j += 1
    #     else:
    #         print(req, i)
    #         pre = req
    #         i += j
    #         j = 1
    #     rd[key] = i
    # pure req rank version
    
    for key,req in l:        
        if pre == req:
            pass
        else:
            pre = req
            i += 1
        rd[key] = i
    dq = [0]*10
    for key,_ in l:                
        dq[int(10*rd[key]/(i+1))] += 1
    print(dq)
    print(dq, file=logFile)
    # print("max rank = ", i)
    # print("max index = ", int(10*i/len(rd)))
    # print("rankdict", rd, file=sys.stdout)
    return (rd, i)

def get_data_quality(number, scope):
    l = ssd.get_top_n(number)
    rd,maxRank = cal_rank_dict(scope)
    dq = [0]*10
    for item in l:
        rank = rd[item]
        dq[int(10*rank/(maxRank+1))] += 1
    print(scope, dq)
    print(scope, dq, file=logFile)

def generic_test_trace():
    trace = open("trace.req", "w")
    for i in range(0,100):
        print("0 0", i, file=trace)
    for i in range(0,50):
        print("0 0 1", file=trace)
        print("0 0 2", file=trace)
    for i in range(0,30):
        for j in range(3,6):
            print("0 0", j, file=trace)
    trace.close()

print("version 1.2")
algL = [mts_cache_algorithm.LRU, mts_cache_algorithm.LFU]
partialL = [10, 30, 100]
for alg in algL:
    init()
    ssd = alg(10000)
    load_file("D:/Chai/MTS/data/usr_0.csv.req", 1, 11)
    print(alg, file = logFile)
    e = time.time()
    print("load file:", e - s, "s comsued")
    # get_data_quality(5000, "global")
    # s = e
    # e = time.time()
    # print("global data quality:", e-s, "s comsued")
    for parLen in partialL:
        get_data_quality(5000, (12, 12+parLen))
    
logFile.close()

