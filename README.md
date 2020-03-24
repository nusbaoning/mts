# mts

这个项目是论文MacroTrend用到的代码，基本原理是通过时间窗口观测数据的长期热度趋势，只缓存长期热数据，从而大幅降低缓存写入量但命中率降低很少

注意：待修改：
目前的mts_four_dimension_bak.py文件的逻辑是ssd.update_block返回更新的单个块或者块列表
除LRU外其他算法运行没问题
但是LRU算法因为ARC被修改为返回被删除块，后续可以考虑在four_dimension中单独调用一个返回删除块的Update函数

最重要的file是mts_alg_core.py和mts_cache_algorithm.py
mts_alg_core.py是用来模拟SSD缓存流程，跑实验的入口文件
mts_cache_algorithm.py实现了LRU/LFU/PLRU/PLFU/ARC/SieveStore等算法

Language: Python3

1. Trace General Information

File: mts_alg_core.py

Description:
Provide functions to run each cache algorithm and collect basic information including hit rate, update.
Function Name Format: **load_file_<alg_name>(traceID, typeID, alg, cache_size/total_size)**

Input: Trace File
Input Path: getPath(traceID, typeID) Get correct filename according to trace type.
pathDirCam = <Cambridge Trace File>

Output: Trace General Information
FileName: logFilename = <Output File>, seperated by comma.
Format: trace,algorithm,ssd size,hit rate,update

这部分其实写的有点问题，有空了改一下
2. Global Rank & Four Dimension
File: mts_four_dimension.py

Global Rank: the global rank of the total access count among all the accessed blocks.

Four Dimension: hotness and updater repeats divide all data blocks into four dimensions.

Method: First, we need to collect static data to get update dict. Second, we rerun the algorithm to get runtime global rand and 4-d data in the cache.

2.1 **load_file_<alg_name>(traceID, typeID, alg)** if <alg_name> is empty, it is LRU.

Description: Every <REQ> request, load_file_<alg_name> invokes ssd_statistics() snapshotting current info.

2.2 **ssd_statistics(traceID, alg, ucln, ssd)**
Description: Collect Global rank and four dimension information.
Parameter: 

a) updateTh, the boundary of the repeat loaded count.
b) reqTh, %5 * ucln, that is to say, we treat top 20% data block as hot blocks.

Output:

四个d代表四个象限，/total是百分比。后面的global rank前一个是rank,后一个是req
traceID, alg, d0, d1 d2, d4, d0/total_d, d1/total_d, d2/total_d, d3/total_d, global_rank(0)/global_rank(2), global_rank(1)/global_rank(2).

3. Cache Algorithm

File: mts_cache_algorithm.py
Description: Implementation of cache algorithms LRU, SeiveStore, PeriodLRU, MT. Invoked by the above two files.
