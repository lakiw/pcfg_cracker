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
    ##############################################################################
    def __lt__(self, other):
        return self.probability < other.probability
    
    def __le__(self, other):
        return self.probability <= other.probability
        
    def __eq__(self, other):
        return self.probability == other.probability
        
    def __ne__(self, other):
        return self.probability != other.probability
        
    def __gt__(self, other):
        return self.probability > other.probability
        
    def __ge__(self, other):
        return self.probability >= other.probability
    
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
        retString += self.printParseTree(pcfg, self.parseTree)
        return retString
        
    def printParseTree(self,pcfg,pt=[]):
        retString = ''
        if len(pt[2])==0:
            retString += pcfg.grammar[pt[0]]['name']
            retString += "[" + str(pt[1] + 1) + " of " + str(len(pcfg.grammar[pt[0]]['replacements'])) + "]"
            if pcfg.grammar[pt[0]]['replacements'][pt[1]]['isTerminal'] == True:
                retString += "->terminal"
            else:
                retString += "->incomplete"
        else:
            retString += pcfg.grammar[pt[0]]['name'] 
            retString += "[" + str(pt[1] + 1) + " of " + str(len(pcfg.grammar[pt[0]]['replacements'])) + "]"
            retString += "-> ("
            for x in range(0,len(pt[2])):
                retString += self.printParseTree(pcfg,pt[2][x])
                if x != len(pt[2])-1:
                    retString +=" , "
            retString += ")"
        
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
        self.pQueue = queue.PriorityQueue()  ##--The actual priority queue
        self.maxProbability = 1.0 #--The current highest priority item in the queue
        self.minProbability = 0.0 #--The lowest prioirty item is allowed to be in order to be pushed in the queue
    

    #############################################################################
    # Push the first value into the priority queue
    # This will likely be 'S' unless you are constructing your PCFG some other way
    #############################################################################
    def initialize(self, pcfg):
        qItem = queueItem(isTerminal=False, probability = 1.0, parseTree = [0,0,[]])
        self.pQueue.put(qItem)
    
    ###############################################################################
    # Pops the top value off the queue and then inserts any children of that node
    # back in the queue
    ###############################################################################
    def nextFunction(self,g_vars,c_vars,pcfg):
        ##--First check if the queue is empty
        if self.pQueue.empty() == True:
            return g_vars.RETValues['QUEUE_EMPTY']
            
        ##--Pop the top value off the stack
        g_vars.qItem = self.pQueue.get()
        #print("--Popping this value1")
        #print(g_vars.qItem.detailedPrint(pcfg))
        #print("-------Top Value ----------")
        #print(g_vars.qItem.detailedPrint(pcfg))
        
        ##--Push the children back on the stack
        ##--Currently using the deadbeat dad algorithm as described in my dissertation
        ##--http://diginole.lib.fsu.edu/cgi/viewcontent.cgi?article=5135
        self.deadbeatDad(g_vars,c_vars,pcfg)
        self.maxProbability = g_vars.qItem.probability
        while (g_vars.qItem.isTerminal == False):
            if self.pQueue.empty() == True:
                return g_vars.RETValues['QUEUE_EMPTY']
            g_vars.qItem = self.pQueue.get()
           # print("--Popping this value2")
            #print(g_vars.qItem.detailedPrint(pcfg))
            self.deadbeatDad(g_vars,c_vars,pcfg)
            self.maxProbability = g_vars.qItem.probability
        
        print("--Returning this value")
        print(g_vars.qItem.detailedPrint(pcfg))
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
        #print("--g_vars is now this value")
        #print(g_vars.qItem.detailedPrint(pcfg))
        childrenList = self.findChildren(pcfg,g_vars.qItem.parseTree)
        #print("--g_vars is now this value")
        #print(g_vars.qItem.detailedPrint(pcfg))
        ##--Now find the children this node is responsible for
        myChildrenList = self.findMyChildren(pcfg,g_vars.qItem,childrenList)
        #print("--g_vars is now this value")
        #print(g_vars.qItem.detailedPrint(pcfg))
        #print("---children----")
        for child in myChildrenList:
            childNode = queueItem(isTerminal = pcfg.findIsTerminal(child), probability = pcfg.findProbability(child), parseTree = child)
            #print(child)
            #print(pcfg.findIsTerminal(child))
            #print(childNode.isTerminal)
            if childNode.probability <= g_vars.qItem.probability:
                self.pQueue.put(childNode)
            else:
                print("Hmmm, trying to push a parent and not a child on the list")
            
        #print("---end children--\n")
        
    #####################################################################
    # Given a list of children, find all the children who do not have
    # parents of a lower priority than the current node
    # Returns the children as a list
    #####################################################################
    def findMyChildren(self,pcfg,qItem,childrenList):
        myChildren = []
        for child in childrenList:
            parentList = self.findMyParents(pcfg,child)
            isMyChild = True
            for parent in parentList:
                ##--First check to make sure the other parent isn't this node
                if parent != qItem.parseTree:
                    ##--If there is another parent that will take care of the child node
                    if pcfg.findProbability(parent) < qItem.probability:
                        isMyChilde = False
                        break
            if isMyChild:
                myChildren.append(child)
        return myChildren
            
    ######################################################################
    # Returns a list of all the parents for a child node
    ######################################################################    
    def findMyParents(self,pcfg,pt):
        retList = []
        #Check the curnode if is at least one other parent
        if pt[1] != 0:     
            retList.append(copy.deepcopy(pt))
            retList[0][1] = pt[1] - 1
        if len(pt[2])!=0:
            ##--First append the non expanded version----#
            retList.append(copy.deepcopy(pt))
            retList[0][2] = []
            for x in range(0,len(pt[2])):
                #Doing it recursively!
                tempList = self.findMyParents(pcfg,pt[2][x])
                #If there were any parents, append them to the main list
                if len(tempList) != 0:
                    for y in tempList:
                        retList.append(y)
                            
        return retList
        
    #################################################################
    # Finds all the potential children and returns them as a list
    #################################################################
    def findChildren(self,pcfg,pt):
        #basically we want to increment one step if possible
        #First check for children of the current nodes
        retList = []
        numReplacements = len(pcfg.grammar[pt[0]]['replacements'])
        #If there are children
        if numReplacements > (pt[1]+1):
            #Return the child
            retList.append(copy.deepcopy(pt))
            retList[0][1] = pt[1] + 1
            retList[0][2] = []
        
        ###-----Next check to see if there are any nodes to the right that need to be checked
        #If the node is a pre-terminal that has already been expanded
        if len(pt[2])!=0:    
            for x in range(0,len(pt[2])):
                #Doing it recursively!
                tempList = self.findChildren(pcfg,pt[2][x])
                #If there were any children, append them to the main list
                if len(tempList) != 0:
                    for y in tempList:
                        retList.append(copy.deepcopy(pt))
                        retList[-1][2][x] = y
        #Else if it needs to be expanded
        else:
            if pcfg.grammar[pt[0]]['replacements'][0]['isTerminal'] != True:
                newExpansion = []
                for x in pcfg.grammar[pt[0]]['replacements'][pt[1]]['pos']:
                    newExpansion.append([x,0,[]])
                retList.append(copy.deepcopy(pt))
                retList[-1][2] = newExpansion
        return retList
            
###################################################################
# Random Test Function
####################################################################                
def testQueue(pcfg):
    sQueueItem = queueItem(parseTree=s_preTerminal)
    print(sQueueItem)
    print("--------------")
    print(sQueueItem.detailedPrint(pcfg))
            
        