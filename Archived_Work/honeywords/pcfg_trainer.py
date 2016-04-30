#!/usr/bin/python

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
	
	def __cmp__(self,input):
		return cmp(self.value,input.value)

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
		self.totalSize=0

		##Init Base Structures
		self.baseStructure=[]
		self.baseSize=0
		
		##Init Digits
		self.digitStructure=[]
		self.digitSize=[]
		for i in range(MAXLENGTH+1):
			self.digitSize.append(0)
			self.digitStructure.append([])

		##Init Special
		self.specialStructure=[]
		self.specialSize=[]
		for i in range(MAXLENGTH+1):
			self.specialSize.append(0)
			self.specialStructure.append([])

		##Init Capitalization
		self.capStructure=[]
		self.capSize=[]
		for i in range(MAXLENGTH+1):
			self.capSize.append(0)
			self.capStructure.append([])

		##Init Keyboard
		self.keyboardStructure=[]
		self.keyboardSize=0

		##Init Replacement
		self.replaceStructure=[]
		self.replaceSize=0

		##Init Context Sensitive Values
		self.contextStructure=[]
		self.contextSize=0
	
	###########################################################################
	# Save command line values
	###########################################################################
	def commandLine(self,baseType):
		#Save the base structure storage type
		#0 is old style base structure storage of LLLLLDDDS
		#1 is new style base structure storage of L5D3S1
		self.baseType=baseType
		


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
def parseCommandLine(ruleName,trainingFile, x):
        parser = argparse.ArgumentParser(description='Generates PCFG Grammar From Password Training Set')
        parser.add_argument('--output','-o', help='Name of generated ruleset. Default is \"Default\"',metavar='RULESET_NAME',required=False,default="Default")
	parser.add_argument('--training','-t', help='The training set of passwords to train from',metavar='TRAINING_SET',required=True)

        args=vars(parser.parse_args())
        ruleName.append(args['output'])
        trainingFile.append(args['training'])

	x.commandLine(0)

        return 0


###############################################################################
# Removes "invalid" passwords
# Invalid in this case means you don't want to train on them
# Returns TRUE if the password is valid
#
# TODO: Add more reject functions to the command line and pass them here
###############################################################################
def validPass(password):

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
def findRowValue(char):
	#Yeah I'm leavinging off '`' but who really uses that in a keyboard combo, and it makes the code cleaner
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
def isNextOnKeyboard(past,current):
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
def interestingKeyboard(combo):

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
		#print str(combo) + " " + str(len(combo))
		return True
	return False


##########################################################################################
# Identifies keyboard patterns
# Note, will only classify something as a keyboard pattern if it contains two or
# more classes of characters, since simple patterns like '123456' will be detected by the
# respective class trainers
##########################################################################################
def detectKeyboard(x,password,mask):
	i=0
	curRun=0
	past = (-2,-2)
	while i < (len(password)-1):
		pos = findRowValue(password[i])
		if isNextOnKeyboard(past,pos):
			curRun = curRun + 1
		else:
			if curRun >=4:
				if interestingKeyboard(password[i-curRun:i]):
					x.keyboardSize = x.keyboardSize + 1
                                	insertList(x.keyboardStructure, password[i-curRun:i]) 
					for y in range(i-curRun,i):
						mask[y]='K'
			curRun = 1
		past = pos
		i = i + 1

	if curRun >=4:
		if interestingKeyboard(password[i-curRun:i]):
			x.keyboardSize = x.keyboardSize + 1
                	insertList(x.keyboardStructure, password[i-curRun:i])
			#print password + " " +str(mask) + " " + str(i)
			for y in range(i-curRun,i):
				mask[y]='K'
		
####################################################################################
# Finds the range of alpha characters given a random position inside them
####################################################################################
def findRange(password,i):
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
def detectReplacement(x,password,mask):
	i=0
	#Note a->4 had too high of a false positive rate, aka 'bob4jesus'
	validReplacements = [('i','1'),('l','1'),('e','3'),('t','7'),('a','@'),('s','$'),('s','5'),('o','0')]
	replaceSet = []
	while i < len(password):
		c = password[i]
		for j in validReplacements:
			if c == j[1]:
				if (i>0) and password[i-1].isalpha():
					if ((i+1)<len(password)) and password[i+1].isalpha():
						replaceSet.append((j,i))

		i = i + 1
	

	#Save the replacements
	insertedSet=[]
	for r in replaceSet:
		if not (r[0] in insertedSet):
			insertedSet.append(r[0])
			x.replaceSize = x.replaceSize + 1
			insertList(x.replaceStructure,str(r[0][0])+","+str(r[0][1]))
			
	
	#Now save the mask
	if (len(replaceSet)!=0):
		for r in replaceSet:
			replaceRange = findRange(password,r[1])
			hasUpper = False
			for j in range(replaceRange[0],replaceRange[1]+1):
				if password[j].isupper():
					hasUpper = True

			for j in range(replaceRange[0],replaceRange[1]+1):
				if hasUpper:
					mask[j]='R'
				else:
					mask[j]='r'


