#!/usr/local/bin/python3

########################################################################################
#
# Name: PCFG_Cracker File IO code
# Description: Holds most of the file IO code used when loading
#              dictionaries, rules, and config files
#
#########################################################################################

from __future__ import print_function
import sys
import string
import struct
import os



##############################################################
# Loads the basic config file
# This contains a lot of information about the basic configuration
# that you may want to keep outside of the Rule files
##############################################################
def loadConfig(g_vars,c_vars):
    return g_vars.RETValues['STATUS_OK']
    
    
##############################################################
# Top level function to read the Rules for the grammar
##############################################################
def loadRules(g_vars,c_vars):
    return g_vars.RETValues['STATUS_OK']