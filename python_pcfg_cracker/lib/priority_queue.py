#!/usr/bin/env python3

########################################################################################
#
# Name: PCFG_Cracker "Next" Function
# Description: Section of the code that is responsible of outputting all of the
#              pre-terminal values of a PCFG in probability order.
#
#########################################################################################


import sys
import string
import struct
import os
import types
import time
import queue
import copy
import heapq

from sample_grammar import s_preterminal

###################################################################################################
# Used to hold the parse_tree of a path through the PCFG that is then stored in the priority queue
###################################################################################################
class QueueItem:
    
    ############################################################################
    # Basic initialization function
    ############################################################################
    def __init__(self, is_terminal = False, probability = 0.0, parse_tree = []):
        self.is_terminal = is_terminal      ##-Used to say if the parse_tree has any expansion left or if all the nodes represent terminals
        self.probability = probability    ##-The probability of this queue items
        self.parse_tree = parse_tree        ##-The actual parse through the PCFG that this item represents
        
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
        ret_string = "isTerminal = " + str(self.is_terminal) + "\n"
        ret_string += "Probability = " + str(self.probability) + "\n"
        ret_string += "ParseTree = " + str(self.parse_tree) + "\n"
        return ret_string
        
    #################################################################################
    # A more detailed print that is easier to read. Requires passing in the pcfg
    #################################################################################
    def detailed_print(self,pcfg):
        ret_string = "isTerminal = " + str(self.is_terminal) + "\n"
        ret_string += "Probability = " + str(self.probability) + "\n"
        ret_string += "ParseTree = "
        ret_string += pcfg.print_parse_tree(self.parse_tree)
        return ret_string
        
    
            
