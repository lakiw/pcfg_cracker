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
def make_rule_dirs(rule_name):
    try:
        make_sure_path_exists('./Rules/'+rule_name+'/Grammar')
        make_sure_path_exists('./Rules/'+rule_name+'/Digits')
        make_sure_path_exists('./Rules/'+rule_name+'/Capitalization')
        make_sure_path_exists('./Rules/'+rule_name+'/Keyboard')
        make_sure_path_exists('./Rules/'+rule_name+'/Special')
        make_sure_path_exists('./Rules/'+rule_name+'/Replace')
        make_sure_path_exists('./Rules/'+rule_name+'/Context')
    except OSError:
        print("Error creating the directories to save the results")
        print(str(error))
        return RetType.FILE_IO_ERROR
    return RetType.STATUS_OK


#############################################################################
# Saves the results that go into a single file
#############################################################################
def save_to_file(filename,data):
    if len(data)>0:
        file = open(filename, "w")
        for x in data:
            file.write(str(x.prob) + "\t" + x.value + "\n")
        file.close()

        
        
##############################################################################
# Generates and writes the config file for the ruleset
##############################################################################        
def write_config(base_dir):
    ##--Using configparser since I'm lazy-------##
    config = configparser.ConfigParser()
    ##--First write info about the training program used---###
    ##--This is me being optimistic that other people may eventaully write their own training programs---###
    config['TRAINING_PROGRAM_DETAILS'] = {'Program':'pcfg_trainer.py','Version': '1.0','Author':'Matt Weir','Contact':'cweir@vt.edu'}
    
    ##--Now write info about the training dataset---###
    ##--Yup, this will totally leak info about training sets people are using but since this tool is meant for academic uses
    ##--it is important for repeated tests and documentation to keep track of where these rule sets came from
    ##--TODO: Actually use the real data here vs some placeholders
    config['TRAINING_DATASET_DETAILS'] = {'Filename':'TestPasswords.pot', 'Number_of_passwords_in_set':1000,'Number_of_valid_passwords':1000,'Capital_letters_present':True,'Digits_present':True,'Special_chars_present':True,'Comments':'None'}
    
    ##--Finally write info about the actual grammar---###
    ##--This info is used by the pcfg_manager program to read in the grammar---###
    ##--This data will be changing a lot as I go through a couple of revisions and get a better handle how to read in arbitrary PCFG grammars---##
    
    #######################################################################################################
    ##--The first step is to read in the (S)tart transition
    ##--Currently useing the base structure
    #######################################################################################################
    config['START'] =  {}
    section_info = config['START']
    
    ##--Comments about the transition--##
    section_info['Name'] = 'Base Structure'
    section_info['Comments'] = 'Standard base structures as defined by the original PCFG Paper, with some renaming to prevent naming collisions. Examples are A4D2 from the training word "pass12"'
    
    ##--File info where it is saved--##
    section_info['Directory'] = 'Grammar'
    section_info['Filename'] = 'Grammar.txt'
    
    ##--Info on how to actually read in and apply the transition--##
    section_info['File_type'] = 'Grammar.txt'  ##Only one file vs 1.txt, 2.txt, 3.txt, etc.
    section_info['Inject_type'] = 'Base_Structure'  ##How the PCFG program should read in the data. Eventually want to make this more generic
    section_info['Function'] = 'Transparent' ##How the PCFG should treat this transition when invoking it
    section_info['Is_terminal'] = 'False'  ##If this is a terminal replacement
    
    ##--Info about the replacements---##
    ##--Format is an array of replacements, {Transition_id,Config_id}
    ##--Transition_id is the id from the transition file
    ##--Config_id is the id associated in THIS config file
    ##--There is a difference to avoid conflicts if two transition types have a name confict.
    ##--A good example is 'S' might represent 'Start' or "Special Character"
    
    ##--Key---
    # A = Alpha string, (commonly referred to as letters). Used to be categorized as 'L'
    # O = Other. Used to be refered to as Special character replacements, 'S'.
    # D = Digit replacement
    # K = Keyboard replacement
    # X = conteXt sensitive replacement (Grab-bag)
    replacements = [
        {'Transition_id':'A','Config_id':'BASE_A'},
        {'Transition_id':'O','Config_id':'BASE_O'},
        {'Transition_id':'D','Config_id':'BASE_D'},
        {'Transition_id':'K','Config_id':'BASE_K'},
        {'Transition_id':'X','Config_id':'BASE_X'},
        
    ]
    section_info['Replacements'] = str(replacements)
    
    #####################################################################################################
    ##---Now deal with the "Base_L" transition where L represents all lower case letter replacements of a base structure
    ######################################################################################################
    config['BASE_L'] =  {}
    section_info = config['BASE_L']
    
    ##--Comments about the transition--##
    section_info['Name'] = 'L'
    section_info['Comments'] = '(L)ower case letter replacement for base structure. Aka "pass12" = L4D2, so this is the L4'
    
    ##--File info where it is saved--##
    ##--Input dictionaries are currently used for this
    
    ##--Info on how to actually read in and apply the transition--##
    section_info['File_type'] = 'Length'  ##Replacements are broken up by length. Aka L1 = a, L2= aa, L3=aaa
    section_info['Inject_type'] = 'Wordlist'  ##How the PCFG program should read in the data. Eventually want to make this more generic
    section_info['Function'] = 'Copy' ##How the PCFG should treat this transition when invoking it
    section_info['Is_terminal'] = 'True'  ##If this is a terminal replacement
    
    
    #####################################################################################################
    ##---Now deal with the "Base_U" transition where U represents all UPPERCASE letter replacements of a base structure
    ######################################################################################################
    config['BASE_U'] =  {}
    section_info = config['BASE_U']
    
    ##--Comments about the transition--##
    section_info['Name'] = 'U'
    section_info['Comments'] = '(U)pper case letter replacement for base structure. Aka "PASS12" = U4D2, so this is the U4'
    
    ##--File info where it is saved--##
    ##--Input dictionaries are currently used for this
    
    ##--Info on how to actually read in and apply the transition--##
    section_info['File_type'] = 'Length'  ##Replacements are broken up by length. Aka L1 = a, L2= aa, L3=aaa
    section_info['Inject_type'] = 'Wordlist'  ##How the PCFG program should read in the data. Eventually want to make this more generic
    section_info['Function'] = 'Uppercase' ##How the PCFG should treat this transition when invoking it
    section_info['Is_terminal'] = 'True'  ##If this is a terminal replacement
            
    
    #####################################################################################################
    ##---Now deal with the "Base_M" transition where M represents all MiXeDCase letter replacements of a base structure
    ######################################################################################################
    config['BASE_M'] =  {}
    section_info = config['BASE_M']
    
    ##--Comments about the transition--##
    section_info['Name'] = 'M'
    section_info['Comments'] = '(M)ixedCase letter replacement for base structure. Aka "PaSs12" = M4D2, so this is the M4'
    
    ##--File info where it is saved--##
    ##--Input dictionaries are currently used for this
    
    ##--Info on how to actually read in and apply the transition--##
    section_info['File_type'] = 'Length'  ##Replacements are broken up by length. Aka L1 = a, L2= aa, L3=aaa
    section_info['Inject_type'] = 'Wordlist'  ##How the PCFG program should read in the data. Eventually want to make this more generic
    section_info['Function'] = 'Shadow' ##How the PCFG should treat this transition when invoking it
    section_info['Is_terminal'] = 'False'  ##If this is a terminal replacement
    
    ##--Info about the replacements---##
    ##--Format is an array of replacements, {Transition_id,Config_id}
    ##--Transition_id is the id from the transition file
    ##--Config_id is the id associated in THIS config file
    ##--There is a difference to avoid conflicts if two transition types have a name confict.
    ##--A good example is 'S' might represent 'Start' or "Special Character"
    replacements = [
        {'Transition_id':'Capitilization','Config_id':'CAPITILIZATION'},
    ]
    section_info['Replacements'] = str(replacements)    
    
    
    #####################################################################################################################
    ##---Now deal with the "Base_S" transition where S represents Special Character replacements of a base structure
    ######################################################################################################################
    config['BASE_S'] =  {}
    section_info = config['BASE_S']
    
    ##--Comments about the transition--##
    section_info['Name'] = 'S'
    section_info['Comments'] = '(S)pecial character replacement for base structure. Aka "pass$$" = L4S2, so this is the S2'
    
    ##--File info where it is saved--##
    section_info['Directory'] = 'Special'
    section_info['Filename'] = '*.txt'
    
    ##--Info on how to actually read in and apply the transition--##
    section_info['File_type'] = 'Length'  ##Replacements are broken up by length. Aka L1 = a, L2= aa, L3=aaa
    section_info['Inject_type'] = 'Standard_Copy'  ##How the PCFG program should read in the data. Eventually want to make this more generic
    section_info['Function'] = 'Copy' ##How the PCFG should treat this transition when invoking it
    section_info['Is_terminal'] = 'True'  ##If this is a terminal replacement
    
    #####################################################################################################
    ##---Now deal with the "Base_D" transition where D represents digit replacements of a base structure
    ######################################################################################################
    config['BASE_D'] =  {}
    section_info = config['BASE_D']
    
    ##--Comments about the transition--##
    section_info['Name'] = 'D'
    section_info['Comments'] = '(D)igit replacement for base structure. Aka "pass12" = L4D2, so this is the D2'
    
    ##--File info where it is saved--##
    section_info['Directory'] = 'Digits'
    section_info['Filename'] = '*.txt'
    
    ##--Info on how to actually read in and apply the transition--##
    section_info['File_type'] = 'Length'  ##Replacements are broken up by length. Aka L1 = a, L2= aa, L3=aaa
    section_info['Inject_type'] = 'Standard_Copy'  ##How the PCFG program should read in the data. Eventually want to make this more generic
    section_info['Function'] = 'Copy' ##How the PCFG should treat this transition when invoking it
    section_info['Is_terminal'] = 'True'  ##If this is a terminal replacement
    
    
    #####################################################################################################################
    ##---Now deal with the "K" transition where S represents Keyboard-Combinations replacements of a base structure
    ######################################################################################################################
    config['BASE_K'] =  {}
    section_info = config['BASE_K']
    
    ##--Comments about the transition--##
    section_info['Name'] = 'K'
    section_info['Comments'] = '(K)eyboard replacement for base structure. Aka "test1qaz2wsx" = L4K4K4, so this is the K4s'
    
    ##--File info where it is saved--##
    section_info['Directory'] = 'Keyboard'
    section_info['Filename'] = '*.txt'
    
    ##--Info on how to actually read in and apply the transition--##
    section_info['File_type'] = 'Length'  ##Replacements are broken up by length. Aka L1 = a, L2= aa, L3=aaa
    section_info['Inject_type'] = 'Standard_Copy'  ##How the PCFG program should read in the data. Eventually want to make this more generic
    section_info['Function'] = 'Copy' ##How the PCFG should treat this transition when invoking it
    section_info['Is_terminal'] = 'True'  ##If this is a terminal replacement
       
        
    #####################################################################################################################
    ##---Now deal with the "X" transition where X represents random conteXt sensitive replacements of a base structure such as #1 or :p
    ######################################################################################################################
    config['BASE_X'] =  {}
    section_info = config['BASE_X']
    
    ##--Comments about the transition--##
    section_info['Name'] = 'X'
    section_info['Comments'] = 'conte(X)t sensitive replacements to the base structure. This is mostly a grab bag of things like #1 or ;p'
    
    ##--File info where it is saved--##
    section_info['Directory'] = 'Context'
    section_info['Filename'] = '*.txt'
    
    ##--Info on how to actually read in and apply the transition--##
    section_info['File_type'] = 'Length'  ##Replacements are broken up by length. Aka L1 = a, L2= aa, L3=aaa
    section_info['Inject_type'] = 'Standard_Copy'  ##How the PCFG program should read in the data. Eventually want to make this more generic
    section_info['Function'] = 'Copy' ##How the PCFG should treat this transition when invoking it
    section_info['Is_terminal'] = 'True'  ##If this is a terminal replacement
    
    #####################################################################################################################
    ##---Now deal with the "X" transition where X represents random conteXt sensitive replacements of a base structure such as #1 or :p
    ######################################################################################################################
    config['CAPITILIZATION'] =  {}
    section_info = config['CAPITILIZATION']
    
    ##--Comments about the transition--##
    section_info['Name'] = 'Capitlization'
    section_info['Comments'] = 'Capitalization Masks for words. Aka LLLLUUUU for passWORD'
    
    ##--File info where it is saved--##
    section_info['Directory'] = 'Capitalization'
    section_info['Filename'] = '*.txt'
    
    ##--Info on how to actually read in and apply the transition--##
    section_info['File_type'] = 'Length'  ##Replacements are broken up by length. Aka L1 = a, L2= aa, L3=aaa
    section_info['Inject_type'] = 'Standard_Copy'  ##How the PCFG program should read in the data. Eventually want to make this more generic
    section_info['Function'] = 'Capitalize' ##How the PCFG should treat this transition when invoking it
    section_info['Is_terminal'] = 'True'  ##If this is a terminal replacement
    
    
    with open(base_dir + "/config.ini", 'w') as configfile:
        config.write(configfile)

    return True


    
