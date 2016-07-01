#!/usr/bin/env python3

########################################################################################
#
# Name: PCFG_Cracker "Queue Storage" functionality
# Description: Handles the overflow storage for the priority queue
#              Breaking this up into its own class so that I can run this as a multiprocess
#              thread, and also so it is easier to modify its behavior in the future
#
#########################################################################################

import sys   #--Used for printing to stderr

from pcfg_manager.ret_types import RetType

###################################################################################################
# Used to hold the overflow storage for the main priority queue
# If items are deleted to save memory, also responsible for re-creating them in the future when they
# will be needed
###################################################################################################
class QueueStorage:

	############################################################################
    # Basic initialization function
    ############################################################################
    def __init__(self, verbose = False):
    	self.storage_list = [] #--Used to store low probability nodes to keep the size of p_queue down
        self.storage_min_probability = 0.0 #-- The lowest probability item allowed into the storage list. Anything lower than this is discarded
        self.storage_size = 5000000 #--The maximum size to save in the storage list before we start discarding items
        self.backup_reduction_size = self.storage_size - self.storage_size // 4

        self.verbose = verbose