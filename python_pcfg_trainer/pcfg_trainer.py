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
from pcfg_trainer.trainer_file_io import is_jtr_pot, read_input_passwords, detect_file_encoding, make_rule_dirs
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
        
        ##--The character encoding of the training set, (for example UTF-8)
        self.encoding = None
        

        
###################################################################################
# ASCII art for the banner
###################################################################################
def print_banner():
    print()
    print('''                                      ____''')
    print('''                                    .-~. /_"-._''')
    print('''-.                                / /_ "~o\  :Y''')
    print('''  \                               / : \~x.  ` ')''')
    print('''   Y                             /  |  Y< ~-.__j''')
    print('''   !                       _.--~T : l  l<  /.-~''')
    print('''  /                ____.--~ .   ` l /~\ \<|Y   _____   _____ ______ _____ '''   )
    print(''' /            .-~~"        /| .    ',-~\ \L|  |  __ \ / ____|  ____/ ____|'''  )
    print('''/            /     .^   \ Y~Y \.^>/l_   "--'  | |__) | |    | |__ | |  __ ''' ) 
    print('''          .-"(  .  l__  j_j l_/ /~_.-~    .   |  ___/| |    |  __|| | |_ |'''  )      
    print('''         /    \  )    ~~~." / `/"~ / \.__/l_  | |    | |____| |   | |__| | ''' ) 
    print('''\    _.-"      ~-{__     l  :  l._Z~-.___.--~ |_|_____\_____|_|    \_____| '''  )
    print(''' ~--~           /   ~~"---\_  ' __[>          |__   __|      (_)            ''')
    print('''             _.^   ___     _>-y~                 | |_ __ __ _ _ _ __   ___ _ _''') 
    print('''   .      .-~   .-~   ~>--"  /                   | | '__/ _` | | '_ \ / _ \ '__|''')
    print('''\  ~-"         /     ./  _.-'                    | | | | (_| | | | | |  __/ | ''' ) 
    print(''' "-.,__.,  _.-~\     _.-~                        |_|_|  \__,_|_|_| |_|\___|_| ''')
    print('''        ~~     (   _}       ''')
    print('''               `. ~(''')
    print('''                 )  \ ''')
    print('''                /,`--'~\--'~\ ''')
    print('''ASCII art credit to Row ~~~~~~~~~~~~~~~~~~~~~~~~Written by Matt Weir     ''')
    print()
    print()
    return RetType.STATUS_OK
    
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
    parser.add_argument('--encoding','-e', help='File encoding to read the input training set. If not specified autodetect is used', metavar='ENCODING', required=False)
    parser.add_argument('--verbose','-v', help='Turns on verbose output', required=False, action="store_true")
    try:
        args=parser.parse_args()
        command_line_results.rule_name = args.output
        command_line_results.training_file = args.training
        command_line_results.encoding = args.encoding

        if args.verbose:
            command_line_results.verbose = True
    except:
        return RetType.COMMAND_LINE_ERROR

    return RetType.STATUS_OK   
 

############################################################
# Main function, starts everything off
############################################################    
def main():
    #print_banner()
    ##--First start by parsing the command line --##
    command_line_results = CommandLineVars()
    if parse_command_line(command_line_results) != RetType.STATUS_OK:
        return RetType.QUIT

    ##--Set the file encoding for the training set
    ##--If NOT specified on the command line by the user run an autodetect
    if command_line_results.encoding == None:
        possible_file_encodings = []
        ret_value = detect_file_encoding(command_line_results.training_file, possible_file_encodings)
        if ret_value != RetType.STATUS_OK:
            ascii_fail()
            print("Exiting...")
            return
        command_line_results.encoding = possible_file_encodings[0]
        
    ##--Checks to see if the input file is a John the Ripper POT file or a flat file of only passwords
    ##--Also checks to see if there is the minimum number of passwords to train on
    ret_value = is_jtr_pot(command_line_results.training_file,MIN_NUMBER_OF_PASSWORDS, command_line_results.verbose, file_encoding = command_line_results.encoding)
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
    ret_value = read_input_passwords(command_line_results.training_file, is_pot, master_password_list, file_encoding = command_line_results.encoding)    
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
    
    ##--Initialize the training results--## 
    training_results = TrainingData()
    
    ##--Now parse every password in the training set --##
    for password in master_password_list:
        ##--It's a password to process--##
        if password[1] == "DATA":
            ret_value = training_results.parse(password[0])
        ##--Print comments for unit tests
        elif password[1] == "COMMENT":
            print()
            print(password[0])
            ret_value = RetType.STATUS_OK
        ##--Shouldn't ever get to the option below, so print an error and error out in case it does happen
        else:
            print("ERROR processign results from the training data")
            ret_value = RetType.ERROR_QUIT
        ##--An error occured parsing the password, print error and error out
        if ret_value != RetType.STATUS_OK:
            ascii_fail()
            print("Exiting...")
            return
    
    ##--Finalize the data and get it ready to save--##
    ret_value = training_results.finalize_data(precision=7)
    if ret_value != RetType.STATUS_OK:
        ascii_fail()
        print("Exiting...")
        return
        
    ##--Save the data to disk------------------###
    ##--Create the directories if they do not already exist
    ret_value = make_rule_dirs(command_line_results.rule_name)
    if ret_value != RetType.STATUS_OK:
        ascii_fail()
        print("Exiting...")
        return
    
    
if __name__ == "__main__":
    main()
