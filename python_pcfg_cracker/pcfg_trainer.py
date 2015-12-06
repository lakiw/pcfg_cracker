#!/usr/bin/env python3

import sys
import time
import argparse
import string
import bisect
from bisect import bisect_left
import operator
import os
import errno

MAXLENGTH=16

##########################################################################
# As the name implies, holds the data, the counts, and the probability of
# the different structures
##########################################################################
class DataHolder:
    def __init__(self,input):
        self.value = input
        self.num=1
        self.prob=0.0
    
    def __cmp__(self,other):
        return cmp(self.value,other.value)
    def __lt__(self, other):
        return self.value > other.value
    
    def __le__(self, other):
        return self.value >= other.value
        
    def __eq__(self, other):
        return self.value == other.value
        
    def __ne__(self, other):
        return self.value != other.value
        
    def __gt__(self, other):
        return self.value < other.value
        
    def __ge__(self, other):
        return self.value <= other.value

    def inc(self):
        self.num = self.num + 1


############################################################################
# Holds a lot of the various pieces of data, such as lists, comamand line
# arguments, and other values that I use a lot. Basicially it makes
# calling functions much easier
############################################################################
class TrainingData:
    def __init__(self):

        ##Init Random Record Keeping Values
        self.total_size=0

        ##Init Base Structures
        self.base_structure=[]
        self.base_size=0
        
        ##Init Digits
        self.digit_structure=[]
        self.digit_size=[]
        for i in range(MAXLENGTH+1):
            self.digit_size.append(0)
            self.digit_structure.append([])

        ##Init Special
        self.special_structure=[]
        self.special_size=[]
        for i in range(MAXLENGTH+1):
            self.special_size.append(0)
            self.special_structure.append([])

        ##Init Capitalization
        self.cap_structure=[]
        self.cap_size=[]
        for i in range(MAXLENGTH+1):
            self.cap_size.append(0)
            self.cap_structure.append([])

        ##Init Keyboard
        self.keyboard_structure=[]
        self.keyboard_size=0

        ##Init Replacement
        self.replace_structure=[]
        self.replace_size=0

        ##Init Context Sensitive Values
        self.context_structure=[]
        self.context_size=0
    
    ###########################################################################
    # Save command line values
    ###########################################################################
    def command_line(self,base_type):
        #Save the base structure storage type
        #0 is old style base structure storage of LLLLLDDDS
        #1 is new style base structure storage of L5D3S1
        self.base_type=base_type
        


#########################################################
# Basic find command for looking up value in ordered list
##########################################################
def find(a, x):
    'Locate the leftmost value exactly equal to x'
    i = bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return i
    return -1



####################################################
# Simply parses the command line
####################################################
def parse_command_line(rule_name,training_file, x):
    parser = argparse.ArgumentParser(description='Generates PCFG Grammar From Password Training Set')
    parser.add_argument('--output','-o', help='Name of generated ruleset. Default is \"Default\"',metavar='RULESET_NAME',required=False,default="Default")
    parser.add_argument('--training','-t', help='The training set of passwords to train from',metavar='TRAINING_SET',required=True)
    try:
        args=vars(parser.parse_args())
        rule_name.append(args['output'])
        training_file.append(args['training'])
    except:
        return False
    
    x.command_line(0)

    return True


###############################################################################
# Removes "invalid" passwords
# Invalid in this case means you don't want to train on them
# Returns TRUE if the password is valid
#
# TODO: Add more reject functions to the command line and pass them here
###############################################################################
def valid_pass(password):

    # Reject if too long
    if len(password) > (MAXLENGTH+1):
        return False

    # Remove e-mail addrsses since the PCFG doesn't handle them well
    # By that, the way the grammar is set up it's not smart enough to add '.com'
    # Instead it might add '!foo' or '$bar' since it replaces it context free
    # While a special case could be made for e-mails, it would only help when
    # attacking large sets of disclosed passwords, since in a targeted attack
    # you would be attacking a specific e-mail vs a randomly generated one.
    # I'm not that interested in the random large set attacks, so I'm just rejecting
    # e-mails from training. And that's the long reason why I'm rejecting e-mails.

    if ".com" in password:
        return False
    if ".org" in password:
        return False
    if ".edu" in password:
        return False
    if ".gov" in password:
        return False
    if ".mil" in password:
        return False


    return True

