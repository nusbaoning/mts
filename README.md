# mts

这个项目是论文MacroTrend用到的代码，基本原理是通过时间窗口观测数据的长期热度趋势，只缓存长期热数据，从而大幅降低缓存写入量但命中率降低很少


最重要的file是mts_alg_core.py和mts_cache_algorithm.py
mts_alg_core.py是用来模拟SSD缓存流程，跑实验的入口文件
mts_cache_algorithm.py实现了LRU/LFU/PLRU/PLFU/ARC/SieveStore等算法
原始图的
