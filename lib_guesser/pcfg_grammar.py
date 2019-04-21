#!/usr/bin/env python3


#############################################################################
# This file contains the functionality to parse raw passwords for PCFGs
#
# The PCFGPasswordParser class is designed to be instantiated once and then
# process one password at at time that is sent to it
#
#############################################################################


# Global imports
import sys
import configparser


# Local imports
from.grammar_io import load_grammar


## Responsible for holding the PCFG Grammar
#
class PcfgGrammar:

    ## Initializes the class and all the data structures
    #
    # Input:
    #
    #    rule_name: The name of the ruleset to load the grammar from
    #
    #    version: The version of the PCFG Guesser. Used to determine if
    #             this program can load a ruleset that may be generated from
    #             an older version of the trainer
    #
    def __init__(self, rule_name, base_directory, version):
        
        ## Debugging and Status Information
        #
        self.encoding = None
        self.rulename = rule_name
        
        ## If an exception occurs, pass it back up the stack
        self.grammar, self.base, ruleset_info = load_grammar(rule_name, base_directory, version)
       
        