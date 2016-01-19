#!/usr/bin/env python3

#import sys
#import time
#import string
#import bisect
#from bisect import bisect_left
#import operator
#import os
#import errno
#import configparser

import argparse

##--User Defined Imports---##
from pcfg_trainer.ret_types import RetType
from pcfg_trainer.trainer_file_io import is_jtr_pot, read_input_passwords
from pcfg_trainer.training_data import TrainingData


##-- The minimum number of passwords to train on --##
MIN_NUMBER_OF_PASSWORDS = 5



##########################################################################
# Holds data that I want to get from the command line
# Yes, I could just pass back the argparser args but I like explicilty
# stating what I'm returning outside of that
##########################################################################
class CommandLineVars:
    def __init__(self):
        ##--The rule name that the training data will be saved to
        self.rule_name = "Default"
        
        ##--The training file to train from
        self.training_file= "Default_Training_File.pot"
        
        ##--Specifies if verbose output is enables
        self.verbose = False
        
#########################################################
# Basic find command for looking up value in ordered list
##########################################################
def find(a, x):
    'Locate the leftmost value exactly equal to x'
    i = bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return i
    return -1




##########################################################################################
# Identifies keyboard patterns
# Note, will only classify something as a keyboard pattern if it contains two or
# more classes of characters, since simple patterns like '123456' will be detected by the
# respective class trainers
##########################################################################################
def detect_keyboard(x,password,mask):
    i=0
    current_run=0
    past = (-2,-2)
    while i < (len(password)-1):
        pos = find_row_value(password[i])
        if is_next_on_keyboard(past,pos):
            current_run = current_run + 1
        else:
            if current_run >=4:
                if interesting_keyboard(password[i-current_run:i]):
                    x.keyboard_size = x.keyboard_size + 1
                    insert_list(x.keyboard_structure, password[i-current_run:i]) 
                    for y in range(i-current_run,i):
                        mask[y]='K'
            current_run = 1
        past = pos
        i = i + 1

    if current_run >=4:
        if interesting_keyboard(password[i-current_run:i]):
            x.keyboard_size = x.keyboard_size + 1
            insert_list(x.keyboard_structure, password[i-current_run:i])
            #print (password + " " +str(mask) + " " + str(i))
            for y in range(i-current_run,i):
                mask[y]='K'
        
####################################################################################
# Finds the range of alpha characters given a random position inside them
####################################################################################
def find_range(password,i):
    bottom=i
    top = i
    while (bottom > 0) and (password[bottom-1].isalpha()):
        bottom = bottom - 1

    while (top < len(password)) and (password[top+1].isalpha()):
        top = top + 1

    return (bottom,top)

#####################################################################################
# Identifies letter replacements
# Note, faily simplistic check. Could do a lot more when comparing against a real
# dictionary and using modified edit distance
# Currently assumes any replacement between two alpha chracters is valid
# TODO: Add more advanced logic to detect keyboard replacements
####################################################################################
def detect_replacement(x,password,mask):
    i=0
    #Note a->4 had too high of a false positive rate, aka 'bob4jesus'
    valid_replacements = [('i','1'),('l','1'),('e','3'),('t','7'),('a','@'),('s','$'),('s','5'),('o','0')]
    replace_set = []
    while i < len(password):
        c = password[i]
        for j in valid_replacements:
            if c == j[1]:
                if (i>0) and password[i-1].isalpha():
                    if ((i+1)<len(password)) and password[i+1].isalpha():
                        replace_set.append((j,i))

        i = i + 1
    

    #Save the replacements
    inserted_set=[]
    for r in replace_set:
        if not (r[0] in inserted_set):
            inserted_set.append(r[0])
            x.replace_size = x.replace_size + 1
            insert_list(x.replace_structure,str(r[0][0])+","+str(r[0][1]))
            
    
    #Now save the mask
    if (len(replace_set)!=0):
        for r in replace_set:
            replace_range = find_range(password,r[1])
            has_upper = False
            for j in range(replace_range[0],replace_range[1]+1):
                if password[j].isupper():
                    has_upper = True

            for j in range(replace_range[0],replace_range[1]+1):
                if has_upper:
                    mask[j]='R'
                else:
                    mask[j]='r'


######################################################################################
# Find context sensitive replacements
# Note, we need to know what they are in the trainer
# It is not smart enough to find them on its own yet
# TODO: Identify new context sensitive replacements based on the training data
######################################################################################
def detect_context(x,password,mask):
    searchValues=["<3",";p",":p","#1","*0*"]
    for i in searchValues:
        findValue = password.find(i)
        if findValue!=-1:
            for j in range(findValue,findValue+len(i)):
                mask[j]='X'
            x.context_size = x.context_size +1
            insert_list(x.context_structure,i,)   


