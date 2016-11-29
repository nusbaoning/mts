import sys
import time
import collections
import operator 
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
        for key in self.ssd.keys():
            print(key, end=",")
        print("hit", self.hit)
        print("write", self.update)

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
    
    def delete_cache(self,key):
        if key not in self.ssd:
            return
        del(self.ssd[key])

    def get_top_n(self, number):
        l = list(self.ssd.items())        
        l.sort(key=operator.itemgetter(1), reverse=True)
        return l[0:number]

    def print_sample(self):
        print("print LFU ssd")
        for key in self.ssd.keys():
            print(key, self.ssd[key])
        print("hit", self.hit)
        print("write", self.update)








# ssd = LFU(5)
# ssd.print_sample()
# for i in range(1, 5):
#     print(i)
#     for j in range(1,i+1):  
#         ssd.update_cache(i)
#         ssd.is_hit(i)
#     ssd.print_sample()



