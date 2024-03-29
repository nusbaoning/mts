#coding=utf-8
from __future__ import print_function
import sys
import time
import collections
import operator 
import random


PERIODNUM = 10
PERIODLEN = 10 ** 5

'''
普通缓存算法所需接口
__init__(self, size) 初始化
delete_cache(self, block) 删除block
is_hit(self, block) 判断是否命中，更新命中数据
update_cache(self, block) 表示对当前cache来说，遇到了一次对Block的访问，
                          该如何更新、是否需要踢出其他块由具体缓存算法决定。
'''

# PdLRU alg
class Period(object):
    """docstring for Period"""
    # O(1)
    def __init__(self, size, throt, alg, warmup = True, sleepStart = 1, sleepInterval = 10):
        self.period = 1
        self.req = 0
        self.nextUpdatePeriod = 1
        self.warmup = warmup
        self.sleepStart = sleepStart
        self.sleepInterval = sleepInterval
        self.alg = alg
        self.throt = throt
        self.size = size

        self.ssd = alg(size)

        self.hisDict = HistoryDict()
        if self.warmup:
            self.state = "warm"
        elif sleepStart > 1:
            # print("no warm up")
            self.state = "learn"
        else:
            self.state = "sleep"
        
        self.periodRecord = True
        self.init_potential_dict()
    # O(1)
    def is_hit(self, blockID):
        return self.ssd.is_hit(blockID)

    def get_top_n(self, num):
        return self.ssd.get_top_n(num)

    def init_potential_dict(self):
        if self.alg == LRU:
            self.potentialDict = self.alg(int(self.throt * 1.1))
        elif self.alg == MT:
            self.potentialDict = PLFU(PERIODLEN * PERIODNUM)
        else: #PLFU
            self.potentialDict = PLFU(PERIODLEN * PERIODNUM)

    def access_data(self):
        self.req += 1
        if self.req >= PERIODLEN:
            self.req = 0
            self.period += 1
    # warm up : dict set, average O(1)
    # record : dict get & set, average O(1)
    # period update : 
    # PLRU O(throt)
    # PLFU n=max(periodlen*periodnum,ssd size) O(n)
    # MT n = (2*periodlen*periodnum), (max items in record dict)
    # O(n) + O(sizelogsize)
    def update_cache(self, blockID):
        # warm up state
        result=None
        if self.state == "warm":
            result =  self.ssd.update_cache(blockID)
            if self.ssd.update >= self.ssd.size:
                if self.sleepStart > 1:
                    self.state = "learn"
                    self.period = 1
                    self.nextUpdatePeriod = 1
                    self.periodRecord = True
                else:
                    self.state = "sleep"
                    self.period = 1
                    self.nextUpdatePeriod = self.sleepInterval
                    if self.sleepInterval <= PERIODNUM:
                        self.periodRecord = True
                    else:
                        self.periodRecord = False
            return result

        self.req += 1
        # check whether record is needed        
        if self.periodRecord and self.alg != LRU:
            self.hisDict.access_data(blockID, self.period)
        if blockID not in self.ssd.ssd:
            self.potentialDict.update_cache(blockID)
        # check whether period finishes
        if self.req >= PERIODLEN:                       
            # update needed?
            if self.period == self.nextUpdatePeriod: 
                # print("test update", self.period, self.ssd.update, len(self.potentialDict.ssd))  
                if self.alg == LRU:
                   result =  self.ssd.update_cache_k(self.throt, self.potentialDict)
                # elif alg == MT:
                #     self.hisDict = self.ssd.update_cache_k(self.throt, 
                #         self.potentialDict, self.hisDict, self.period)
                else: #PLFU
                    result = self.ssd.update_cache_k(self.throt, self.potentialDict, self.hisDict, self.period)
                
                self.init_potential_dict()

                # compute next update period
                # sleep state
                if self.period+1 >= self.sleepStart:
                    self.state = "sleep"
                    self.nextUpdatePeriod = self.period + self.sleepInterval
                    # check whether the period should be recorded

                    # if period = 1 and next update period = 10, 
                    # when 10th period finishes, ssd will be updated
                    # 1st to 10th period should be recorded
                    # when nextUpdatePeriod = 11, fails
        
                    if self.nextUpdatePeriod - self.period <= PERIODNUM:
                        # print(self.period, "record period")
                        self.periodRecord = True
                    # no need to record
                    # empty the history dict
                    else:
                        # print(self.period, "not record period")
                        self.periodRecord = False
                        self.hisDict = HistoryDict()
                # learn state
                else:
                    self.nextUpdatePeriod += 1
                    self.periodRecord = True

            # check history record
            else:
                if self.nextUpdatePeriod - self.period <= PERIODNUM:
                    self.periodRecord = True        
            self.req = 0 
            self.period += 1
        return result


    def delete_cache(self, blockID):
        self.ssd.delete_cache(blockID)
        self.potentialDict.delete_cache(blockID)

    def print_sample(self):
        self.ssd.print_sample()
        self.hit = self.ssd.hit


        