######################################################################################
# Responsible for finding complex patterns like keyboard combos and letter repacements
#
# TODO: Add logic for conditional replacements for digit/special/alpha combos
######################################################################################
def normalize_base(x,password):
    
    final_base = []
    working_base = list(password.rstrip())

    ## Initialize the mask. This is applied after capitalization normalization occurs
    ## Fully aware this can cause some weirdness if a U is part of a K.
    ## For example 1qaZpassword would be KKKKUUUUUUUU when it really should be
    ## KKKKLLLLLLLL
    ## TODO: Find a better way to do this
    overlay_mask = []
    for i in range(0,len(password)-1):
        overlay_mask.append('.')

    ## Detect letter replacements
    detect_replacement(x,password,overlay_mask)

    ## Detect context sensitive replacements
    detect_context(x,password,overlay_mask)


    ## Detect keyboard combinations
    detect_keyboard(x,password,overlay_mask)


    ## Normalize capitalization for alpha structures
    i=0
    while i < len(working_base):
        if working_base[i].isalpha():
            contains_cap=False
            for y in range(i,len(working_base)):
                if not working_base[y].isalpha():
                    break
                if working_base[y].isupper():
                    contains_cap=True
                    break
            working_mask=[]
            for y in range(i,len(working_base)):
                if not working_base[y].isalpha():
                    break
                if contains_cap:
                    #WorkingMask is used to capture the exact "Capitalization Mask" that was used
                    #Aka Password would be ULLLLLLL
                    if working_base[y].isupper():
                        working_mask.append("U")
                    else:
                        working_mask.append("L")
                    working_base[y]='C'
                        
                else:
                    working_base[y]='L'
                i = i + 1

            #Save the Capitalization Mask
            if contains_cap:
                size = len(working_mask)
                x.cap_size[size] = x.cap_size[size] + 1
                insert_list(x.cap_structure[size], working_mask)

        i = i + 1
    
    #Apply mask from previous transforms
    pos = 0
    for i in overlay_mask:
        if i != '.':
            working_base[pos]=i
        pos = pos + 1
    
    final_base = working_base
    return final_base

#############################################################################
# Inserts value into a sorted list if it does not exist
# Otherwise increments the counter by one
# Made this generic since I was doing it a lot
#############################################################################
def insert_list (sorted_list, insert_value):
    value_holder = DataHolder("".join(insert_value))
    index = find(sorted_list , value_holder)
    if index != -1:
        sorted_list[index].inc()
    else:
        bisect.insort(sorted_list,value_holder)


##############################################################################
# Responsible for parsing the base structures
# Will call the other parsing functions. Doing it this way so I can add
# more complex logic, like letter replacements later
##############################################################################
def parse_base(x, password):
    
    # Check for complex transforms like letter replacements and keyboard combos
    # Also extract the "Case Mangling" masks since that's a good a time as any to do that
    final_base = normalize_base(x,password)

    # Next, extract the digit structures
    count = 0
    while count < len(final_base):
        #Start processing this particular digit
        if final_base[count].isdigit():
            working_digit=[]
            while count < len(final_base):
                if not final_base[count].isdigit():
                    break
                working_digit.append(final_base[count])
                count = count + 1
            #Save that digit
            size = len(working_digit)
            x.digit_size[size] = x.digit_size[size]+1
            insert_list(x.digit_structure[size],working_digit)

        count = count + 1

    # Next, extract the special structures
    count = 0
    while count < len(final_base):
        #Start processing this particular special string
        if not final_base[count].isalnum():
            working_special=[]
            while count < len(final_base):
                if final_base[count].isalnum():
                    break
                working_special.append(final_base[count])
                count = count + 1
            #Save that special string
            size = len(working_special)
            x.special_size[size] = x.special_size[size] + 1
            insert_list(x.special_structure[size],working_special)

        count = count + 1

    # Now actually parese the base structure
    if x.base_type == 0:
        for i in range(0,len(final_base)):
            if final_base[i].isdigit():
                final_base[i]='D'
            elif not final_base[i].isalnum():
                final_base[i]='S'


    else:
        #TODO: add new base structure type
        print ("Add this option")

    #Now insert the base structure into the main list
    x.base_size = x.base_size + 1
    insert_list(x.base_structure, final_base)

