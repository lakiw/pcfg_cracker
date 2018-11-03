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
import bisect

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
    def __init__(self):
        self.storage_list = [] #--Used to store low probability nodes to keep the size of p_queue down
        self.storage_min_probability = 0.0 #-- The lowest probability item allowed into the storage list. Anything lower than this is discarded
        self.storage_size = 5000000 #--The maximum size to save in the storage list before we start discarding items
        self.backup_reduction_size = self.storage_size - self.storage_size // 4
        self.restore_size = 50000 #--Size of data to send back when requested. May want to change this to be set somewhere else
        
        
    #############################################################################
    # Run when the class gets started as its own process
    # Data from backup_save_comm takes the form of a dictionary {"Command":"<command>", "Value":[List of items]}
    #     Command = Save, Send, Quit, Status 
    #############################################################################
    def start_process(self, backup_save_comm, backup_restore_comm):
        while True:
            command = backup_save_comm.get()
            
            ##--If we need to save/process extra values
            if command["Command"] == "Save":
                self.insert_into_backup_storage(command["Value"])
            
            ##--If we need to send back values
            ##-- Note, since this is being treated more like a pipe with only one sender, don't need to check
            ##--if other save commands are waiting behind this. If there are multiple processes pushing to this queue
            ##--then additional logic may need to be added later
            elif command["Command"] == "Send":
                self.pull_from_storage(backup_restore_comm)
             
            ##--Return the status of the backup storage
            elif command["Command"] == "Status":
                backup_restore_comm.put({"Size":len(self.storage_list)})
                
            ##--If we need to finish up the process and quit
            elif command["Command"] == "Quit":
                break
            
            ##--General error use-case
            else:
                print("Error with unknown command sent to backup server " + str(command["Command"]),file=sys.stderr)
                raise Exception
      
    
    #####################################################################################################################
    # Finds a divider in the input_list where to delete items
    # Goes to where the desired trim location and then finds the last item in the list with that probability
    #####################################################################################################################
    def find_list_delete_point(self, input_list, target_size):

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
    
    #####################################################################################################################
    # Stores a QueueItem in the backup storage mechanism, or drops it depending on how that storage mechanism handles it
    #####################################################################################################################
    def insert_into_backup_storage(self,work_list):
        ##--Insert the items
        for item in work_list:
            bisect.insort(self.storage_list, item)
        
        ##--Check if the backup storage has grown too large
        if len(self.storage_list) >= self.storage_size:
            ##--Find the point at where we want to trim the storage_list
            divider =  self.find_list_delete_point(self.storage_list, self.backup_reduction_size)
             
            ##--Delete the entries from the list
            del(self.storage_list[divider+1:])
            self.storage_min_probability = self.storage_list[-1].probability
            ##--This can happen if the queue is full of items all of the same probability
            if len(self.storage_list) == self.storage_size:
                return RetType.QUEUE_FULL_ERROR

        return RetType.STATUS_OK    

    #####################################################################################################################
    # Stores a QueueItem in the backup storage mechanism, or drops it depending on how that storage mechanism handles it
    #####################################################################################################################
    def pull_from_storage(self,backup_restore_comm):
        
        ##--If we can copy the entire storage list into the priority queue
        if len(self.storage_list) <= self.restore_size:
            backup_restore_comm.put({'Value':list(self.storage_list), 'Min_Prob':self.storage_min_probability})
            self.storage_list = []
            
        else:
            divider = self.restore_size
            while (divider < len(self.storage_list)-1) and (self.storage_list[divider].probability == self.storage_list[divider + 1].probability):
                divider = divider + 1
            
            backup_restore_comm.put({'Value':list(self.storage_list[:divider+1]), 'Min_Prob':self.storage_list[divider].probability})
            del(self.storage_list[:divider+1])        
        
        return RetType.STATUS_OK
        