#########################################################################################
# Finds the row and pos of a value
#########################################################################################
def find_row_value(char):
    #Yeah I'm leaving off '`' but who really uses that in a keyboard combo, and it makes the code cleaner
    row1=['1','2','3','4','5','6','7','8','9','0','-','=']
    s_row1=['!','@','#','$','%','^','&','*','(',')','_','+']
    #leaving off '\|'
    row2=['q','w','e','r','t','y','u','i','o','p','[',']']
    s_row2=['Q','W','E','R','T','Y','U','I','O','P','{','}']

    row3=['a','s','d','f','g','h','j','k','l',';','\'']
    s_row3=['A','S','D','F','G','H','J','K','L',':','"']

    row4=['z','x','c','v','b','n','m',',','.','/']
    s_row4=['Z','X','C','V','B','N','M','<','>','?']

    if char in row1:
        return (1,row1.index(char))
        
    if char in s_row1:
        return (1,s_row1.index(char))

    if char in row2:
        return (2,row2.index(char))
        
    if char in s_row2:
        return (2,s_row2.index(char))

    if char in row3:
        return (3,row3.index(char))
        
    if char in s_row3:
        return (3,s_row3.index(char))

    if char in row4:
        return (4,row4.index(char))
                
    if char in s_row4:
        return (4,s_row4.index(char))

    #Default value for keys we don't check + non-ASCII chars
    return (-2,-2)

#########################################################################################
# Finds if a new key is next to the previous key
#########################################################################################
def is_next_on_keyboard(past,current):
    if (current[0] == past[0]):
        if (current[1] == past[1]) or (current[1] == past[1]-1) or (current[1] == past[1]+1):
            return True
    elif (current[0] == past[0]+1):
        if (current[1] == past[1]) or (current[1] == past[1]-1):
            return True
    elif (current[0] == past[0]-1):
        if (current[1] == past[1]) or (current[1] == past[1]+1):
            return True
    return False


###########################################################################################
# Currently only defining "interesting" keyboard combos as a combo that has
# multiple types of characters, aka alpha + digit
# Also added some sanity checks for common words that tend to look like keyboard combos
##########################################################################################
def interesting_keyboard(combo):

    #Remove "likely" partial words
    if (combo[0]== 'e') and (combo[1]== 'r'):
        return False
    
    if (combo[1]== 'e') and (combo[2]== 'r'):
        return False

    if (combo[0]=='t') and (combo[1]=='t') and (combo[2]=='y'):
        return False

    #TODO: Figure out why \ are being counted. This is a bug fix
    if (combo[1]=='\\'):
        return False
    if (combo[1]=='|'):
        return False
    if (combo[1]=='`'):
        return False
    if (combo[1]=='~'):
        return False

    #Check for complexity requirements
    alpha = 0
    special = 0
    digit = 0
    for c in combo:
        if c.isalpha():
            alpha=1
        elif c.isdigit():
            digit=1
        else:
            special=1
    if (alpha + special + digit) >=2:
        #print (str(combo) + " " + str(len(combo)))
        return True
    return False


##########################################################################################
# Identifies keyboard patterns
# Note, will only classify something as a keyboard pattern if it contains two or
# more classes of characters, since simple patterns like '123456' will be detected by the
# respective class trainers
##########################################################################################
def detect_keyboard(x,password,mask):
    i=0
    current_run=0
    past = (-2,-2)
    while i < (len(password)-1):
        pos = find_row_value(password[i])
        if is_next_on_keyboard(past,pos):
            current_run = current_run + 1
        else:
            if current_run >=4:
                if interesting_keyboard(password[i-current_run:i]):
                    x.keyboard_size = x.keyboard_size + 1
                    insert_list(x.keyboard_structure, password[i-current_run:i]) 
                    for y in range(i-current_run,i):
                        mask[y]='K'
            current_run = 1
        past = pos
        i = i + 1

    if current_run >=4:
        if interesting_keyboard(password[i-current_run:i]):
            x.keyboard_size = x.keyboard_size + 1
            insert_list(x.keyboard_structure, password[i-current_run:i])
            #print (password + " " +str(mask) + " " + str(i))
            for y in range(i-current_run,i):
                mask[y]='K'
        
####################################################################################
# Finds the range of alpha characters given a random position inside them
####################################################################################
def find_range(password,i):
    bottom=i
    top = i
    while (bottom > 0) and (password[bottom-1].isalpha()):
        bottom = bottom - 1

    while (top < len(password)) and (password[top+1].isalpha()):
        top = top + 1

    return (bottom,top)