######################################################################################
# Find context sensitive replacements
# Note, we need to know what they are in the trainer
# It is not smart enough to find them on it's own yet
# TODO: Identify new context sensitive replacements based on the training data
######################################################################################
def detectContext(x,password,mask):
	searchValues=["<3",";p",":p","#1","*0*"]
	for i in searchValues:
		findValue = password.find(i)
		if findValue!=-1:
			for j in range(findValue,findValue+len(i)):
				mask[j]='X'
			x.contextSize = x.contextSize +1
			insertList(x.contextStructure,i,)	


######################################################################################
# Responsible for finding complex patterns like keyboard combos and letter repacements
#
# TODO: Add logic for conditional replacements for digit/special/alpha combos
######################################################################################
def normalizeBase(x,password):
	
	finalBase = []
	workingBase = list(password.rstrip())

	## Initialize the mask. This is applied after capitalization normalization occurs
	## Fully aware this can cause some weirdness if a U is part of a K.
	## For example 1qaZpassword would be KKKKUUUUUUUU when it really should be
	## KKKKLLLLLLLL
	## TODO: Find a better way to do this
	overlayMask = []
	for i in range(0,len(password)-1):
		overlayMask.append('.')

	## Detect letter replacements
	detectReplacement(x,password,overlayMask)

	## Detect context sensitive replacements
	detectContext(x,password,overlayMask)


	## Detect keyboard combinations
	detectKeyboard(x,password,overlayMask)


	## Normalize capitalization for alpha structures
	i=0
	while i < len(workingBase):
		if workingBase[i].isalpha():
			containsCap=False
			for y in range(i,len(workingBase)):
				if not workingBase[y].isalpha():
					break
				if workingBase[y].isupper():
					containsCap=True
					break
			workingMask=[]
			for y in range(i,len(workingBase)):
				if not workingBase[y].isalpha():
					break
				if containsCap:
					#WorkingMask is used to capture the exact "Capitalization Mask" that was used
					#Aka Password would be ULLLLLLL
					if workingBase[y].isupper():
						workingMask.append("U")
					else:
						workingMask.append("L")
					workingBase[y]='C'
						
				else:
					workingBase[y]='L'
				i = i + 1

			#Save the Capitalization Mask
			if containsCap:
				size = len(workingMask)
				x.capSize[size] = x.capSize[size] + 1
				insertList(x.capStructure[size], workingMask)

		i = i + 1
	
	#Apply mask from previous transforms
	pos = 0
	for i in overlayMask:
		if i != '.':
			workingBase[pos]=i
		pos = pos + 1
	
	finalBase = workingBase
	return finalBase

#############################################################################
# Inserts value into a sorted list if it does not exist
# Otherwise increments the counter by one
# Made this generic since I was doing it a lot
#############################################################################
def insertList (sortedList, insertValue):
        valueHolder = DataHolder("".join(insertValue))
        index = find(sortedList , valueHolder)
        if index != -1:
        	sortedList[index].inc()
        else:
        	bisect.insort(sortedList,valueHolder)


##############################################################################
# Responsible for parsing the base structures
# Will call the other parsing functions. Doing it this way so I can add
# more complex logic, like letter replacements later
##############################################################################
def parseBase(x, password):
	
	# Check for complex transforms like letter replacements and keyboard combos
	# Also extract the "Case Mangling" masks since that's a good a time as any to do that
	finalBase = normalizeBase(x,password)

	# Next, extract the digit structures
	count = 0
	while count < len(finalBase):
		#Start processing this particular digit
		if finalBase[count].isdigit():
			workingDigit=[]
			while count < len(finalBase):
				if not finalBase[count].isdigit():
					break
				workingDigit.append(finalBase[count])
				count = count + 1
			#Save that digit
			size = len(workingDigit)
			x.digitSize[size] = x.digitSize[size]+1
			insertList(x.digitStructure[size],workingDigit)

		count = count + 1

	# Next, extract the special structures
	count = 0
	while count < len(finalBase):
		#Start processing this particular special string
		if not finalBase[count].isalnum():
			workingSpecial=[]
			while count < len(finalBase):
				if finalBase[count].isalnum():
					break
				workingSpecial.append(finalBase[count])
				count = count + 1
			#Save that special string
			size = len(workingSpecial)
			x.specialSize[size] = x.specialSize[size] + 1
			insertList(x.specialStructure[size],workingSpecial)

		count = count + 1

	# Now actually parese the base structure
	if x.baseType == 0:
		for i in range(0,len(finalBase)):
                	if finalBase[i].isdigit():
                        	finalBase[i]='D'
			elif not finalBase[i].isalnum():
				finalBase[i]='S'


	else:
		#TODO: add new base structure type
		print "Add this option"

	#Now insert the base structure into the main list
	x.baseSize = x.baseSize + 1
	insertList(x.baseStructure, finalBase)

	

