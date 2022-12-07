import mts_cache_algorithm
import operator 
import time
import sys


TIME_WINDOW = 10**4
readReq = 0
reqdict = {}
ssd = None
period = 0
logFile = open("log", "a")
s = time.time()
ucln = 0

def init():
    global readReq, reqdict, ssd, period
    period = 0
    readReq = 0
    reqdict = {}
    ssd = None
    ucln = 0

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
    percent = 0
    for line in lines:
        i += 1

        if readReq % TIME_WINDOW == 0:     
            # print(readReq, period, ssd.period)             
            presentPercent = int(100*i/lineNum)
            if presentPercent >= percent+5:
                e = time.time()
                print(presentPercent, "%", (e-s), "s consumed")
                s = e
                percent = presentPercent

        if line[-1] == "\n":
            line = line[0:-1]
        items = line.split(' ')
        reqtype = int(items[0])
        block = int(items[2])
        if reqtype == 0:
            readReq += 1            
            period = ssd.period
            if period == -1:
                ssd.update_cache(block)                          
            elif period in range(start, end):
                ssd.update_cache(block)
            elif period >= end:
                ssd.access_data()   
            update_req_dict(block)
        else:
            if period in range(start, end):
                ssd.delete_cache(block)
    fin.close()

def simulator(filename):
    global ssd, readReq, s
    # try:
    fin = open(filename, 'r', encoding='utf-8', errors='ignore')
    lines = fin.readlines()
    lineNum = len(lines)
    i = 0
    percent = 0
    for line in lines:
        i += 1
        if readReq % TIME_WINDOW == 0:                  
            presentPercent = int(100*i/lineNum)
            if presentPercent >= percent+5:
                e = time.time()
                print(presentPercent, "%", (e-s), "s consumed")
                s = e
                percent = presentPercent
            
        if line[-1] == "\n":
            line = line[0:-1]
        items = line.split(' ')
        reqtype = int(items[0])
        block = int(items[2])
        if reqtype == 0:
            readReq += 1
            ssd.is_hit(block)
            ssd.update_cache(block)
        else:
            ssd.delete_cache(block)
    fin.close()


# return the request of block in [start, end)
def get_req(block, start, end):
    if block not in reqdict:
        return 0
    l = reqdict[block]    
    r = 0
    for item in l:
        per,req = item
        if per >= end:
            break
        if per < start:
            continue
        r += req
    return r


# original version of 10 windows and get data quality
# '''
# return a dict [(key, rank)]
# scope = "global" / (start, end)
# test finished
# '''
# def cal_rank_dict(scope):
#     rd = {}
#     if scope == "global":
#         for key in reqdict.keys():
#             l = reqdict[key]
#             rd[key] = sum(i for _, i in l)
#     else:
#         start, end = scope
#         for key in reqdict.keys():
#             l = reqdict[key]
#             rd[key] = 0
#             for item in l:
#                 per,req = item
#                 if per >= end:
#                     break
#                 if per < start:
#                     continue
#                 rd[key] += req
#             # if rd[key] == 0:
#             #     del rd[key]
#     # print(rd)
#     l = list(rd.items())        
#     l.sort(key=operator.itemgetter(1), reverse=True)
#     # print("sorted line", l, file=sys.stdout)
#     # print("line76", l)
#     i = 0
#     pre = -1
#     # the version for a list that the number of a specific value is counted
#     # j = 1
#     # for key,req in l:        
#     #     if pre == req:
#     #         j += 1
#     #     else:
#     #         print(req, i)
#     #         pre = req
#     #         i += j
#     #         j = 1
#     #     rd[key] = i
#     # pure req rank version
    
#     for key,req in l:        
#         if pre == req:
#             pass
#         else:
#             pre = req
#             i += 1
#         rd[key] = i
#     dq = [0]*10
#     for key,_ in l:                
#         dq[int(10*rd[key]/(i+1))] += 1
#     print(dq)
#     print(dq, file=logFile)
#     # print("max rank = ", i)
#     # print("max index = ", int(10*i/len(rd)))
#     # print("rankdict", rd, file=sys.stdout)
#     return (rd, i)

# def get_data_quality(number, scope):
#     l = ssd.get_top_n(number)
#     rd,maxRank = cal_rank_dict(scope)
#     dq = [0]*10
#     for item in l:
#         rank = rd[item]
#         dq[int(10*rank/(maxRank+1))] += 1
#     print(scope, dq)
#     print(scope, dq, file=logFile)

def get_ucln():
    global ucln
    ucln = len(reqdict)
    print("ucln", ucln)

def get_data_quality(start, interval):
    end = start + interval
    while end < period:
        print(start, end)
        cal_data(start, end)
        start = end
        end += interval

def cal_data(start, end):
    l = []
    d = {}
    for block in reqdict.keys():
        req = get_req(block, start, end)
        if req > 0:
            d[block] = req
    l = list(d.items())
    l.sort(key=operator.itemgetter(1), reverse=True)
    loc = min(int(0.01*ucln), len(l)-1)
    print("1%", loc, l[loc])
    _, req1 = l[loc]
    loc = min(int(0.1*ucln), len(l)-1)
    print("10%", loc, l[loc])
    _, req10 = l[loc]
    print("medium", len(l))
    ssdL = ssd.get_top_n(ssd.size)
    print(len(ssdL))
    resultL = [0]*4
    for block in ssdL:
        if block not in d:
            resultL[-1] += 1
        elif d[block] >= req1:
            resultL[0] += 1
        elif d[block] >= req10:
            resultL[1] += 1
        else:
            resultL[2] += 1
    print(resultL)

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

print("version 2.1.1")
periodSign = [True] * 2
algL = [mts_cache_algorithm.PLFU, mts_cache_algorithm.LRU]
for i in range(0, len(algL)):
    start = time.time()
    init()
    ssdSize = 10 ** 4
    if periodSign[i]:
        ssd = mts_cache_algorithm.Period(size = ssdSize, alg = algL[i])
    else:
        ssd = algL[i](ssdSize)
    print(ssd.size)
    load_file("D:/Chai/MTS/data/usr_0.csv.req", 1, 11)
    end = time.time()
    print("load file consumed", end-start, "s")
    get_ucln()
    print("period is", period)
    get_data_quality(11, 30)

# periodSign = [True] * 2
# algL = [mts_cache_algorithm.PLFU, mts_cache_algorithm.LRU]
# for i in range(0, len(algL)):
#     start = time.time()
#     init()
#     ssdSize = 10 ** 5
#     if periodSign[i]:
#         ssd = mts_cache_algorithm.Period(size = ssdSize, alg = algL[i])
#     else:
#         ssd = algL[i](ssdSize)
#     simulator("D:/Chai/MTS/data/usr_0.csv.req")
#     ssd.print_sample()
#     print(100.0 * ssd.hit / readReq, "%")
#     end = time.time()
#     print("consumed", end-start, "s")


