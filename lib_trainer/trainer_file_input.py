#!/usr/bin/env python3


#########################################################################
# Contains all the file reading logic for the python pcfg trainer
#
#########################################################################


import os
import errno
import codecs


## Prints a warning message and asks for user confirmation
#
# Return Values:
# --True: User selected Yes
# --False: User selected No
#
def get_confirmation(warningtext):
    print()
    print(warningtext)
    while True:
        try:
            user_input = input("Please confirm (Y/N): ")
        except:
            user_input = ''
        if user_input.lower() == 'y' or user_input.lower() == 'yes':
            return True
        elif user_input.lower() == 'n' or user_input.lower() == 'no':
            return False
        else:
            print("The option: " + str(user_input) + " : is not a valid input")
            print("Valid options: [Y]es or [N]o")

            
## Used for autodetecting file encoding of the training password set
#
# Requires the python package chardet to be installed
#
# pip install chardet
#
# You can also get it from https://github.com/chardet/chardet
#
# I'm keeping the declarations for the chardet package local to this file 
# so people can run this tool without installing it if they don't want to 
# use this feature
#
def detect_file_encoding(training_file, file_encoding, max_passwords = 10000):

    ##Try to import chardet
    #
    # If that package is not installed print out a warning and use is ok,
    # then use ascii as the default values
    #
    try:
        from chardet.universaldetector import UniversalDetector
        detector = UniversalDetector()
    except ImportError as error:
        print("FAILED: chardet not insalled")
        print("It is highly recommended that you install the 'chardet' Python package")
        print("or manually specify the file encoding of the training set via the command line")
        print("You can download chardet from https://pypi.python.org/pypi/chardet")
        if get_confirmation("Do you want to continue using the default encoding 'ascii'?"):
            file_encoding.append('ascii')
            return True
        
        else:
            # User wanted to exit instead
            print("Understood. Please install chardet or specify an encoding " +
                "format on the command line"
            )
            return False
                
    try:
        cur_count = 0
        with open(training_file, 'rb') as file:
            for line in file.readlines():
                detector.feed(line)
                if detector.done: 
                    break
                cur_count = cur_count + 1
                if cur_count >= max_passwords:
                    break
            detector.close()
            
    except IOError as error:
        print ("Error opening file " + training_file)
        print ("Error is " + str(error))
        return False
        
    try:
        file_encoding.append(detector.result['encoding'])
        print("File Encoding Detected: " + str(detector.result['encoding']))
        print("Confidence for file encoding: " + str(detector.result['confidence']))
        print("If you think another file encoding might have been used please ")
        print("manually specify the file encoding and run the training program again")
        print()
    except KeyError as error:
        print("Error encountered with file encoding autodetection")
        print("Error : " + str(error))
        return False

    return True
    

## Checks to see if the input password is valid for this training program
#
# Invalid in this case means you don't want to train on them
#
# Additionaly grammar checks may be run later to futher exclude passwords#
# This just features that will likely be universal rejections
#
# Returns 
#   TRUE if the password is valid
#   FALSE if invalid
# 
def check_valid(input_password):

    # Don't accept blank passwords for training.
    if len(input_password) == 0:
        return False
         
    # Remove tabs from the training data
    # This is important since when the grammar is saved to disk tabs are used 
    # as seperators. There certainly are other approaches but putting this 
    # placeholder here for now since tabs are unlikely to be used in passwords
    if "\t" in input_password:
        return False
        
    # Below are other values that cause problems that we are going to remove.
    # These values include things like LineFeed LF
    
    #Invalid characters at the begining of the ASCII table
    for invalid_hex in range (0x0,0x20):
        if chr(invalid_hex) in input_password:
            return False
            
    # UTF-8 Line Seperator
    if u"\u2028" in input_password:
        return False
        
    return True
        

## Reads input passwords from file, one by one
#
# Making this a class so it can return one password at a time from the 
# training file
#
class TrainerFileInput:


    ## Open the file for reading
    #
    # Passes file exceptions back up if they occur
    # Eg: if the file doesn't exist
    #
    def __init__(self, filename, encoding = 'utf-8'):
        
        # Using surrogateescape to handle errors so we can detect encoding 
        # issues without raising an exception during the reading 
        # of the original password
        #
        self.encoding = encoding
        self.filename = filename
        self.file = codecs.open(
            self.filename, 
            'r', 
            encoding= self.encoding, 
            errors= 'surrogateescape'
        )

        # Keep track of the number of encoding errors
        self.num_encoding_errors = 0    
        
        # Keep track of the number of valid passwords that have been parsed
        self.num_passwords = 0
        
        # Duplicate password detection
        #
        # Duplicates are good. If this doesn't see duplicate passwords warn the
        # user.
        self.duplicates_found = False
        
        # Mini dictionary of the first X passwords to look for duplicates
        self.duplicate_detection = {}
        
        # Number of passwords to read in to check for duplicates
        self.num_to_look_for_duplicates = 100000
        
        
    ## Returns one password from the training set
    #
    # If there are no more passwords returns None
    #   
    def read_password(self):
        
        # Read an input password from the training set        
        try:
            # Loop until we find a valid password
            while True:
                try:
                    password = self.file.readline()
                
                # Unicode errors will throw an exception here, so catch it
                # and skip the password
                except UnicodeError as msg:
                    self.num_encoding_errors += 1
                    continue
            
                # Check to see if the file is done
                if password == "":
                    # Close file and return None
                    self.file.close()
                    return None
                    
                ## Check the encoding of the file
                #
                # Re-encode it and detect surrogates, this way we can 
                # identify encoding errors.
                #
                # I know, could simplify by throwing an exception during 
                # the original parsing and not use surrogate escapes, but this 
                # has helped with troubleshooting in the past
                #
                try:
                    password.encode(self.encoding)
                except UnicodeEncodeError as e:
                    if e.reason == 'surrogates not allowed':
                        self.num_encoding_errors += 1
                    else:
                        #print("Hmm, there was a weird problem reading in a line from the training file")
                        #print("")
                        self.num_encoding_errors += 1
                    continue
                
                # Remove newlines but leave whitespace
                clean_password = password.rstrip('\r\n')
      
                # Checks to see if the password is valid
                if not check_valid(clean_password):
                    continue
                
                ## This is a valid password
                self.num_passwords += 1
                
                # Perform duplicate check if needed
                if not self.duplicates_found:
                    if self.num_passwords < self.num_to_look_for_duplicates:
                        # It is a duplicate!!
                        if clean_password in self.duplicate_detection:
                            self.duplicates_found = True
                            # clean up duplicate_detection dic since we do
                            # not need it anymore
                            self.duplicate_detection.clear()
                        
                        # Not a duplicate
                        self.duplicate_detection[clean_password] = 1
                
                # Return the password   
                return clean_password
        
        # File errors *shouldn't* happen but if they do raise them to make 
        # sure they don't silently halt the training
        #
        # Aka we want the training to stop and the user to know something 
        # went wrong
        #        
        except IOError as error:
            print (error)
            print ("Error reading file " + self.filename)
            raise