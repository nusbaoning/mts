import sys
import time
import collections
import operator 

PERIODNUM = 10
PERIODLEN = 10 ** 4


class Period(object):
    """docstring for Period"""


    # O(1)
    def __init__(self, size, alg, sleepStart = 51, sleepInterval = 30, throt = 1000):
        self.period = -1
        self.req = 0
        self.nextUpdatePeriod = -1

        self.sleepStart = sleepStart
        self.sleepInterval = sleepInterval
        self.alg = alg
        self.throt = throt
        self.size = size

        self.ssd = alg(size)

        self.hisDict = HistoryDict()

        self.state = "warm"
        
        self.init_potential_dict()
    # O(1)
    def is_hit(self, blockID):
        self.ssd.is_hit(blockID)

    def get_top_n(self, num):
        return self.ssd.get_top_n(num)

    def init_potential_dict(self):
        if self.alg == LRU:
            self.potentialDict = self.alg(int(self.throt * 1.1))
        elif self.alg == MT:
            self.potentialDict = LFU(self.throt)
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
    # pLRU O(throt)
    # pLFU n=max(periodlen*periodnum,ssd size) O(n)
    # MT n = (2*periodlen*periodnum), (max items in record dict)
    # O(n) + O(sizelogsize)
    def update_cache(self, blockID):
        # warm up state
        if self.state == "warm":
            self.ssd.update_cache(blockID)
            if self.ssd.update >= self.ssd.size:
                self.state = "learn"
                self.period = 1
                self.nextUpdatePeriod = 1
                self.periodRecord = True
            return

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
                    self.ssd.update_cache_k(self.throt, self.potentialDict)
                # elif alg == MT:
                #     self.hisDict = self.ssd.update_cache_k(self.throt, 
                #         self.potentialDict, self.hisDict, self.period)
                else: #PLFU
                    self.ssd.update_cache_k(self.throt, self.potentialDict, self.hisDict, self.period)
                
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


    def update_cache(self, key):
        # First, see if any value is stored under 'key' in the cache already.
        # If so we are going to replace that value with the new one.
        if key in self.ssd:
            # Lookup the node
            node = self.ssd[key]
            # Update the list ordering.
            self.mtf(node)
            self.head = node
            return

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

        # If the node already contains something we need to remove the old
        # key from the dictionary.
        if not node.empty:
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
        
        if size > self.listSize:
            self.add_tail_node(size - self.listSize)
        elif size < self.listSize:
            self.remove_tail_node(self.listSize - size)
        return self.listSize

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
        assert self.listSize > n
        for i in range(n):
            node = self.head.prev
            if not node.empty:
                del self.ssd[node.key]
            # Splice the tail node out of the list
            self.head.prev = node.prev
            node.prev.next = self.head
        self.listSize -= n

    def get_top_n(self, number):
        node = self.head
        l = []
        for i in range(0, number):
            l.append(node.key)
            node = node.next
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



class LFU(CacheAlgorithm):
    """docstring for LFU"""
    def __init__(self, size): 
        super().__init__()
        self.size = size
        self.ssd = {}
        self.victims = collections.deque()
        self.minreq = 1
        self.sorttime = 0
    def is_hit(self, key):        
        if key in self.ssd:
            super().is_hit()
            return True
        return False

    def update_cache(self, key):
        if key in self.ssd:            
            if self.ssd[key] == self.minreq:
                try:
                    self.victims.remove(key)
                except Exception as e:
                    pass
            self.ssd[key] += 1
            return
        if self.minreq > 1:
            # self.update_victim(vk)
            return
        super().update_cache()    
        if len(self.ssd) < self.size:
            self.ssd[key] = 1
            return
        vk = self.get_victim()        
        self.delete_cache(vk)
        self.ssd[key] = 1
        # self.update_victim(key)

    def get_victim(self):
        if len(self.victims) > 0:
            return self.victims.pop()
        else:
            self.update_victim()
            return self.victims.pop()

    def update_victim(self):
        l = list(self.ssd.items())        
        l.sort(key=operator.itemgetter(1))
        self.sorttime += 1        
        _, self.minreq = l[0]
        for i in range(0,int(0.2*len(self.ssd))):
            key, req = l[i]
            if req > self.minreq:
                break
            self.victims.append(key)
    
    def delete_cache(self, key):
        if key not in self.ssd:
            return
        del(self.ssd[key])

    def get_top_n(self, number):
        l = list(self.ssd.items())        
        l.sort(key=operator.itemgetter(1), reverse=True)
        return (list(i for i,_ in l[0:number]))

    def print_sample(self):
        print("print LFU ssd")
        if len(self.ssd) <= 100:
            for key in self.ssd.keys():
                print(key, self.ssd[key])
        print("hit", self.hit)
        print("write", self.update)


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
            # print("evictnum", evictNum)
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
        print("this function")
        # print(len(list(self.ssd.keys())[0:num]))
        result = list(self.ssd.keys())
        return result
        
class MT(CacheAlgorithm):
    """docstring for MT"""
    def __init__(self, arg):
        super(MT, self).__init__()
        self.arg = arg
        



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
    print(mydict.get_history_data(1, 15))
    print(mydict.get_history_data(2,15))
    print(mydict.get_history_data(1,20))
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

