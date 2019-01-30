#!/usr/bin/env python3


#########################################################################
# Contains all the file output logic for the python pcfg trainer
#
#########################################################################


import os
import errno


## Create a directory if one does not already exist
#
# Will re-raise any exceptions and send them back to the calling program
#
def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


## Creates all the directories from a list of files
#
# Returns:
#     True: If Sucessful
#     False: If an error occured
#
def make_directories_from_list(directory_listing):
    try:
        for path in directory_listing:
            make_sure_path_exists(path)
    except OSError:
        print("Error creating the directories to save the results")
        print(str(error))
        return False
    return True
    

## Creates all the folders for saving a pcfg rule to disk
#
# Will create all files in the folder specified by base directory
#
# Returns:
#     True: If Sucessful
#     False: If an error occured
#
def create_rule_folders(base_directory):

    # Set up the list of all the directories to create
    directory_listing = [base_directory]
    
    # Non-PCFG related directories
    directory_listing.append(os.path.join(base_directory,"Masks"))
    directory_listing.append(os.path.join(base_directory,"Prince"))
    
    # PCFG replacements directories
    directory_listing.append(os.path.join(base_directory,"Grammar"))
    directory_listing.append(os.path.join(base_directory,"Alpha"))
    directory_listing.append(os.path.join(base_directory,"Capitalization"))
    directory_listing.append(os.path.join(base_directory,"Prince"))
    directory_listing.append(os.path.join(base_directory,"Digits"))
    directory_listing.append(os.path.join(base_directory,"Years"))
    directory_listing.append(os.path.join(base_directory,"Other"))
    directory_listing.append(os.path.join(base_directory,"Context"))
    directory_listing.append(os.path.join(base_directory,"Keyboard"))
    directory_listing.append(os.path.join(base_directory,"Websites"))
    directory_listing.append(os.path.join(base_directory,"Emails"))
    
    return make_directories_from_list(directory_listing)