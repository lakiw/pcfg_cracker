#!/usr/bin/env python3


##--Including this to print error message if python < 3.0 is used
from __future__ import print_function
import sys
###--Check for python3 and error out if not--##
if sys.version_info[0] < 3:
    print("This program requires Python 3.x", file=sys.stderr)
    sys.exit(1)
    
import argparse
import configparser
import os
import math #Used for the MeasurementStatus bar

##--Program Specific Imports---##
from pcfg_trainer.ret_types import RetType
from pcfg_trainer.trainer_file_io import is_jtr_pot, read_input_passwords, detect_file_encoding, make_rule_dirs, write_config
from pcfg_trainer.training_data import TrainingData


##-- The minimum number of passwords to train on --##
MIN_NUMBER_OF_PASSWORDS = 1



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

        ##--The default amount of probability smoothing to perform
        ##  This is how much "similar" items should be given the same probability
        ##  For example if it is set to 0.1 then items differening by 10% will be given the same probability
        ##  Setting this to 0 effectivly turns off probability smoothing
        ##  Why would you want to use probability smoothing? Well it can mean more terminals are generated from pre-terminals on avearge
        ##  for your generated grammar. Essentially the grammar becomes less precise but since generating the pre-terminals
        ##  takes a large amount of time in a password cracking attack, the grammar becomes "faster".
        self.smoothing = 0.01
        
        ##--The amount to trust the generated grammar
        ##  The resulting value is used to figure out how much to perform brute force guesses instead
        ##  Brute force = 1 - coverage
        self.coverage = 0.6
        
#############################################################################
# Used to print out the status of a current measurement
# I know, yet another class that could have been taken care of with a couple
# of variables, but this will hopefully make it easier to make changes later
#############################################################################
class MeasurementStatus:
    def __init__(self, input_size, display_status = True):
        ##--The total number of passwords
        self.input_size = input_size
        ##--The number of passwords currently parsed
        self.parsed_passwords = 0
        ##--The size between each bar
        self.step_size = self.input_size // 100
        ##--If there are less than 100 passwords....
        if self.step_size == 0:
            self.step_size = 1
        ##--If true, show a periodic status update. Will be false if debugging is going on
        self.display_status = display_status   
    
    
    ##########################################################################
    # Increments the number of parsed passwords by one and prints out any
    # status updates
    ##########################################################################
    def update_status(self):
        self.parsed_passwords = self.parsed_passwords + 1
        if self.display_status == True:
            if self.parsed_passwords == self.input_size:
                print("100%")
            elif (self.parsed_passwords % self.step_size == 0):
                print(str(math.floor((self.parsed_passwords / self.input_size) * 100)) +"%, ",end="")
                sys.stdout.flush()
        return RetType.STATUS_OK
        
              
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
    print('''             _.^   ___     _>-y~                 | |_ __ __ _ _ _ __   ___ _ __''') 
    print('''   .      .-~   .-~   ~>--"  /                   | | '__/ _` | | '_ \ / _ \ '_/''')
    print('''\  ~-"         /     ./  _.-'                    | | | | (_| | | | | |  __/ |''' ) 
    print(''' "-.,__.,  _.-~\     _.-~                        |_|_|  \__,_|_|_| |_|\___|_|''')
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
    print("                                          __ ")
    print("                                      _  |  |")
    print("                  Yye                |_| |--|")
    print("               .---.  e           AA | | |  |")
    print("              /.--./\  e        A")
    print("             // || \/\  e      ")
    print("            //|/|| |\/\   aa a    |\o/ o/--")
    print("           ///|\|| | \/\ .       ~o \.'\.o'")
    print("          //|\|/|| | |\/\ .      /.` \o'")
    print("         //\|/|\|| | | \/\ ( (  . \o'")
    print("___ __ _//|/|\|/|| | | |\/`--' '")
    print("__/__/__//|\|/|\|| | | | `--'")
    print("|\|/|\|/|\|/|\|/|| | | | |")
    print()
    return RetType.STATUS_OK

    
####################################################
# Simply parses the command line
####################################################
def parse_command_line(command_line_results):
    parser = argparse.ArgumentParser(description='Generates PCFG Grammar From Password Training Set')
    parser.add_argument('--rule','-r', help='Name of generated ruleset. Default is \"Default\"',metavar='RULESET_NAME',required=False,default=command_line_results.rule_name)
    parser.add_argument('--training','-t', help='The training set of passwords to train from',metavar='TRAINING_SET',required=True)
    parser.add_argument('--encoding','-e', help='File encoding to read the input training set. If not specified autodetect is used', metavar='ENCODING', required=False)
    parser.add_argument('--verbose','-v', help='Turns on verbose output', required=False, action="store_true")
    parser.add_argument('--smoothing', '-s', 
        help='<ADVANCED> The amount of probability smoothing to apply to the generated grammar. For example, if it is 0.01 then items with a prob difference of 1%% will be given the same prob. A setting of 0 will turn this off. Default: (%(default)s)',
        required=False, default=command_line_results.smoothing, type = float)
    parser.add_argument('--coverage', '-c', 
        help='<ADVANCED> The percentage to trust the trained grammar. 1 - coverage = persentage of grammar to devote to brute force guesses. Range: Between 1.0 and 0.0. Default: (%(default)s)',
        required=False, default=command_line_results.coverage, type = float)
    try:
        args=parser.parse_args()
        command_line_results.rule_name = args.rule
        command_line_results.training_file = args.training
        command_line_results.encoding = args.encoding
        command_line_results.smoothing = args.smoothing
        
        ##--Check to make sure smothing makes sense--##
        if command_line_results.smoothing < 0 or command_line_results.smoothing > 0.9:
            print("Error, smoothing must be a value between 0.9 and 0")
            return RetType.COMMAND_LINE_ERROR
            
        command_line_results.coverage = args.coverage    
        ##--Check to make sure coverage makes sense--##
        if command_line_results.coverage < 0 or command_line_results.coverage > 1.0:
            print("Error, smoothing must be a value between 0.9 and 0")
            return RetType.COMMAND_LINE_ERROR  
            
        if args.verbose:
            command_line_results.verbose = True
    except Exception as msg:
        print(msg)
        return RetType.COMMAND_LINE_ERROR

    return RetType.STATUS_OK   
 

