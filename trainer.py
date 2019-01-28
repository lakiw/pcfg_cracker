#!/usr/bin/env python3


################################################################################
#
# Name: PCFG Trainer
#  -- Training program that creates Probabilistic Context Free Grammars (PCFGs)
#     from plaintext passwords
#
#  -- Can also be used to generate statistical data and dictionaries for other
#     cracking methods such as MASK attacks and OMEN
#
#  Written by Matt Weir
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
#
#  Contact Info: cweir@vt.edu
#
#  pcfg_trainer.py
#
################################################################################


# Including this to print error message if python < 3.0 is used
from __future__ import print_function
import sys
# Check for python3 and error out if not
if sys.version_info[0] < 3:
    print("This program requires Python 3.x", file=sys.stderr)
    sys.exit(1)
    
import argparse
import os  
import traceback

# Local imports
from lib_trainer.banner_info import print_banner
from lib_trainer.trainer_file_input import detect_file_encoding
from lib_trainer.trainer_file_input import TrainerFileInput
from lib_trainer.trainer_file_input import get_confirmation

from lib_trainer.trainer_file_output import create_rule_folders

from lib_trainer.omen.alphabet_generator import AlphabetGenerator
from lib_trainer.omen.alphabet_lookup import AlphabetLookup
from lib_trainer.omen.omen_file_output import save_omen_rules_to_disk

from lib_trainer.multiword_detector import MultiWordDetector

from lib_trainer.pcfg_password_parser import PCFGPasswordParser

from lib_trainer.config_file import save_config_file
from lib_trainer.save_pcfg_data import save_pcfg_data


## Parses the command line
#
# Responsible for parsing the command line.
#
# If you have any command line options that you want to add, they go here.
#
# All results are returned as a dictionary in 'program_info'
#
# If successful, returns True, returns False if value error, program exits if
# argparse catches a problem.
#
def parse_command_line(program_info):

    # Keeping the title text to be generic to make re-using code easier
    parser = argparse.ArgumentParser(
        description= program_info['name'] +
        ', version: ' + 
        program_info['version']
    )
        
    ## Standard options for filename, encoding, etc
    #
    # The rule name to save the grammar as. This will create a directory of
    # this name. Will also put associated other files, such as PRINCE wordlists
    # here.
    parser.add_argument(
        '--rule',
        '-r',
        help = 'Name of generated ruleset. Default is ' + 
        program_info['rule_name'],
        metavar = 'RULESET_NAME',
        required = False,
        default = program_info['rule_name']
    )
    
    # The training file of passwords to train on
    parser.add_argument(
        '--training',
        '-t',
        help = 'The training set of passwords to train from',
        metavar = 'TRAINING_SET',
        required = True
    )
    
    # The file encoding of the training file
    parser.add_argument(
        '--encoding',
        '-e', 
        help = 'File encoding to read the input training set. If not ' +
        'specified autodetect is used', 
        metavar = 'ENCODING', 
        required = False
    )
    
    # Any comments someone may want to add to the training file
    parser.add_argument(
        '--comments', 
        help = 'Comments to save in the generated rule configuration file, encapsulated in quotes ""', 
        metavar = '"COMMENTS"', 
        required = False,
        default = program_info['comments']
    )
    
    # If PII info like e-mails and full websites should be saved
    parser.add_argument(
        '--save_sensitive', 
        help = 'Saves sensitive info like full e-mail addresses to the rules file', 
        default=False, 
        required = False,
        action='store_true'
    )
    
    ## OMEN Options
    #
    # ngram is the size of the conditional probabilty strings to compare
    # NGRAM = 4 would mean "d|wor" for "word"
    parser.add_argument(
        '--ngram', 
        '-n', 
        help = '<ADVANCED> The depth to generate conditional probabilites ' +
        'for Markov brute force guesses. NGRAM=4 would mean "d|wor" for ' +
        '"word". Default: ' + str(program_info['ngram']),
        required = False, 
        default = program_info['ngram'], 
        type = int, 
        metavar = 'INT', 
        choices = range(2,6)
    )
    
    # Alphabet size for the OMEN parsing    
    parser.add_argument(
        '--alphabet',
        '-a', 
        help = 'Dynamically learn the alphabet from training set for Markov ' +
        'brute force guesses. Note, the size of alphabet will get up to the ' +
        'N most common characters. Higher values can slow down the cracker ' +
        'and increase memory requirements. Default: ' + 
        str(program_info['alphabet_size']),
        type = int, 
        default = program_info['alphabet_size'], 
        metavar = 'SIZE_OF_ALPHABET', 
        required = False
    )
    
    ## Other Advanced Options
    #
    # Smoothing is used to smooth out differences in probabilities between 
    # different items. Higher smoothing will slightly speed up the cracker
    # and reduce its memory usage significanlty, but makes it less precise
    parser.add_argument(
        '--smoothing', 
        '-s', 
        help = '<ADVANCED> The amount of probability smoothing to apply to ' +
        'the generated grammar. For example, if it is 0.01 then items with ' +
        'a prob difference of 1%% will be given the same prob. A setting ' +
        'of 0 will turn this off. Default: ' +  str(program_info['smoothing']),
        required = False, 
        default = program_info['smoothing'], 
        type = float
    )
    
    # Sets the coverage of the trained grammer. Set it to 1.0 to disable Markov
    # guesses. If you set it to 0.0 it will only generate Markov guesses.
    parser.add_argument(
        '--coverage', 
        '-c', 
        help = '<ADVANCED> The percentage to trust the trained grammar. ' +
        '(1 - coverage) = percentage of grammar to devote to brute ' +
        'force guesses. Range: Between 1.0 and 0.0. Default: ' + 
        str(program_info['coverage']),
        required = False, 
        default = program_info['coverage'],
        type = float
    )   
    # Parse all the args and save them    
    args=parser.parse_args() 
    # Standard Options
    program_info['rule_name'] = args.rule
    program_info['training_file'] = args.training
    program_info['encoding']= args.encoding
    program_info['comments'] = args.comments
    program_info['save_sensitive'] = args.save_sensitive
    
    # OMEN Options
    program_info['ngram'] = args.ngram
    program_info['alphabet_size'] = args.alphabet
    
    # Advanced Options
    program_info['smoothing'] = args.smoothing
    program_info['coverage'] = args.coverage

    ## Sanity checking of values
    #
    # Check to make sure smoothing makes sense
    if program_info['smoothing'] < 0 or program_info['smoothing'] > 0.9:
        print("Error, smoothing must be a value between 0.9 and 0")
        return False
         
    # Check to make sure coverage makes sense
    if program_info['coverage'] < 0 or program_info['coverage'] > 1.0:
        print("Error, coverage must be a value between 0.0 and 1.0")
        return False
    
    # Require an alphabet size of at least 10.
    # Not that I have ever accidentally not typed the second character of
    # the alphabet size before...       
    if args.alphabet < 10:
        print("Minimum alphabet size is 10 because based on past "+
            "experience anything less than that is probably a typo. "+
            "If this is a problem please post on the github site"
        )

    return True   
    
    
