#!/usr/bin/env python3

#############################################################################
# This file contains the functionality to actually parse the raw passwords
# The PasswordParser class is designed to work with a single password only
# it is up to the calling function to aggrigate any data from multiple passwords
#############################################################################

##--User Defined Imports---##
from pcfg_trainer.ret_types import RetType

############################################################################
# Holds the "scratch space" for parsing a password as well as the individual
# parsing rules
#############################################################################
class PasswordParser:
    ##########################################################################
    # Initializes the class and all the data structures
    ##########################################################################
    def __init__(self,input_password):
        ## Holds the actual password that we will be parsing
        ## Keeping this around just to make debugging easier
        self.password = input_password
        
        ## Specifies which characters in the input password have been processed_mask
        ## This is important for things like keyboard combinations. For example:
        ## '1qaz2wsxtest' should be K4K4L4, not D1L3D1L7
        ## Takes the format of (string,MASK) where MASK == None if not processed
        self.processed_mask = [(input_password,None)]
        
        ## static varaibles that should not be changed dymically by the program
        ## The minimum number of characters that should constitute a keyboard run
        self.MIN_KEYBOARD_RUN = 4
        
        ## List of all context sensitive replacements
        self.CONTEXT_SENSITIVE_REPLACEMENTS=["<3",";p",":p","*0*", "#1", "#11"]
        
    
    #########################################################################################
    # Finds the keyboard row and column of a character
    #########################################################################################
    def find_keyboard_row_column(self,char):
        #Yeah I'm leaving off '`' but it is rarely used in keyboard combos and it makes the code cleaner
        row1=['1','2','3','4','5','6','7','8','9','0','-','=']
        s_row1=['!','@','#','$','%','^','&','*','(',')','_','+']
        
        row2=['q','w','e','r','t','y','u','i','o','p','[',']','\\']
        s_row2=['Q','W','E','R','T','Y','U','I','O','P','{','}','|']

        row3=['a','s','d','f','g','h','j','k','l',';','\'']
        s_row3=['A','S','D','F','G','H','J','K','L',':','"']

        row4=['z','x','c','v','b','n','m',',','.','/']
        s_row4=['Z','X','C','V','B','N','M','<','>','?']

        if char in row1:
            return (0,row1.index(char))
        
        if char in s_row1:
            return (0,s_row1.index(char))

        if char in row2:
            return (1,row2.index(char))
        
        if char in s_row2:
            return (1,s_row2.index(char))

        if char in row3:
            return (2,row3.index(char))
        
        if char in s_row3:
            return (2,s_row3.index(char))

        if char in row4:
            return (3,row4.index(char))
                
        if char in s_row4:
            return (3,s_row4.index(char))

        #Default value for keys that are not checked + non-ASCII chars
        return None
        
    #########################################################################################
    # Finds if a new key is next to the previous key
    #########################################################################################
    def is_next_on_keyboard(self, past, current):
        ##--First check to see if either past or current are not valid--##
        if (past == None) or (current == None):
            return RetType.IS_FALSE
            
        ##--If they both occur on the same row (easy)
        if (current[0] == past[0]):
            if (current[1] == past[1]) or (current[1] == past[1]-1) or (current[1] == past[1]+1):
                return RetType.IS_TRUE
                
        ##-- If it occurs one row down from the past combo
        ##-- Gets a bit weird since they "rows" don't exactly line up
        ##-- aka 'w' (pos 1) is next to 'a' (pos 0) and 's' (pos 1)
        elif (current[0] == past[0]+1):
            if (current[1] == past[1]) or (current[1] == past[1]-1):
                return RetType.IS_TRUE
        
        ##-- If it occurs one row up from the past combo
        elif (current[0] == past[0]-1):
            if (current[1] == past[1]) or (current[1] == past[1]+1):
                return RetType.IS_TRUE
        
        ##-- Looks like the two keys are not adjacent
        return RetType.IS_FALSE
    
    ###########################################################################################
    # Currently only defining "interesting" keyboard combos as a combo that has
    # multiple types of characters, aka alpha + digit
    # Also added some sanity checks for common words that tend to look like keyboard combos
    ##########################################################################################
    def interesting_keyboard(self,combo):
        # Sanity length check
        if len(combo) < 3:
            return RetType.IS_FALSE
       
       # Remove "likely" partial words
       # These occur from common english words that look like keyboard combos
       # aka 'deer43'
        if (combo[0]== 'e') and (combo[1]== 'r'):
            return RetType.IS_FALSE
    
        if (combo[1]== 'e') and (combo[2]== 'r'):
            return RetType.IS_FALSE

        if (combo[0]=='t') and (combo[1]=='t') and (combo[2]=='y'):
            return RetType.IS_FALSE

        #Check for complexity requirements
        alpha = 0
        special = 0
        digit = 0
        for c in combo:
            if c.isalpha():
                alpha=1
            elif c.isdigit():
                digit=1
            else:
                special=1
                
        ##--If it meets all the complexity requirements        
        if (alpha + special + digit) >=2:
            return RetType.IS_TRUE
            
        return RetType.IS_FALSE
    
    ############################################################################
    # Function that looks for keyboard combinations in the training data for a section
    # For example 1qaz or xsw2
    # items is a list of the different transitions parsed
    # for example ['1qaz','1qaz','2wsx']
    # Doing this recursive so input_section is the section to processed
    # section list is a list of the sections to return
    # For example, assume input_section is ('test1qaztest',None)
    # section_list should return [('test',None),('1qaz','K4'),('test',None)]
    ############################################################################
    def parse_keyboard_section(self, items, input_section, section_list):
        ##--The keyboard position of the last key processed
        past_pos = None
        ##--The current keyboard combo--##
        cur_combo = []
        ##-Loop through each character to find the combos
        for index, x in enumerate(input_section):
            #--Find the current location of the key on the keyboard
            pos = self.find_keyboard_row_column(x)
            #--Check to see if a run is occuring, (two keys next to each other)
            is_run = self.is_next_on_keyboard(past_pos, pos)
            #-- If it is a run, keep it going!
            if is_run == RetType.IS_TRUE:
                cur_combo.append(x)
            #-- The keyboard run has stopped
            else:
                if len(cur_combo) >= self.MIN_KEYBOARD_RUN: 
                    ##--Look at saving this keyboard combo--##
                    ##--First see if the keyboard combo is interesting enough to save
                    ret_value = self.interesting_keyboard(cur_combo)
                    if ret_value == RetType.IS_TRUE:
                        ##--Now actually save the results
                        items.append(''.join(cur_combo))
                        ##--Update base structure mask--
                        ##--Update any unprocessed sections before the current run
                        if len(cur_combo) != index:
                            section_list.append((input_section[0:index-len(cur_combo)],None))
                        ##--Now update the mask for the current run
                        section_list.append((''.join(cur_combo),"K"+str(len(cur_combo))))
                        ##--If not the last section, go recursive and call it with what's remaining--##
                        if index != (len(input_section) - 1):
                            ret_value = self.parse_keyboard_section(items, input_section[index:], section_list)
                            ##-- Sanity error return check --##
                            if ret_value != RetType.STATUS_OK:
                                return ret_value
                                
                        ##-- Ok, thanks the the recursive checking of the rest of it we are done processing this section so break
                        return RetType.STATUS_OK
                    ##--Sanity error return check
                    elif ret_value != RetType.IS_FALSE:
                        print("Error parsing keyboard combos, exiting")
                        return RetType.ERROR_QUIT
                        
                #--Now start a new run--
                cur_combo = [x]
                
            # What was new is now old. Update the previous position    
            past_pos = pos
            
        ##--Update the last run if needed
        if len(cur_combo) >= self.MIN_KEYBOARD_RUN: 
            ##--Look at saving this keyboard combo--##
            ##--First see if the keyboard combo is interesting enough to save
            ret_value = self.interesting_keyboard(cur_combo)
            if ret_value == RetType.IS_TRUE:
                ##--Now actually save the results
                items.append(''.join(cur_combo))
                ##--Update base structure mask--
                ##--Update any unprocessed sections before the current run
                if len(cur_combo) != len(input_section):
                    section_list.append((input_section[0:len(input_section)-len(cur_combo)],None))
                ##--Now update the mask for the current run
                section_list.append((''.join(cur_combo),"K"+str(len(cur_combo))))
            ##--Not treating it as a keyboard combo since it is not intersting
            elif ret_value == RetType.IS_FALSE:
                section_list.append((input_section,None))
            ##--Sanity error return check
            else:
                print("Error parsing keyboard combos, exiting")
                return RetType.ERROR_QUIT
        ##--No keyboard run found
        else:
            section_list.append((input_section,None))
        return RetType.STATUS_OK
        
    ############################################################################
    # The toplevel function that looks for keyboard combinations in the training data
    # For example 1qaz or xsw2
    # items is a list of the different transitions parsed
    # for example ['1qaz','1qaz','2wsx']
    # mostly just a loop and sets up the recursive calling of parse_keybaord_section
    ############################################################################
    def parse_keyboard(self,items):

        ##--Used to hold the new mask--##
        section_list = []
        ##--Loop through the different sections for the mask
        for section in self.processed_mask:
            ret_type = self.parse_keyboard_section(items, section[0], section_list)
            if ret_type != RetType.STATUS_OK:
                print("Error parsing keyboard combos")
                return ret_type
        ##--Now copy the section list to the main processed_mask
        self.processed_mask = section_list.copy()
        return RetType.STATUS_OK
        
    ############################################################################
    # The toplevel function that looks for context sensitive combinations in the
    # training data that contain two or more 'categories' of characters such as letters and numbers
    # For example, [';p', or '#1']
    # These are mostly emoticons and have to be manually specified
    # Doing this recursive so input_section is the section to processed
    # section list is a list of the sections to return
    # For example, assume input_section is ('test#1test',None)
    # section_list should return [('test',None),('#1','X2'),('test',None)]
    ############################################################################
    def parse_context_sensitive_section(self, items, input_section, section_list):
        ##--Doing this a bit weird by using the find option since I want to support
        ##--context sensitive replacements that may be a subset of each other
        ##--aka there might be a '#1' and a '#11' 
        ##--going character by character for this got way too complicated
        
        # Item to use as context sensitive replacement, will take the form of (replacement, position), aka ('#1',4) for 'test#1'
        replacement_item = None
        # Loop through all the possible replacements looking for matches
        for cur_replacement in self.CONTEXT_SENSITIVE_REPLACEMENTS:
            index = input_section.find(cur_replacement)
            ##--If a replacement is found
            if index != -1:
                # If no existing replacement has been found, or the replacement happens sooner
                if (replacement_item == None) or (index < replacement_item[1]):
                    replacement_item = (cur_replacement,index)
                # If both replacements happen at the same location, pick the bigger one
                elif index == replacement_item[1]:
                    if len(cur_replacement) > len(replacement_item[0]):
                        replacement_item = (cur_replacement,index)
        
        # If no replacements were found
        if replacement_item == None:
            section_list.append((input_section,None))
        # Else take care of the replacement
        else:
            items.append(replacement_item[0])
            # Insert any unprocessed section at the begining if it exists
            if replacement_item[1] != 0:
                section_list.append((input_section[0:replacement_item[1]],None))
            # Now insert the context sensitive replacement
            section_list.append((replacement_item[0],"X" + str(len(replacement_item[0]))))
            # Go recursive if there exists a section that occurs after the replacements
            if (len(replacement_item[0]) + replacement_item[1]) < len(input_section):
                ret_value = self.parse_context_sensitive_section(items, input_section[len(replacement_item[0]) + replacement_item[1]:], section_list)
                if ret_value != RetType.STATUS_OK:
                    return ret_value
        return RetType.STATUS_OK

    
    ##################################################################################
    # The toplevel function that looks for context sensitive combinations in the
    # training data that contain two or more 'categories' of characters such as letters and numbers
    # For example, [';p', or '#1']
    # These are mostly emoticons and have to be manually specified
    # This function is mostly just a loop and sets up the recursive calling of parse_context_sensitive_section
    ###################################################################################
    def parse_context_sensitive(self,items):
        ##--Used to hold the new mask--##
        section_list = []
        ##--Loop through the different sections for the mask
        for section in self.processed_mask:
            ret_type = self.parse_context_sensitive_section(items, section[0], section_list)
            if ret_type != RetType.STATUS_OK:
                print("Error parsing keyboard combos")
                return ret_type
        ##--Now copy the section list to the main processed_mask
        self.processed_mask = section_list.copy()
        return RetType.STATUS_OK