#####################################################################################
# Identifies letter replacements
# Note, faily simplistic check. Could do a lot more when comparing against a real
# dictionary and using modified edit distance
# Currently assumes any replacement between two alpha chracters is valid
# TODO: Add more advanced logic to detect keyboard replacements
####################################################################################
def detect_replacement(x,password,mask):
    i=0
    #Note a->4 had too high of a false positive rate, aka 'bob4jesus'
    valid_replacements = [('i','1'),('l','1'),('e','3'),('t','7'),('a','@'),('s','$'),('s','5'),('o','0')]
    replace_set = []
    while i < len(password):
        c = password[i]
        for j in valid_replacements:
            if c == j[1]:
                if (i>0) and password[i-1].isalpha():
                    if ((i+1)<len(password)) and password[i+1].isalpha():
                        replace_set.append((j,i))

        i = i + 1
    

    #Save the replacements
    inserted_set=[]
    for r in replace_set:
        if not (r[0] in inserted_set):
            inserted_set.append(r[0])
            x.replace_size = x.replace_size + 1
            insert_list(x.replace_structure,str(r[0][0])+","+str(r[0][1]))
            
    
    #Now save the mask
    if (len(replace_set)!=0):
        for r in replace_set:
            replace_range = find_range(password,r[1])
            has_upper = False
            for j in range(replace_range[0],replace_range[1]+1):
                if password[j].isupper():
                    has_upper = True

            for j in range(replace_range[0],replace_range[1]+1):
                if has_upper:
                    mask[j]='R'
                else:
                    mask[j]='r'


######################################################################################
# Find context sensitive replacements
# Note, we need to know what they are in the trainer
# It is not smart enough to find them on its own yet
# TODO: Identify new context sensitive replacements based on the training data
######################################################################################
def detect_context(x,password,mask):
    searchValues=["<3",";p",":p","#1","*0*"]
    for i in searchValues:
        findValue = password.find(i)
        if findValue!=-1:
            for j in range(findValue,findValue+len(i)):
                mask[j]='X'
            x.context_size = x.context_size +1
            insert_list(x.context_structure,i,)   


######################################################################################
# Responsible for finding complex patterns like keyboard combos and letter repacements
#
# TODO: Add logic for conditional replacements for digit/special/alpha combos
######################################################################################
def normalize_base(x,password):
    
    final_base = []
    working_base = list(password.rstrip())

    ## Initialize the mask. This is applied after capitalization normalization occurs
    ## Fully aware this can cause some weirdness if a U is part of a K.
    ## For example 1qaZpassword would be KKKKUUUUUUUU when it really should be
    ## KKKKLLLLLLLL
    ## TODO: Find a better way to do this
    overlay_mask = []
    for i in range(0,len(password)-1):
        overlay_mask.append('.')

    ## Detect letter replacements
    detect_replacement(x,password,overlay_mask)

    ## Detect context sensitive replacements
    detect_context(x,password,overlay_mask)


    ## Detect keyboard combinations
    detect_keyboard(x,password,overlay_mask)


    ## Normalize capitalization for alpha structures
    i=0
    while i < len(working_base):
        if working_base[i].isalpha():
            contains_cap=False
            for y in range(i,len(working_base)):
                if not working_base[y].isalpha():
                    break
                if working_base[y].isupper():
                    contains_cap=True
                    break
            working_mask=[]
            for y in range(i,len(working_base)):
                if not working_base[y].isalpha():
                    break
                if contains_cap:
                    #WorkingMask is used to capture the exact "Capitalization Mask" that was used
                    #Aka Password would be ULLLLLLL
                    if working_base[y].isupper():
                        working_mask.append("U")
                    else:
                        working_mask.append("L")
                    working_base[y]='C'
                        
                else:
                    working_base[y]='L'
                i = i + 1

            #Save the Capitalization Mask
            if contains_cap:
                size = len(working_mask)
                x.cap_size[size] = x.cap_size[size] + 1
                insert_list(x.cap_structure[size], working_mask)

        i = i + 1
    
    #Apply mask from previous transforms
    pos = 0
    for i in overlay_mask:
        if i != '.':
            working_base[pos]=i
        pos = pos + 1
    
    final_base = working_base
    return final_base

#############################################################################
# Inserts value into a sorted list if it does not exist
# Otherwise increments the counter by one
# Made this generic since I was doing it a lot
#############################################################################
def insert_list (sorted_list, insert_value):
    value_holder = DataHolder("".join(insert_value))
    index = find(sorted_list , value_holder)
    if index != -1:
        sorted_list[index].inc()
    else:
        bisect.insort(sorted_list,value_holder)


