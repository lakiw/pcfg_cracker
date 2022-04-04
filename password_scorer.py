#!/usr/bin/env python3


"""
Name: PCFG Password Scorer
  --Will attempt to assign a probability score to an input values

  --Uses previously trained grammars created by trainer.py to assign
    probabilities to different transistions and terminals

  --PLEASE DO NOT USE AS PART OF A PASSWORD CREATION POLICY OR BLACKLIST
    WITHOUT MAJOR MODIFICATIONS. YOUR USERS WILL HATE YOU AND THERE'S
    A LOT OF FUNDAMENTAL WORK THAT STILL NEEDS TO BE DONE TO MAKE THIS
    USEFUL FOR THOSE USE CASES.

Copyright 2021 Matt Weir

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Contact Info: cweir@vt.edu

"""


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
from lib_scorer.banner_info import print_banner
from lib_scorer.pcfg_password_scorer import PCFGPasswordScorer
from lib_scorer.grammar_io import load_grammar
from lib_scorer.file_output import FileOutput
from lib_trainer.trainer_file_input import TrainerFileInput


def parse_command_line(program_info):
    """
    Parses the command line

    Responsible for parsing the command line.
    If you have any command line options that you want to add, they go here.
    All results are returned as a dictionary in 'program_info'
    
    If successful, returns True, returns False if value error, program exits if
    argparse catches a problem.
    
    Inputs:
        program_info: A python dictionary that contains information about
        the program, and variables which cotain default values for
        command line options
        
    Returns:
        True: If the command line was parsed correctly
        
        False: If an error occured parsing the command line
    
    """

    # Keeping the title text to be generic to make re-using code easier
    parser = argparse.ArgumentParser(
        description= program_info['name'] +
        ', version: ' +
        program_info['version']
    )

    # Standard options

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

    # The probability limit used to classify password/not passwords
    parser.add_argument(
        '--limit',
        '-l',
        help = 'The probability to use as a cut-off for password/not_password',
        metavar = 'LIMIT_PERCENTAGE',
        required = False,
        default = program_info['limit'],
        type = float,
    )

    # The OMEN limit used to classify password/not password
    parser.add_argument(
        '--max_omen',
        '-m',
        help = 'The maximum OMEN level for categorization as a password. Set to "0" to disable OMEN matching',
        metavar = 'MAX_OMEN_LEVEL',
        required = False,
        default = program_info['max_omen_level'],
        type = int,
    )

    # Parse all the args and save them
    args=parser.parse_args()

    # Standard Options
    program_info['rule_name'] = args.rule
    program_info['input_file'] = args.input
    program_info['output_file']= args.output
    program_info['limit'] = args.limit
    program_info['max_omen_level'] = args.max_omen

    # Sanity checking of values

    # Check to make sure limit makes sense
    if program_info['limit'] < 0 or program_info['limit'] > 1.0:
        print("Error, limit must be a value between 1.0 and 0.0")
        print("Also, your limit probably should be very close to 0.0, or most values will be classified as non-passwords")
        print("This is because most password guesses have very low probabilities of actually being a target's password.")
        return False

    return True


def main():
    """
    Main function, starts everything off
    
    Inputs:
        None
        
    Returns:
        None
    """

    # Information about this program
    program_info = {

        # Program and Contact Info
        'name':'PCFG Password Scorer',
        'version': '4.3',
        'author':'Matt Weir',
        'contact':'cweir@vt.edu',

        # Standard Options
        'rule_name':'Default',
        'output_file':None,
        'limit':0,

        # OMEN Options
        #
        # Note, picking 9 as the default because the keyspace when training
        # on rockyou for level 9 is roughly 600 million which seems reasonable
        'max_omen_level':9

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

    # Create the pw_parser object
    # Does not load the pcfg grammar yet
    pw_parser = PCFGPasswordScorer(limit = program_info['limit'])

    # Attempt to load the rules file into the pw_parser
    print("Loading Rule: " + str(program_info['rule_name']))
    if not load_grammar(pw_parser, base_directory):
        print("Exiting...")
        return

    # Initialize the multiword detector
    print("Initializing Multi-Word Detector")
    pw_parser.create_multiword_detector()

    # Initalize the OMEN scorer
    print("Initializing the OMEN scorer")
    pw_parser.create_omen_scorer( base_directory, program_info['max_omen_level'])

    # Initialize the file input to read input values from
    # Re-using the TrainerFileInput from the trainer
    file_input = TrainerFileInput(
                    program_info['input_file'],
                    pw_parser.encoding)

    # Open file for output
    writer = FileOutput(program_info['output_file'], pw_parser.encoding)

    # Start processing input
    print("Processing input wordlist")
    print()

    false_negative = 0
    try:
        input_value = file_input.read_password()
        while input_value:

            result = pw_parser.parse(input_value)

            writer.write(result)

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
