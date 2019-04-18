#!/usr/bin/env python3


################################################################################
#
# Name: PCFG Password Scorer
#  -- Will attempt to assign a probability score to an input values
#
#  -- Uses previously trained grammars created by trainer.py to assign
#     probabilities to different transistions and terminals
#
#  -- PLEASE DO NOT USE THIS WITHOUT MAJOR MODIFICATIONS AS PART OF A PASSWORD
#     CREATION POLICY OR BLACKLIST. YOUR USERS WILL HATE YOU AND THERE'S
#     A LOT OF FUNDAMENTAL WORK THAT STILL NEEDS TO BE DONE TO MAKE THIS
#     USEFUL FOR THAT USE CASE.
#
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
#  password_scorer.py
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
from collections import Counter

# Local imports
from lib_scorer.banner_info import print_banner
from lib_scorer.pcfg_grammar import PcfgGrammar
from lib_scorer.grammar_io import load_grammar
from lib_trainer.trainer_file_input import TrainerFileInput


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
        
    ## Standard options
    #
    # The rule name to use when scoring the inpput. 
    parser.add_argument(
        '--rule',
        '-r',
        help = 'Name of PCFG ruleset for use in scoring. Default is ' + 
        program_info['rule_name'],
        metavar = 'RULESET_NAME',
        required = False,
        default = program_info['rule_name']
    )
    
    # The input file of items to score
    parser.add_argument(
        '--input',
        '-i',
        help = 'The filename of the input set to score. Newline seperated',
        metavar = 'INPUT_FILENAME',
        required = True
    )
    
    # The output file to save results too 
    parser.add_argument(
        '--output',
        '-o',
        help = 'The output file to save results to. If not specified will output to stdout',
        metavar = 'OUTPUT_FILENAME',
        required = False,
        default = program_info['output_file']
    )
    
    # The output file to save results too 
    parser.add_argument(
        '--limit',
        '-l',
        help = 'The probability to use as a cut-off for password/not_password',
        metavar = 'LIMIT_PERCENTAGE',
        required = False,
        default = program_info['limit'],
        type = float, 
    )
    
    # Parse all the args and save them    
    args=parser.parse_args() 
    
    # Standard Options
    program_info['rule_name'] = args.rule
    program_info['input_file'] = args.input
    program_info['output_file']= args.output
    program_info['limit'] = args.limit
    
    ## Sanity checking of values
    #
    # Check to make sure limit makes sense
    if program_info['limit'] < 0 or program_info['limit'] > 1.0:
        print("Error, limit must be a value between 1.0 and 0.0")
        print("Also, your limit probably should be very close to 0.0, or have a lot of 0's in it")
        print("This is because most password guesses have very low probabilities of actually being a target's password.")
        return False

    return True
    

## Main function, starts everything off
#    
def main():

    # Information about this program
    program_info = {
    
        # Program and Contact Info
        'name':'PCFG Password Scorer',
        'version': '4.0',
        'author':'Matt Weir',
        'contact':'cweir@vt.edu',
        
        # Standard Options
        'rule_name':'Default',
        'output_file':None,
        'limit':0,
        
    }
      
    print_banner()
    print("Version: " + str(program_info['version']))
    print()
    
    # Parsing the command line
    if not parse_command_line(program_info):
        # There was a problem with the command line so exit
        print("Exiting...")
        return
    
    # Load Rules file from the standard storage location    
    # Making this OS independent
    base_directory = os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        'Rules',
                        program_info['rule_name'])
    
    ## Create the grammar object
    #
    # Does not load the grammar yet
    grammar = PcfgGrammar()
    
    # Attempt to load the rules file into the grammar
    print("Loading Rule: " + str(program_info['rule_name']))
    if not load_grammar(grammar, base_directory):
        print("Exiting...")
        return
    
    # Initialize the multiword detector
    print("Initializing Multi-Word Detector")
    grammar.create_multiword_detector()

    # Initialize the file input to read input values from
    # Re-using the TrainerFileInput from the trainer
    file_input = TrainerFileInput(
                    program_info['input_file'], 
                    grammar.encoding)
    

    # Start processing input
    print("Processing input wordlist")
    print()
    
    false_negative = 0
    try:
        input_value = file_input.read_password()
        while input_value:
            
            result = grammar.parse(input_value)
            print (result)
            if result[1] == 'o':
                false_negative += 1
            
            input_value = file_input.read_password()
    
    except Exception as msg:
        traceback.print_exc(file=sys.stdout)
        print("Exception: " + str(msg))
        print("Exiting...")
        return
    
    print("False negatives: " + str(false_negative))
        
if __name__ == "__main__":
    main() 