############################################################
# Main function, starts everything off
############################################################    
def main():
    ##--Information about this program--##
    program_details = {
        'Program':'pcfg_trainer.py',
        'Version': '3.3',
        'Author':'Matt Weir',
        'Contact':'cweir@vt.edu'
    }
    
    print_banner()
    
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
    print("Reading in the training passwords")
    master_password_list = [] # The list that contains all the iput passwords
    ret_value = read_input_passwords(command_line_results.training_file, is_pot, master_password_list, file_encoding = command_line_results.encoding)
    ##--Set up the progress bar based on if it should print out a periodic status update or not    
    if ret_value == RetType.DEBUG:
        progress_bar = MeasurementStatus(len(master_password_list),display_status = False)
    elif ret_value == RetType.STATUS_OK:
        progress_bar = MeasurementStatus(len(master_password_list),display_status = True)
    ##-- Exit gracefully if error occurs
    else:
        ascii_fail()
        print("Exiting...")
        return
        
    ##--Now the real work starts--
    print()
    print("Done processing the input training file")
    print("Starting to analyzing the input passwords")
    print("Passwords left to parse : " + str(len(master_password_list)))
    if len(master_password_list) > 10000000:
        print("DevNote: Most of my training has been with sets of 1 million passwords. I'm not sure how things will scale with bigger datasets so if problems occur please submit a bug report on the github repo and then try training on a smaller sample size")
    print()
    print("Current Status:") 
    
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
            print("ERROR processing results from the training data")
            ret_value = RetType.ERROR_QUIT
        ##--An error occured parsing the password, print error and error out
        if ret_value != RetType.STATUS_OK:
            ascii_fail()
            print("Exiting...")
            return
        progress_bar.update_status()
    
    print("\nCalculating overall Markov probabilities")
    training_results.calc_markov_stats() 
    
    print("\nGoing through and looking at password distribution in regards to Markov Probabilities")
    for password in master_password_list:
        if password[1] == "DATA":
            rank = training_results.find_markov_rank(password[0]) 
    
    print("\nParsing is done. Now calculating probabilities, applying smoothing, and saving the results")
    print("This may take a few minutes depending on your training list size")
    
    training_results.markov.final_sorted_ranks()
    
    ##--Save the data to disk------------------###
    ##--Get the base directory to save all the data to
    ##  Don't want to use the relative path since who knows where someone is invoking this script from
    ##  Also aiming to make this OS independent
    ##  Will create all files in absolute_path_of_pcfg_trainer.py/Rules/RULE_NAME/
    absolute_base_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)),'Rules',command_line_results.rule_name)
    
    ##--Find the directories we need to create
    ##--Initailize with the base directory just in case there are no additioanl directories to create, (hey it could happen down the line)
    directory_listing = [absolute_base_directory]
    ret_value = training_results.update_directory_list(absolute_base_directory, directory_listing)
    if ret_value != RetType.STATUS_OK:
        ascii_fail()
        print("Exiting...")
        return
   
    ##--Create the directories if they do not already exist 
    ret_value = make_rule_dirs(directory_listing)
    if ret_value != RetType.STATUS_OK:
        ascii_fail()
        print("Exiting...")
        return
        
    ##--Gather the config data to save--##
    config = configparser.ConfigParser()
    ##--First write info about the training program used---###
    ##--This is me being optimistic that other people may eventaully write their own training programs---###
    config['TRAINING_PROGRAM_DETAILS'] = program_details
   
    ##--Now write info about the training dataset---###
    ##--Yup, this will leak info about training sets people are using but since this tool is meant for academic uses
    ##--it is important for repeated tests and documentation to keep track of where these rule sets came from
    config['TRAINING_DATASET_DETAILS'] = {
        'Filename':command_line_results.training_file,
        'Comments':'None',
        'Encoding':command_line_results.encoding,
        'Smoothing':command_line_results.smoothing
    }
    ##--Gather info from the training set
    ret_value = training_results.update_config(config)
    if ret_value != RetType.STATUS_OK:
        ascii_fail()
        print("Exiting...")
        return
   
    ##--Save the config file--##
    ret_value = write_config(absolute_base_directory, config)
    if ret_value != RetType.STATUS_OK:
        ascii_fail()
        print("Exiting...")
        return 
     
    ##--Now finalize the data and save it to disk--##
    ret_value = training_results.save_results(directory = absolute_base_directory, 
        encoding = command_line_results.encoding, precision = 7, smoothing = command_line_results.smoothing, coverage = command_line_results.coverage)
    if ret_value != RetType.STATUS_OK:
        ascii_fail()
        print("Exiting...")
        return
    
if __name__ == "__main__":
    main()
