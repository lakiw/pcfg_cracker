#!/usr/bin/env python3


###############################################################################
# Saves data relating to the PCFG cracker to disk
#
# This also calls functions to calculate the statistics and apply prob smoothing
#
###############################################################################


import os
import codecs

# Local imports
from .calculate_probabilities import calculate_probabilities


## Saves data for an individual Python Counter of pcfg data
#
# Variables:
#
#    filename: The fill path and filename to save the data to disk
#
#    counter: The counter containing all of the data for this particular data
#
#    encoding: The encoding to save the data as. Aka 'ascii'
#
# Return:
#   
#    True: If it completed successfully
#    False: If any errors occured 
#
def calculate_and_save_counter(filename, item, encoding):

    prob_list = calculate_probabilities(item)
    
    # Note, if there is no items, just write an empty file anyways. That
    # will simplify the logic in the pcfg_manager than needs to use these
    # rules
    #
    try:
        with codecs.open(filename, 'w', encoding= encoding) as datafile:
            for item in prob_list:
                datafile.write(str(item[0]) + '\t' + str(item[1])+'\n')
    
    except Exception as msg:
        print("Exception : " + str(msg))
        return False
        
    return True
            

## Saves data stored in a pcfg_parser to disk
#
# This is the top level function to call to save all of the pcfg data to disk
#
# Variables:
#
#    base_directory: The base directory to save the data to
#
#    pcfg_parser: Contains all of the statistics in Python counters 
#
#    encoding: The encoding to save the data as
#
# Return:
#   
#    True: If it completed successfully
#    False: If any errors occured 
#
def save_pcfg_data(base_directory, pcfg_parser, encoding, save_sensitive):
    
    ## Save keyboard data
    #
    
    item_folder = os.path.join(base_directory, "Keyboard")
    
    # Delete files in this folder if they already exist
    #
    # I know, I could delete the whole folder structure in Rules instead, but
    # I want to reduce the potential damage if I mess this up so I'm not
    # deleting directories
    for root, dirs, files in os.walk(item_folder):
        for f in files:
            os.unlink(os.path.join(root, f))
    
    for index, item in pcfg_parser.count_keyboard.items():
        filename = os.path.join(item_folder, str(index) + ".txt")
        if not calculate_and_save_counter(filename, item, encoding):
            return False
            
    ## Save e-mail data
    #
    
    item_folder = os.path.join(base_directory, "Emails")
    
    # Delete files in this folder if they already exist

    for root, dirs, files in os.walk(item_folder):
        for f in files:
            os.unlink(os.path.join(root, f))
    
    # Save the raw e-mails
    
    # Only save them if the user specified to save sensitive data
    if save_sensitive:
        filename = os.path.join(item_folder, "full_emails.txt")
        if not calculate_and_save_counter(filename, pcfg_parser.count_emails, encoding):
            return False
    
    # Save the email providers
    filename = os.path.join(item_folder, "email_providers.txt")
    if not calculate_and_save_counter(filename, pcfg_parser.count_email_providers, encoding):
        return False
        
        
    ## Save website data
    #
    
    item_folder = os.path.join(base_directory, "Websites")
    
    # Delete files in this folder if they already exist

    for root, dirs, files in os.walk(item_folder):
        for f in files:
            os.unlink(os.path.join(root, f))
    
    # Save the raw websites
    # Only save them if the user specified to save sensitive data
    if save_sensitive:
        filename = os.path.join(item_folder, "website_urls.txt")
        if not calculate_and_save_counter(filename, pcfg_parser.count_website_urls, encoding):
            return False
    
    # Save the website hosts
    filename = os.path.join(item_folder, "website_hosts.txt")
    if not calculate_and_save_counter(filename, pcfg_parser.count_website_hosts, encoding):
        return False
        
    # Save the website prefixes
    filename = os.path.join(item_folder, "website_prefixes.txt")
    if not calculate_and_save_counter(filename, pcfg_parser.count_website_prefixes, encoding):
        return False
                      
    return True