class HistoryDict(object):    
    """docstring for HistoryDict"""
    def __init__(self):
        self.d = {}

    def access_data_time(self, blockID, period, reqCount):
        if blockID in self.d:
            (pointer, accL, lastAccP, lastAccT) = self.d[blockID]
            if lastAccP == period:
                accL[pointer] += 1
                self.d[blockID] = (pointer, accL, lastAccP, reqCount)
            else:
                if period - lastAccP >= PERIODNUM:
                    accL = [0]*PERIODNUM
                    accL[0] = 1
                    self.d[blockID] = (0, accL, period, reqCount)
                else:
                    i = 0
                    for p in range(lastAccP + 1, period):
                        i += 1
                        accL[(pointer + p) % PERIODNUM] = 0
                    pointer = (pointer + i + 1) % PERIODNUM
                    accL[pointer] = 1
                    self.d[blockID] = (pointer, accL, period, reqCount)
        else:
            accL = [0]*PERIODNUM
            accL[0] = 1
            self.d[blockID] = (0, accL, period, reqCount)

    def access_data(self, blockID, period):
        if blockID in self.d:
            (pointer, accL, lastAccT) = self.d[blockID]
            if lastAccT == period:
                accL[pointer] += 1
            else:
                if period - lastAccT >= PERIODNUM:
                    accL = [0]*PERIODNUM
                    accL[0] = 1
                    self.d[blockID] = (0, accL, period)
                else:
                    i = 0
                    for p in range(lastAccT + 1, period):
                        i += 1
                        accL[(pointer + p) % PERIODNUM] = 0
                    pointer = (pointer + i + 1) % PERIODNUM
                    accL[pointer] = 1
                    self.d[blockID] = (pointer, accL, period)
        else:
            accL = [0]*PERIODNUM
            accL[0] = 1
            self.d[blockID] = (0, accL, period)

    # return a list with PERIODNUM requests
    # corresponding to period [now, now-1, ... now-PERIODNUM+1]
    def get_history_data(self, blockID, period):
        if blockID in self.d:
            (pointer, accL, lastAccT) = self.d[blockID]
            if lastAccT == period:
                l = [0] * PERIODNUM
                for i in range(0,PERIODNUM):
                    l[i] = accL[(pointer + i) % PERIODNUM]
                return l
            elif period - lastAccT >= PERIODNUM:
                del self.d[blockID]
                return None
            else:
                l = [0] * PERIODNUM
                for i in range(max(0,period-9), lastAccT+1):
                    # print("test", i, period - i, ((pointer + (PERIODNUM - lastAccT + i)) % PERIODNUM))
                    l[period - i] = accL[(pointer + (PERIODNUM - lastAccT + i)) % PERIODNUM]
                return l                
        else:
            return None
    def get_history_data_time(self, blockID, period):
        if blockID in self.d:
            (pointer, accL, lastAccT, lct) = self.d[blockID]
            if lastAccT == period:
                l = [0] * PERIODNUM
                for i in range(0,PERIODNUM):
                    l[i] = accL[(pointer + i) % PERIODNUM]
                return (l,lct)
            elif period - lastAccT >= PERIODNUM:
                del self.d[blockID]
                return None
            else:
                l = [0] * PERIODNUM
                for i in range(max(0,period-9), lastAccT+1):
                    # print("test", i, period - i, ((pointer + (PERIODNUM - lastAccT + i)) % PERIODNUM))
                    l[period - i] = accL[(pointer + (PERIODNUM - lastAccT + i)) % PERIODNUM]
                return (l,lct)                
        else:
            return None
class CacheAlgorithm(object):

    """docstring for CacheAlgorithm"""
    def __init__(self):
        self.hit = 0
        self.update = 0
    def is_hit(self):
        self.hit += 1
    def update_cache(self):
        self.update += 1
    def delete_cache(self, key):
        pass
    '''
    get the top n blockids from ssd
    '''
    def get_top_n(self, number):
        pass

class MyNode(object):
    """docstring for MyNode"""
    def __init__(self):
        self.empty = True

