# mts

这个项目是论文MacroTrend用到的代码，基本原理是通过时间窗口观测数据的长期热度趋势，只缓存长期热数据，从而大幅降低缓存写入量但命中率降低很少


最重要的file是mts_alg_core.py和mts_cache_algorithm.py
mts_alg_core.py是用来模拟SSD缓存流程，跑实验的入口文件
mts_cache_algorithm.py实现了LRU/LFU/PLRU/PLFU/ARC/SieveStore等算法
原始图的experiment部分的overall和不同size都是用mts_alg_core跑出来的
配置时调用的具体参数可以在数据部分找到

cambridge.py （parse_fb.py可能和cambridge.py是同一个文件）
将Cambridge trace原始的csv文件转化为req文件
1. 过滤了原始文件信息，只留下Blockid和访问类型(read/write)
2. 将原始访问统一切割为4K

cut.sh
有个别过大文件，如usr_1，提取前500MB，usr_10是用cut.sh处理cambridge.py生成的usr_1.csv.req得到的

handle_production.py
功能类似cambridge.py，只是处理production trace

mts_alg_analysis.py/mts_get_global_distribution.py/mts_local_write_efficiency.py
粗看结构类似mts_four_dimension.py，是对cache算法获得的结果进行分析的代码，无法确定是否用于论文

mts_data_quality.py
没有把结果输出到log文件中，可能是中间想获得一些对trace了解编写的code

python.sh
并行跑mts_alg_core.py的命令行代码

mts_trace_analysis.py 
没有check，猜测这是生成论文Trace Analysis for LRU and LFU图的代码
感觉这个file更像生成Trace Analysis的代码，里面的trace名都是websearch

mts_four_dimension.py
生成论文四象限和globa rank结果的代码

mts_ta.py
基于trace文件生成一个统计信息，没啥用

缺失code
1. 图3时空图（不会再次生成，且代码很简单，就是生成一个灰度图）
2. Fig. 4和Fig. 6两个统计图可能是

