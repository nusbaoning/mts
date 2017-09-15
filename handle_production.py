import math
import sys

reqCount = [0,0]  
reqSize = [0,0]
blockDict = [{}, {}, {}]
lba=[[sys.maxsize,0], [sys.maxsize,0], [sys.maxsize,0]]
blockSize = 4096
log = "/home/bn/data/metadata.csv"
logFile = open(log, "a")

def handle_pro_csv(fileid, filename):
    
    blockCount=0    
    flag=False
    nrline = 0
    i = 0
    global reqCount, reqSize, blockDict, lba
    reqCount = [0,0]  
    reqSize = [0,0]
    blockDict = [{}, {}, {}]
    lba=[[sys.maxsize,0], [sys.maxsize,0], [sys.maxsize,0]]
    maxCount = [0]
    outname = filename +'.req'
    infile = open(filename, 'r', encoding='utf-8', errors='ignore')
    outfile = open(outname, 'w')
    
    for line in infile.readlines():
        nrline += 1
        line = line.strip().replace(' ','').split(',')
        if not flag and line[0] == "EndHeader":
            flag=True
        if flag:
            i+=1
            if line[0]=='DiskWrite':
                rw = 1
                blockID, blockCount = parseLine(line, 5, rw)
                # if blockCount >= 100:
                #     maxCount[0]+=1
                #     maxCount.append(nrline)
                for i in range(blockID,blockID+blockCount):
                    print('{0} {1} {2}'.format(rw,line[8],i),file=outfile)
                    blockDict[rw][i] = True
                    blockDict[2][i] = True
            elif line[0]=='DiskRead':
                rw = 0
                blockID, blockCount = parseLine(line, 5, rw)
                for i in range(blockID,blockID+blockCount):
                    print('{0} {1} {2}'.format(rw,line[8],i),file=outfile)
                    blockDict[rw][i] = True
                    blockDict[2][i] = True
                # print(nrline, "DiskRead", blockID, blockCount)
            elif line[0]=='FileIoWrite':
                rw = 1
                blockID, blockCount = parseLine(line, 7, rw)
                # if blockCount >= 100:
                #     maxCount[0]+=1
                #     maxCount.append(nrline)
                for i in range(blockID,blockID+blockCount):
                    print('{0} {1} {2}'.format(rw,0,i),file=outfile)
                    blockDict[rw][i] = True
                    blockDict[2][i] = True
            elif line[0]=='FileIoRead':
                rw = 0
                blockID, blockCount = parseLine(line, 7, rw)
                for i in range(blockID,blockID+blockCount):
                    print('{0} {1} {2}'.format(rw,0,i),file=outfile)
                    blockDict[rw][i] = True
                    blockDict[2][i] = True
                # print(nrline, "FildRead", blockID, blockCount)
            # if i > 100:
            #     break
    
    
    print("read write", reqCount[0], reqCount[1], reqSize[0], reqSize[1], sep=',')
    # print("read write", reqCount[0], reqCount[1], reqCount[0]/reqCount[1], reqSize[0], reqSize[1], reqSize[0]/reqSize[1], sep=',')
    print("ucln", len(blockDict[2]), len(blockDict[0]), len(blockDict[1]), 
        lba[2][1]-lba[2][0]+1, lba[0][1]-lba[0][0]+1, lba[1][1]-lba[1][0]+1, sep=',')
    print(fileid, reqCount[0]+reqCount[1], reqCount[0], reqCount[1], round(reqCount[0]/reqCount[1], 2), 
        reqSize[0]+reqSize[1], reqSize[0], reqSize[1], round(reqSize[0]/reqSize[1], 2), 
        len(blockDict[2]), len(blockDict[0]), len(blockDict[1]), 
        lba[2][1]-lba[2][0]+1, lba[0][1]-lba[0][0]+1, lba[1][1]-lba[1][0]+1, sep=',', file=logFile)
    # print(maxCount)
    infile.close()
    outfile.close()

def parseLine(line, num, rw):
    global reqCount, reqSize, blockDict, lba
    blockID = int(line[num],16)
    blockID = int(float(blockID)/blockSize)
    blockCount = int(line[num+1],16)
    blockCount = math.ceil(1.0*blockCount/blockSize)
    blockEnd = blockID + blockCount - 1
    reqCount[rw] += 1
    reqSize[rw] += blockCount
    if lba[2][0] > blockID:
        lba[2][0] = blockID
    if lba[2][1] < blockEnd:
        lba[2][1] = blockEnd
    if lba[rw][0] > blockID:
        lba[rw][0] = blockID
    if lba[rw][1] < blockEnd:
        lba[rw][1] = blockEnd

    # print(blockID, blockCount, blockEnd)
    return (blockID,blockCount)

# print(reqCount, reqSize, blockDict, lba)
# handle_pro_csv("buildServer", "/mnt/raid5/trace/MS-production/BuildServer/Traces/24.hour.BuildServer.11-28-2007.07-24-PM.trace.csv")                
handle_pro_csv("dev5.3.11.19", "/home/bn/python/DevelopmentToolsRelease/Traces/DevDivRelease.03-05-2008.11-19-PM.trace.csv")
logFile.close()
                           

