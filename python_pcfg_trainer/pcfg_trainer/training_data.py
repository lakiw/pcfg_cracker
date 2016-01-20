#!/usr/bin/env python3

#############################################################################
# This file contains the top level functionality to parse a password dataset
# and generate a grammar from it
#
# The TrainingData class takes as input individual passwords from the "parse" functionality
# but it remembers state so multiple password parsing results will be saved
# it also determines which particual parsing functions to call for the individual password under
# the PasswordParser class
#############################################################################

##--User Defined Imports---##
from pcfg_trainer.ret_types import RetType
from pcfg_trainer.password_parser import PasswordParser
from pcfg_trainer.data_list import ListType, DataList
        
############################################################################
# Holds the data that we'll be saving for the grammar
# For example it has the BaseStructures, Digit probabilities, etc
############################################################################
class TrainingData:
    def __init__(self):

        ##Init Base Structures
        self.base_structure = DataList(type= ListType.FLAT)
        
        ##Init Digits
        self.digit_structure = DataList(type= ListType.LENGTH)

        ##Init Special
        self.special_structure = DataList(type= ListType.LENGTH)

        ##Init Capitalization
        self.cap_structure = DataList(type= ListType.LENGTH)

        ##Init Keyboard
        self.keyboard_structure = DataList(type= ListType.LENGTH)

        ##Init Replacement
        self.replace_structure = DataList(type= ListType.FLAT)

        ##Init Context Sensitive Values
        self.context_structure = DataList(type= ListType.LENGTH)
        
        ##Number of passwords that were rejected
        ##Used for record keeping and debugging
        self.num_rejected_passwords = 0
        
        ##Number of valid passwords trained on
        ##Used for record keeping and debugging
        self.valid_passwords = 0
    
    ###################################################################################
    # Checks to see if the input password is valid for this training program
    # Invalid in this case means you don't want to train on them
    # Returns 
    #   RetType.IS_TRUE if the password is valid
    #   RetType.IS_FALSE if invalid 
    ###################################################################################
    def check_valid(self,input_password):
        # Don't accept blank passwords for training. I'm adding that check here vs in the file IO section
        # becasue in some cases you might want to train on blank passwords
        if len(input_password) == 0:
            return RetType.IS_FALSE
        
        # Remove e-mail addrsses since the PCFG doesn't handle them well
        # By that, the way the grammar is set up it's not smart enough to add '.com'
        # Instead it might add '!foo' or '$bar' since it replaces it context free
        # While a special case could be made for e-mails, it would only help when
        # attacking large sets of disclosed passwords, since in a targeted attack
        # you would be attacking a specific e-mail vs a randomly generated one.
        # I'm not that interested in the random large set attacks, so I'm just rejecting
        # e-mails from training. And that's the long reason why I'm rejecting e-mails.
        if ".com" in input_password:
            return RetType.IS_FALSE
        if ".org" in input_password:
            return RetType.IS_FALSE
        if ".edu" in input_password:
            return RetType.IS_FALSE
        if ".gov" in input_password:
            return RetType.IS_FALSE
        if ".mil" in input_password:
            return RetType.IS_FALSE
        return RetType.IS_TRUE
    
    ###################################################################################
    # Actually do the work of parsing a password and inserting it into the grammar
    # Variable Types:
    #     input_password = the password to parse
    ###################################################################################
    def parse(self, input_password):
        
        ##-Check to see if the password is a valid password to parse--##
        ret_value = self.check_valid(input_password)
        ##-If the password isn't valid for the training data
        if ret_value != RetType.IS_TRUE:
            self.num_rejected_passwords = self.num_rejected_passwords + 1
            if ret_value == RetType.IS_FALSE:
                return RetType.STATUS_OK
            ##--Sanity check to pass an unexpected state back up the stack
            else:
                print("Error checking to see if the input password should be rejected")
                return ret_value
        
        self.valid_passwords = self.valid_passwords + 1
            
        ##-Initialize the PasswordParser for this particular password
        cur_pass = PasswordParser(input_password)
        
        #################################################################
        ##--Parse out all the keyboard combinations
        #################################################################
        ##--items holds all the keyboard combos found
        items = []
        ret_value = cur_pass.parse_keyboard(items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing keyboard combos")
            return ret_value
        ##--Now update the keyboard combo list
        ret_value = self.keyboard_structure.insert_list(items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing keyboard combos")
            return ret_value
            
        ##################################################################
        ##--Parse out all of the context sensitive combinations
        ##################################################################
        ##--items holds all the context sensitive combos found
        items = []
        ret_value = cur_pass.parse_context_sensitive(items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing context sensitive combos")
            return ret_value
        ##--Now update the context sensitive combo list
        ret_value = self.context_structure.insert_list(items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing context sensitive combos")
            return ret_value
        
        return RetType.STATUS_OK
    
    ###########################################################################################
    # Finalizes the grammar and gets it ready to saved
    # The precision value is the precision to store the values
    # For example, a precision of 4 could save 0.0001 while a
    # precision of 5 could save 0.00012
    # Setting default to 7, (will measure 1 in a million)
    ############################################################################################
    def finalize_data(self, precision=7):
        ##--Calculate probabilities for keyboard combos--##
        ret_value = self.keyboard_structure.update_probabilties(precision = precision)
        if ret_value != RetType.STATUS_OK:
            print("Error finalizing the data")
            return ret_value
        ##--Calculate probabillities for context sensitive combos--##
        ret_value = self.context_structure.update_probabilties(precision = precision)
        if ret_value != RetType.STATUS_OK:
            print("Error finalizing the data")
            return ret_value
        print(self.context_structure.main_dic)
        return RetType.STATUS_OK