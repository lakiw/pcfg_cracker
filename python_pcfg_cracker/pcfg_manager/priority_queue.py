#!/usr/bin/env python3

########################################################################################
#
# Name: PCFG_Cracker "Next" Function
# Description: Section of the code that is responsible of outputting all of the
#              pre-terminal values of a PCFG in probability order.
#              Because of that, this section also handles all of the memory management
#              of a running password generation session
#
#########################################################################################


import sys   #--Used for printing to stderr
import string
import struct
import os
import types
import time
import queue
import copy
import heapq


from sample_grammar import s_preterminal
from pcfg_manager.ret_types import RetType

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
        self.max_queue_size = 500000 #--Used for memory management. The maximum number of items before triming the queue. (Note, the queue can temporarially be larger than this)
        self.reduction_size = self.max_queue_size // 4  #--Used to reduce the p_queue by this amount when managing memory

    #############################################################################
    # Push the first value into the priority queue
    # This will likely be 'START' unless you are constructing your PCFG some other way
    #############################################################################
    def initialize(self, pcfg):
        
        ##--Find the START index into the grammar--##
        index = pcfg.start_index()
        if index == -1:
            print("Could not find starting position for the pcfg", file=sys.stderr)
            return RetType.GRAMMAR_ERROR
        
        ##--Push the very first item into the queue--##
        q_item = QueueItem(is_terminal=False, probability = pcfg.find_probability([index,0,[]]), parse_tree = [index,0,[]])
        heapq.heappush(self.p_queue,q_item)
        
        return RetType.STATUS_OK
 
    ###############################################################################
    # Memory managment function to reduce the size of the priority queue by
    # deleting the last 1/2 ish of the priority queue
    # It's not an exact number since if multiple items have the same probability
    # and those items fall in the middle of the priority queue then it will save
    # all of them.
    # Aka if the list looks like [0,1,2,3,3,3,7], it will save [0,1,2,3,3,3]
    # If the list looked like [0,1,2,3,4,5,6,7] it will save [0,1,2,3]
    # There is an edge case where no items will be deleted if they all are the same probabilities
    ###############################################################################
    def trim_queue(self):
        ##--First sort the queue so we can easily delete the least probable items--##
        ##--Aka turn it from a heap into a sorted list, since heap pops are somewhat expensive--##
        self.p_queue.sort()
        
        ##--Save the size information about the list
        orig_size = len(self.p_queue)
        
        ##--middle represents the point where we are going to cut the list to remove low probability items
        middle = orig_size//2
        
        ##--Assign the min probabilty to the item currently in the middle of the queue--##
        self.min_probability = self.p_queue[middle].probability
        print("min prob: " + str(self.min_probability), file=sys.stderr)
        
        ##--Now find the middle we want to cut in case multiple items in the current middle share the same probability
        while (middle < orig_size-1) and (self.p_queue[middle].probability == self.p_queue[middle+1].probability):
            middle = middle + 1
            
        ##--Sanity check for edge case where nothing gets deleted
        if middle == orig_size - 1:
            print("Could not trim the priority queue since at least half the items have the same probability", file=sys.stderr)
            print("Not so much a bug as an edge case I haven't implimented a solution for. Performance is going to be slow until you stop seeing this message --Matt", file=sys.stderr)
        
        ##--Now actually delete the entries--##
        del(self.p_queue[middle+1:])

        ##--Re-heapify the priority queue
        heapq.heapify(self.p_queue)
        
        ##--This can happen if the queue is full of items all of the same probability
        if len(self.pqueue) == orig_size:
            return RetType.QUEUE_FULL_ERROR
        ##--Not an immediate problem but this state will cause issues with resuming sessions. For now report an error state
        if self.min_probability == self.max_probability:
            return RetType.QUEUE_FULL_ERROR
        
        return RetType.STATUS_OK
        
     
    ###############################################################################
    # Used to restore the priority queue from a previous state
    # Allows resuming paused, (or crashed), sessions and is used in the memory management
    ###############################################################################
    def rebuild_queue(self,pcfg):
        print("Rebuilding p_queue", file=sys.stderr)
        
        ##--Initialize the values
        self.p_queue = []
        ##--Initially don't bound the minimum probability. We are only bounding the maximum probability
        self.min_probability = 0.0
        
        ##--Build the first node in the parse tree
        index = pcfg.start_index()
        if index == -1:
            print("Could not find starting position for the pcfg")
            return RetType.GRAMMAR_ERROR
          
        current_parse_tree = [index,0,[]]
        cur_node = current_parse_tree
        
        ##--Now go through and actually rebuild the priority queue
        ret_value = rebuild_queue_from_node(current_parse_tree, cur_node)
        if ret_value != RetType.STATUS_OK:
            print("Error rebuilding the priority queue", file=sys.stderr)
            return ret_value
            
        ##--Now re-heapify the priority queue--##    
        heapq.heapify(self.p_queue)
        
        print("Done", file=sys.stderr)
        return RetType.STATUS_OK    
        
    

    ###############################################################################################################
    # Quick (hopefully) way to go through all the parse trees and insert items that fall between the min and max
    # allowed probabilities
    # --Note, this digs a bit more into the core grammar structures than I'd really like, but it fits in better
    #   here. I may move this around a bit in the future.
    ###############################################################################################################
    def rebuild_queue_from_node(current_parse_tree, cur_node):
        ##--Quick bail out while I write the part below
        return RetType.STATUS_OK
        #########################################################################################################
        # First check to see if we can increment the current node
        # --Only increment and expand if the transition options are blank, aka (x,y,[]) vs (x,y,[some values])
        # --So (1,2,[]) => (1,3,[])
        # --But if it is (1,2,[[5,0,[]]]) do not increment it
        #
        # After that we need to also create children for the expastion
        # --So (1,2,[]) => (1,2,[[5,0,[]]])
        #########################################################################################################
        if len(cur_node[2])==0:
            numReplacements = len(self.grammar[cur_node[0]]['replacements'])
            #Takes care of the incrementing if there are children for the current node. Aka(1,2,[]) => (1,3,[])
            if numReplacements > (cur_node[1]+1):
                ##--Make this a child node
                cur_node[1] = cur_node[1] + 1   
                ##--An id to identify the calling node as the parent                
                cur_node.append(True) 
                if self.dd_is_my_parent(this_parent, is_expansion=False):
                    ##--Remove the id  
                    del cur_node[3]
                    my_children_list.append(self.copy_node(this_parent))
                else:
                    ##--Remove the id  
                    del cur_node[3]
                ##--Replace the parent's value    
                cur_node[1] = cur_node[1] - 1

                
            #Now take care of the expansion. Aka (1,2,[]) => (1,2,[[5,0,[]]])
            if self.grammar[cur_node[0]]['replacements'][0]['is_terminal'] != True:
                #--First fill out the expansion for the new child
                new_expansion = []
                for x in self.grammar[cur_node[0]]['replacements'][cur_node[1]]['pos']:
                    new_expansion.append([x,0,[]])
                
                ##--Make this a child node
                cur_node[2] = new_expansion
                ##--An id to identify the calling node as the parent                
                cur_node.append(True) 
                
                if self.dd_is_my_parent(this_parent, is_expansion=True):
                    ##--Remove the id  
                    del cur_node[3]
                    my_children_list.append(self.copy_node(this_parent))
                else:
                    ##--Remove the id  
                    del cur_node[3]
                    
                ##--Replace the parent's value 
                cur_node[2] = []
                
                
        ###-----Next check to see if there are any nodes to the right that need to be checked
        ###-----This happens if the node is a pre-terminal that has already been expanded
        ###-----Ex: [5,2,[[1,2,[]],[3,1,[]]]] => [5,2,[[1,3,[]],[3,1,[]]]] + [5,2,[[1,2,[]],[3,2,[]]]] + [5,2,[[1,2,[....]],[3,1,[]]]] + [5,2,[[1,2,[]],[3,1,[....]]]]
        else:    
            for x in range(0,len(cur_node[2])):
                #Doing it recursively!
                self.dd_find_children(cur_node[2][x], this_parent, my_children_list)
        
        return RetType.STATUS_OK
        
        
      
        
    ###############################################################################
    # Pops the top value off the queue and then inserts any children of that node
    # back in the queue
    ###############################################################################
    def next_function(self,pcfg, queue_item_list = []):
        
        ##--Only return terminal structures. Don't need to return parse trees that don't actually generate guesses 
        while True:
            ##--First check if the queue is empty
            while len(self.p_queue) == 0:
                ##--If there was some memory management going on, try to rebuild the queue
                if self.min_probability != 0.0:
                    self.rebuild_queue(pcfg)
                ##--The grammar has been exhaused, exit---##
                else:
                    return RetType.QUEUE_EMPTY
                
            ##--Pop the top value off the stack
            queue_item = heapq.heappop(self.p_queue)
            self.max_probability = queue_item.probability
            ##--Push the children back on the stack
            ##--Currently using the deadbeat dad algorithm as described in my dissertation
            ##--http://diginole.lib.fsu.edu/cgi/viewcontent.cgi?article=5135
            self.add_children_to_queue(pcfg, queue_item)
            
            ##--Memory management
            if len(self.p_queue) > self.max_queue_size:
                print("trimming Queue", file=sys.stderr)
                self.trim_queue()
                print("done", file=sys.stderr)
            ##--If it is a terminal structure break and return it
            if queue_item.is_terminal == True:
                queue_item_list.append(queue_item)
                break

        #print("--Returning this value")
        #print(queue_item_list[0].detailed_print(pcfg), file=sys.stderr)
        return RetType.STATUS_OK

        
    #################################################################################################################################################
    # Adds children to the priority queue
    # Currently using the deadbeat dad algorithm to determine which children to add
    # The deadbead dad "next" algorithm as described in http://diginole.lib.fsu.edu/cgi/viewcontent.cgi?article=5135
    ##################################################################################################################################################
    def add_children_to_queue(self,pcfg, queue_item):
        
        my_children_list = pcfg.deadbeat_dad(queue_item.parse_tree)

        ##--Create the actual QueueItem for each child and insert it in the Priority Queue
        for child in my_children_list:
            child_node = QueueItem(is_terminal = pcfg.find_is_terminal(child), probability = pcfg.find_probability(child), parse_tree = child)
            if child_node.probability <= queue_item.probability:
                ##--Memory management check---------
                ##--If the probability of the child node is too low don't bother to insert it in the queue
                if child_node.probability >= self.min_probability:
                    heapq.heappush(self.p_queue,child_node)
            else:
                print("Hmmm, trying to push a parent and not a child on the list", file=sys.stderr)

            
###################################################################
# Random Test Function
####################################################################                
def test_queue(pcfg):
    s_queue_item = QueueItem(parse_tree=s_pre_terminal)
    print(s_queue_item, file=sys.stderr)
    print("--------------", file=sys.stderr)
    print(s_queue_item.detailed_print(pcfg), file=sys.stderr)
            
        