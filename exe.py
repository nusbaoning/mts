import mts_cache_algorithm
import operator 
import time
import sys
import math
import os

#traces1 = ["as1-4K", "as2-4K"]
#traces2 = []

traces1 = ["as1-4K", "as2-4K", "filebench-netsfs", "filebench-randomfileaccess", "spc-financial-150w-4K", "spc-websearch1-500w-4K", "spc-websearch2-470w-4K", "production-adServer-1-4K", "production-adServer-2-4K", "production-adServer-3-4K", "production-build00-1-4K", "production-build00-2-4K", "production-LiveMap-Backend-4K", "production-MSN-CFS-4K", "production-MSN-FS-4k"]

traces2 = ["hm_0", "mds_0", "mds_1", "prn_0", "prn_1", "proj_0", "proj_1", "proj_2", "proj_3", "proj_4", "prxy_0", "prxy_1", "rsrch_0", "rsrch_1", "rsrch_2", "src1_0", "src1_1", "src1_2", "src2_0", "src2_1", "src2_2", "stg_0", "stg_1", "ts_0", "usr_0", "usr_1", "usr_2", "wdev_0", "wdev_1", "wdev_2", "wdev_3", "web_0", "web_1", "web_2", "web_3"]

for trace in traces1:
    os.system("python trace_stat.py " + "/home/trace/" + trace + ".req > " + trace + ".result")

for trace in traces2:
    os.system("python trace_stat.py " + "/home/trace/MS-Cambridge/" + trace + ".csv.req > " + trace + ".result")
