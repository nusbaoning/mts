import sys
import os
import time




log = "/home/bn/data/metadata.csv"
logFile = open(log, "a")

def handle_csv(fileid, filename):
    block_size = 4096
    flag=False
    readcount=0
    writecount=0   
    readsize = 0
    writesize = 0 
    outname = filename +'.req'
    count = 0
    totalDict = {}
    readDict = {}
    writeDict = {}
    lba=[[sys.maxsize,0], [sys.maxsize,0], [sys.maxsize,0]]
    infile = open(filename, 'r', encoding='utf-8', errors='ignore')
    outfile = open(outname, 'w')

    for line in infile.readlines():
        count += 1
        line = line.strip().split(',')
        block_id = int((float(line[4]))/block_size)
        block_end = int((float(line[4])+float(line[5])-1)/block_size)
        if count % 100000 == 0:
            print(count)
        if line[3]=='Write':
            rw = 1
            writecount += 1
            writesize+=block_end-block_id+1
        elif line[3]=='Read':
            rw = 0
            readcount+=1
            readsize+=block_end-block_id+1
        else:
            rw = 2
        if lba[2][0] > block_id:
            lba[2][0] = block_id
        if lba[2][1] < block_end:
            lba[2][1] = block_end
        if lba[rw][0] > block_id:
            lba[rw][0] = block_id
        if lba[rw][1] < block_end:
            lba[rw][1] = block_end
        for i in range(block_id,block_end+1):
            print('{0} {1} {2}'.format(rw,line[2],i),file=outfile)
            totalDict[i] = True
            
            if rw == 0:
                readDict[i] = True
            elif rw == 1:
                writeDict[i] = True

    print("read write", readcount, writecount, readcount/writecount, readsize, writesize, readsize/writesize, sep=',')
    print("ucln", len(totalDict), len(readDict), len(writeDict), 
        lba[2][1]-lba[2][0], lba[0][1]-lba[0][0], lba[1][1]-lba[1][0], sep=',')
    print(fileid, readcount+writecount, readcount, writecount, round(readcount/writecount, 2), 
        readsize+writesize, readsize, writesize, round(readsize/writesize, 2), 
        len(totalDict), len(readDict), len(writeDict), 
        lba[2][1]-lba[2][0], lba[0][1]-lba[0][0], lba[1][1]-lba[1][0], sep=',', file=logFile)
    infile.close()
    outfile.close()

l = ["rsrch_0", "src2_0", "stg_0", "ts_0", "wdev_0", "web_0"]
for i in l:
    print(i)
    start = time.clock()
    handle_csv(i, "/mnt/raid5/trace/MS-Cambridge/" + i + ".csv")            
    end = time.clock()
    print("consumed ", end-start, "s")
logFile.close()                   
                 
  







