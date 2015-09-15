#!/usr/local/bin/python3

########################################################################################
#
# Name: PCFG_Cracker "Next" Function
# Description: Section of the code that is responsible of outputting all of the
#              pre-terminal values of a PCFG in probability order.
#
#########################################################################################


from __future__ import print_function
import sys
import string
import struct
import os
import types
import time
import queue
import copy
import heapq

from sample_grammar import s_preTerminal

###################################################################################################
# Used to hold the parseTree of a path through the PCFG that is then stored in the priority queue
###################################################################################################
class queueItem:
    
    ############################################################################
    # Basic initialization function
    ############################################################################
    def __init__(self, isTerminal = False, probability = 0.0, parseTree = []):
        self.isTerminal = isTerminal      ##-Used to say if the parseTree has any expansion left or if all the nodes represent terminals
        self.probability = probability    ##-The probability of this queue items
        self.parseTree = parseTree        ##-The actual parse through the PCFG that this item represents
        
    ##############################################################################
    # Need to have a custom compare functions for use in the priority queue
    # Really annoying that I have to do this the reverse of what I'd normally expect
    # since the priority queue will output stuff of lower values first.
    # Aka if there are two items with probabilities of 0.7 and 0.4, the PQueue will
    # by default output 0.4 which is ... not what I'd like it to do
    ##############################################################################
    def __lt__(self, other):
        return self.probability > other.probability
    
    def __le__(self, other):
        return self.probability >= other.probability
        
    def __eq__(self, other):
        return self.probability == other.probability
        
    def __ne__(self, other):
        return self.probability != other.probability
        
    def __gt__(self, other):
        return self.probability < other.probability
        
    def __ge__(self, other):
        return self.probability <= other.probability
    
    ###############################################################################
    # Overloading print operation to make debugging easier
    ################################################################################
    def __str__(self):
        retString = "isTerminal = " + str(self.isTerminal) + "\n"
        retString += "Probability = " + str(self.probability) + "\n"
        retString += "ParseTree = " + str(self.parseTree) + "\n"
        return retString
        
    #################################################################################
    # A more detailed print that is easier to read. Requires passing in the pcfg
    #################################################################################
    def detailedPrint(self,pcfg):
        retString = "isTerminal = " + str(self.isTerminal) + "\n"
        retString += "Probability = " + str(self.probability) + "\n"
        retString += "ParseTree = "
        retString += pcfg.printParseTree(self.parseTree)
        return retString
        
    
            
