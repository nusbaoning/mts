# -*- coding: utf-8 -*-
# author Bao Ning
''' 
input : .req file
function : block is identified by original block id + update times
output : a ranklist of traces, the request lists in time windows of each blocks
# 
'''
import time
import traceback
from operator import itemgetter

TIME_WINDOW = 10**5
RANK = True
FILEPATH = "/mnt/raid5/zf/"


period = 0

reqdict = {}
def updateReqDict(key):
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
def testReqDict():
    global period
    print("******************")
    print("start test req dict")
    print(reqdict)
    for _ in range(1,10):
        updateReqDict((10,1))
    print(reqdict)
    period += 3
    for _ in range(1,10):
        updateReqDict((10,1))
    period += 3
    for _ in range(1,10):
        updateReqDict((10,2))
    period += 3
    for _ in range(1,10):
        updateReqDict((10,2))
    print(reqdict)
def outputReqDict(filename):
    fout = open(filename, "w")
    for key in reqdict.keys():
        block, write = key
        reqlist = reqdict[key]
        present = 0
        print(block, write, sep = ",", end = ",", file=fout)
        for reqitem in reqlist:
            time, reqnum = reqitem
            if time-present-1==0:
                print(reqnum, end=",", file=fout)
            else:
                print(",".join(["0"]*(time-present-1)), reqnum, sep = ",", end = ",", file=fout)
            present = time
        print(file=fout)

rankdict = {}
def updateRankDict(key):
    global rankdict
    if key in rankdict:
        rankdict[key] += 1
    else:
        rankdict[key] = 1

def sortRankDict():
    ranklist = []
    for key in rankdict.keys():
        reqnum = rankdict[key]
        ranklist.append((key, reqnum))
    ranklist.sort(key=itemgetter(1), reverse=True) 
    return ranklist

def outputRankList(filename, ranklist):
    fout = open(filename, "w")
    rank = 1
    for item in ranklist:
        key, acc = item
        block, write = key
        print("%d,%d,%d,%d" % (block, write, rank, acc), file=fout)
        rank+=1
    fout.close()



def testRankDict():
    print("******************")
    print("start test rankdict")
    print(rankdict)
    for _ in range(1,10):
        updateRankDict((1,2))
    for _ in range(1,20):
        updateRankDict((1,0))
    for _ in range(1,5):
        updateRankDict((3,2))
    print(rankdict)
    print(sortRankDict())


writedict = {}
def getWriteTime(block):
    if block in writedict:
        return writedict[block]
    else:
        return 0
def updateWriteTime(block):
    global writedict
    if block in writedict:
        writedict[block]+=1
    else:
        writedict[block]=1
def testdict():
    print(writedict)
    print(getWriteTime(1))
    updateWriteTime(1)
    updateWriteTime(1)
    print(writedict)
    print(getWriteTime(1))
    updateWriteTime(2)
    print(writedict)

def printstate():
    print("write dict is")
    print(writedict)
    print("req dict is")
    print(reqdict)


def loadfile(filename, rankfile, reqfile):
    i = 0
    global period
    try:
        fin = open(filename, 'r', encoding='utf-8', errors='ignore')
        for line in fin.readlines():
            if i % TIME_WINDOW == 0:
                print(period, " finished")
                period+=1
            i+=1
            if line[-1] == "\n":
                line = line[0:-1]
            items = line.split(' ')
            reqtype = int(items[0])
            block = int(items[2])
            if reqtype == 0:
                key = (block, getWriteTime(block))
                if RANK:
                    updateRankDict(key)
                updateReqDict(key)
            else:
                updateWriteTime(block)
                continue
    except Exception as e:
        print (traceback.print_exc())
        print (traceback.format_exc())
    else:
        pass
    finally:
        fin.close()
        if RANK:
            ranklist = sortRankDict()
            outputRankList(rankfile, ranklist)
        outputReqDict(reqfile)

def testloadfile():
    loadfile(FILEPATH+tracefile)
    printstate()

def clear_state():
    global period, reqdict, writedict, rankdict
    period = 0
    reqdict = writedict = rankdict = {}

filelist = ["usr_0.csv.req", "proj_3.csv.req", "src2_1.csv.req"]
for file in filelist:
    print(file)
    loadfile(FILEPATH + file, FILEPATH + "ranklist_" + file, FILEPATH + "req_" + file)
    clear_state()