###############################################################################
# Build the grammar from the training file
# Aka figures out all the Base Structures, D Structures, S Structures, etc.
###############################################################################
def build_grammar(training_file,x):
    file = open(training_file[0], 'r')
    
    # Extract all the replacements from the training set
    print ("Starting to parse the training password file")
    for password in file:
        
        ## Added a reject function to remove "invalid" passwords nativly
        ## Invalid in this case means you don't want to train on them
        if valid_pass(password):
            x.total_size=x.total_size+1
            parse_base(x,password)
        if (x.total_size % 100000) == 0:
            print ("Processed " + str(x.total_size) + " passwords so far")


    # Calculate probabilities
    print ("Done parsing the training file. Now calculating probabilities.")
    for i in range(1,MAXLENGTH+1):
        calc_prob(x.special_structure[i],x.special_size[i])

    for i in range(1,MAXLENGTH+1):
        calc_prob(x.digit_structure[i],x.digit_size[i])

    for i in range(1,MAXLENGTH+1):
        calc_prob(x.cap_structure[i],x.cap_size[i])

    calc_prob(x.base_structure, x.base_size)
    
    calc_prob(x.keyboard_structure, x.keyboard_size)

    calc_prob(x.replace_structure, x.replace_size)

    calc_prob(x.context_structure, x.context_size)


    #for i in range(0,MAXLENGTH):
    #   print ("LENGTH " + str(i))
    #   for y in range(0,len(x.digit_structure[i])):
    #       print (x.digit_structure[i][y].value + " " +str(x.digit_structure[i][y].num) + " " + str(x.digit_structure[i][y].prob))
    #   print (x.digit_size[i])    
    return 0    

##############################################################################
# Calculate probabilities for a list
# Also sorts the list
##############################################################################
def calc_prob(input_list, size):
    # First calculate the probability for each item
    for value in input_list:
        value.prob = (1.0 * value.num) / size

    # Now sort the list
    input_list.sort(key=operator.attrgetter('num'), reverse=True)

    
###################################################################################
# ASCII art for when program fails
###################################################################################
def ascii_fail():
    print("                                         __ ")
    print("                                     _  |  |")
    print("                 Yye                |_| |--|")
    print("              .---.  e           AA | | |  ")
    print("             /.--./\  e        A")
    print("            // || \/\  e      ")
    print("           //|/|| |\/\   aa a    |\o/ o/--")
    print("          ///|\|| | \/\ .       ~o \.'\.o'")
    print("         //|\|/|| | |\/\ .      /.` \o'")
    print("        //\|/|\|| | | \/\ ( (  . \o'")
    print("__ __ _//|/|\|/|| | | |\/`--' '")
    print("__/__/__//|\|/|\|| | | | `--'")
    print("|\|/|\|/|\|/|\|/|| | | | |")
    print()
    return RetType.STATUS_OK

####################################################
# Simply parses the command line
####################################################
def parse_command_line(command_line_results):
    parser = argparse.ArgumentParser(description='Generates PCFG Grammar From Password Training Set')
    parser.add_argument('--output','-o', help='Name of generated ruleset. Default is \"Default\"',metavar='RULESET_NAME',required=False,default=command_line_results.rule_name)
    parser.add_argument('--training','-t', help='The training set of passwords to train from',metavar='TRAINING_SET',required=True)
    parser.add_argument('--verbose','-v', help='Turns on verbose output', required=False, action="store_true")
    try:
        args=parser.parse_args()
        command_line_results.rule_name = args.output
        command_line_results.training_file = args.training
        if args.verbose:
            command_line_results.verbose = True
    except:
        return RetType.COMMAND_LINE_ERROR

    return RetType.STATUS_OK   
 

############################################################
# Main function, starts everything off
############################################################    
def main():
    ##--First start by parsing the command line --##
    command_line_results = CommandLineVars()
    if parse_command_line(command_line_results) != RetType.STATUS_OK:
        return RetType.QUIT

    ##--Checks to see if the input file is a John the Ripper POT file or a flat file of only passwords
    ##--Also checks to see if there is the minimum number of passwords to train on
    ret_value = is_jtr_pot(command_line_results.training_file,MIN_NUMBER_OF_PASSWORDS, command_line_results.verbose)
    if ret_value == RetType.IS_TRUE: 
        is_pot = True
    elif ret_value == RetType.IS_FALSE:
        is_pot = False
    ##--Bad input so exit--
    else:
        ascii_fail()
        print("Exiting...")
        return
    
    ##--Now actually read in the raw passwords, (minus any POT formatting)
    master_password_list = [] # The list that contains all the iput passwords
    ret_value = read_input_passwords(command_line_results.training_file, is_pot, master_password_list)    
    ##-- An error shouldn't occur here since we checked it earlier but stanger things have happened
    ##-- Exit gracefully if error occurs
    if ret_value != RetType.STATUS_OK:
        ascii_fail()
        print("Exiting...")
        return
        
    ##--Now the real work starts--
    if command_line_results.verbose == True:
        print("Done processing the input training file")
        print("Starting to analyzing the input passwords")
        print("Passwords left to parse : " + str(len(master_password_list)))
    
    training_results = TrainingData()
    ret_value = RetType.STATUS_OK
    for password in master_password_list:
        ##--It's a password to process--##
        if password[1] == "DATA":
            ret_value = training_results.parse(password[0])
        ##--Print comments for unit tests
        elif password[1] == "COMMENT":
            print()
            print(password[0])
        else:
            print("ERROR processign results from the training data")
            ret_value = RetType.ERROR_QUIT
        
        if ret_value != RetType.STATUS_OK:
            ascii_fail()
            print("Exiting...")
            return
    
if __name__ == "__main__":
    main()
