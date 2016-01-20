#!/usr/bin/env python3

#############################################################################
# DataList is a class that holds a list of items and can provide statistics on them
#
# The probablity statistics are only updated on a call to update_probability
# to reduce running time during multiple inserts
#############################################################################

import enum
from decimal import *

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
    def __init__(self, type = ListType.FLAT ):        
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
    #####################################################
    def update_probabilties(self,precision=7):
        ##--Set the precision--##
        with localcontext() as ctx:
            ctx.prec = precision
            ##--Walk the main top level dictionary
            for main_key, main_item in self.main_dic.items():
                ##--Now walk each list
                for list_key, list_item in main_item['lists'].items():
                    ##--Calculate the probability
                    list_item['probability'] = Decimal(list_item['num']) / Decimal(main_item['total_size'])
        
        return RetType.STATUS_OK