#!/usr/bin/env python3


###############################################################################
# This file contains logic for extracting data that will be useful for
# generating wordlists to use in an optimized PRINCE guessing session
#
# Note: While PRINCE is not a PCFG based guess generator, the data generated
#       by this trainer can be useful for supporting other attack modes
#
###############################################################################

    
## Save any statistics that would be useful to generating PRINCE wordlists
#
# Note: This should be called after all the individual sections of an input
#       password has already been parsed
#
# Variables:
#    count_prince: A Python Counter object that holds all the sections that
#                  will be saved for PRINCE metrics
#
#    section_list: A list containing all of the base_structure sections
#                  for the parsed password
#
# Returns:
#    None: No return value
#
def prince_evaluation(count_prince, section_list):

    #Loop through the section list and add it to the PRINCE counts
    for item in section_list:
        count_prince[item[1]] += 1
        
    return