##############################################################################
# Calculate probabilities for a list
# Also sorts the list
##############################################################################
def calcProb(inputList, size):
	# First calculate the probability for each item
	for value in inputList:
		value.prob = (1.0 * value.num) / size

	# Now sort the list
	inputList.sort(key=operator.attrgetter('num'), reverse=True)

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
def make_rule_dirs(ruleName):
	make_sure_path_exists('./Rules/'+ruleName+'/Grammar')
	make_sure_path_exists('./Rules/'+ruleName+'/Digits')
	make_sure_path_exists('./Rules/'+ruleName+'/Capitalization')
	make_sure_path_exists('./Rules/'+ruleName+'/Keyboard')
	make_sure_path_exists('./Rules/'+ruleName+'/Special')
	make_sure_path_exists('./Rules/'+ruleName+'/Replace')
	make_sure_path_exists('./Rules/'+ruleName+'/Context')


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
def save_results(ruleName,x):
	# First create the directory structure
	print "Finished calculating probabilities. Saving results"
        make_rule_dirs(ruleName)

	#Now save the results
	baseDir = "./Rules/"+ruleName

	#Save grammar
	save_to_file(baseDir+"/Grammar/Grammar.txt", x.baseStructure)

	#Save capitalization
	for i in range(1,MAXLENGTH):
		save_to_file(baseDir+"/Capitalization/"+str(i)+".txt", x.capStructure[i])

	#Save digits
	for i in range(1,MAXLENGTH):
                save_to_file(baseDir+"/Digits/"+str(i)+".txt", x.digitStructure[i])

	#Save special
	for i in range(1,MAXLENGTH):
                save_to_file(baseDir+"/Special/"+str(i)+".txt", x.specialStructure[i])

	#Save keyboard
	save_to_file(baseDir+"/Keyboard/1.txt", x.keyboardStructure)

	#Save replacements
	save_to_file(baseDir+"/Replace/1.txt", x.replaceStructure)

	#Save context sentivite replacements
	save_to_file(baseDir+"/Context/1.txt", x.contextStructure)

###############################################################################
# Build the grammar from the training file
# Aka figures out all the Base Structures, D Structures, S Structures, etc.
###############################################################################
def buildGrammar(trainingFile,x):
	file = open(trainingFile[0], 'r')
	
	# Extract all the replacements from the training set
	print "Starting to parse the training password file"
	for password in file:
		
		## Added a reject function to remove "invalid" passwords nativly
		## Invalid in this case means you don't want to train on them
		if validPass(password):
			x.totalSize=x.totalSize+1
			parseBase(x,password)
		if (x.totalSize % 100000) == 0:
			print "Processed " + str(x.totalSize) + " passwords so far"


	# Calculate probabilities
	print "Done parsing the training file. Now calculating probabilities."
	for i in range(1,MAXLENGTH+1):
		calcProb(x.specialStructure[i],x.specialSize[i])

	for i in range(1,MAXLENGTH+1):
                calcProb(x.digitStructure[i],x.digitSize[i])

	for i in range(1,MAXLENGTH+1):
                calcProb(x.capStructure[i],x.capSize[i])

	calcProb(x.baseStructure, x.baseSize)
	
	calcProb(x.keyboardStructure, x.keyboardSize)

	calcProb(x.replaceStructure, x.replaceSize)

	calcProb(x.contextStructure, x.contextSize)


	#for i in range(0,MAXLENGTH):
	#	print "LENGTH " + str(i)
	#	for y in range(0,len(x.digitStructure[i])):
	#		print x.digitStructure[i][y].value + " " +str(x.digitStructure[i][y].num) + " " + str(x.digitStructure[i][y].prob)
	#	print x.digitSize[i]	
	return 0




###################################################################################
# Read the first 1000 entries and determine if it is a JTR pot or a plain wordlist
###################################################################################
def isJTRPot(trainingFile):
	return 0


def main():
        ruleName=[]
        trainingFile=[]
	x=TrainingData()

        parseCommandLine(ruleName,trainingFile,x)

	potType = isJTRPot(trainingFile)
	
	buildGrammar(trainingFile,x)

	# Save the results
	save_results(ruleName[0],x)


if __name__ == "__main__":
        main()
