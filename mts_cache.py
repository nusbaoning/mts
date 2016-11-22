import sys
import time
import collections
import operator 
class cache_algorithm(object):
    """docstring for cache_algorithm"""
    def isHit(self, key):
        pass
    def updateCache(self, key):
        pass
    def deleteCache(self, key):
        pass

class mynode(object):
    """docstring for mynode"""
    def __init__(self):
        self.empty = True

class lru(cache_algorithm):
    """docstring for lru"""
    def __init__(self, size):
        self.size = size
        self.ssd = {}
        self.head = mynode()
        self.head.next = self.head
        self.head.prev = self.head
        self.listSize = 1
        # Adjust the size
        self.changesize(size)
    def __len__(self):
        return len(self.ssd)

    def clear(self):
        for node in self.dli():
            node.empty = True
        self.ssd.clear()


    def isHit(self, key):
        return key in self.ssd


    def updateCache(self, key):
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


    def deleteCache(self, key):

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

    def changesize(self, size):
        
        if size > self.listSize:
            self.addTailNode(size - self.listSize)
        elif size < self.listSize:
            self.removeTailNode(self.listSize - size)
        return self.listSize

    # Increases the size of the cache by inserting n empty nodes at the tail
    # of the list.
    def addTailNode(self, n):
        for i in range(n):
            node = mynode()
            node.next = self.head
            node.prev = self.head.prev

            self.head.prev.next = node
            self.head.prev = node

        self.listSize += n

    # Decreases the size of the list by removing n nodes from the tail of the
    # list.
    def removeTailNode(self, n):
        assert self.listSize > n
        for i in range(n):
            node = self.head.prev
            if not node.empty:
                del self.ssd[node.key]
            # Splice the tail node out of the list
            self.head.prev = node.prev
            node.prev.next = self.head
        self.listSize -= n

class lfu(cache_algorithm):
    """docstring for lfu"""
    def __init__(self, size):        
        self.size = size
        self.ssd = {}
        self.victims = collections.deque()
        self.minreq = 1
        self.sorttime = 0
    def isHit(self, key):
        return key in self.ssd
    def updateCache(self, key):
        if key in self.ssd:            
            if self.ssd[key] == self.minreq:
                try:
                    self.victims.remove(key)
                except Exception as e:
                    pass
            self.ssd[key] += 1
            return
        if len(self.ssd) < self.size:
            self.ssd[key] = 1
        else:
            vk = self.getvictim()
            # print(key,vk)
            # print(self.victims)
            if self.minreq > 1:
                # self.updateVictim(vk)
                return
            else:
                self.deleteCache(vk)
                self.ssd[key] = 1
        # self.updateVictim(key)

    def getvictim(self):
        if len(self.victims) > 0:
            return self.victims.pop()
        else:
            self.updateVictim()
            return self.victims.pop()

    def updateVictim(self):
        l = list(self.ssd.items())
        
        l.sort(key=operator.itemgetter(1))
        self.sorttime += 1
        
        
        _, self.minreq = l[0]
        for i in range(0,int(0.2*len(self.ssd))):
            key, req = l[i]
            if req > self.minreq:
                break
            self.victims.append(key)
    
    def deleteCache(self,key):
        if key not in self.ssd:
            return
        del(self.ssd[key])

    def printsample(self):
        print("print lfu ssd")
        for key in self.ssd.keys():
            print(key, self.ssd[key])


        
# class lfu(cache_algorithm):
#     """docstring for lfu"""
#     def __init__(self, size):
#         self.size = size
#         self.ssd = {}
#         self.head = mynode()
#         self.head.next = self.head
#         self.head.prev = self.head
#         for i in range(1,size):
#             node = mynode()
#             node.next = self.head
#             node.prev = self.head.prev

#             self.head.prev.next = node
#             self.head.prev = node
#     def isHit(self, key):
#         return key in self.ssd
#     def updateCache(self, key):
#         if key in self.ssd:
#             preNode = self.ssd[key]
#             preNode.data += 1

#             # move the data to higher frequency part
#             node = preNode.prev
#             while node!=self.head.prev:
#                 if node.data == preNode.data:
#                     preNode.prev.next = preNode.next
#                     preNode.next.prev = preNode.prev

#                     preNode.next = node.next
#                     node.next.prev = preNode
#                     node.next = preNode
#                     preNode.prev = node
#                     break
#             # if the present node becomes the best node
#             if node == head.prev and preNode != head:
#                 self.head.prev.next = preNode
#                 preNode.prev = self.head.prev

#                 preNode.next = self.head
#                 self.head.prev = preNode

#                 self.head = preNode

#         else:
#             node = self.head.prev
#             if not node.empty:
#                 del self.ssd[node.key]
#             else:
#                 if len(self.ssd) == 0:
#                     self.head = node
#                 else:
#                     if len(self.ssd) < 0.5*self.size:
#                         tnode = self.head
#                         for i in range(1,len(self.ssd)+1):
#                             if tnode.data == 1:
#                                 break
#                     else:
#                         tnode = node.prev
#                         for i in range(1,len(self.ssd)+1):
#                             if tnode.empty == False:
#                                 break

#                     self.head.prev = node.prev
#                     node.prev.next = self.head

#                     tnode.next.prev = node
#                     node.next = tnode.next.prev

#                     tnode.next = node
#                     node.prev = tnode



#             # Place the new key and value in the node
#             node.empty = False
#             node.key = key
#             node.data = 1
        
#             # Add the node to the dictionary under the new key.
#             self.ssd[key] = node
#     def deleteCache(self,key):
#         if key not in ssd:
#             return
#         node = self.ssd[key]
#         del self.ssd[node.key]
#         node.prev.next = node.next
#         node.next.prev = node.prev

#         self.head.prev.next = node
#         node.prev = self.head.prev.next
#         node.next = self.head
#         self.head.prev = node

    
#     def dli(self):
#         node = self.head
#         for i in range(len(self.ssd)):
#             yield node
#             node = node.next
#     def printsample(self):
#         print("print lfu ssd")
#         for x in ssd.dli():
#             print(x.key, x.data)


ssd = lfu(5)
ssd.printsample()
for i in range(5):
    for j in range(i+1):
        ssd.updateCache(i)
ssd.printsample()
for i in range(5):
    ssd.updateCache(i+6)
    ssd.printsample()
print(ssd.isHit(1))
print(ssd.isHit(0))
ssd.deleteCache(10)
ssd.printsample()

