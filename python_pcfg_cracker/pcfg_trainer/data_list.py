#!/usr/bin/env python3

#############################################################################
# DataList is a class that holds a list of items and can provide statistics on them
#
# The probablity statistics are only updated on a call to update_probability
# to reduce running time during multiple inserts
#############################################################################

import enum
import json
from decimal import *
import copy

##--User Defined Imports---##
from pcfg_trainer.ret_types import RetType

#########################################################################
## Enum of list types to make my code more readabe
##########################################################################
@enum.unique
class ListType(enum.IntEnum):    
    ## flat list, everything goes into one list/dictionary
    FLAT                            = 0       
    ## break lists up by length. All items of length N go into the same list/dictionary
    LENGTH                          = 1  

##########################################################################
# Conceptually holds a list of items of type data_holder
# In practice it is a bit more difficult since it can hold multiple lists
# based on the item's length if that is important
# That way probabilites for one letter digits are different from six letter digits
# This class holds all the functionality to insert a new item into the list
# as well as calculate probabilities for the entire list
#
# In fact, it really uses a dictionary to keep track of all the different values for
# each of the conceptual lists
##########################################################################
class DataList:
    
    ################################################
    # initialize the list
    # Variables:
    #     type = [ListType.FLAT, ListType.LENGTH]  ##--Way to create multiple sub lists. FLAT = no sub lists, LENGTH = break it up by length
    ################################################
    def __init__(self, type = ListType.FLAT , config_name = 'DEFAULT', config_data = {'Name':'Default','Comments':'','Directory':'Default','Filenames':'Default','Inject_type':'Wordlist','Function':'Copy','Is_terminal':'True'}):      
        ##--Used to break up the lists by type--##
        self.type = type
        
        ##--Holds the actual lists--##
        ##-- for ListType.FLAT the main key is always '0'
        ##-- for ListType.Length the main key is the length of items in the list
        ##-- The dictionary takes the format of
        ##    {6:{
        ##        'lists':{
        ##            '123456':{
        ##                'num':5,
        ##                'probability':Decimal(0.1)
        ##            },
        ##            '654321':{
        ##                'num':5,
        ##                'probability':Decimal(0.1)
        ##            },
        ##            ...,
        ##        },
        ##        'total_size':50
        ##    }
        ##-- the main key is the index key, (for example length of the words if type LENGTH)
        ##-- the sub key is the value we are storing in the list
        self.main_dic = {}
        
        ##--Configuration File Info--##
        ##-- Holds information about the list to write to the config file
        ##-- Breaking it out by list item since that should hopefully make it easier
        ##-- to add / modify list items in one spot
        self.config_name = config_name
        self.config_data = config_data

        ## Set the list type in the config file
        if self.type == ListType.FLAT:
            self.config_data['File_type'] = 'Flat'
        elif self.type == ListType.LENGTH:
            self.config_data['File_type'] = 'Length'
           
        
    ##################################################
    # Returns a config file for saving to disk
    # Note, this may have some differences in how the data_list item
    # was initialized
    ##################################################
    def update_config(self, section_config={}):
        ##--Copy the config file over to the output
        for key in self.config_data.keys():
            section_config[key] = copy.deepcopy(self.config_data[key])
        ##--Update the filenames for the json output--##
        if self.type == ListType.LENGTH:
            file_list = []
            for item in self.main_dic.keys():
                file_list.append(str(item) + ".txt")
            section_config['Filenames'] = json.dumps(file_list)
        elif self.type == ListType.FLAT:
            section_config['Filenames'] = json.dumps([self.config_data['Filenames']])
        else:
            print("Error, unsupported list type")
            return RetType.ERROR_QUIT
            
        return RetType.STATUS_OK
    

    ##################################################
    # Manually insert an item + probability into a list
    # Currently only supports ListType.FLAT
    # Really just a hack to get Markov probabilities in here
    # Note, this totally messes with all the other stats besides
    # probabilities so may want to clean this up in the future
    ###################################################
    def manual_insert(self, item, precision = 7, probability = 1.0):
        if self.type != ListType.FLAT:
            print("Error calling manual_insert on a non-flat list")
            raise
        
        working_dictionary = self.main_dic[0]
        with localcontext() as ctx:
            ctx.prec = precision
            ##--Doing this weird by multiplying by Decimal(1.0) to have the precision be applied properly
            working_dictionary['lists']['M'] = {'probability':Decimal(probability) * Decimal(1.0)}
            
    
    ##################################################
    # inserts an item into the list
    ##################################################
    def insert(self, item):
        
        ##--Find out the dictionary key to perform the lookup/insertion on--##
        if self.type == ListType.FLAT:
            key = 0
        elif self.type == ListType.LENGTH:
            key = len(item)
        ##--shouldn't happen but alert and quit if it does
        else:
            print("Error, unsupported list type")
            return RetType.ERROR_QUIT
            
        ##--First, get the top level dictionary that holds the list we'll be updating, or create it if necessary when a KeyError is thrown--##
        try:
            working_dictionary = self.main_dic[key]
        ##---The key doesn't exist so create it
        except KeyError:
            self.main_dic[key] = {'lists':{},'total_size':0}
            working_dictionary = self.main_dic[key]
        
        ##--Update the total number of items--#
        working_dictionary['total_size'] = working_dictionary['total_size'] + 1
        
        ##--Now get the item if it exists or create it if necessary when a KeyError is thrown--##
        try:
            working_item = working_dictionary['lists'][item]
        except KeyError:
            working_dictionary['lists'][item] = {'num':0}
            working_item = working_dictionary['lists'][item]
            
        ##--Now update the count for the item
        working_item['num'] = working_item['num'] + 1
        
        return RetType.STATUS_OK     
        
    ##################################################
    # inserts a list of items all at once
    ##################################################
    def insert_list(self, item_list):
        ##--Simply loop through all the items in the list and call insert() on them
        for item in item_list:
            ret_value = self.insert(item)
            ##--Pass errors back up the stack and stop working--##
            if ret_value != RetType.STATUS_OK:
                print("Error inserting item into DataList")
                return ret_value     
        return RetType.STATUS_OK
        
    #####################################################
    # Updates the probabilities of all the items stored
    # Manually forcing people to call this vs doing this
    # on every new insert to lower the computation costs
    # of inserts
    # The precision value is the precision to calculate the values
    # For example, a precision of 4 could save 0.0001 while a
    # precision of 5 could save 0.00012
    # Setting default to 7, (will measure 1 in a million)
    # NOTE: Due to the way Decimal handles division, the precsion
    #       is not guarenteed to be exactly enforced
    #
    # Coverage is used to rebase the max amount that these items should
    # equal. Currently adding this to add after the fact Markov into the base structure
    # coverage = 1.0 is no change, 0.5 would represent a 50% reduction
    #####################################################
    def update_probabilties(self,precision=7, coverage=1.0):
        ##--Set the precision--##
        ##--Updating the precision using localcontext so that will apply to the Decimal math
        with localcontext() as ctx:
            ctx.prec = precision
            ##--Walk the main top level dictionary and assign probabilities to each item
            for main_key, main_item in self.main_dic.items():
                ##--Now walk each list
                for list_key, list_item in main_item['lists'].items():
                    ##--Calculate the probability
                    list_item['probability'] = Decimal(coverage) * (Decimal(list_item['num']) / Decimal(main_item['total_size']))
                
        return RetType.STATUS_OK
        
    
    #########################################################################
    # Creates a dictionary of sorted lists of all the main_dic (name,probability) tuples
    # Probability smoothing takes place here to to combine items of similar enough probabilty
    ## Dictionary for saving the sorted output of the values
    ##-- The dictionary takes the format of
    ##      {0:[sorted list of index lists into the main_dic]
    ##
    ##-- For example consider the following main_dic
    ##      {3:{
    ##          'lists:{
    ##              'edf': num:1,
    ##              'probability':Decimal(0.1)
    ##          },              
    ##          'lists:{
    ##              'abc': num:5,
    ##              'probability':Decimal(0.5)
    ##          },
    ##          'lists:{
    ##              'xyz': num:4,
    ##              'probability':Decimal(0.4)
    ##          },
    ##          'total_size':10
    ##      }
    ##
    ##-- It will create the sorted_index
    ##      {3:[('abc',Decimal(0.5)),('xyz',Decimal(0.4)),('edf',Decimal(0.1))]}
    ##
    #########################################################################
    def get_sorted_results(self, sorted_results, precision = 7, smoothing = 0):
        try:
            ##Loop through the main indexes and sort the results of each sub dictionary
            for index in self.main_dic:
                ##--Set the key for the results to be the filename
                if self.type == ListType.FLAT:
                    if index != 0:
                        print("Wow that should not happen. Error sorting the results")
                        return RetType.GENERIC_ERROR
                    try:
                        key = self.config_data['Filenames']
                    except KeyError as error:
                        print("Error reading config data for structure. The config needs to specify the filename to save results for. This is a programing problem, not a user error")
                        return RetType.GENERIC_ERROR
                else:
                    try:
                        ##--Right now the 'Filename' should just be '.txt'.
                        key = str(index) + self.config_data['Filenames']
                    except KeyError as error:
                        print("Error reading config data for structure. The config needs to specify the filename to save results for. This is a programing problem, not a user error")
                        return RetType.GENERIC_ERROR
                sorted_results[key] = []
                
                ##--Note, if you want values with the same probability to be sorted in dictionary order then add a sort above this to sort by name, then do the sort below--##
                ##--Not doing that now since A) It's just a cosmetic feature, and B) I still need to see what the running time is
                # Sort based on the probability index
                for sorted_item in sorted(self.main_dic[index]['lists'], key = lambda x: (self.main_dic[index]['lists'][x]['probability']), reverse = True):
                    ##--Now save the data in the sorted_results list
                    sorted_results[key].append((sorted_item,self.main_dic[index]['lists'][sorted_item]['probability']))
                
                ##--Now apply probability smoothing
                ##--Only do this if probabilty smoothing is enabled and there is more than one item
                if (smoothing != 0) and (len(sorted_results[key]) > 1):
                    self.__smooth_probabilities(sorted_results[key] , precision, smoothing)
                    
                                
                    
        except KeyError as error:
            print("Error: " + str(error))
            return RetType.GENERIC_ERROR
        return RetType.STATUS_OK
    
    
    ##############################################################################################
    # Applies probability smoothing to the "sorted_list"
    # 
    # Currently creates "runs" of all items that are within smoothing * "prob first item in run"
    # When an item falls outside the run, the run resets with that item being the new head of a run
    # When a run of two or more items occur, their probabilty is set to (sum of all items probabilities)/(number of items)
    # This way the top item's probability is reduced while other items potentially gain a higher probability
    # In short, it "smooths" the probability of similar items
    #
    # Example: [(a,0.5), (b,0.3), (c,0.1), (d,0.099), (e,0.001)], smoothing = 0.02 (which is a 2% smoothing)
    #
    # 1) For a run starting with (a,0.5), the minimum prob to continue the run would be
    #  --- 0.5 - (0.5 * 0.02) = 0.49
    # 2) b is too low so it forms the start of a new run. The minimum prob to continue would be
    #  --- 0.3 - (0.3 * 0.02) = 0.294
    # 3) c is too low so it forms the start of a new run. The minimum prob to continue would be
    #  --- 0.1 - (0.1 * 0.02) = 0.098
    # 4) d matches it so the run continues
    # 5) e does not match it so the run ends. e is the last item so no more runs occur
    # 6) At the same time to finish up the previous run, the probability of c and d is set to be the same smoothed prob between them
    #  --- (0.1 + 0.099) / 2 = 0.0995
    #    the list then look like
    #    [(a,0.5), (b,0.3), (c,0.0995), (d,0.0995), (e,0.001)]
    # 
    #
    # Note, there are a lot of other ways to do this and there can be some counter-intutive results from this approach
    # For example, two items might be near to the same prob but fall into different runs since the 2nd item is past the threshold
    # to match with the first run.
    #
    # The reason I choose this method was because it's fairly straight forward, all the probabilities will still add up to 100% at the end
    # and a couple other options I considered had worse side effects. Still, looking for a better smoothing algorithm as it could potentially
    # add a lot of value in the future
    #######################################################################################################
    def __smooth_probabilities(self, sorted_list , precision = 7, smoothing = 0):
        ##--set the precision. That way the smoothed probabilities will fall into what the user specified for maximum precision
        with localcontext() as ctx:
            ctx.prec = precision
            
            ##--The probability of the most recent item (for debuging)
            top_probability = sorted_list[0][1]  
            
            ##--The probability that the item has to equal or exceed for it to be part of a run and smoothing to be applied 
            match_probability = top_probability - (top_probability * Decimal(smoothing))
            
            ##--The index of the top item in the run so we know how far to go back to apply smoothing
            top_index = 0
            
            ##--The combined (added) probablity of all items being smoothed
            ##--Used for recalulating their new probability
            combined_prob_total = top_probability

            ##--Starting at the second item in the list
            ##--so the initialization of this loop is handled above this
            for index, value in enumerate(sorted_list[1:], start = 1):  
                ##--This item is not going to be smoothed with the previous item
                if value[1] < match_probability: 
                    
                    ##--There was a previous run going on
                    ##--Close it up and save the results
                    if top_index != index - 1:
                        ##--Find the probability to assign all the items
                        new_probability = combined_prob_total / Decimal(index - top_index)
                        
                        ##--Now smooth out the probabilty for every item in the set
                        for fixup_index in range(top_index, index):
                            sorted_list[fixup_index] = (sorted_list[fixup_index][0],new_probability)                               
                        
                    ###--Set up new run    
                    top_index = index
                    top_probability = value[1]
                    combined_prob_total = value[1]
                    match_probability = top_probability - (top_probability * Decimal(smoothing))
                
                ##--This is part of a run
                else:
                    combined_prob_total += value[1]
  
            ##--Now need to cover if the last item was a part of a run
            if top_index != len(sorted_list) -1:
                ##--Find the probability to assign all the items
                new_probability = combined_prob_total / Decimal(len(sorted_list) - top_index)     
                ##--Now smooth out the probabilty for every item in the set
                for fixup_index in range(top_index, len(sorted_list)):
                    sorted_list[fixup_index] = (sorted_list[fixup_index][0],new_probability)    