##############################################################################
# Saves the results
##############################################################################
def save_results(rule_name,x):
    # First create the directory structure
    print ("Finished calculating probabilities. Saving results")
    make_rule_dirs(rule_name)

    #Now save the results
    base_dir = "./Rules/"+rule_name

    #Save the config file
    write_config(base_dir)
    
    #Save grammar
    save_to_file(base_dir+"/Grammar/Grammar.txt", x.base_structure)

    #Save capitalization
    for i in range(1,MAXLENGTH):
        save_to_file(base_dir+"/Capitalization/"+str(i)+".txt", x.cap_structure[i])

    #Save digits
    for i in range(1,MAXLENGTH):
        save_to_file(base_dir+"/Digits/"+str(i)+".txt", x.digit_structure[i])

    #Save special
    for i in range(1,MAXLENGTH):
        save_to_file(base_dir+"/Special/"+str(i)+".txt", x.special_structure[i])

    #Save keyboard
    save_to_file(base_dir+"/Keyboard/1.txt", x.keyboard_structure)

    #Save replacements
    save_to_file(base_dir+"/Replace/1.txt", x.replace_structure)

    #Save context sentivite replacements
    save_to_file(base_dir+"/Context/1.txt", x.context_structure)


#########################################################################################
# Reads in all of the passwords and returns the raw passwords, (minus any POT formatting
# to master_password_list
# Format of the raw passwords is (password,"DATA" or "COMMENT")
# I wanted to pass my comments through to the main program to make displaying results of
# unit tests easier
#########################################################################################
def read_input_passwords(training_file, is_pot, master_password_list, file_encoding = 'utf-8'):
    ##-- First try to open the file--##
    try:
        with codecs.open(training_file, 'r', encoding=file_encoding) as file:
            # Read though all the passwords
            try:
                for password in file:
                    ##--If it is a JtR POT file
                    if is_pot:
                        #- I'm starting password values of # as comments for my unit tests, so ignore them
                        if (len(password) > 0) and (password[0] != '#'):
                            #-I'm going to assume that the first ':' is the deliminator. I know, it could fail if that
                            #-value shows up in the username, but that should be rare enough not to throw off the
                            #-statistical results of the final grammar
                            master_password_list.append((password[password.find(':')+1:].rstrip(),"DATA"))
                        elif len(password) > 0:
                            master_password_list.append((password.rstrip(),"COMMENT"))
                    ##--Really simple, just append the password if it is a flat file
                    else:
                        master_password_list.append((password.rstrip(),"DATA"))
            except UnicodeDecodeError as error:
                print("Encountered invalid character while reading in training set, ignoring the problematic password")
                print("You may want to manually set the file encoding to something else and re-try training on this dataset")
                print(str(error))
                print()
    except IOError as error:
        print (error)
        print ("Error opening file " + training_file)
        return RetType.FILE_IO_ERROR
    
    return RetType.STATUS_OK

###################################################################################
# Read the first 100 entries and determine if it is a JTR pot or a plain wordlist
# There's no sophisticated approach. I'm just looking to see if it is a combination
# of user_id : password
###################################################################################
def is_jtr_pot(training_file, num_to_test, verbose = False, file_encoding = 'utf-8'):
    
    ##-- First try to open the file--##
    try:
        with codecs.open(training_file, 'r', encoding=file_encoding) as file:
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
                        print()
                        print("Treating input file as a flat password file")
                        print()
                        return RetType.IS_FALSE
        # It looks a lot like a POT file
        print()
        print("Treating input file as a John the Ripper POT file")
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
def detect_file_encoding(training_file, file_encoding):
    print()
    print("Attempting to autodetect file encoding of the training passwords")
    print("-----------------------------------------------------------------")
    from chardet.universaldetector import UniversalDetector
    detector = UniversalDetector()
    try:
        with open(training_file, 'rb') as file:
            for line in file.readlines():
                detector.feed(line)
                if detector.done: 
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