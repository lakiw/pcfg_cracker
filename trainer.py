#!/usr/bin/env python3


"""

Name: PCFG Trainer

    Training program that creates Probabilistic Context Free Grammars (PCFGs)
    from plaintext passwords

    Can also be used to generate statistical data and dictionaries for other
    cracking methods such as MASK attacks and OMEN

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

# Local imports
from lib_trainer.banner_info import print_banner
from lib_trainer.trainer_file_input import detect_file_encoding

from lib_trainer.run_trainer import run_trainer

from lib_trainer.trainer_file_output import create_rule_folders


def parse_command_line(program_info):
    """
    Responsible for parsing the command line.

    Note: This is a fairly standardized format that I use in many of my programs

    Inputs:
        program_info: A dictionary that contains the default values of
        command line options. Results overwrite the default values and the
        dictionary is returned after this function is done.
    Returns:
        True: If successfully

        False: If a value error occurs

        (Special: Program Exits): If Argparse is given the --help option
    """

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
        help = 'Comments to save in the rule configuration file, encapsulated in quotes ""',
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
    #
    # Note, not implimented yet
    #
    #parser.add_argument(
    #    '--smoothing',
    #    '-s',
    #    help = '<ADVANCED> The amount of probability smoothing to apply to ' +
    #    'the generated grammar. For example, if it is 0.01 then items with ' +
    #    'a prob difference of 1%% will be given the same prob. A setting ' +
    #    'of 0 will turn this off. Default: ' +  str(program_info['smoothing']),
    #    required = False,
    #    default = program_info['smoothing'],
    #    type = float
    #

    # Sets the coverage of the trained grammer. Set it to 1.0 to disable Markov
    # guesses. If you set it to 0.0 it will only generate Markov guesses.
    parser.add_argument(
        '--coverage',
        '-c',
        help = '<ADVANCED> The coverage you expect the training set to have ' +
        'when cracking passwords. What this really means is how many guesses ' +
        'should be generated from strings found in the training set, and how ' +
        'many guesses should be generated by Brute-Force/Markov/OMEN. A higher ' +
        'coverage means less guesses generated by fall back options like Markov. ' +
        'Roughly coverage translates to the percentage of guesses to generate ' +
        'using strings found in the training set, so a coverage of 1.0 means do ' +
        'not generate Brute-Force/Markov/OMEN guesses, and a coverage of 0.0 ' +
        'means ONLY generate Brute-Force/Makov/OMEN guesses. A coverage of 0.5 ' +
        'would mean splitting the guesses between them 50/50. ' +
        'Range: Between 1.0 and 0.0. Default: ' +
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
    #program_info['smoothing'] = args.smoothing
    program_info['coverage'] = args.coverage

    ## Sanity checking of values
    #
    # Check to make sure smoothing makes sense
    #if program_info['smoothing'] < 0 or program_info['smoothing'] > 0.9:
    #    print("Error, smoothing must be a value between 0.9 and 0")
    #    return False

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


def main():
    """

    Main function, starts everything off

    Responsible for calling the command line parser, detecting the
    encoding of the training set, creating the initial folders
    and then kicking off the training via run_trainer()

    Inputs:
        None

    Returns:
        None
    """

    # Information about this program
    program_info = {

        # Program and Contact Info
        'name':'PCFG Trainer',
        'version': '4.3',
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
    print("Version: " + str(program_info['version']))

    # Parsing the command line
    if not parse_command_line(program_info):
        # There was a problem with the command line so exit
        print("Exiting...")
        return

    ## Set the file encoding for the training set
    #
    # If NOT specified on the command line by the user run an autodetect
    if program_info['encoding'] is None:
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
    # Also aiming to make this OS independent
    #
    base_directory = os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        'Rules',
                        program_info['rule_name'])

    if not create_rule_folders(base_directory):
        print("Exiting...")
        return

    # Start training the ruleset
    if not run_trainer(program_info, base_directory):
        print("The training did not complete successfully. Exiting")


if __name__ == "__main__":
    main()
