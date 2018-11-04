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
    directory_listing.append(os.path.join(base_directory,"Masks"))
    directory_listing.append(os.path.join(base_directory,"Prince"))
    
    # Create the directories
    
    return make_directories_from_list(directory_listing)