## Main function, starts everything off
#    
def main():

    # Information about this program
    program_info = {
    
        # Program and Contact Info
        'name':'PCFG Trainer',
        'version': '4.0',
        'author':'Matt Weir',
        'contact':'cweir@vt.edu',
        
        # Standard Options
        'rule_name':'Default',
        'training_file':None,
        'encoding':None,
        'comments':'',
        'save_sensitive': False,
        
        # OMEN Options
        'ngram': 4,
        'alphabet_size':100,
        'alphabet':'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!.*@-_$#<?',
        
        # Advanced Options
        'smoothing': 0.01,
        'coverage':0.6,
        'max_len':21,
    }
      
    print_banner()
    
    # Parsing the command line
    if not parse_command_line(program_info):
        # There was a problem with the command line so exit
        print("Exiting...")
        return

    ## Set the file encoding for the training set
    #
    # If NOT specified on the command line by the user run an autodetect
    if program_info['encoding'] == None:
        print()
        print("-----------------------------------------------------------------")
        print("Attempting to autodetect file encoding of the training passwords")
        print("-----------------------------------------------------------------")
    
        possible_file_encodings = []
        if not detect_file_encoding(
            program_info['training_file'], 
            possible_file_encodings
        ):
            print("Exiting...")
            return
        
        # Select the most likely file encoding        
        program_info['encoding'] = possible_file_encodings[0]
        
    ## Create Rules folder for the saved grammar
    #
    # Doing this before parsing the input file further since if a permission
    # error occurs here want to fail fast vs. waiting 10 minutes to finialize
    # parsing the data
    
    # Get the base directory to save all the data
    #
    # Don't want to use the relative path since who knows where someone is 
    # invoking this script from
    #
    # Also aiming to make this OS independent/
    #
    base_directory = os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        'Rules',
                        program_info['rule_name'])
    
    if not create_rule_folders(base_directory):
        print("Exiting...")
        return
    
    ## Perform the first pass of the training list
    #
    # This pass is responsible for the following:
    #
    # -Identifying number of passwords trained on
    # -Identifying OMEN alphabet
    # -Duplicate password detection, (duplicates are good!)
    #
    print("-------------------------------------------------")    
    print("Performing first pass on the training passwords")
    print("-------------------------------------------------")
    print("")
    
    # Initialize the file input to read passwords from
    file_input = TrainerFileInput(
                    program_info['training_file'], 
                    program_info['encoding'])
                    
    # Initialize the alphabet generator to learn the alphabet
    ag = AlphabetGenerator(program_info['alphabet_size'], program_info['ngram'])
    
    # Intitialize the multi-word detector
    multiword_detector = MultiWordDetector(
                            threshold = 5,
                            min_len = 4,
                            max_len = 21)
    
    # Used for progress_bar
    num_parsed_so_far = 0
    print("Printing out status after every million passwords parsed")
    print("------------")
 
    ## Loop until we hit the end of the file
    try:
        password = file_input.read_password()
        while password:
        
            # Print status indicator if needed
            num_parsed_so_far += 1
            if num_parsed_so_far % 1000000 == 0:
                print(str(num_parsed_so_far//1000000) +' Million')
            
            # Save statistics for the alphabet
            ag.process_password(password)
            
            # Train multiword detector
            multiword_detector.train(password)
            
            # Get the next password
            password = file_input.read_password()
            
    except Exception as msg:
        print("Exception: " + str(msg))
        print("Exiting...")
        return
        
    # Save the learned alphabet
    program_info['alphabet'] = ag.get_alphabet()
        
    # Print some basic statistics after first loop
    print()
    print("Number of Valid Passwords: " + str(file_input.num_passwords))
    print("Number of Encoding Errors Found in Training Set:" + str(file_input.num_encoding_errors))
    print()
        
    # Perform duplicate detection and warn user if no duplicates were found
    if not file_input.duplicates_found:
        print()
        print("WARNING:")
        print("    No duplicate passwords were detected in the first " + 
            str(file_input.num_to_look_for_duplicates) + " parsed passwords")
        print()
        print("    This may be a problem since the training program needs to know frequency")
        print("    info such as '123456' being more common than '629811'")
        if get_confirmation("Do you want to exit and try again with a different training set (RECOMENDED)"):
            return
            
    ## Perform second loop through training data
    #
    # This pass is responsible for the following:
    #
    # -Learning OMEN NGRAMs
    # -Training the PCFG grammar
    #
    print("-------------------------------------------------")    
    print("Performing second pass on the training passwords")
    print("-------------------------------------------------")
    print("")   
    
    # Re-Initialize the file input to read passwords from
    file_input = TrainerFileInput(
                    program_info['training_file'], 
                    program_info['encoding'])
                    
    # Reset progress_bar
    num_parsed_so_far = 0
    print("Printing out status after every million passwords parsed")
    print("------------")
    
    # Initialize OMEN lookup tables
    omen_trainer = AlphabetLookup(
        alphabet = program_info['alphabet'], 
        ngram = program_info['ngram'],
        max_length = program_info['max_len']
        )
    
    # Initialize the PCFG Password parse
    pcfg_parser = PCFGPasswordParser(multiword_detector)
    
    ## Loop until we hit the end of the file
    try:
        password = file_input.read_password()
        while password:
        
            # Print status indicator if needed
            num_parsed_so_far += 1
            if num_parsed_so_far % 1000000 == 0:
                print(str(num_parsed_so_far//1000000) +' Million')
                
            # Parse OMEN info
            omen_trainer.parse(password)
            
            # Parse the pcfg info
            pcfg_parser.parse(password)
            
            # Get the next password
            password = file_input.read_password()
                        
    except Exception as msg:
        traceback.print_exc(file=sys.stdout)
        print("Exception: " + str(msg))
        print("Exiting...")
        return
    
    print()    
    print("-------------------------------------------------") 
    print("Compleated Parsing Training Data")    
    print("Calculating Statistics")
    print("-------------------------------------------------")
    print()

    # Calculate the OMEN level data
    omen_trainer.apply_smoothing()
    
    print()    
    print("-------------------------------------------------") 
    print("Saving Data")   
    print("-------------------------------------------------")
    print()
    
    # Save the configuration file
    if not save_config_file(base_directory,program_info, file_input, pcfg_parser):
        print("Error, something went wrong saving the configuration file to disk")
        print("The training did not compleate correctly")
        print("Exiting...")
        return
    
    # Save the OMEN data
    if not save_omen_rules_to_disk(omen_trainer, base_directory, program_info):
        print("Error, something went wrong saving the OMEN data to disk")
        print("The training did not compleate correctly")
        print("Exiting...")
        return
        
    # Save the pcfg data to disk
    if not save_pcfg_data(
                base_directory, 
                pcfg_parser, 
                program_info['encoding'], 
                program_info['save_sensitive']
            ):
        print("Error, something went wrong saving the pcfg data to disk")
        print("The training did not compleate correctly")
        print("Exiting...")
        return
        
    ## Print statisticts to the screen
   
    print()    
    print("-------------------------------------------------") 
    print("Top 5 e-mail providers")   
    print("-------------------------------------------------")
    print()
    top5= pcfg_parser.count_email_providers.most_common(5)
    for item in top5:
        print(item[0] + " : " + str(item[1]))
        
    print()    
    print("-------------------------------------------------") 
    print("Top 5 URL domains")   
    print("-------------------------------------------------")
    print()
    top5 = pcfg_parser.count_website_hosts.most_common(5)
    for item in top5:
        print(item[0] + " : " + str(item[1]))
        
    print()    
    print("-------------------------------------------------") 
    print("Top 10 Years found")   
    print("-------------------------------------------------")
    print()
    top10 = pcfg_parser.count_years.most_common(10)
    for item in top10:
        print(item[0] + " : " + str(item[1]))      
    
    
if __name__ == "__main__":
    main()    