#######################################################################################################
# I may make changes to the underlying priority queue code in the future to better support
# removing low probability items from it when it grows too large. Therefore I felt it would be best
# to treat it as a class. Right now though it uses the standared python queue priorityQueue as its
# backend
#######################################################################################################
class pcfgQueue:
    ############################################################################
    # Basic initialization function
    ############################################################################
    def __init__(self):
        self.pQueue = []  ##--The actual priority queue
        self.maxProbability = 1.0 #--The current highest priority item in the queue. Used for memory management and restoring sessions
        self.minProbability = 0.0 #--The lowest prioirty item is allowed to be in order to be pushed in the queue. Used for memory management
        self.maxQueueSize = 5000 #--Used for memory management. The maximum number of items before triming the queue. (Note, the queue can temporarially be larger than this)

    #############################################################################
    # Push the first value into the priority queue
    # This will likely be 'S' unless you are constructing your PCFG some other way
    #############################################################################
    def initialize(self, pcfg):
        qItem = queueItem(isTerminal=False, probability = 1.0, parseTree = [0,0,[]])
        heapq.heappush(self.pQueue,qItem)
    
 
    ###############################################################################
    # Memory managment function to reduce the size of the priority queue
    # This is *hugely* wasteful right now. On my todo list is to modify the
    # pQueue code to allow easier deletion of low priority items
    ###############################################################################
    def trimQueue(self,g_vars,c_vars):
        keepList = []
        orig_size = len(self.pQueue)
        
        ##---Pop the top 1/2 of the priority queue off and save it ---##
        #for index in range(0,(self.maxQueueSize//2)):
        for index in range(0,self.maxQueueSize-100):
            item = heapq.heappop(self.pQueue)
            heapq.heappush(keepList,item)
            #if index == (self.maxQueueSize//2)-1:
            if index == (self.maxQueueSize-100)-1:
                ###--- Save the probability of the lowest priority item on the new Queue
                self.minProbability = item.probability
                print("min prob: " + str(self.minProbability))
                ###--- Copy all items of similar probabilities over so everything dropped is lower probability
                item = heapq.heappop(self.pQueue)
                while item.probability == self.minProbability:
                    heapq.heappush(keepList,item)
                    item = heapq.heappop(self.pQueue)
                    
        ##--Now copy the top 1/2 of the priority queue back----##
        self.pQueue = copy.deepcopy(keepList)

        ##--The grammar would have to be pretty weird for this sanity check to fail, but it's better to check
        ##--since weirdness happens
        if orig_size == len(keepList):
            return g_vars.RETValues['QUEUE_FULL_ERROR']
        return g_vars.RETValues['STATUS_OK']
        
     
    ###############################################################################
    # Used to restore the priority queue from a previous state
    # Allows resuming paused, (or crashed), sessions and is used in the memory management
    ###############################################################################
    def rebuildQueue(self,g_vars,c_vars,pcfg):
        print("Rebuilding pQueue")
        self.pQueue = []
        rebuildList = []
        self.minProbability = 0.0
        rebuildList.append(queueItem(isTerminal=False, probability = 1.0, parseTree = [0,0,[]]))
        while len(rebuildList) != 0:
            qItem = rebuildList.pop(0)
            retList = self.rebuildFromMax(g_vars,c_vars,pcfg,qItem)
            if len(self.pQueue) > self.maxQueueSize:
                print("trimming Queue")
                self.trimQueue(g_vars,c_vars)
                print("done")
            for item in retList:
                rebuildList.append(item)
                
        
        if len(self.pQueue) > self.maxQueueSize:
            print("Going to have to trim: " + str(len(self.pQueue)))
        print("Done")
        return g_vars.RETValues['STATUS_OK']    
        
    ##############################################################################################
    # Used for memory management. I probably should rename it. What this function does is
    # determine whether to insert the item into the pQueue if it is lower probability than maxProbability
    # or returns the item's children if it is higher probability than maxProbability    
    def rebuildFromMax(self,g_vars,c_vars,pcfg,qItem):
        ##--If we potentially want to push this into the pQueue
        if qItem.probability <= self.maxProbability:
            ##--Check to see if any of it's parents should go into the pQueue--##
            parentList = pcfg.findMyParents(qItem.parseTree)
            for parent in parentList:
                ##--The parent will be inserted in the queue so do not insert this child--##
                if pcfg.findProbability(parent) <=self.maxProbability:
                    return []
            ##--Insert this item in the pQueue----##
            if qItem.probability >= self.minProbability:
                heapq.heappush(self.pQueue,qItem) 
            return []
            
        ##--Else check to see if we need to push this items children into the queue--##
        else:
            childrenList = pcfg.findChildren(qItem.parseTree)
            myChildrenList = self.findMyChildren(c_vars,pcfg,qItem,childrenList)
            retList = []
            for child in myChildrenList:
                retList.append(queueItem(isTerminal = pcfg.findIsTerminal(child), probability = pcfg.findProbability(child), parseTree = child))
            return retList
            
        
    ###############################################################################
    # Pops the top value off the queue and then inserts any children of that node
    # back in the queue
    ###############################################################################
    def nextFunction(self,g_vars,c_vars,pcfg):
        
        ##--Only return terminal structures. Don't need to return parse trees that don't actually generate guesses 
        while True:
            ##--First check if the queue is empty
            while len(self.pQueue) == 0:
                ##--There was some memory management going on so try to rebuild the queue
                if self.minProbability != 0.0:
                    self.rebuildQueue(g_vars,c_vars,pcfg)
                ##--The grammar has been exhaused, exit---##
                else:
                    return g_vars.RETValues['QUEUE_EMPTY']
                
            ##--Pop the top value off the stack
            g_vars.qItem = heapq.heappop(self.pQueue)
            self.maxProbability = g_vars.qItem.probability
            
            ##--Push the children back on the stack
            ##--Currently using the deadbeat dad algorithm as described in my dissertation
            ##--http://diginole.lib.fsu.edu/cgi/viewcontent.cgi?article=5135
            self.deadbeatDad(g_vars,c_vars,pcfg)
            
            ##--Memory management
            if len(self.pQueue) > self.maxQueueSize:
                print("trimming Queue")
                self.trimQueue(g_vars,c_vars)
                print("done")
            ##--If it is a terminal strucutre break and return it
            if g_vars.qItem.isTerminal == True:
                break

        #print("--Returning this value")
        #print(g_vars.qItem.detailedPrint(pcfg))
        return g_vars.RETValues['STATUS_OK']

    ################################################################################
    # The deadbead dad "next" algorithm as described in http://diginole.lib.fsu.edu/cgi/viewcontent.cgi?article=5135
    # In a nutshell, imagine the parse tree as a graph with the 'S' node at top
    # The original "next" function inserted every child parse through it by incrementing the counter by one to the left
    # so the node (1,1,1) would have the children (2,1,1), (1,2,1), and (1,1,2).
    # The child (1,2,1) would only have the children (1,3,1) and (1,2,2) though.
    # This was to prevent any duplicate entries being pushing into the queue
    # The problem was this was *very* memory intensive
    #
    # The deadbeat dad algorithm instead looks at all the potential parents of *every* child node it could create
    # If any of those parents have lower probability than the current node, it "abandons" that child for the other parent to take care of it
    # Only the parent with the lowest probability inserts the child into the queue. That is because that parent knows there are no other parents
    # that will appear later. I know the name is unfortunate, but it really sums up the approach.
    # Basically we're trading computation time for memory. Keeping the queue small though saves computation time too though so
    # in longer runs this approach should be a clear winner compared to the original next function
    # TODO: There is a *TON* of optimization I can do in the current version of this "next" function
    def deadbeatDad(self,g_vars,c_vars,pcfg):
        ##--First find all the potential children
        childrenList = pcfg.findChildren(g_vars.qItem.parseTree)

        ##--Now find the children this node is responsible for
        myChildrenList = self.findMyChildren(c_vars,pcfg,g_vars.qItem,childrenList)

        ##--Create the actual queueItem for each child and insert it in the Priority Queue
        for child in myChildrenList:
            childNode = queueItem(isTerminal = pcfg.findIsTerminal(child), probability = pcfg.findProbability(child), parseTree = child)
            if childNode.probability <= g_vars.qItem.probability:
                ##--Memory management chck---------
                ##--If the probability of the child node is too low don't bother to insert it in the queue
                if childNode.probability >= self.minProbability:
                    heapq.heappush(self.pQueue,childNode)
            else:
                print("Hmmm, trying to push a parent and not a child on the list")
        
    #####################################################################
    # Given a list of children, find all the children who do not have
    # parents of a lower priority than the current node
    # Returns the children as a list
    #####################################################################
    def findMyChildren(self,c_vars,pcfg,qItem,childrenList):
        myChildren = []
        for child in childrenList:
            parentList = pcfg.findMyParents(child)
            isMyChild = True
            for parent in parentList:
                ##--First check to make sure the other parent isn't this node
                if parent != qItem.parseTree:
                    ##--If there is another parent that will take care of the child node
                    if pcfg.findProbability(parent) < qItem.probability:
                        isMyChild = False
                        break
                    ##--Need to make sure only one parent pushes the child in if there are multiple parents of same probability
                    ##--Currently just cheating and using the python compare operator
                    elif pcfg.findProbability(parent) == qItem.probability:
                        if parent < qItem.parseTree:
                            isMyChild = False
                            break
                        
            if isMyChild:
                myChildren.append(child)
        return myChildren
                
            
###################################################################
# Random Test Function
####################################################################                
def testQueue(pcfg):
    sQueueItem = queueItem(parseTree=s_preTerminal)
    print(sQueueItem)
    print("--------------")
    print(sQueueItem.detailedPrint(pcfg))
            
        