class LRU(CacheAlgorithm):
    """docstring for LRU"""
    def __init__(self, size):
        super().__init__()
        self.size = size
        self.ssd = {}
        self.head = MyNode()
        self.head.next = self.head
        self.head.prev = self.head
        self.listSize = 1
        # Adjust the size
        self.change_size(size)
    def __len__(self):
        return len(self.ssd)

    def clear(self):
        for node in self.dli():
            node.empty = True
        self.ssd.clear()


    def is_hit(self, key):
        if key in self.ssd:
            super().is_hit()
            return True
        return False


    def update_cache_four(self, key):
        self.update_cache(key)
        return key

    def update_cache(self, key):
        # First, see if any value is stored under 'key' in the cache already.
        # If so we are going to replace that value with the new one.
        if key in self.ssd:
            # Lookup the node
            node = self.ssd[key]
            # Update the list ordering.
            self.mtf(node)
            self.head = node
            return None

        # Ok, no value is currently stored under 'key' in the cache. We need
        # to choose a node to place the new item in. There are two cases. If
        # the cache is full some item will have to be pushed out of the
        # cache. We want to choose the node with the least recently used
        # item. This is the node at the tail of the list. If the cache is not
        # full we want to choose a node that is empty. Because of the way the
        # list is managed, the empty nodes are always together at the tail
        # end of the list. Thus, in either case, by chooseing the node at the
        # tail of the list our conditions are satisfied.

        # Since the list is circular, the tail node directly preceeds the
        # 'head' node.
        super().update_cache()
        node = self.head.prev
        delkey = None
        # If the node already contains something we need to remove the old
        # key from the dictionary.
        if not node.empty:
            delkey = node.key
            del self.ssd[node.key]

        # Place the new key and value in the node
        node.empty = False
        node.key = key
        
        # Add the node to the dictionary under the new key.
        self.ssd[key] = node

        # We need to move the node to the head of the list. The node is the
        # tail node, so it directly preceeds the head node due to the list
        # being circular. Therefore, the ordering is already correct, we just
        # need to adjust the 'head' variable.
        self.head = node
        return delkey


    def delete_cache(self, key):

        # Lookup the node, then remove it from the hash ssd.
        if key not in self.ssd:
            return
        node = self.ssd[key]
        del self.ssd[key]

        node.empty = True

        

        # Because this node is now empty we want to reuse it before any
        # non-empty node. To do that we want to move it to the tail of the
        # list. We move it so that it directly preceeds the 'head' node. This
        # makes it the tail node. The 'head' is then adjusted. This
        # adjustment ensures correctness even for the case where the 'node'
        # is the 'head' node.
        self.mtf(node)
        self.head = node.next

    

    # This method adjusts the ordering of the doubly linked list so that
    # 'node' directly precedes the 'head' node. Because of the order of
    # operations, if 'node' already directly precedes the 'head' node or if
    # 'node' is the 'head' node the order of the list will be unchanged.
    def mtf(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

        node.prev = self.head.prev
        node.next = self.head.prev.next

        node.next.prev = node
        node.prev.next = node

    # This method returns an iterator that iterates over the non-empty nodes
    # in the doubly linked list in order from the most recently to the least
    # recently used.
    def dli(self):
        node = self.head
        for i in range(len(self.ssd)):
            yield node
            node = node.next

    def change_size(self, size):
        evictList = None
        if size > self.listSize:
            self.add_tail_node(size - self.listSize)
        elif size < self.listSize:
            evictList = self.remove_tail_node(self.listSize - size)
        return evictList

    # Increases the size of the cache by inserting n empty nodes at the tail
    # of the list.
    def add_tail_node(self, n):
        for i in range(n):
            node = MyNode()
            node.next = self.head
            node.prev = self.head.prev

            self.head.prev.next = node
            self.head.prev = node

        self.listSize += n

    # Decreases the size of the list by removing n nodes from the tail of the
    # list.
    def remove_tail_node(self, n):
        assert self.listSize >= n
        l = []
        for i in range(n):
            node = self.head.prev
            if not node.empty:
                del self.ssd[node.key]
                l.append(node.key)
            # Splice the tail node out of the list
            self.head.prev = node.prev
            node.prev.next = self.head
        self.listSize -= n
        return l

    def get_top_n(self, number):
        node = self.head
        l = []
        for i in range(0, min(number, len(self.ssd))):
            l.append(node.key)
            node = node.next
        # print("debug", len(l), l==None)
        return l

    def print_sample(self):
        print("print LRU ssd")
        if len(self.ssd) <= 100:            
            node = self.head
            for i in range(len(self.ssd)):
                print(node.key, end=",")
                node = node.next        
            print()
        print("hit", self.hit)
        print("write", self.update)

    def update_cache_k(self, throt, potentialDict):

        node = potentialDict.head
        # print("potential dict")
        # print(len(potentialDict.ssd))
        # potentialDict.print_sample()
        throt = min(throt, len(potentialDict.ssd))
        for i in range(1, throt):
            node = node.next
        for i in range(0, throt):
            self.update_cache(node.key)
            # print(node.key)
            node = node.prev

class SieveStore(CacheAlgorithm):
    """docstring for SieveStore"""
    def __init__(self, size):
        super().__init__()
        self.size = size
        self.ssd = {}
        self.lru = LRU(size)

    def is_hit(self, key):
        hit = self.lru.is_hit(key)
        if hit:
            super().is_hit()
        return hit
    
    def update_cache(self, key):
        hit = self.lru.is_hit(key)
        if hit:
            self.lru.update_cache(key)
            return
        if key in self.ssd:
            acc = self.ssd[key]
            if acc >= 6:
                super().update_cache()
                self.lru.update_cache(key)
                self.ssd[key] = 0
            else:
                self.ssd[key] = acc+1
        else:
            self.ssd[key] = 1

    def delete_cache(self, key):
        self.lru.delete_cache(key)

# class LFU(CacheAlgorithm):
#     """docstring for LFU"""
#     def __init__(self, size): 
#         super().__init__()
#         self.size = size
#         self.ssd = {}
#         self.victims = collections.deque()
#         self.minreq = 1
#         self.sorttime = 0

#     def __len__(self):
#         return len(self.ssd)

#     def is_hit(self, key):        
#         if key in self.ssd:
#             super().is_hit()
#             return True
#         return False

#     def update_cache(self, key):
#         if key in self.ssd:            
#             if self.ssd[key] == self.minreq:
#                 try:
#                     self.victims.remove(key)
#                 except Exception as e:
#                     pass
#             self.ssd[key] += 1
#             return
#         if self.minreq > 1:
#             # self.update_victim(vk)
#             return
#         super().update_cache()    
#         if len(self.ssd) < self.size:
#             self.ssd[key] = 1
#             return
#         vk = self.get_victim()        
#         self.delete_cache(vk)
#         self.ssd[key] = 1
#         # self.update_victim(key)

#     def get_victim(self):
#         if len(self.victims) > 0:
#             return self.victims.pop()
#         else:
#             self.update_victim()
#             return self.victims.pop()

#     def update_victim(self):
#         l = list(self.ssd.items())        
#         l.sort(key=operator.itemgetter(1))
#         self.sorttime += 1        
#         _, self.minreq = l[0]
#         for i in range(0,int(0.2*len(self.ssd))):
#             key, req = l[i]
#             if req > self.minreq:
#                 break
#             self.victims.append(key)
    
#     def delete_cache(self, key):
#         if key not in self.ssd:
#             return
#         del(self.ssd[key])

#     def get_top_n(self, number):
#         l = list(self.ssd.items())        
#         l.sort(key=operator.itemgetter(1), reverse=True)
#         return (list(i for i,_ in l[0:number]))

#     def print_sample(self):
#         print("print LFU ssd")
#         if len(self.ssd) <= 100:
#             for key in self.ssd.keys():
#                 print(key, self.ssd[key])
#         print("hit", self.hit)
#         print("write", self.update)

class CacheNode(object):
    def __init__(self, key, value, freq_node, pre, nxt):
        self.key = key
        self.value = value
        self.freq_node = freq_node
        self.pre = pre # previous CacheNode
        self.nxt = nxt # next CacheNode

    def free_myself(self):
        if self.freq_node.cache_head == self.freq_node.cache_tail:
            self.freq_node.cache_head = self.freq_node.cache_tail = None
        elif self.freq_node.cache_head == self:
            self.nxt.pre = None
            self.freq_node.cache_head = self.nxt
        elif self.freq_node.cache_tail == self:
            self.pre.nxt = None
            self.freq_node.cache_tail = self.pre
        else:
            self.pre.nxt = self.nxt
            self.nxt.pre = self.pre

        self.pre = None
        self.nxt = None
        self.freq_node = None

class FreqNode(object):
    def __init__(self, freq, pre, nxt):
        self.freq = freq
        self.pre = pre # previous FreqNode
        self.nxt = nxt # next FreqNode
        self.cache_head = None # CacheNode head under this FreqNode
        self.cache_tail = None # CacheNode tail under this FreqNode

    def count_caches(self):
        if self.cache_head is None and self.cache_tail is None:
            return 0
        elif self.cache_head == self.cache_tail:
            return 1
        else:
            return '2+'

    def remove(self):
        if self.pre is not None:
            self.pre.nxt = self.nxt
        if self.nxt is not None:
            self.nxt.pre = self.pre

        pre = self.pre
        nxt = self.nxt
        self.pre = self.nxt = self.cache_head = self.cache_tail = None

        return (pre, nxt)

    # 去掉第一个结点
    def pop_head_cache(self):
        if self.cache_head is None and self.cache_tail is None:
            return None
        elif self.cache_head == self.cache_tail:
            cache_head = self.cache_head
            self.cache_head = self.cache_tail = None
            return cache_head
        else:
            cache_head = self.cache_head
            self.cache_head.nxt.pre = None
            self.cache_head = self.cache_head.nxt
            return cache_head

    def append_cache_to_tail(self, cache_node):
        cache_node.freq_node = self

        if self.cache_head is None and self.cache_tail is None:
            self.cache_head = self.cache_tail = cache_node
        else:
            cache_node.pre = self.cache_tail
            cache_node.nxt = None
            self.cache_tail.nxt = cache_node
            self.cache_tail = cache_node

    def insert_after_me(self, freq_node):
        freq_node.pre = self
        freq_node.nxt = self.nxt

        if self.nxt is not None:
            self.nxt.pre = freq_node
        
        self.nxt = freq_node

    def insert_before_me(self, freq_node):
        if self.pre is not None:
            self.pre.nxt = freq_node
        
        freq_node.pre = self.pre
        freq_node.nxt = self
        self.pre = freq_node

# LFU中的结构是
# FreqNode是访问次数为freq-1(即freq从0开始，但应该没影响)的块按照最近访问从远到近排，
# 即新来的块加在队尾cache_tail，踢出的块在队头cache_head
# FreqNode本身连接顺序也是从低到高排，访问次数少的在前头，访问次数多的在后头
class LFU(CacheAlgorithm):

    def __init__(self, size):
        super().__init__()
        self.cache = {} # {key: cache_node}
        self.size = size
        self.freq_link_head = None
    
    def __len__(self):
        return len(self.cache)

    def update_cache(self, key):
        self.set(key, True)

    # def update_cache_k(self, throt, potentialDict):

    #     node = potentialDict.head
    #     # print("potential dict")
    #     # print(len(potentialDict.ssd))
    #     # potentialDict.print_sample()
    #     throt = min(throt, len(potentialDict.ssd))
    #     for i in range(1, throt):
    #         node = node.next
    #     for i in range(0, throt):
    #         self.update_cache(node.key)
    #         # print(node.key)
    #         node = node.prev

    def is_hit(self, key):
        if key in self.cache:
            super().is_hit()
            return True
        return False

    def delete_cache(self, key):
        if key not in self.cache:
            return
        # print(key)
        # print(self.cache)

        cache_node = self.cache.pop(key)
        freq_node = cache_node.freq_node
        cache_node.free_myself()
        if freq_node.count_caches() == 0:
            if self.freq_link_head == freq_node:
                self.freq_link_head = freq_node.nxt

            freq_node.remove()

    # def get(self, key):
    #     if key in self.cache:
    #         cache_node = self.cache[key]
    #         freq_node = cache_node.freq_node
    #         value = cache_node.value

    #         self.move_forward(cache_node, freq_node)

    #         return value
    #     else:
    #         return -1

    def set(self, key, value):
        if self.size <= 0:
            return -1
        
        if key not in self.cache:
            if len(self.cache) >= self.size:
                self.dump_cache()
            super().update_cache()
            self.create_cache(key, value)
        else:
            cache_node = self.cache[key]
            freq_node = cache_node.freq_node
            cache_node.value = value

            self.move_forward(cache_node, freq_node)

    # 把freq_node中已有的cache_node放到freq+1的freqnode中
    def move_forward(self, cache_node, freq_node):
        if freq_node.nxt is None or freq_node.nxt.freq != freq_node.freq + 1:
            target_freq_node = FreqNode(freq_node.freq + 1, None, None)
            target_empty = True
        else:
            target_freq_node = freq_node.nxt
            target_empty = False
        
        cache_node.free_myself()
        target_freq_node.append_cache_to_tail(cache_node)

        if target_empty:
            freq_node.insert_after_me(target_freq_node)


        if freq_node.count_caches() == 0:
            if self.freq_link_head == freq_node:
                self.freq_link_head = target_freq_node

            freq_node.remove()

    def dump_cache(self):
        head_freq_node = self.freq_link_head
        self.cache.pop(head_freq_node.cache_head.key)
        assert head_freq_node.pop_head_cache()!=None

        if head_freq_node.count_caches() == 0:
            self.freq_link_head = head_freq_node.nxt
            head_freq_node.remove()

    def create_cache(self, key, value):
        cache_node = CacheNode(key, value, None, None, None)
        self.cache[key] = cache_node
        
        if self.freq_link_head is None or self.freq_link_head.freq != 0:
            new_freq_node = FreqNode(0, None, None)
            new_freq_node.append_cache_to_tail(cache_node)

            if self.freq_link_head is not None:
                self.freq_link_head.insert_before_me(new_freq_node)
            
            self.freq_link_head = new_freq_node
        else:
            self.freq_link_head.append_cache_to_tail(cache_node)

    def print_cache(self):
        print(self.cache)

class PLFU(CacheAlgorithm):
    """docstring for PLFU"""
    def __init__(self, size):
        super().__init__()
        self.size = size
        self.ssd = {}

    def is_hit(self, key):
        if key in self.ssd:
            super().is_hit()
            return True
        return False   

    # attention : only called in warm state
    # no check of size
    def update_cache(self, blockID):
        if blockID not in self.ssd:            
            self.ssd[blockID] = 1
            super().update_cache()

    def delete_cache(self, key):
        if key not in self.ssd:
            return
        del(self.ssd[key])

    def update_cache_k(self, throt, potentialDict, hisDict, period):
        # get evict items from ssd and do eviction
        if self.size - len(self.ssd) < throt:
            evictNum = min(throt, len(potentialDict.ssd)) - (self.size - len(self.ssd))
            # print("evictNum", evictNum)
            # calculate requests of ssd data and record to a dict based on request numbers
            d = {}
            for blockID in self.ssd.keys():
                rl = hisDict.get_history_data(blockID, period)
                if rl == None:
                    s = 0
                else:
                    s = sum(rl)
                if s not in d:
                    d[s] = [blockID]
                else:
                    d[s].append(blockID)
                # print("test hisDict, return list & sum", blockID, rl, s)

            # directly delete evictNum data with least requests
            keys = list(d.keys())
            keys.sort()
            

            for key in keys:
                for i in range(0, len(d[key])):
                    if evictNum == 0:
                        break
                    del(self.ssd[d[key][i]])
                    evictNum -= 1
                if evictNum == 0:
                    break 

        # print("potential dict", potentialDict.ssd.keys())
        # calculate sum for potential data
        d = {}
        for blockID in potentialDict.ssd.keys():
            l = hisDict.get_history_data(blockID, period)
            if l == None:
                pass
            else:
                s = sum(l)
                if s not in d:
                    d[s] = [blockID]
                else:
                    d[s].append(blockID)

        # get top throt data from potential list and add to ssd
        # if period == 80:
        #     print(throt)


        keys = list(d.keys())
        keys.sort(reverse=True)
        # if period == 80:
        #     print(len(keys))
        for key in keys:
            # if period == 80:
            #     print(key)
            for i in range(0, len(d[key])):
                if throt == 0:
                    break
                # if period == 80:
                #     print("before update", self.update, len(self.ssd))
                self.update_cache(d[key][i])
                # if period == 80:
                #     print("after update", self.update, len(self.ssd))
                throt -= 1
            if throt == 0:
                break 

    def print_sample(self):
        print("print PLFU ssd")
        if len(self.ssd) <= 100:
            print(self.ssd.keys())  
        print("hit", self.hit)
        print("write", self.update)

    # no order in PLFU
    # will only return total ssd
    def get_top_n(self, num):
        # print("this function")
        # print(len(list(self.ssd.keys())[0:num]))
        result = list(self.ssd.keys())
        return result
        
class MT(CacheAlgorithm):
    """docstring for MT"""
    def __init__(self, size, goodReq, goodSum):
        super().__init__()
        self.size = size
        self.ssd = {}
        self.minGoodReq = goodReq
        self.minGoodSum = goodSum

    def __len__(self):
        return len(self.ssd)


    def is_hit(self, key):
        if key in self.ssd:
            super().is_hit()
            return True
        return False   

    # attention : only called in warm state
    # no check of size
    def update_cache(self, blockID):
        if blockID not in self.ssd:            
            self.ssd[blockID] = 1
            super().update_cache()

    def delete_cache(self, blockID):
        if blockID not in self.ssd:
            return
        del(self.ssd[blockID])

    # period is the present finishing period
    # For example, if the 10th period is finished and we want to update cache, period=10
    def update_cache_k(self, throt, potentialDict, hisDict, period):
        # start = time.time()
        # some special case, ssd is very small, possible that all data is hit in one period
        updateNum = min(throt, len(potentialDict.ssd))
        sign = False
        if updateNum <= 0:
            print("update num is 0", throt, len(potentialDict.ssd))
            return (False, None)
        # print("test updateNum = ", updateNum, "len(self.ssd) = ", len(self.ssd), "size =", self.size,
        #     "len(potential)=", len(potentialDict.ssd))

        # special case : all potentials can be updated into ssd
        # rarely occur
        # if len(potentialDict.ssd) + len(self.ssd) <= self.size:
        #     # print("entry here", updateNum + len(self.ssd), self.size)
        #     for blockID in potentialDict.ssd:
        #         self.update_cache(blockID)
        #     return

                
        # get request number for good period
        reqD = {}
        sumL = []
        for blockID in potentialDict.ssd.keys():
            rl = hisDict.get_history_data(blockID, period)
            if rl == None:
                continue
            req = rl[0]
            reqS = sum(rl)
            sumL.append((blockID, reqS))
            if req in reqD:
                reqD[req].append(blockID)
            else:
                reqD[req] = [blockID]
        reqL = list(reqD.keys())
        reqL.sort(reverse=True)
        sumL.sort(key=operator.itemgetter(1), reverse=True)
        # print("test", len(sumL), len(potentialDict.ssd), updateNum)
        _, goodSum = sumL[updateNum-1]
        goodSum = max(goodSum, self.minGoodSum)
        
        # if updateNum <= 1.2 * len(sumL):
        #     goodReq = 2
        # else:
        goodReq = self.minGoodReq
        totalNum = len(potentialDict.ssd)
        for req in reversed(reqL):
            # print(req, len(reqD[req]), num, updateNum)
            if totalNum - len(reqD[req]) < updateNum:
                goodReq = max(req, self.minGoodReq)
                break
            else:
                totalNum -= len(reqD[req])   
        # print("test goodReq", goodReq, goodSum)
        # sys.exit(-1)

        l = [[], [], [], []]
        for blockID,_ in sumL:
            rl = hisDict.get_history_data(blockID, period)
            # no way to get l==None
            gc = get_good_condition(rl, goodReq, goodSum)
            l[gc].append(blockID)
        i = 3
        # print("test potentialDict", len(potentialDict.ssd))
        if len(l[3])>0:
            sign = True
        num = 0
        updateNum = min(updateNum, len(l[1])+len(l[2])+len(l[3]))

        # get evict items from ssd and do eviction
        if self.size - len(self.ssd) < updateNum:
            evictNum = updateNum - (self.size - len(self.ssd))
            # print("test evictNum=", evictNum)
            # calculate requests of ssd data and record to a dict based on request numbers
            evictList = [[], [], [], []]
            for blockID in self.ssd.keys():
                rl = hisDict.get_history_data(blockID, period)
                if rl == None:
                    evictList[0].append((blockID,0))
                else:
                    s = sum(rl)
                    gc = get_good_condition(rl, goodReq, goodSum)
                    evictList[gc].append((blockID,s))
            
            for item in evictList:
                if evictNum <= 0:
                    break
                if len(item) <= evictNum:
                    for blockID,_ in item:
                        self.delete_cache(blockID)
                        evictNum -= 1
                else:
                    item.sort(key=operator.itemgetter(1))
                    for i in range(0,evictNum):
                        blockID, _ = item[i]
                        self.delete_cache(blockID)
                    break

            # print("test ssd evict, size=", len(self.ssd), "分布情况=", len(l[0]), len(l[1]), len(l[2]), len(l[3]))
            
        # print("potential dict", potentialDict.ssd.keys())
        # calculate good conditions for potential data
        i = 3
        updateList = []

        while i >= 0:
            # print(i, updateNum, len(l[i]))
            if updateNum <= 0:
                break
            if len(l[i]) <= updateNum:
                for blockID in l[i]:
                    self.update_cache(blockID)
                    updateNum -= 1
                    updateList.append(blockID)
                i -= 1
            else:
                for j in range(0,updateNum):
                    self.update_cache(l[i][j])
                    updateList.append(l[i][j])
                break
        # print("test ssd update, size=", len(self.ssd), self.update, "分布情况=", len(l[0]), len(l[1]), len(l[2]), len(l[3]))
        if len(l[3])>0:
            sign = True
        return (sign, updateList)
        # end = time.time()
        # print("test update k speed, consumed", end-start)

    def print_sample(self):
        print("print MT ssd")
        print(len(self.ssd))
        # if len(self.ssd) <= 100:
        #     print(self.ssd.keys())  
        print("hit", self.hit)
        print("write", self.update)

    # no order in PLFU
    # will only return total ssd
    def get_top_n(self, num):
        # print("this function")
        # print(len(list(self.ssd.keys())[0:num]))
        result = list(self.ssd.keys())
        return result

class MTtime(CacheAlgorithm):
    """docstring for MT"""
    def __init__(self, size):
        super().__init__()
        self.size = size
        self.ssd = {}
        self.goodReq = 1
        self.goodSum = 1

    def __len__(self):
        return len(self.ssd)


    def is_hit(self, key):
        if key in self.ssd:
            super().is_hit()
            return True
        return False   

    # attention : only called in warm state
    # no check of size
    def update_cache(self, blockID):
        assert self.size > len(self.ssd)
        if blockID not in self.ssd:            
            self.ssd[blockID] = 1
            super().update_cache()

    def delete_cache(self, blockID):
        if blockID not in self.ssd:
            return
        del(self.ssd[blockID])

    # period is the present finishing period
    # For example, if the 10th period is finished and we want to update cache, period=10
    def update_cache_k(self, throt, potentialDict, hisDict, period):
        # start = time.time()

        updateNum = min(throt, len(potentialDict.ssd))
        
        # get evict items from ssd and do eviction
        evictNum = updateNum - (self.size - len(self.ssd))
        # print("test, throt=%d, updateNum=%d, evictNum=%d, size=%d, actual ssd size=%d" % (throt, updateNum, evictNum, self.size, len(self.ssd)))
        # print("goodReq=", self.goodReq, ", goodSum=", self.goodSum)
        if evictNum > 0:
            # calculate requests of ssd data and record to a dict based on request numbers
            l = [[], [], [], []]
            for blockID in self.ssd.keys():
                r = hisDict.get_history_data_time(blockID, period)
                if r == None:
                    l[0].append((blockID,0,0))
                else:
                    rl,lct = r
                    s = sum(rl)
                    gc = get_good_condition(rl, self.goodReq, self.goodSum)
                    l[gc].append((blockID,s,lct))
            # print("test gc", l)
            for item in l:
                # print("test evict", len(item), evictNum, len(self.ssd))
                if evictNum <= 0:
                    break
                if len(item) <= evictNum:
                    for blockID,_,_ in item:
                        self.delete_cache(blockID)
                    evictNum -= len(item)
                else:
                    # item.sort(key=operator.itemgetter(1,2), reverse=True)
                    # the list is sorted first as LFU, then as LRU
                    # let the data with the least req and oldest accessed time first
                    # evict from the head to the tail
                    item.sort(key=lambda l:(l[1],l[2]))
                    # print("test sort", item)
                    for i in range(0,evictNum):
                        blockID, _, _ = item[i]
                        # print(blockID)
                        self.delete_cache(blockID)
                    break

            # print("test ssd evict, size=", len(self.ssd), "分布情况=", len(l[0]), len(l[1]), len(l[2]), len(l[3]))


        sumD = {}    
        reqD = {}
        l = [[], [], [], []]
        totalNum = 0
        for blockID in potentialDict.ssd.keys():
            r = hisDict.get_history_data_time(blockID, period)
            if r==None:
                print("potential bug none")
                continue
            totalNum += 1
            rl, lct = r
            gc = get_good_condition(rl, self.goodReq, self.goodSum)
            dataReq = rl[0]
            dataSum = sum(rl)
            
            update_req_sum(dataReq, reqD)
            update_req_sum(dataSum, sumD)

            l[gc].append((blockID, dataSum, lct))
        self.goodSum = get_good_sum_req(sumD, updateNum, totalNum)
        self.goodReq = get_good_sum_req(reqD, updateNum, totalNum)
        
        l.reverse()
        # print(l)
        for item in l:
            # print("test update", len(item), updateNum, len(self.ssd))
            if updateNum<=0:
                break
            if len(item) < updateNum:
                for blockID,_,_ in item:
                    self.update_cache(blockID)
                updateNum -= len(item)
            else:
                item.sort(key=lambda l:(l[1],l[2]), reverse=True)                    
                for i in range(0,updateNum):
                    blockID, _, _ = item[i]                    
                    self.update_cache(blockID)
                break
        # print("test ssd update, size=", len(self.ssd), "分布情况=", len(l[3]), len(l[2]), len(l[1]), len(l[0]))
    

# ARC的原理
# 管理空间大小为2*SSD size
# 分成四个队列LRU/LFU/ghost LRU/ghost LFU
# 满足LRU+LFU=ghost LRU+LRU=ghost LFU+LFU=size
# 第一次进入SSD的块进LRU
# 在管理空间内hit(包括ghost LRU)进LFU
# ghost LRU命中会导致LRU队列大小增加，ghost LFU命中同理
 

# 实现版本与原设计方案的不同
# 在原有的设计方案中，如果ghost LFU命中，p比LRU队列数量小，但是SSD实际不满的情况下
# 是不会把LRU队列中元素踢出的，要等到SSD满了之后，才会踢出块
# 但在运行中，SSD很快就会填满，ghost LFU命中会踢出一个SSD中的块，就无所谓了

# ghost LFU命中，会引起LFU空间增加，正常来说SSD满的情况下应该踢出LRU的块
# 但是为了实现简便，先执行了踢出操作，再调整队列大小，感觉影响不大

class ARC(CacheAlgorithm):
    def __init__(self, size):
        super().__init__()
        self.size = size
        self.p = int(size/2)
        self.lru = LRU(self.p)
        self.glru = LRU(size-self.p)

        self.lfu = LRU(size-self.p)        
        self.glfu = LRU(self.p)

        self.list = [self.lru, self.glru, self.lfu, self.glfu]

    def delete_cache(self, block):
        for i in self.list:
            i.delete_cache(block)


    def is_hit(self, block):
        if self.lru.is_hit(block):
            super().is_hit()
            return True
        if self.lfu.is_hit(block):
            super().is_hit()
            return True
        return False

    def inner_change_size(self, p):
        
        evictList = self.lru.change_size(int(self.p))
        if evictList:
            for i in evictList:
                self.glru.update_cache(i)
        self.glru.change_size(int(self.size-self.p))
        evictList = self.lfu.change_size(int(self.size-self.p))
        if evictList:
            for i in evictList:
                self.glfu.update_cache(i)
        self.glfu.change_size(int(self.p))

    def update_cache(self, block):
        if self.lru.is_hit(block):
            self.lru.delete_cache(block)
            delkey = self.lfu.update_cache(block)
            if delkey!=None:
                self.glfu.update_cache(delkey)


        elif self.lfu.is_hit(block):
            self.lfu.update_cache(block)

        elif self.glru.is_hit(block):
            # 更新p
            oldp = self.p
            self.p = min(self.p+max(1, 1.0*len(self.glfu)/len(self.glru)) , self.size-1)
            
            # 将块从glru删掉，在lfu中更新
            self.glru.delete_cache(block)
            delkey = self.lfu.update_cache(block)
            if delkey!=None:
                self.glfu.update_cache(delkey)
            super().update_cache()
            return block

            # 更新各个队列大小
            self.inner_change_size(oldp)

        elif self.glfu.is_hit(block):
            # 更新p
            oldp = self.p
            self.p = max(self.p-max(1, 1.0*len(self.glru)/len(self.glfu)) , 1)
            
            # 将块从glfu删掉，在lfu中更新
            self.glfu.delete_cache(block)
            # 更新各个队列大小
            delkey = self.lfu.update_cache(block)
            if delkey!=None:
                self.glfu.update_cache(delkey)
            return block
            super().update_cache()
            self.inner_change_size(oldp) 

            

        else:
            delkey = self.lru.update_cache(block)
            if delkey!=None:
                self.glru.update_cache(delkey)
            super().update_cache()
            return block
        return None

class LARC(CacheAlgorithm):
    """docstring for LARC"""
    def __init__(self, size):
        super().__init__()
        self.size = size
        self.cr = 0.1*size
        self.ssd = LRU(size)
        self.shadow = LRU(int(self.cr))

    def delete_cache(self, block):
        self.ssd.delete_cache(block)
        self.shadow.delete_cache(block)
      
    def warm_up(self, block):
        self.ssd.update_cache(block)
        super().update_cache()

    def update_cache(self, block):
        if self.ssd.is_hit(block):
            self.cr = max(0.1*self.size, self.cr-(1.0*self.size/(self.size-self.cr)))
            self.ssd.update_cache(block)
            return block
            # self.shadow.change_size(int(self.cr))
        else:
            self.cr = min(0.9*self.size, self.cr+1.0*self.size/self.cr)
            if self.shadow.is_hit(block):
                self.shadow.delete_cache(block)
                self.ssd.update_cache(block)
                super().update_cache()
                return block
            else:
                self.shadow.change_size(int(self.cr))
                self.shadow.update_cache(block)
        return None    
        

    def is_hit(self, block):
        if self.ssd.is_hit(block):
            super().is_hit()
            return True
        return False

class SieveStoreOriginal(CacheAlgorithm):
    """docstring for MT"""
    def __init__(self, size, right, t1=9, t2=4):
        super().__init__()
        self.size = size
        self.impt = {}
        self.mpt = {}
        self.right = right        
        self.lru = LRU(size)
        self.t1 = t1
        self.t2 = t2

    def __len__(self):
        return len(self.ssd)

    def is_hit(self, key):
        hit = self.lru.is_hit(key)
        if hit:
            super().is_hit()
        return hit
             
    def update_cache(self, blockID, period):
        hit = self.lru.is_hit(blockID)
        if hit:
            self.lru.update_cache(blockID)
            return None
        key = blockID >> self.right
        acc = seive_acc_pt(key, period, self.impt)
        if acc >= self.t1:
            acc = seive_acc_pt(blockID, period, self.mpt)
            if acc >= self.t2:
                super().update_cache()
                self.lru.update_cache(blockID)
                del self.impt[key]
                del self.mpt[blockID]
                return blockID
            else:
                return None
        else:
            return None
    def delete_cache(self, key):
        self.lru.delete_cache(key)

    def get_top_n(self, num):
        # print("debug", len(self.lru.ssd))
        return self.lru.get_top_n(num)

def seive_acc_pt(key, period, pt):

    if key in pt:
        (pointer, accL, lastPeriod) = pt[key]
        if lastPeriod == period:
            accL[pointer] += 1
            return sum(accL)
        if period - lastPeriod >= PERIODNUM:
            accL = [0]*PERIODNUM
            accL[0] = 1
            pt[key] = (0, accL, period)
            return 1
        i = 0
        for p in range(lastPeriod + 1, period):
            i += 1
            accL[(pointer + p) % PERIODNUM] = 0
        pointer = (pointer + i + 1) % PERIODNUM
        accL[pointer] = 1
        pt[key] = (pointer, accL, period)
        return sum(accL)

    # every case of key in impt return
    # key not in impt
    accL = [0]*PERIODNUM
    accL[0] = 1
    pt[key] = (0, accL, period)
    return 1



    # every case of key in impt return
    # key not in impt
    accL = [0]*PERIODNUM
    accL[0] = 1
    impt[key] = (0, accL, period)
    return 1

    
def update_req_sum(num, d):
    if num not in d:
        d[num] = 1
    else:
        d[num] += 1

def get_good_sum_req(d, num, totalNum):

    if totalNum <= num:
        return 1
    # print(d.keys())
    # print(type(d.keys()))
    # print(list(d.keys()))
    l = list(d.keys())
    l.sort()
    # print(l)
    for item in l:
        if totalNum - d[item] >= num:
            totalNum -= d[item]
            continue
        return item
    
# reqList[0] is the request of the latest period, [-1] is the earliest period
def get_good_condition(reqList, goodReq, goodSum):
    gc = 0
    reqS = sum(reqList)
    if reqS >= goodSum:
        gc += 1
    if get_continuous_good_period(reqList, goodReq) >= 2:
        gc += 1
    if get_good_period(reqList, goodReq) >= 3:
        gc += 1
    return gc

def get_continuous_good_period(reqList, goodReq):
    for i in range(0, len(reqList)):
        if reqList[i] < goodReq:
            break
    return i

def get_good_period(reqList, goodReq):
    i = 0
    for req in reqList:
        if req >= goodReq:
            i+=1
    return i

def test_hisdict_acc():
    mydict = HistoryDict()
    mydict.access_data(0, 1)
    print(mydict.d)
    mydict.access_data(0, 1)
    print(mydict.d)
    mydict.access_data(0, 2)
    print(mydict.d)
    mydict.access_data(0, 5)
    print(mydict.d)
    mydict.access_data(0, 16)
    print(mydict.d)
    mydict.access_data(1, 5)
    print(mydict.d)


def test_plru():
    ssd = Period(alg = LRU, size = 10, throt = 5, sleepStart = 3, sleepInterval = 2)
    period = 1
    for i in range(1,100):
        ssd.update_cache(i)
        if period < ssd.period:
            period = ssd.period
            print(i, ":")   
            ssd.ssd.print_sample()
            print("state", ssd.state)

def test_get_history_data():
    mydict = HistoryDict()
    for i in range(1,10):
        for j in range(0,i):
            mydict.access_data(1, i)
    print(mydict.d[1])
    print(mydict.d)
    print(mydict.get_history_data(1, 15))
    print(mydict.d)
    print(mydict.get_history_data(2,15))
    print(mydict.d)
    print(mydict.get_history_data(1,20))
    print("last", mydict.d)

def test_get_history_data_time():
    mydict = HistoryDict()
    k = 0
    for i in range(1,10):
        for j in range(0,i):
            k += 1
            mydict.access_data_time(1, i, k)
    print(mydict.d[1])
    print(mydict.get_history_data_time(1, 15))
    print(mydict.get_history_data_time(2,15))
    print(mydict.get_history_data_time(1,20))
    print(mydict.d)

def test_plfu():
    
    ssd = Period(alg = PLFU, size = 10, throt = 5, sleepStart = 3, sleepInterval = 2)
    period = 0
    for i in range(0,50):
        for j in range(0, (i % 10 + 1)):
            ssd.update_cache(i)  
        if period < ssd.period:      
            period = ssd.period
            print(i, ":")   
            ssd.ssd.print_sample()
            print("state", ssd.state)

def test_sievestore():
    ssd = SieveStore(2)
    for i in range(0,10):
        ssd.update_cache(1)
        ssd.update_cache(2)
        print(ssd.is_hit(1))
        print(ssd.is_hit(2))
        print(ssd.hit)
        print(ssd.update)
    ssd.delete_cache(1)
    print(ssd.is_hit(1))
# test_sievestore()

def test_mttime_evict():
    ssd = MTtime(5)
    for i in range(1,6):
        ssd.update_cache(i)
    hisDict = HistoryDict()
    potentialDict = PLFU(5)
    l = 0
    for i in range(1,11):
        for j in range(3,6):
            for k in range(1,3):
                l += 1                
                hisDict.access_data_time(j,i,l)
    for i in range(1,11):
        for j in range(6,10):
            potentialDict.update_cache(j)
            for k in range(1,3):
                l += 1                
                hisDict.access_data_time(j,i,l)
    potentialDict.update_cache(9)
    potentialDict.update_cache(10)
    hisDict.access_data_time(9,10,l+1)
    hisDict.access_data_time(9,10,l+2)
    hisDict.access_data_time(10,10,l+3)
    hisDict.access_data_time(3,10,l+4)
    

    print(potentialDict.ssd)
    print(hisDict.d)
    ssd.update_cache_k(3, potentialDict, hisDict, 10)
    print(ssd.ssd)

def test_get_good_req():
    d = {}
    for i in range(1,11):
        for j in range(0,i):
            update_req_sum(i, d)
    print(d)
    # print(get_good_sum_req(d, 5, 3))
    print(get_good_sum_req(d, 15, 55))
    print(get_good_sum_req(d, 27, 55))


def test_arc():
    l = []
    # for i in range(200):
    #     l.append(random.randint(0,19))
    # print(l)

    l = [10, 6, 14, 8, 7, 11, 0, 12, 6, 9, 
    17, 9, 6, 2, 4, 19, 8, 3, 15, 6, 
    12, 6, 12, 13, 5, 1, 19, 16, 5, 2, 
    12, 8, 14, 15, 10, 11, 11, 5, 4, 17, 
    11, 9, 17, 15, 6, 14, 0, 18, 9, 15, 
    5, 6, 2, 2, 2, 4, 3, 6, 10, 19, 
    14, 7, 13, 16, 3, 6, 7, 8, 19, 12, 
    4, 12, 13, 18, 3, 15, 11, 10, 13, 11, 
    4, 7, 11, 19, 6, 11, 18, 11, 6, 1, 
    18, 14, 3, 7, 11, 5, 9, 14, 0, 18, 
    0, 2, 5, 18, 2, 6, 5, 11, 19, 16, 7, 0, 3, 4, 15, 4, 1, 1, 6, 14, 17, 17, 14, 2, 8, 6, 12, 18, 19, 3, 10, 6, 9, 11, 7, 8, 13, 19, 1, 13, 17, 17, 5, 6, 15, 4, 4, 18, 11, 12, 5, 11, 12, 7, 18, 0, 15, 9, 16, 1, 19, 10, 6, 1, 0, 14, 5, 17, 16, 16, 7, 2, 14, 11, 7, 12, 2, 5, 1, 5, 10, 8, 15, 0, 14, 2, 19, 6, 4, 19, 14, 18, 11, 15, 15, 0, 15, 7, 4, 19]
    ssd = ARC(12)
    for i in l:
        print(ssd.hit, ssd.update, ssd.p)
        for j in ssd.glru.dli():
            if not j.empty:
                print(j.key, end=',')
        print(end=';')
        for j in ssd.lru.dli():
            if not j.empty:
                print(j.key, end=',')
        print(end=';')
        for j in ssd.lfu.dli():
            if not j.empty:
                print(j.key, end=',')
        print(end=';')
        for j in ssd.glfu.dli():
            if not j.empty:
                print(j.key, end=',')
        print()
        # for j in ssd.lru.dli():
        #     print(j, end=',')
        hit = ssd.is_hit(i)
        print(hit)
        ssd.update_cache(i)
 
def test_larc():
    l = [0, 5, 15, 8, 14, 16, 3, 16, 4, 1, 8, 10, 1, 
    3, 17, 1, 6, 4, 10, 9, 13, 11, 2, 8, 3, 2, 
    10, 5, 3, 14, 3, 16, 12, 3, 6, 7, 17, 5, 15, 8, 18, 9, 9, 19, 10, 8, 0, 12, 16, 17, 12, 16, 1, 1, 5, 14, 10, 9, 15, 18, 12, 18, 0, 18, 4, 15, 14, 9, 18, 6, 11, 19, 5, 9, 10, 7, 6, 11, 5, 19, 14, 9, 2, 3, 19, 13, 11, 5, 3, 17, 14, 0, 6, 11, 3, 6, 10, 10, 18, 18, 8, 2, 8, 2, 5, 13, 13, 6, 2, 7, 17, 5, 7, 11, 9, 0, 9, 14, 14, 14, 19, 4, 12, 16, 11, 15, 10, 13, 7, 12, 17, 7, 2, 7, 19, 17, 9, 6, 18, 1, 15, 12, 12, 16, 4, 2, 0, 8, 3, 18, 16, 4, 12, 0, 17, 19, 9, 3, 2, 13, 17, 18, 10, 0, 13, 3, 0, 9, 12, 4, 10, 16, 16, 18, 17, 17, 18, 14, 6, 0, 7, 14, 11, 12, 1, 10, 13, 6, 5, 13, 0, 11, 6, 3, 11, 2, 3, 18, 17, 13]
    # for i in range(200):
    #     l.append(random.randint(0,19))
    # print(l)

    ssd = LARC(10)
    
    for i in l:
        print(ssd.hit, ssd.update, ssd.cr)
        ssd.is_hit(i)
        ssd.update_cache(i)
        for j in ssd.ssd.dli():
            if not j.empty:
                print(j.key, end=',')
        print(end=';')
        for j in ssd.shadow.dli():
            if not j.empty:
                print(j.key, end=',')
        print()
    print(ssd.hit, ssd.update, ssd.cr)

# def test_mt():
#     cache = MT(5, )


# test_larc()       

# cache = LFU(3)
# cache.update_cache(1)
# cache.update_cache(1)
# cache.update_cache(2)
# cache.print_cache()
# cache.update_cache(3)
# cache.update_cache(3)
# cache.update_cache(4)
# cache.print_cache()
# cache.delete_cache(1)
# cache.print_cache()
# cache.update_cache(2)
# cache.print_cache()
# cache.update_cache(1)
# cache.print_cache()
