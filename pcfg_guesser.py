#!/usr/bin/env python3


"""

Name: PCFG Guesser
  
  Probabilistic Context Free Grammar (PCFG) Password Guessing Program
  
  Alt Title: Pretty Cool Fuzzy Guesser (PCFG)

Written by Matt Weir

Initial backend algorithm developed by Matt Weir, Sudhir Aggarwal, and Breno de Medeiros

Special thanks to Bill Glodek for collaboration on original proof of concept

Special thanks to the National Institute of Justice and the NW3C for support with the initial reasearch

Huge thanks to Florida State University's ECIT lab where the original version was developed

And the list goes on and on... And thank you whoever is reading this. Be good!

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

# Global imports
import argparse
import os
import configparser # Used to save/load status of guessing sessions
import datetime

# Local imports
from lib_guesser.banner_info import print_banner
from lib_guesser.pcfg_grammar import PcfgGrammar
from lib_guesser.cracking_session import CrackingSession
from lib_guesser.honeyword_session import HoneywordSession


def parse_command_line(program_info):
    """
    Responsible for parsing the command line.

    Note: This is a fairly standardized format that I use in many of my programs

    Inputs:

        program_info: A dictionary that contains the default values of
        command line options. Results overwrite the default values and the
        dictionary is returned after this function is done.

    Returns:
        True: If the command line was parsed successfully

        False: If an error occured parsing the command line

        (Program Exits): If the --help option is specified on the command line
    """

    # Keeping the title text to be generic to make re-using code easier
    parser = argparse.ArgumentParser(
        description= program_info['name'] +
        ', version: ' +
        program_info['version']
    )

    ## Standard options for ruleset, etc
    #
    # The rule name to load the grammar from. Should be saved under the
    # 'Rules' folder. This rule needs to have been previously created by
    # the pcfg 'trainer.py' program.
    parser.add_argument(
        '--rule',
        '-r',
        help = 'The ruleset to use. Default is ' +
        program_info['rule_name'],
        metavar = 'RULESET_NAME',
        required = False,
        default = program_info['rule_name']
    )

    parser.add_argument(
        '--session',
        '-s',
        help = 'Session name. Used for saving/restoring sessions Default is ' +
            program_info['session_name'],
        metavar = 'SESSION_NAME',
        required = False,
        default = program_info['session_name']
    )

    parser.add_argument(
        '--load',
        '-l',
        help='Loads a previous guessing session',
        dest='load',
        action='store_const',
        const= not program_info['load_session'],
        default = program_info['load_session']
    )

    # Advanced options

    parser.add_argument(
        '--limit',
        '-n',
        help='Generate N guesses and then exit. This can be used for wordlist generation and/or research evaluation',
        type=int,
        default=program_info['limit']
    )

    parser.add_argument(
        '--skip_brute',
        help='Do not perform Markov based guesses using OMEN. This is useful ' +
            'if you are running a seperate dedicated Markov based attack',
        dest='skip_brute',
        action='store_const',
        const= not program_info['skip_brute'],
        default = program_info['skip_brute']
    )

    parser.add_argument(
        '--all_lower',
        help='Only generate lowercase guesses. No case mangling. (Setting is currently not applied to OMEN generated guesses)',
        dest='skip_case',
        action='store_const',
        const= not program_info['skip_case'],
        default = program_info['skip_case']
    )

    # Debugging and research information
    parser.add_argument(
        '--debug',
        '-d',
        help='Prints out debugging info vs guesses.',
        dest='debug',
        action='store_const',
        const= not program_info['debug'],
        default = program_info['debug']
    )

    parser.add_argument(
        '--mode',
        '-m',
        help = "Method in which guesses are generated Default is '" +
            program_info['cracking_mode'] +
            "' Supported Modes: " + str(program_info['supported_modes']),
        metavar = 'MODE',
        required = False,
        default = program_info['cracking_mode'],
        choices = program_info['supported_modes']
    )

    # Parse all the args and save them
    args=parser.parse_args()

    # Standard Options
    program_info['rule_name'] = args.rule
    program_info['session_name'] = args.session
    program_info['load_session'] = args.load

    # Advanced Options
    program_info['limit'] = args.limit
    program_info['skip_brute'] = args.skip_brute
    program_info['skip_case'] = args.skip_case
    program_info['cracking_mode'] = args.mode

    # Debugging Options
    program_info['debug'] = args.debug

    # Check validity of options
    if program_info['limit'] and program_info['limit'] <= 0:
        print(f"The guess --limit/-n must be a positive number. The value specified was {program_info['limit']}")
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
        'name':'PCFG Guesser',
        'version': '4.8',
        'author':'Matt Weir',
        'contact':'cweir@vt.edu',

        # Standard Options
        'rule_name':'Default',
        'session_name':'default_run',
        'load_session':False,
        'limit': None,

        # Cracking Mode options
        'cracking_mode':'true_prob_order',
        'supported_modes':['true_prob_order', 'random_walk', 'honeywords'],

        # Advanced Options
        'skip_brute': False,
        'skip_case': False,

        # Debugging Options
        'debug': False,

    }

    print_banner()
    print("Version: " + str(program_info['version']),file=sys.stderr)
    print('',file=sys.stderr)

    # Parsing the command line
    if not parse_command_line(program_info):
        # There was a problem with the command line so exit
        print("Exiting...",file=sys.stderr)
        return

    # The configfile to load/save the guessing session status
    save_filename = os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        program_info['session_name'] + '.sav'
                        )

    # Get the base directory to load all of the rules from
    #
    # Don't want to use the relative path since who knows where someone is
    # invoking this script from
    #
    # Also aiming to make this OS independent
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
            save_filename,
            skip_brute = program_info['skip_brute'],
            skip_case = program_info['skip_case'],
            debug = program_info['debug']
            )

    except:
        print("Exiting")
        return

    # Initiate cracking mode specific features
    if program_info['cracking_mode'] == 'true_prob_order':
        # Check to see if we need to load up a previous guessing session
        if program_info['load_session']:     
            print("Restoring previous session: " + program_info['session_name'],file=sys.stderr)
            save_config = load_save(save_filename, program_info)

            # Check to make sure it is valid
            if save_config is None:
                print("Exiting...",file=sys.stderr)
                return

        # Create a new save config
        # It's easeir to just create a default config even if a non-supported guessing mode like honeywords was selected
        else:
            save_config = create_save_config(program_info)

        # Check to make the ruleset is the same if restoring a guessing session
        if save_config.has_option('rule_info','uuid'):
            # Looks like the rule was changed since the last session
            if save_config['rule_info']['uuid'] != pcfg.ruleset_info['uuid']:
                print("Error: The UUID of the save file and the loaded rules do not match",file=sys.stderr)
                print("       This normally happens if you retrain a ruleset and then try to restore an old session",file=sys.stderr)
                print("       Expected UUID: " + str(save_config['rule_info']['uuid']), file=sys.stderr)
                print("       Found UUID: " + str(pcfg.ruleset_info['uuid']), file=sys.stderr)
                print("Exiting...",file=sys.stderr)
                return

        # Initalize the rule UUID for a new guessing session
        else:
            save_config.set('rule_info', 'uuid', pcfg.ruleset_info['uuid'])

        # Initalize the cracking session
        current_cracking_session = CrackingSession(pcfg, save_config, save_filename)

        # Setup is done, now start generating rules
        current_cracking_session.run(load_session = program_info['load_session'], limit = program_info['limit'])

    elif program_info['cracking_mode'] in ['random_walk', 'honeywords']:
        current_cracking_session = HoneywordSession(pcfg, program_info['cracking_mode'])
        # Setup is done, now start generating rules
        current_cracking_session.run(limit = program_info['limit'])


def create_save_config(program_info):
    """
    Creates the configparser object that will be used to save/load sessions

    Inputs:
        program_info: A dictionary containing information about the current session

    Returns:
        save_config: A configparser containing some of the values to save

    """

    save_config = configparser.ConfigParser()

    section = "rule_info"
    save_config.add_section(section)
    save_config.set(section, 'rule_name', program_info['rule_name'])
    save_config.set(section, 'skip_brute', str(program_info['skip_brute']))
    save_config.set(section, 'skip_case', str(program_info['skip_case']))

    section = "session_info"
    save_config.add_section(section)
    save_config.set(section, 'first_started', datetime.datetime.now().isoformat())

    section = "guessing_info"
    save_config.add_section(section)

    return save_config


def load_save(save_filename, program_info):
    """
    Loads a configparser object containing info about a saved guessing session

    Inputs:
        base_directory: The directory to load the save file from

        program_info: A dictionary containing information about the current session

    Returns:
        save_config: A configparser containing some of the values to save

    """

    save_config = configparser.ConfigParser()

    try:
        save_config.read_file(open(save_filename))

        ## Check to make sure it is well formed
        #
        if not save_config.has_option('rule_info', 'rule_name'):
            raise configparser.Error('Missing rule_name')
        if not save_config.has_option('rule_info','uuid'):
            raise configparser.Error('Missing rule uuid')
        if not save_config.has_option('rule_info','skip_brute'):
            raise configparser.Error('Missing the skip_brute flag for session')
        if not save_config.has_option('rule_info','skip_case'):
            raise configparser.Error('Missing the skip_case flag for session')
        if not save_config.has_option('session_info','last_updated'):
            raise configparser.Error('Missing last_updated')

        # Set the ruleset info
        program_info['rule_name'] = save_config.get('rule_info','rule_name')

        # Set the skip_brute flag
        program_info['skip_brute'] = save_config.getboolean('rule_info','skip_brute')

        # Set the skip_case flag for not doing case mangling
        program_info['skip_case'] = save_config.getboolean('rule_info','skip_case')

        return save_config

    except IOError as msg:
        print("Could not open the session save file.",file=sys.stderr)
        print("Save File: " + save_filename,file=sys.stderr)
        return None
    except configparser.Error as msg:
        print("Error occured parsing the save file: " + str(msg),file=sys.stderr)
        return None


if __name__ == "__main__":
    main()
