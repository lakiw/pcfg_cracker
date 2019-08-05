#!/usr/bin/env python3

################################################################################
#
# Name: PCFG_Guesser Priority Queue Handling Function
# Description: Section of the code that is responsible of outputting all of the
#              pre-terminal values of a PCFG in probability order.
#              Because of that, this section also handles all of the memory 
#              management of a running password generation session
#
################################################################################


import sys   # Used for printing to stderr
import heapq



## Wrapper for a parse tree item
#
# This is so the Priority Queue can determine where to place a parse tree item
# Aka it holds all the "less than", "greater than", "equal to", logic for abs
# parse tree
#
class QueueItem:
    
    
    ## Initialization function
    #
    def __init__(self, pt_item):
        self.pt_item = pt_item
        
        
    ## Need to have a custom compare functions for use in the priority queue
    #
    # I have to do this the reverse of what I'd normally expect
    # since the priority queue will output stuff of lower values first.
    # Aka if there are two items with probabilities of 0.7 and 0.4, the PQueue 
    # will by default output 0.4
    #
    def __lt__(self, other):
        return self.pt_item['prob'] > other.pt_item['prob']
    
    def __le__(self, other):
        return self.pt_item['prob'] >= other.pt_item['prob']
        
    def __eq__(self, other):
        return self.pt_item['prob'] == other.pt_item['prob']
        
    def __ne__(self, other):
        return self.pt_item['prob'] != other.pt_item['prob']
        
    def __gt__(self, other):
        return self.pt_item['prob'] < other.pt_item['prob']
        
    def __ge__(self, other):
        return self.pt_item['prob'] <= other.pt_item['prob']


## Main class for handling the classic PCFG next function using a PQueue
#
# This is the "next" function to use if you want to generate guesses in true
# probability order
#
# I may make changes to the underlying priority queue code in the future to 
# better support removing low probability items from it when it grows too 
# large. Therefore I felt it would be best to treat it as a class. Right now 
# though it uses the standared python queue HeapQ as its backend
#
class PcfgQueue:


    ## Basic initialization function
    #
    # saved_session is a dictionary that takes the following format:
    #
    # {
    #    'min_probability': float,
    #    'max_probability': float,
    # }
    #
    def __init__(self, pcfg, save_config = None):
    
        # Holds the grammar
        self.pcfg = pcfg
    
        # The actual priority queue
        self.p_queue = []
        
        # The current highest priority item in the queue. Used for memory 
        # management and restoring sessions
        self.max_probability = 1.0
        
        # The lowest prioirty item is allowed to be in order to be pushed in 
        # the queue. Used for memory management
        self.min_probability = 0.0 
        
        # Used for memory management. The maximum number of items before 
        # triming the queue. 
        # Note: the queue can temporarially be larger than this
        self.max_queue_size = 50000
        
        ## New Guessing Session
        #
        if save_config == None:
            # Initalize the priority queue with all of the initial base 
            # structures from the pcfg
            for base_item in self.pcfg.initalize_base_structures():
                heapq.heappush(self.p_queue, QueueItem(base_item))
            
            return
                
        ## Restore Guessing Session
        #
        self.min_probability = save_config.getfloat('guessing_info', 'min_probability')
        self.max_probability = save_config.getfloat('guessing_info', 'max_probability')
        
        for base_item in self.pcfg.initalize_base_structures():
            self.restore_base_item(base_item)
            
            
    ## Pops the top value off the queue and inserts children back
    #
    # Return Values:
    #   pt_item: A parse tree item that was popped off the queue
    #
    #   None: If no items are left to be popped from the queue
    #
    def next(self):
         
        # Check if the queue is empty
        if len(self.p_queue) == 0:
            return None
            
        # Pop the top value off the queue
        queue_item = heapq.heappop(self.p_queue)
        self.max_probability = queue_item.pt_item['prob']
        
        ## Push the children back on the stack
        #
        # Currently using the deadbeat dad algorithm as described 
        # in my dissertation:
        # http://diginole.lib.fsu.edu/cgi/viewcontent.cgi?article=5135
        #
        for child in self.pcfg.find_children(queue_item.pt_item):
            self.insert_queue(child)
            
        return queue_item.pt_item
            
    
    ## Inserts an item into the pqueue
    #
    # Making this its own function in case I decide to change how the pqueue
    # operates in the future
    #
    # Input Values:
    #    queue_item: The value to save in the pqueue
    #
    def insert_queue(self, queue_item):    
        heapq.heappush(self.p_queue, QueueItem(queue_item))
    
    
    ## Restores all the items from the base_item to the pqueue
    #
    # This is used to restore a previous guessing session
    #
    # Input Values:
    #    base_item: A pt of the most probable pre-terminal for a base_item
    #
    def restore_base_item(self, base_item):   
        self.pcfg.restore_prob_order(base_item, self.max_probability, self.min_probability, self.insert_queue)
        
        
    ## Updates the config file for saving/loading sessions, with current status
    #
    # Input Values:
    #    save_config: A configparser object to save the current state
    #
    def update_save_config(self, save_config):
        save_config.set('guessing_info', 'min_probability', str(self.min_probability))
        save_config.set('guessing_info', 'max_probability', str(self.max_probability))    
     

        
