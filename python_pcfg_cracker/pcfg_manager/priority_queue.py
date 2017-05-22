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
import types
import time
import heapq

from pcfg_manager.ret_types import RetType
from pcfg_manager.core_grammar import PcfgClass

###################################################################################################
# Used to hold the parse_tree of a path through the PCFG that is then stored in the priority queue
###################################################################################################
class QueueItem:
    
    ############################################################################
    # Basic initialization function
    ############################################################################
    def __init__(self, is_terminal = False, probability = 0.0, parse_tree = []):
        self.is_terminal = is_terminal      ##-Used to say if the parse_tree has any expansion left or if all the nodes represent terminals
        self.probability = probability      ##-The probability of this queue items
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
    def __init__(self, backup_save_comm, backup_restore_comm):
        self.p_queue = []  ##--The actual priority queue
        self.max_probability = 1.0 #--The current highest priority item in the queue. Used for memory management and restoring sessions
        self.min_probability = 0.0 #--The lowest prioirty item is allowed to be in order to be pushed in the queue. Used for memory management
        self.max_queue_size = 50000 #--Used for memory management. The maximum number of items before triming the queue. (Note, the queue can temporarially be larger than this)
        self.reduction_size = self.max_queue_size - self.max_queue_size // 4  #--Target size for the p_queue when it is reduced for memory management
        
        self.backup_save_comm = backup_save_comm
        self.backup_restore_comm = backup_restore_comm         

        
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
 
 
    #####################################################################################################################
    # Finds a divider in the input_list where to delete items
    # Basically it first sorts the list
    # Then it goes to where the desired trim location and then finds the last item in the list with that probability
    #####################################################################################################################
    def find_list_delete_point(self, input_list, target_size):
        ##--First sort the list so we can easily delete the least probable items--##
        ##--Aka turn it from a heap into a sorted list, since heap pops are somewhat expensive--##
        input_list.sort()
        
        ##--Save the size information about the list
        orig_size = len(input_list)
        
        ##--divider represents the point where we are going to cut the list to remove low probability items
        divider = target_size
        
        ##--Shouldn't happen so fail out
        if divider > orig_size:
            raise Exception
        
        ##--Now find the divider we want to cut in case multiple items in the current divider share the same probability
        while (divider < orig_size-1) and (input_list[divider].probability == input_list[divider+1].probability):
            divider = divider + 1
            
        ##--Sanity check for edge case where nothing gets deleted
        if divider == orig_size - 1:
            print("Could not trim one of the storage lists since too many items have the same probability", file=sys.stderr)
            print("Not so much a bug as an edge case I haven't implimented a solution for. Performance is going to be slow until you stop seeing this message --Matt", file=sys.stderr)
        
        return divider

        
    ###############################################################################
    # Memory managment function to reduce the size of the priority queue by
    # deleting the last 1/2 ish of the priority queue
    # It's not an exact number since if multiple items have the same probability
    # and those items fall in the divider of the priority queue then it will save
    # all of them.
    # Aka if the list looks like [0,1,2,3,3,3,7], it will save [0,1,2,3,3,3]
    # If the list looked like [0,1,2,3,4,5,6,7] it will save [0,1,2,3]
    # There is an edge case where no items will be deleted if they all are the same probabilities
    ###############################################################################
    def trim_queue(self):
        
        ##--Find the point at where we want to trim the priority queue
        divider =  self.find_list_delete_point(self.p_queue, self.reduction_size)
        
        ##--Assign the min probabilty to the item currently in the divider of the queue--##
        self.min_probability = self.p_queue[divider].probability
        
        ##--Save the items off into the storage list
        self.backup_save_comm.put({'Command':'Save','Value':self.p_queue[divider+1:]})
            
        ##--Delete the entries from the p_queue
        del(self.p_queue[divider+1:])

        ##--Re-heapify the priority queue
        heapq.heapify(self.p_queue)
        
        ##--This can happen if the queue is full of items all of the same probability
        if len(self.p_queue) == self.max_queue_size:
            return RetType.QUEUE_FULL_ERROR
        ##--Not an immediate problem but this state will cause issues with resuming sessions. For now report an error state
        if self.min_probability == self.max_probability:
            return RetType.QUEUE_FULL_ERROR
        
        return RetType.STATUS_OK
        

    ###############################################################################
    # Rebuild the priority queue when it becomes empty
    # Currently just copying items from the storage list back into the priorty queue
    ###############################################################################
    def rebuild_queue(self,pcfg):
        ##--Remove the min probability
        ##--Depending on what type of memory management functionality is in place this may be raised
        ##--at a later point as items get copied back into the priority queue
        self.min_probability = 0
        self.p_queue = []
        
        ##--Get values from the backup storage queue
        #-Send request for data
        self.backup_save_comm.put({'Command':'Send'})
        #-Grab data from the queue once it's placed there
        backup_data = self.backup_restore_comm.get()
        
        self.p_queue = backup_data['Value']
        self.min_probability = backup_data['Min_Prob']
   
        #--Now re-hepify the priority_queue
        heapq.heapify(self.p_queue)
        
        ##--This can happen if the queue is full of items all of the same probability
        if len(self.p_queue) >= self.max_queue_size:
            return RetType.QUEUE_FULL_ERROR
        ##--Not an immediate problem but this state will cause issues with resuming sessions. For now report an error state
        if self.min_probability == self.max_probability:
            return RetType.QUEUE_FULL_ERROR
        
        return RetType.STATUS_OK   
    
    
    #####################################################################################################################
    # Stores a QueueItem in the backup storage mechanism, or drops it depending on how that storage mechanism handles it
    #####################################################################################################################
    def insert_into_backup_storage(self,queue_item):
        ##--Insert the item
        self.backup_save_comm.put({'Command':'Save','Value':[queue_item]})
    
    
    ###############################################################################
    # Pops the top value off the queue and then inserts any children of that node
    # back in the queue
    #
    # Args:
    #   pcfg = the grammar to use
    #   queue_item_list = The list of terminals to return. 
    #   block_size = The number of terminals to return if possible
    ###############################################################################
    def next_function(self,pcfg, queue_item_list = [], block_size = 1):
        
        ##--Only return terminal structures. Don't need to return parse trees that don't actually generate guesses 
        while True:
            ##--First check if the queue is empty
            while len(self.p_queue) == 0:
                ##--If there was some memory management going on, try to rebuild the queue
                if self.min_probability != 0.0:
                    self.rebuild_queue(pcfg)
                ##--The grammar has been exhaused, exit---##
                else:
                    ##--Splitting up the return value on if there were any items returne or not
                    ##--The next call will cause a RetType.QUEUE_EMPTY regardless though
                    if len(queue_item_list) == 0:
                        return RetType.QUEUE_EMPTY
                    else:
                        return RetType.STATUS_OK
                
            ##--Pop the top value off the stack
            queue_item = heapq.heappop(self.p_queue)
            self.max_probability = queue_item.probability
            ##--Push the children back on the stack
            ##--Currently using the deadbeat dad algorithm as described in my dissertation
            ##--http://diginole.lib.fsu.edu/cgi/viewcontent.cgi?article=5135
            self.add_children_to_queue(pcfg, queue_item)
            
            ##--Memory management
            if len(self.p_queue) > self.max_queue_size:
                self.trim_queue()

            ##--If it is a terminal structure break and return it
            if queue_item.is_terminal == True:
                queue_item_list.append(queue_item)
                if len(queue_item_list) >= block_size:
                    break

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
                ##--Else insert it into the backup storage
                else:
                    self.insert_into_backup_storage(child_node)
            else:
                print("Hmmm, trying to push a parent and not a child on the list", file=sys.stderr)
