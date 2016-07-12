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
from pcfg_manager.priority_queue import QueueItem

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
        
        
    #############################################################################
    # Run when the class gets started as its own process
    # Data from backup_save_comm takes the form of a dictionary {"Command":"<command>", "Value":[List of items]}
    #     Command = Save, Send, Quit 
    #############################################################################
    def start_process(self, backup_save_comm, backup_restore_comm):
        while True:
            command = backup_save_comm.get()
            ##--If we need to save/process extra values
            if command["Command"] == "Save":
                self.insert_into_backup_storage(command["Value"])
            
            ##--If we need to send back values
            elif command["Command"] == "Send":
                self.pull_from_storage(send_pipe)
                
            ##--If we need to finish up the process and quit
            elif command["Command"] == "Quit":
                break
            
            ##--General error use-case
            else:
                print("Error with unknown command sent to backup server " + str(command["Command"]),file=sys.stderr)
                raise Exception
      
      
    #####################################################################################################################
    # Stores a QueueItem in the backup storage mechanism, or drops it depending on how that storage mechanism handles it
    #####################################################################################################################
    def insert_into_backup_storage(self,work_list):
        ##--Insert the item
        self.storage_list.extend(work_list)
      
        return RetType.STATUS_OK    

    #####################################################################################################################
    # Stores a QueueItem in the backup storage mechanism, or drops it depending on how that storage mechanism handles it
    #####################################################################################################################
    def pull_from_storage(self,send_pipe):
        
        return RetType.STATUS_OK
        