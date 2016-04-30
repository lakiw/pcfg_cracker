#!/usr/bin/env python3

#########################################################################
# Contains all the file IO for the python pcfg trainer
#
# Note, this file contains a lot of grammar specific info as it has_key
# to know how to save the grammar to disk
#
#########################################################################

import os
import errno
import codecs

##--User Defined Imports---##
from pcfg_trainer.ret_types import RetType

##############################################################################
# Create a directory if one does not already exist
##############################################################################
def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


##############################################################################
# Creates all the directories needed to save a file
##############################################################################
def make_rule_dirs(directory_listing):
    try:
        for path in directory_listing:
            make_sure_path_exists(path)
    except OSError:
        print("Error creating the directories to save the results")
        print(str(error))
        return RetType.FILE_IO_ERROR
    return RetType.STATUS_OK
    
        
##############################################################################
# Writes the config file for the ruleset
##############################################################################        
def write_config(directory_name, config):
    try:
        with open(os.path.join(directory_name,"config.ini"), 'w') as configfile:
            config.write(configfile)
    except IOError as error:
        print (error)
        print ("Error opening file " + os.path.join(directory_name,"config.ini"))
        return RetType.FILE_IO_ERROR
    return RetType.STATUS_OK


#########################################################################################
# Reads in all of the passwords and returns the raw passwords, (minus any POT formatting
# to master_password_list
# Format of the raw passwords is (password,"DATA" or "COMMENT")
# I wanted to pass my comments through to the main program to make displaying results of
# unit tests easier
#########################################################################################
def read_input_passwords(training_file, is_pot, master_password_list, file_encoding = 'utf-8'):
    ##--keep track of the return value. If there are any Commnents return RetType.DEBUG vs RetType.STATUS_OK
    ret_value = RetType.STATUS_OK
    ##-- First try to open the file--##
    try:
        with codecs.open(training_file, 'r', encoding=file_encoding, errors= 'surrogateescape') as file:
            
            num_encoding_errors = 0  ##The number of encoding errors encountered when parsing the input file
            
            # Read though all the passwords
            for password in file:
                ##--Note, there is a large potential for encoding errors to slip in
                ##--   I don't want to silently ignore these errors, but instead warn the user they are
                ##--   occuring so they can look at what file encoding they are using again
                try:
                    password.encode(file_encoding)
                except UnicodeEncodeError as e:
                    if e.reason == 'surrogates not allowed':
                        num_encoding_errors = num_encoding_errors + 1
                    else:
                        print("Hmm, there was a weird problem reading in a line from the training file")
                        print()
                    continue
      
                ##--If it is a JtR POT file
                if is_pot:
                    #- I'm starting password values of # as comments for my unit tests, so ignore them
                    if (len(password) > 0) and (password[0] != '#'):
                        #-I'm going to assume that the first ':' is the deliminator. I know, it could fail if that
                        #-value shows up in the hash, but that should be rare enough not to throw off the
                        #-statistical results of the final grammar
                        master_password_list.append((password[password.find(':')+1:].rstrip(),"DATA"))
                    elif len(password) > 0:
                        ret_value = RetType.DEBUG
                        master_password_list.append((password.rstrip(),"COMMENT"))
                ##--Really simple, just append the password if it is a flat file
                else:
                    master_password_list.append((password.rstrip(),"DATA"))

            if num_encoding_errors != 0:
                print()
                print("WARNING: One or more passwords in the training set did not decode properly")
                print("         Number of encoding errors encountered: " + str(num_encoding_errors))
                print("         Ignoring passwords that contained encoding errors so it does not skew the grammar")
                print("         If you see a lot of these errors then you may want to re-run the training")
                print("         with a different file encoding")
                    
    except IOError as error:
        print (error)
        print ("Error opening file " + training_file)
        return RetType.FILE_IO_ERROR
    
    return ret_value

