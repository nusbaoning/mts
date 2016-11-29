import mts_cache_algorithm
import operator 
import time

TIME_WINDOW = 10 ** 4

readReq = 0
reqdict = {}
period = 0
sign = False
ssd = None

def init():
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
    global period, ssd, readReq, sign, reqdict
    # try:
    fin = open(filename, 'r', encoding='utf-8', errors='ignore')
    for line in fin.readlines():
        if readReq % TIME_WINDOW == 0 and (not sign):
            print(period, " period finished")
            period+=1
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
            ssd.delete_cache(block)
    fin.close()

'''
return a list [(key, rank)]
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
                if per > end:
                    break
                if per < start:
                    continue
                rd[key] += req

    l = list(rd.items())        
    l.sort(key=operator.itemgetter(1), reverse=True)
    # print("line76", l)
    i = 0
    j = 1
    pre = 0
    for key,req in l:        
        if pre == req:
            j += 1
        else:
            pre = req
            i += j
            j = 1
        rd[key] = i
    # print("max rank = ", i)
    # print("max index = ", int(10*i/len(rd)))
    return (rd, i)

def get_data_quality(number, scope):
    l = ssd.get_top_n(number)
    rd,maxRank = cal_rank_dict(scope)
    dq = [0]*10
    for item in l:
        rank = rd[item]
        dq[int(10*rank/(maxRank+1))] += 1
    print(dq)

s = time.time()
ssd = mts_cache_algorithm.LFU(10000)
load_file("D:/Chai/MTS/data/usr_0.csv.req", 1, 11)
e = time.time()
print("lfu load file:", e - s, "s comsued")
get_data_quality(5000, "global")
s = e
e = time.time()
print("global data quality:", e-s, "s comsued")
get_data_quality(5000, (12, 12+30))
s = e
e = time.time()
print("partial data quality:", e-s, "s comsued")
