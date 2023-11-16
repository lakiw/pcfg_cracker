#!/usr/bin/env python3

"""

Name: PCFG Rule Editor

   Edit pretrained rules to make them match a password policy.

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
import shutil
import re


def parse_command_line(program_info):
    # Keeping the title text to be generic to make re-using code easier
    parser = argparse.ArgumentParser(
        description= program_info['name'] +
        ', version: ' + 
        program_info['version']
    )

    parser.add_argument(
        '--rule',
        '-r',
        help = 'Ruleset which will be edited.',
        required = True,
    )

    parser.add_argument(
        '--copy',
        help = 'If used, instead on editing the ruleset, this option creats a copy which will be edited.',
    )

    parser.add_argument(
        '--min_length',
        help = 'If used, checks for the minimal length of grammars.',
        default = 0,
    )

    parser.add_argument(
        '--max_length',
        help = 'If used, checks for the minimal length of grammars.',
        default = 0,
    )

    parser.add_argument(
        '--terminal_set',
        help = 'Comma seperated of list of terminals to keep. Any grammar containing a terminal that is not in this list will be removed.',
    )

    parser.add_argument(
        '--regex',
        help = 'Comma seperated of list of regexes to check grammars. All regexes must match to keep the grammar. Usefull to filter on password policy.',
    )


    args=parser.parse_args()

    # Standard Options
    program_info['rule'] = args.rule
    program_info['copy'] = args.copy
    program_info['min_length'] = int(args.min_length)
    program_info['max_length'] = int(args.max_length)
    if args.terminal_set:
        program_info['terminal_set'] = [x.upper() for x in args.terminal_set.split(',')]
    else:
        program_info['terminal_set'] = False
    if args.regex:
        program_info['regex'] = [x for x in args.regex.split(',')]
    return True

def _create_copy(rule_dir, output_dir):
    shutil.copytree(rule_dir, output_dir)


def check_regex(grammar, grammar_regex):
    print('Checking grammars with regex...')
    return_grammar = ''
    for line in grammar.split('\n'):
        if not line:
            continue
        structure = line.split('\t')[0]
        prob = line.split('\t')[1]
        prob = prob.strip()

        stop = False
        for regex in grammar_regex:
            if re.search(regex, structure):
                continue
            else:
                stop = True
                break
        
        if not stop:
            return_grammar += line
            return_grammar += '\n'
    return return_grammar


def edit_terminal_set(grammar, terminal_set):
    print('Checking grammars for terminals...')
    return_grammar = ''
    for line in grammar.split('\n'):
        if not line:
            continue
        structure = line.split('\t')[0]
        prob = line.split('\t')[1]
        prob = prob.strip()

        line = re.findall('[A-Z][0-9]{0,3}', line)
        if not line:
            print(f'Line containing invalid structure found {line}. Skipping.')
            continue
        skip = False
        for x in line:
            if x[0] not in terminal_set:
                skip = True
        if not skip:
            return_grammar += ''.join(line) + '\t' + prob + '\n'
    return return_grammar
            

def edit_length(grammar, min_length, max_length):
    print('Checking length of gramamrs...')
    return_grammar = ''
    for line in grammar.split('\n'):
        if not line:
            continue
        structure = line.split('\t')[0]
        prob = line.split('\t')[1]
        prob = prob.strip()

        line = re.findall('[A-Z][0-9]{0,3}', line)
        if not line:
            print(f'Line containing invalid structure found {line}. Skipping.')
            continue
        
        total_length = 0
        for x in line:
            if x[0] == 'A':
                total_length += int(x[1:])
            elif x[0] == 'D':
                total_length += int(x[1:])
            elif x[0] == 'Y':
                total_length += 4
            elif x[0] == 'O':
                total_length += int(x[1:])
            elif x[0] == 'K':
                total_length += int(x[1:])
            elif x[0] == 'X':
                total_length += int(x[1:])
        if not total_length and total_length <= max_length:
            return_grammar += ''.join(line) + '\t' + prob + '\n'
        elif total_length >= min_length and not max_length:
            return_grammar += ''.join(line) + '\t' + prob + '\n'
        elif total_length >= min_length and total_length <= max_length:
            return_grammar += ''.join(line) + '\t' + prob + '\n'
    
    return return_grammar


def edit_rules(config):
    if config.get('copy'):
        print(f'Creating copy of {config.get("copy")} to {config.get("rule")}')
        _create_copy(os.path.join(config.get('rules_dir'), config.get('rule')),
                    os.path.join(config.get('rules_dir'), config.get('copy')))
        config['rule'] = config['copy']
    
    grammar_file = os.path.join(config.get('rules_dir'), config.get('rule'), 'Grammar', 'grammar.txt')
    grammar = open(grammar_file, 'r').read()

    if config.get('min_length') or config.get('max_length'):
        grammar = edit_length(grammar, config.get('min_length'), config.get('max_length'))
    if config.get('terminal_set'):
        grammar = edit_terminal_set(grammar, config.get('terminal_set'))
    if config.get('regex'):
        grammar = check_regex(grammar, config.get('regex'))
    with open(grammar_file, 'w') as grammar_fp:
        print('Done editing, writing back results.')
        for line in grammar:
            grammar_fp.write(line)

    return True

def main():
    # Information about this program
    program_info = {
        # Program and Contact Info
        'name':'PCFG Edit Rules',
        'version': '1.1',
        'author':'Romke van Dijk',
        'contact':'github.com@ocbios.nl',
        'rules_dir': os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        'Rules',
                     ),
    }

    print(program_info['name'])
    print("Version: " + str(program_info['version']))

    # Parsing the command line
    if not parse_command_line(program_info):
        # There was a problem with the command line so exit
        print("Exiting...")
        return
   
    if not edit_rules(program_info):
        print('Error while editing rules. Exiting...')
        return

if __name__ == "__main__":
    main()   