##############################################################################
# Responsible for parsing the base structures
# Will call the other parsing functions. Doing it this way so I can add
# more complex logic, like letter replacements later
##############################################################################
def parse_base(x, password):
    
    # Check for complex transforms like letter replacements and keyboard combos
    # Also extract the "Case Mangling" masks since that's a good a time as any to do that
    final_base = normalize_base(x,password)

    # Next, extract the digit structures
    count = 0
    while count < len(final_base):
        #Start processing this particular digit
        if final_base[count].isdigit():
            working_digit=[]
            while count < len(final_base):
                if not final_base[count].isdigit():
                    break
                working_digit.append(final_base[count])
                count = count + 1
            #Save that digit
            size = len(working_digit)
            x.digit_size[size] = x.digit_size[size]+1
            insert_list(x.digit_structure[size],working_digit)

        count = count + 1

    # Next, extract the special structures
    count = 0
    while count < len(final_base):
        #Start processing this particular special string
        if not final_base[count].isalnum():
            working_special=[]
            while count < len(final_base):
                if final_base[count].isalnum():
                    break
                working_special.append(final_base[count])
                count = count + 1
            #Save that special string
            size = len(working_special)
            x.special_size[size] = x.special_size[size] + 1
            insert_list(x.special_structure[size],working_special)

        count = count + 1

    # Now actually parese the base structure
    if x.base_type == 0:
        for i in range(0,len(final_base)):
            if final_base[i].isdigit():
                final_base[i]='D'
            elif not final_base[i].isalnum():
                final_base[i]='S'


    else:
        #TODO: add new base structure type
        print ("Add this option")

    #Now insert the base structure into the main list
    x.base_size = x.base_size + 1
    insert_list(x.base_structure, final_base)

    

##############################################################################
# Calculate probabilities for a list
# Also sorts the list
##############################################################################
def calc_prob(input_list, size):
    # First calculate the probability for each item
    for value in input_list:
        value.prob = (1.0 * value.num) / size

    # Now sort the list
    input_list.sort(key=operator.attrgetter('num'), reverse=True)

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
    make_sure_path_exists('./Rules/'+rule_name+'/Grammar')
    make_sure_path_exists('./Rules/'+rule_name+'/Digits')
    make_sure_path_exists('./Rules/'+rule_name+'/Capitalization')
    make_sure_path_exists('./Rules/'+rule_name+'/Keyboard')
    make_sure_path_exists('./Rules/'+rule_name+'/Special')
    make_sure_path_exists('./Rules/'+rule_name+'/Replace')
    make_sure_path_exists('./Rules/'+rule_name+'/Context')


#############################################################################
# Saves the results that go into a single file
#############################################################################
def save_to_file(filename,data):
    if len(data)>0:
        file = open(filename, "w")
        for x in data:
            file.write(x.value + "\t" + str(x.prob) + "\n")
        file.close()

##############################################################################
# Saves the results
##############################################################################
def save_results(rule_name,x):
    # First create the directory structure
    print ("Finished calculating probabilities. Saving results")
    make_rule_dirs(rule_name)

    #Now save the results
    base_dir = "./Rules/"+rule_name

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

###############################################################################
# Build the grammar from the training file
# Aka figures out all the Base Structures, D Structures, S Structures, etc.
###############################################################################
def build_grammar(training_file,x):
    file = open(training_file[0], 'r')
    
    # Extract all the replacements from the training set
    print ("Starting to parse the training password file")
    for password in file:
        
        ## Added a reject function to remove "invalid" passwords nativly
        ## Invalid in this case means you don't want to train on them
        if valid_pass(password):
            x.total_size=x.total_size+1
            parse_base(x,password)
        if (x.total_size % 100) == 0:
            print ("Processed " + str(x.total_size) + " passwords so far")


    # Calculate probabilities
    print ("Done parsing the training file. Now calculating probabilities.")
    for i in range(1,MAXLENGTH+1):
        calc_prob(x.special_structure[i],x.special_size[i])

    for i in range(1,MAXLENGTH+1):
        calc_prob(x.digit_structure[i],x.digit_size[i])

    for i in range(1,MAXLENGTH+1):
        calc_prob(x.cap_structure[i],x.cap_size[i])

    calc_prob(x.base_structure, x.base_size)
    
    calc_prob(x.keyboard_structure, x.keyboard_size)

    calc_prob(x.replace_structure, x.replace_size)

    calc_prob(x.context_structure, x.context_size)


    #for i in range(0,MAXLENGTH):
    #   print ("LENGTH " + str(i))
    #   for y in range(0,len(x.digit_structure[i])):
    #       print (x.digit_structure[i][y].value + " " +str(x.digit_structure[i][y].num) + " " + str(x.digit_structure[i][y].prob))
    #   print (x.digit_size[i])    
    return 0




###################################################################################
# Read the first 1000 entries and determine if it is a JTR pot or a plain wordlist
# TODO: Actually impliment this
###################################################################################
def is_jtr_pot(training_file):
    return 0


def main():
    rule_name=[]
    training_file=[]
    x=TrainingData()

    if not parse_command_line(rule_name,training_file,x):
        return False

    pot_type = is_jtr_pot(training_file)
    
    build_grammar(training_file,x)

    # Save the results
    save_results(rule_name[0],x)


if __name__ == "__main__":
    main()