###################################################################################
# Read the first 100 entries and determine if it is a JTR pot or a plain wordlist
# There's no sophisticated approach. I'm just looking to see if it is a combination
# of user_id : password
###################################################################################
def is_jtr_pot(training_file, num_to_test, verbose = False, file_encoding = 'utf-8'):
    
    ##-- First try to open the file--##
    try:
        with codecs.open(training_file, 'r', encoding=file_encoding, errors = 'replace') as file:
            if verbose == True:
                print ("Starting to parse the training password file")   
            # Only check the first NUM_TO_TEST entries to verify if it is a POT file or not
            for x in range(0,num_to_test):
                #Get the next password
                password = file.readline()
                #Check to make sure there isn't an issue with too few training passwords
                if len(password) == 0:
                    print ("Sorry, the training file needs to have at least " + str(num_to_test) + " passwords")
                    print ("The training program was only able to parse " + str(x) + " passwords")
                    return RetType.NOT_ENOUGH_TRAINING_PASSWORDS
                #Strips off newline characters
                password = password.rstrip()
                
                #Checks for the characteristic ":" in POT files. If it's not there it's probably not a POT file
                #Side note, the JtR term of "POT" file comes from the fact that JtR is based on the original
                #"Cracker Jack" program. Therefore it was Jack POT ;p
                #Ignorning blank lines and lines that start with # due to my unit test files containing them for comments
                if (len(password)>1) and (password[0] != '#'):
                    if password.find(":") == -1:
                        print("Treating input file as a flat password file")
                        print()
                        return RetType.IS_FALSE
        # It looks a lot like a POT file
        print("Treating input file as a John the Ripper POT file")
        print("!!!! Warning, the generated grammars are much less effective if duplicate passwords are not included in the training set")
        print("!!!! Reading passwords directly form POT files was added more for testing and development purposes")
        print("!!!! If possible it will likely be better to train on the output from JtR's '-show' command")
        print()
        return RetType.IS_TRUE
    ##--An error occured trying ot open the file--##
    except IOError as error:
        print ("Error opening file " + training_file)
        print ("Error is " + str(error))
        return RetType.FILE_IO_ERROR
    ##--An error occured when trying to read the individual passwords (encoding error) --#
    except UnicodeError as error:
        print ("Error decoding file, unable to recover, aborting")
        print ("It is recommended to try a different file encoding to train on this dataset")
        return RetType.ENCODING_ERROR
    ##--Almost always caused by the user entering an invalid encoding type in the command line
    except LookupError as error:
        print("Error, the file encoding specified on the command line was not valid, exiting")
        print(str(error)) 
        return RetType.ENCODING_ERROR
        
    return RetType.IS_TRUE
    
    
#################################################################################################
# Used for autodetecting file encoding of the training password set
# Requires the python package chardet to be installed
# pip install chardet
# You can also get it from https://github.com/chardet/chardet
# I'm keeping the declarations for the chardet package local to this file so people can run this
# tool without installing it if they don't want to use this feature
##################################################################################################
def detect_file_encoding(training_file, file_encoding, max_passwords = 10000):
    print()
    print("Attempting to autodetect file encoding of the training passwords")
    print("-----------------------------------------------------------------")

    ##--Try to import chardet. If that package is not installed print out a warning and use the default ascii--##
    try:
        from chardet.universaldetector import UniversalDetector
        detector = UniversalDetector()
    except ImportError as error:
        print("FAILED: chardet not insalled")
        print("IT IS HIGHLY RECOMMENDED THAT YOU INSTALL THE chardet PACKAGE")
        print("or manually specify the file encoding of the training set via the command line")
        print("You can download chardet from https://pypi.python.org/pypi/chardet")
        print("Defaulting as ascii")
        file_encoding.append('ascii')
        return RetType.STATUS_OK
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
        return RetType.FILE_IO_ERROR
        
    try:
        file_encoding.append(detector.result['encoding'])
        print("File Encoding Detected: " + str(detector.result['encoding']))
        print("Confidence for file encoding: " + str(detector.result['confidence']))
        print("If you think another file encoding might have been used please manually specify the file encoding and run the training program again")
        print()
    except KeyError as error:
        print("Error encountered with file encoding autodetection")
        print("Error : " + str(error))
        return RetType.ENCODING_ERROR

    return RetType.STATUS_OK
