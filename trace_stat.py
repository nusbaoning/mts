import mts_cache_algorithm
import operator 
import time
import sys
import math


TIME_WINDOW = 10**4
readReq = 0
writeReq = 0
readset = set()
writeset = set()

bandset = set()
tmpbandset = set()
bandsum = 0
bandcount = 0

reqdict = {}
ssd = None
period = 0
logFile = open("log", "a")
s = time.time()
ucln = 0


def get_band_num(blkid):
    band_size_num = 19
    num_each_size = math.ceil(5*1024*1024/27) // band_size_num
    BNDSZ = 9*1024  # in 4KB-block
    i = 0
    size = 0 
    total_size = 0
    for i in range(0, band_size_num):
        size = BNDSZ / 2 + i * 256
        if total_size + size * num_each_size > blkid:
            return math.ceil(num_each_size * i + (blkid - total_size) // size)
        total_size += size * num_each_size

    return blkid // BNDSZ


def get_band_size(bandid):
    band_size_num = 19
    num_each_size = math.ceil(5*1024*1024/27) // band_size_num
    bandsize = 9*1024//2 + math.ceil(bandid/num_each_size)*(1024//4)
    if bandsize > 9*1024:
        bandsize = 9*1024
    return bandsize 


def get_all_band_size():
    global bandset
    size = 0
    for bandid in bandset:
        size += get_band_size(bandid)
    return size


def load_file(filename, fifo_size):
    global readReq, writeReq, readset, writeset, bandset, tmpbandset, bandsum, bandcount, s
    readReq = 0
    writeReq = 0
    readset = set()
    writeset = set()
    bandset = set()
    tmpbandset = set()
    bandsum = 0
    bandcount = 0
    # try:
    fin = open(filename, 'r', encoding='utf-8', errors='ignore')
    lines = fin.readlines()
    lineNum = len(lines)
    print("reqCount = ", lineNum) 
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
            readset.add(block)
        else:
            writeReq += 1
            writeset.add(block)
            #bandid = block//4608
            bandid = get_band_num(block)
            bandset.add(bandid)
            tmpbandset.add(bandid)
            if writeReq % fifo_size == fifo_size-1:
                # print("tmpbandset size = ", len(tmpbandset))
                bandsum += len(tmpbandset)
                bandcount += 1
                tmpbandset.clear()
       
    fin.close()
    print("read req count = ", readReq)
    print("write req count = ", writeReq)
    print("read set = ", len(readset))
    print("write set = ", len(writeset))
    print("global band count = ", len(bandset))
    if bandcount > 0:
        print("average band count per FIFO = ", bandsum/bandcount)

# traces = ["mds_0", "mds_1", "src2_1", "proj_2", "proj_3", "proj_4", "prn_0", "usr_0", "usr_1", "usr_2", "hm_0", "proj_0", "prn_1", "prxy_0", "rsrch_0", "rsrch_1", "rsrch_2", "src1_1", "stg_0", "stg_1", "ts_0", "wdev_0", "wdev_1", "wdev_2", "wdev_3", "web_0", "web_1", "web_2", "web_3", "proj_1"]

#traces = ["src2_0", "src2_2"]

# traces = ["as1-4K", "as2-4K", "filebench-netsfs", "filebench-randomfileaccess", "metanode-hive-join"]
# traces = ["spc-financial-150w-4K", "spc-websearch1-500w-4K", "spc-websearch2-470w-4K"]

#traces = ["production-adServer-1-4K", "production-adServer-2-4K", "production-adServer-3-4K", "production-build00-1-4K", "production-build00-2-4K", "production-LiveMap-Backend-4K", "production-MSN-CFS-4K", "production-MSN-FS-4k"]

#blkid = int(sys.argv[0])
#print(sys.argv[1], "'s band id = ", get_band_num(int(sys.argv[1])))


traces = [sys.argv[1]]
print("version 2.7")
for tracename in traces:
    print("Processing trace: ", tracename)
    load_file(tracename, 1000)
    #fifo_size = math.ceil(len(bandset)*4608/250)
    fifo_size = math.ceil(get_all_band_size()/250)
    #fifo_size_another = math.ceil(len(writeset)/250)
    print("-- fifo size = ", fifo_size)
    load_file(tracename, fifo_size)


