#!/usr/bin/env python3


#########################################################################
# Contains file operations for saving output of a PCFG Scoring Run
#
#########################################################################


import os
import sys
import codecs


## Saves output to a file, one by one
#
# Making this a class so it can save one result at a time
#
class FileOutput:


    ## Open the file for writing
    #
    # Passes file exceptions back up if they occur
    # Eg: if the program doesn't have permission to create the file
    #
    def __init__(self, filename, encoding = 'utf-8'):
    
        self.encoding = encoding
        self.filename = filename
        
        # If a file was specified to write the data to, open it for writing
        if filename != None:
            self.file = codecs.open(
                self.filename, 
                'w', 
                encoding= self.encoding, 
            )
        
        ## If no filename was specified, output all results to stdout
        #
        # Doing this by re-assigning the function so I don't have to include
        # this logic throughout the rest of the scorer
        else:
            self.write_data = self.stdout_data
        
    
    ## Takes a Python tuple and writes it as tab seperated to a file followed
    #  by a newline
    #   
    def write_data(self, data):
    
        last_index = len(data) -1
        for index, item in enumerate(data):
            self.file.write(str(item))
            if index < last_index:
                self.file.write('\t')
        
        self.file.write('\n')
        
    
    ## Takes a Python tuple and writes it as tab seperated to stdout followed
    #  by a newline
    #   
    def stdout_data(self, data):
    
        last_index = len(data) -1
        for index, item in enumerate(data):
            sys.stdout.write(str(item))
            if index < last_index:
                sys.stdout.write('\t')
        
        sys.stdout.write('\n')