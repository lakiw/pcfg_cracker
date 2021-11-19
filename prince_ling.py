#!/usr/bin/env python3


"""

Name: PRINCE-LING
    -- PRINCE Language Indexed N-Grams

    -- Uses data from the PCFG trainer to make wordlists optimized for use
    in PRINCE stlye attacks

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
from lib_princeling.banner_info import print_banner
from lib_princeling.wordlist_generation import create_prince_wordlist
from lib_guesser.pcfg_grammar import PcfgGrammar

def parse_command_line(program_info):
    """
    Responsible for parsing the command line.

    Note: This is a fairly standardized format that I use in many of my programs

    Inputs:
        program_info: A dictionary that contains the default values of
        command line options. Results overwrite the default values and the
        dictionary is returned after this function is done.

    Returns:
        True: If the command line was parsed sucessfully

        False: If a value error occurs

        (Program Exit): If argparse is given the -h option

    """

    # Keeping the title text to be generic to make re-using code easier
    parser = argparse.ArgumentParser(
        description= program_info['name'] +
        ', version: ' +
        program_info['version']
    )

    # The rule name to use for generating the wordlist
    parser.add_argument(
        '--rule',
        '-r',
        help = 'Name of PCFG ruleset to generate the PRINCE wordlist. Default is ' +
        program_info['rule_name'],
        metavar = 'RULESET_NAME',
        required = False,
        default = program_info['rule_name']
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

    # Max size of wordlist to generate
    parser.add_argument(
        '--size',
        '-s',
        help = 'The maximum size of wordlist to generate. By default, will create words until grammar is exhausted',
        metavar = 'MAX_SIZE',
        required = False,
        default = program_info['max_size'],
        type = int,
    )

    # Only generate lowercase words for the wordlist
    parser.add_argument(
        '--all_lower',
        help='Only save lowercase words. No case mangling.',
        dest='skip_case',
        action='store_const',
        const= not program_info['skip_case'],
        default = program_info['skip_case']
    )

    # Parse all the args and save them
    args=parser.parse_args()

    # Standard Options
    program_info['rule_name'] = args.rule
    program_info['output_file']= args.output
    program_info['max_size'] = args.size

    # Advanced options
    program_info['skip_case'] = args.skip_case

    # Sanity checking of values
    # Check to make sure limit makes sense
    if program_info['max_size'] is not None and program_info['max_size'] <= 0:
        print("Error, max size must be greater than 0")
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
        'name':'PRINCE-LING',
        'version': '4.3',
        'author':'Matt Weir',
        'contact':'cweir@vt.edu',

        # Standard Options
        'rule_name':'Default',
        'output_file':None,
        'max_size':None,

        # Advanced Options
        'skip_case':False,
        }

    print_banner()
    print("Version: " + str(program_info['version']),file=sys.stderr)
    print("",file=sys.stderr)

    # Parsing the command line
    if not parse_command_line(program_info):
        # There was a problem with the command line so exit
        print("Exiting...",file=sys.stderr)
        return

    # Get the base directory to load all of the rules from
    #
    # Don't want to use the relative path since who knows where someone is
    # invoking this script from
    #
    # Also aiming to make this OS independent/
    #
    base_directory = os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        'Rules',
                        program_info['rule_name']
                        )

    # Create the grammar
    #
    # Note, if the ruleset can not be loaded, (for example it doesn't exist),
    # it will throw an exception.
    try:
        print("Loading Ruleset: " + str(program_info['rule_name']),file=sys.stderr)
        print('',file=sys.stderr)
        pcfg = PcfgGrammar(
            program_info['rule_name'],
            base_directory,
            program_info['version'],
            base_structure_folder = "Prince",
            skip_case = program_info['skip_case'],
            )

    except Exception as msg:
        print(msg,file=sys.stderr)
        print("Exiting",file=sys.stderr)
        return

    # Set up the wordlist save option, either stdout or write to file
    pcfg.save_to_file(program_info['output_file'])

    create_prince_wordlist(
        pcfg,
        program_info['max_size']
        )

    pcfg.shutdown()


if __name__ == "__main__":
    main()
