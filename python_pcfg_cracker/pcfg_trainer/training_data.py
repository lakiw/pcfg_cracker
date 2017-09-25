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

import os
import codecs
import json

##--User Defined Imports---##
from pcfg_trainer.ret_types import RetType
from pcfg_trainer.password_parser import PasswordParser
from pcfg_trainer.data_list import ListType, DataList
from pcfg_trainer.markov import Markov
        
############################################################################
# Holds the data that we'll be saving for the grammar
# For example it has the BaseStructures, Digit probabilities, etc
############################################################################
class TrainingData:
    def __init__(self):
        
        ##--Holds all of the individual DataList objects for iterating though them when it comes time to save the data
        self.master_data_list = []
        
        ##--Brute force data
        self.markov = Markov()
        
        ######################################################
        ##Init Base Structures
        ######################################################
        config = {
            'Name':'Base Structure',
            'Comments':'Standard base structures as defined by the original PCFG Paper, with some renaming to prevent naming collisions. Examples are A4D2 from the training word "pass12"',
            'Directory':'Grammar',
            'Filenames':'Grammar.txt',
            'Inject_type':'Wordlist',
            'Function':'Transparent',
            'Is_terminal':'False',
            'Replacements': json.dumps([
                {'Transition_id':'A','Config_id':'BASE_A'},
                {'Transition_id':'D','Config_id':'BASE_D'},
                {'Transition_id':'O','Config_id':'BASE_O'},
                {'Transition_id':'K','Config_id':'BASE_K'},
                {'Transition_id':'X','Config_id':'BASE_X'},
                {'Transition_id':'M','Config_id':'BASE_M'},
            ]),
        }     
        self.base_structure = DataList(type= ListType.FLAT, config_name= 'START', config_data = config)
        self.master_data_list.append(self.base_structure)
        
        ########################################################
        ##Init Alpha structures
        ########################################################
        config = {
            'Name':'A',
            'Comments':'(A)lpha letter replacements for base structure. Aka "pass12" = A4D2, so this is the A4. Note, this is encoding specific so non-ASCII characters may be considered alpha. For example Cyrillic characters will be considered alpha characters',
            'Directory':'Alpha',
            'Filenames' : '.txt',
            'Inject_type':'Wordlist',
            'Function':'Shadow',
            'Is_terminal':'False',
            'Replacements': json.dumps([
                {'Transition_id':'Capitalization','Config_id':'CAPITALIZATION'},
            ]),
        }     
        self.letter_structure = DataList(type= ListType.LENGTH, config_name= 'BASE_A', config_data = config)
        self.master_data_list.append(self.letter_structure)
        
        #########################################################
        ##Init Digits
        #########################################################
        config = {
            'Name':'D',
            'Comments':'(D)igit replacement for base structure. Aka "pass12" = L4D2, so this is the D2',
            'Directory':'Digits',
            'Filenames' : '.txt',
            'Inject_type':'Copy',
            'Function':'Copy',
            'Is_terminal':'True', 
        }
        self.digit_structure = DataList(type= ListType.LENGTH, config_name = 'BASE_D', config_data = config)
        self.master_data_list.append(self.digit_structure)
        
        #########################################################
        ##Init Special
        #########################################################
        config = {
            'Name':'O',
            'Comments':'(O)ther character replacement for base structure. Aka "pass$$" = L4S2, so this is the S2',
            'Directory':'Other',
            'Filenames' : '.txt',
            'Inject_type':'Copy',
            'Function':'Copy',
            'Is_terminal':'True', 
        }
        self.special_structure = DataList(type= ListType.LENGTH, config_name = 'BASE_O', config_data = config)
        self.master_data_list.append(self.special_structure)
        
        #########################################################
        ##Init Capitalization
        #########################################################
        config = {
            'Name':'Capitalization',
            'Comments':'Capitalization Masks for words. Aka LLLLUUUU for passWORD',
            'Directory':'Capitalization',
            'Filenames' : '.txt',
            'Inject_type':'Copy',
            'Function':'Capitalization',
            'Is_terminal':'True', 
        }
        self.cap_structure = DataList(type= ListType.LENGTH, config_name = 'CAPITALIZATION', config_data = config)
        self.master_data_list.append(self.cap_structure)
        
        ###########################################################
        ##Init Keyboard
        ###########################################################
        config = {
            'Name':'K',
            'Comments':'(K)eyboard replacement for base structure. Aka "test1qaz2wsx" = L4K4K4, so this is the K4s',
            'Directory':'Keyboard',
            'Filenames' : '.txt',
            'Inject_type':'Copy',
            'Function':'Copy',
            'Is_terminal':'True', 
        }
        self.keyboard_structure = DataList(type= ListType.LENGTH, config_name = 'BASE_K', config_data = config)
        self.master_data_list.append(self.keyboard_structure)
        
        ############################################################
        ##Init Context Sensitive Values
        ############################################################
        config = {
            'Name':'X',
            'Comments':'conte(X)t sensitive replacements to the base structure. This is mostly a grab bag of things like #1 or ;p',
            'Directory':'Context',
            'Filenames' : '.txt',
            'Inject_type':'Copy',
            'Function':'Copy',
            'Is_terminal':'True', 
        }
        self.context_structure = DataList(type= ListType.LENGTH, config_name = 'BASE_X', config_data = config)
        self.master_data_list.append(self.context_structure)
        
        ############################################################
        ##Init Markov brute force smoothing
        ##--Note, currently doing this flat, (will create chains length 1 to MAX)
        ##--May in the future want to do it differently, AKA brute force length 4 characters
        ############################################################
        config = {
            'Name':'M',
            'Comments':'Markov based brute force of a string. Currently based on John the Rippers Markov mode',
            'Directory':'Markov',
            'Filenames':'markov_prob.txt',
            'Inject_type':'Markov',
            'Function':'Markov',
            'Is_terminal':'True',
        }
        self.markov_structure = DataList(type= ListType.FLAT, config_name = 'BASE_M', config_data = config)
        self.master_data_list.append(self.markov_structure)
        
        ##--Hackish way to create the Markov probability threshold--##
        
        ##Number of passwords that were rejected
        ##Used for record keeping and debugging
        self.num_rejected_passwords = 0
        
        ##Number of valid passwords trained on
        ##Used for record keeping and debugging
        self.valid_passwords = 0
    
    
    ###################################################################################
    # Returns a list of all the directories that need to be created to save the data
    ###################################################################################
    def update_directory_list(self, rule_directory, directory_listing):  
        #--Loop through all of the data structures and get their direcory listings
        for data in self.master_data_list:
            try:
                directory_listing.append(os.path.join(rule_directory,data.config_data['Directory']))
            except KeyError as error:
                print("Error with the config for " + data.config_name)
                return RetType.GENERIC_ERROR 
        return RetType.STATUS_OK
    
    
    ####################################################################################
    # Updates the config of the saved grammar with all of the various DataList structures
    ####################################################################################
    def update_config(self, config):
        #--Update the global training info
        if 'TRAINING_DATASET_DETAILS' not in config:
            config['TRAINING_DATASET_DETAILS'] = {}
        config['TRAINING_DATASET_DETAILS']['Number_of_passwords_in_set'] = str(self.valid_passwords + self.num_rejected_passwords)
        config['TRAINING_DATASET_DETAILS']['Number_of_valid_passwords'] = str(self.valid_passwords)
        
        #--Loop through all of the data structures and get their config sections
        for data in self.master_data_list:
            data_config = {}
            data.update_config(data_config)
            config[data.config_name] = data_config
            
        return RetType.STATUS_OK
    
    
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
        #
        # A TODO for the future is to record how often e-mails occur in general so we could try
        # specific e-mail replacements for a given target, (aka when auditing a company)
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
            
        # Remove tabs from the training data
        # This is important since when the grammar is saved to disk tabs are used as seperators
        # Another approach is to only use the last tab as a seperator for terminals that could contain a tab
        # but putting this placeholder here for now since tabs are unlikely to be used in passwords
        if "\t" in input_password:
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
        ##--Save the brute force (MARKOV) data for this password
        #################################################################
        self.markov.parse_password(input_password)

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
            
        ###################################################################
        #--Parse the digit combinations
        ###################################################################
        items = []
        ret_value = cur_pass.parse_digits(items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing digit combos")
            return ret_value
        ##--Now update the digit combo list
        ret_value = self.digit_structure.insert_list(items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing digit combos")
            return ret_value
            
        ###################################################################
        #--Parse the alpha combinations
        ###################################################################    
        alpha_items = []
        cap_items = [] 
        ret_value = cur_pass.parse_letters(alpha_items, cap_items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing alpha combos")
            return ret_value 
        ##--Now update the alpha combo list
        ret_value = self.letter_structure.insert_list(alpha_items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing alpha combos")
            return ret_value             
        ##--Now update the capitalization mask list
        ret_value = self.cap_structure.insert_list(cap_items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing capitalization masks")
            return ret_value 
        #####################################################################
        #--Parse the special character combinations
        #####################################################################
        items = []
        ret_value = cur_pass.parse_special(items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing special character combos")
            return ret_value
        ##--Now update the special character combo list
        ret_value = self.special_structure.insert_list(items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing special charcter combos")
            return ret_value
        
        ###########################################################################
        #--Finally save the base structure data as everything should be parsed now
        ###########################################################################
        
        # Doing this a bit overboard to match it with all the other parsing
        # Also this provides a nice sanity check to make sure no errors creeped in somewhere
        items = []
        ret_value = cur_pass.parse_base(items)
        if ret_value != RetType.STATUS_OK:
            print("Error parsing a password. There were sections that were not processed")
            return ret_value
        ##--Now update the base structure list
        ret_value = self.base_structure.insert_list(items)
        if ret_value != RetType.STATUS_OK:
            print("Error inserting a base structure object")
            return ret_value
            
        return RetType.STATUS_OK
    
    
    ######################################################################################
    # Once you have all the counts, calculate the actual probabilities associated with 
    # the Markov grammar
    #######################################################################################
    def calc_markov_stats(self):
        ##--Calculate Markov probabilities
        self.markov.calculate_probabilities()

    
    #######################################################################################
    # Finds the Markov rank of a password
    #######################################################################################    
    def find_markov_rank(self, input_password):        
        ret_value = self.check_valid(input_password)
        ##-If the password isn't valid for the training data
        if ret_value != RetType.IS_TRUE:
            return None
            
        rank = self.markov.evaulate_ranking(input_password)
        return rank
          
           
    ###########################################################################################
    # Finalizes the grammar and gets it ready to saved
    # The precision value is the precision to store the values
    # For example, a precision of 4 could save 0.0001 while a
    # precision of 5 could save 0.00012.
    # Note, this currently can create final values with a precision 1 more than the current setting
    # Setting default to 7, (will measure 1 in a million)
    ############################################################################################
    def finalize_data(self, precision=7, smoothing=0.01, coverage=1.0):
        for current_structure in self.master_data_list:
            ##--Calculate probabilities --##
            ##--Adding Markov into the base structure so we need to change the prob of what we saw
            if current_structure.config_name == 'START':
                ret_value = current_structure.update_probabilties(precision = precision, coverage= coverage)
                ##--Manually insert the new 'M' Markov into it
                if coverage != 1.0:
                    current_structure.manual_insert('M', precision = precision, probability = 1-coverage)
            else:    
                ret_value = current_structure.update_probabilties(precision = precision)
            if ret_value != RetType.STATUS_OK:
                print("Error finalizing the data")
                return ret_value
         
        return RetType.STATUS_OK
    
    
    #############################################################################################
    # Actually writes the data to disk
    #############################################################################################
    def write_data_to_disk(self, base_directory, section_directory, filename, file_encoding, items):
        try:
            with codecs.open(os.path.join(base_directory,section_directory,filename), 'w', encoding=file_encoding) as datafile:
                for x in items:
                    datafile.write(str(x[0]) + '\t' + str(x[1])+'\n')
        except IOError as error:
            print (error)
            print ("Error opening file " + str(os.path.join(base_directory,section_directory,filename)))
            return RetType.FILE_IO_ERROR
        return RetType.STATUS_OK
    
    
    ########################################################################################
    # Saves the data to file
    # The precision value is the precision to store the values
    # The smoothing is the amount that individual nodes should be different probabilities to actually
    #    be assigned different probabilities
    # The encoding is what encoding to use to save the files
    # The directory is the base directory to save the data
    #########################################################################################
    def save_results(self, directory='.', encoding='ASCII', precision=7, smoothing=0.01, coverage = 1.0):

        ##--First finalize the probabilities so we can sort the data
        ret_value = self.finalize_data(precision, coverage = coverage)
        if ret_value != RetType.STATUS_OK:
            return ret_value
        
        ##--now save results to disk
        for current_structure in self.master_data_list:
            sorted_results = {}    
            ret_value = current_structure.get_sorted_results(sorted_results, precision = precision, smoothing =smoothing)
            for filename, items in sorted_results.items():
                ret_value = self.write_data_to_disk(directory, current_structure.config_data['Directory'] ,filename, encoding, items)
            if ret_value != RetType.STATUS_OK:
                return ret_value
        
        ##--Save the Markov results to disk
        self.markov.save_results(os.path.join(directory,'Markov'))
        
        return RetType.STATUS_OK