#######################################################################################################
# I may make changes to the underlying priority queue code in the future to better support
# removing low probability items from it when it grows too large. Therefore I felt it would be best
# to treat it as a class. Right now though it uses the standared python queue HeapQ as its
# backend
#######################################################################################################
class PcfgQueue:
    ############################################################################
    # Basic initialization function
    ############################################################################
    def __init__(self):
        self.p_queue = []  ##--The actual priority queue
        self.max_probability = 1.0 #--The current highest priority item in the queue. Used for memory management and restoring sessions
        self.min_probability = 0.0 #--The lowest prioirty item is allowed to be in order to be pushed in the queue. Used for memory management
        self.max_queue_size = 50000 #--Used for memory management. The maximum number of items before triming the queue. (Note, the queue can temporarially be larger than this)
        self.reduction_size = self.max_queue_size // 4  #--Used to reduce the p_queue by this amount when managing memory

    #############################################################################
    # Push the first value into the priority queue
    # This will likely be 'S' unless you are constructing your PCFG some other way
    #############################################################################
    def initialize(self, pcfg):
        q_item = QueueItem(is_terminal=False, probability = 1.0, parse_tree = [0,0,[]])
        heapq.heappush(self.p_queue,q_item)
    
 
    ###############################################################################
    # Memory managment function to reduce the size of the priority queue
    # This is *hugely* wasteful right now. On my todo list is to modify the
    # p_queue code to allow easier deletion of low priority items
    ###############################################################################
    def trim_queue(self,g_vars,c_vars):
        keep_list = []
        orig_size = len(self.p_queue)
        
        ##---Pop the top 1/2 of the priority queue off and save it ---##
        #for index in range(0,(self.max_queue_size//2)):
        for index in range(0,self.max_queue_size-self.reduction_size):
            item = heapq.heappop(self.p_queue)
            heapq.heappush(keep_list,item)
            #if index == (self.max_queue_size//2)-1:
            if index == (self.max_queue_size-self.reduction_size)-1:
                ###--- Save the probability of the lowest priority item on the new Queue
                self.min_probability = item.probability
                print("min prob: " + str(self.min_probability))
                ###--- Copy all items of similar probabilities over so everything dropped is lower probability
                item = heapq.heappop(self.p_queue)
                while item.probability == self.min_probability:
                    heapq.heappush(keep_list,item)
                    item = heapq.heappop(self.p_queue)
                    
        ##--Now copy the top 1/2 of the priority queue back----##
        self.p_queue = copy.deepcopy(keep_list)

        ##--The grammar would have to be pretty weird for this sanity check to fail, but it's better to check
        ##--since weirdness happens
        if orig_size == len(keep_list):
            return g_vars.ret_values['QUEUE_FULL_ERROR']
        return g_vars.ret_values['STATUS_OK']
        
     
    ###############################################################################
    # Used to restore the priority queue from a previous state
    # Allows resuming paused, (or crashed), sessions and is used in the memory management
    ###############################################################################
    def rebuild_queue(self,g_vars,c_vars,pcfg):
        print("Rebuilding p_queue")
        self.p_queue = []
        rebuild_list = []
        self.min_probability = 0.0
        rebuild_list.append(QueueItem(is_terminal=False, probability = 1.0, parse_tree = [0,0,[]]))
        while len(rebuild_list) != 0:
            q_item = rebuild_list.pop(0)
            ret_list = self.rebuild_from_max(g_vars,c_vars,pcfg,q_item)
            if len(self.p_queue) > self.max_queue_size:
                print("trimming Queue")
                self.trim_queue(g_vars,c_vars)
                print("done")
            for item in ret_list:
                rebuild_list.append(item)
                
        print("Done")
        return g_vars.ret_values['STATUS_OK']    
        
    ##############################################################################################
    # Used for memory management. I probably should rename it. What this function does is
    # determine whether to insert the item into the p_queue if it is lower probability than max_probability
    # or returns the item's children if it is higher probability than max_probability    
    def rebuild_from_max(self,g_vars,c_vars,pcfg,q_item):
        ##--If we potentially want to push this into the p_queue
        if q_item.probability <= self.max_probability:
            ##--Check to see if any of it's parents should go into the p_queue--##
            parent_list = pcfg.findMyParents(q_item.parse_tree)
            for parent in parent_list:
                ##--The parent will be inserted in the queue so do not insert this child--##
                if pcfg.find_probability(parent) <=self.max_probability:
                    return []
            ##--Insert this item in the p_queue----##
            if q_item.probability >= self.min_probability:
                heapq.heappush(self.p_queue,q_item) 
            return []
            
        ##--Else check to see if we need to push this items children into the queue--##
        else:
            children_list = pcfg.find_children(q_item.parse_tree)
            my_children_list = self.lazy_find_my_children(c_vars,pcfg,q_item,children_list)
            ret_list = []
            for child in my_children_list:
                ret_list.append(QueueItem(is_terminal = pcfg.find_is_terminal(child), probability = pcfg.find_probability(child), parse_tree = child))
            return ret_list
     
    #####################################################################
    # Given a list of children, find all the children who this parent should
    # insert into the list for rebuilding the queue
    # Note, this is a lazy insert since the parent is determined by position in
    # the child's parent list vs the lowest probability parent
    #####################################################################
    def lazy_find_my_children(self,c_vars,pcfg,q_item,children_list):
        my_children = []
        for child in children_list:
            parent_list = pcfg.findMyParents(child)
            if parent_list[0] == q_item.parse_tree:
                my_children.append(child)
        return my_children    
        
    ###############################################################################
    # Pops the top value off the queue and then inserts any children of that node
    # back in the queue
    ###############################################################################
    def next_function(self,g_vars,c_vars,pcfg):
        
        ##--Only return terminal structures. Don't need to return parse trees that don't actually generate guesses 
        while True:
            ##--First check if the queue is empty
            while len(self.p_queue) == 0:
                ##--There was some memory management going on so try to rebuild the queue
                if self.min_probability != 0.0:
                    self.rebuild_queue(g_vars,c_vars,pcfg)
                ##--The grammar has been exhaused, exit---##
                else:
                    return g_vars.ret_values['QUEUE_EMPTY']
                
            ##--Pop the top value off the stack
            g_vars.q_item = heapq.heappop(self.p_queue)
            self.max_probability = g_vars.q_item.probability
            
            ##--Push the children back on the stack
            ##--Currently using the deadbeat dad algorithm as described in my dissertation
            ##--http://diginole.lib.fsu.edu/cgi/viewcontent.cgi?article=5135
            self.deadbeat_dad(g_vars,c_vars,pcfg)
            
            ##--Memory management
            if len(self.p_queue) > self.max_queue_size:
                print("trimming Queue")
                self.trim_queue(g_vars,c_vars)
                print("done")
            ##--If it is a terminal strucutre break and return it
            if g_vars.q_item.is_terminal == True:
                break

        #print("--Returning this value")
        #print(g_vars.q_item.detailed_print(pcfg))
        return g_vars.ret_values['STATUS_OK']

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
    def deadbeat_dad(self,g_vars,c_vars,pcfg):
        ##--First find all the potential children
        children_list = pcfg.find_children(g_vars.q_item.parse_tree)

        ##--Now find the children this node is responsible for
        my_children_list = self.find_my_children(c_vars,pcfg,g_vars.q_item,children_list)

        ##--Create the actual QueueItem for each child and insert it in the Priority Queue
        for child in my_children_list:
            child_node = QueueItem(is_terminal = pcfg.find_is_terminal(child), probability = pcfg.find_probability(child), parse_tree = child)
            if child_node.probability <= g_vars.q_item.probability:
                ##--Memory management chck---------
                ##--If the probability of the child node is too low don't bother to insert it in the queue
                if child_node.probability >= self.min_probability:
                    heapq.heappush(self.p_queue,child_node)
            else:
                print("Hmmm, trying to push a parent and not a child on the list")
        
    #####################################################################
    # Given a list of children, find all the children who do not have
    # parents of a lower priority than the current node
    # Returns the children as a list
    #####################################################################
    def find_my_children(self,c_vars,pcfg,q_item,children_list):
        my_children = []
        for child in children_list:
            parent_list = pcfg.findMyParents(child)
            is_my_child = True
            for parent in parent_list:
                ##--First check to make sure the other parent isn't this node
                if parent != q_item.parse_tree:
                    ##--If there is another parent that will take care of the child node
                    if pcfg.find_probability(parent) < q_item.probability:
                        is_my_child = False
                        break
                    ##--Need to make sure only one parent pushes the child in if there are multiple parents of same probability
                    ##--Currently just cheating and using the python compare operator
                    elif pcfg.find_probability(parent) == q_item.probability:
                        if parent < q_item.parse_tree:
                            is_my_child = False
                            break
                        
            if is_my_child:
                my_children.append(child)
        return my_children
                
            
###################################################################
# Random Test Function
####################################################################                
def test_queue(pcfg):
    s_queue_item = QueueItem(parse_tree=s_pre_terminal)
    print(s_queue_item)
    print("--------------")
    print(s_queue_item.detailed_print(pcfg))
            
        