import sys
import time
import argparse
import glob
import random
from random import randrange
import string

####################################################
# Simply parses the command line
####################################################
def parseCommandLine(ruleName,outputFile,numHoneyWords,wordlists):
	parser = argparse.ArgumentParser(description='Generate HoneyWords from Training Set')
	parser.add_argument('--rule', '-r', help='Training ruleset to use when generating honeywords',required=True) 
	parser.add_argument('--output','-o', help='Output filename to save honeywords',required=True)
	parser.add_argument('--num','-n', help='The number of honeywords to generate',required=True)
	parser.add_argument('--dname1','-dn1', help='The name of the main dictionary to use',required=True)
	parser.add_argument('--dprob1','-dp1', help='The probability of the main dictionary, default is 1.0',required=False,default=1.0)
	parser.add_argument('--dname2','-dn2', help='The name of a supplementary dictionary',required=False, default='')
	parser.add_argument('--dprob2','-dp2', help='The probability of a supplemenatry dictionary',required=False, default=0.0)

	args=vars(parser.parse_args())
	ruleName.append(args['rule'])
	outputFile.append(args['output'])
	numHoneyWords.append(args['num'])
	wordlists.append([args['dname1'],float(args['dprob1'])])
	if args['dname2']!='':
		wordlists.append([args['dname2'],float(args['dprob2'])])

	return 0


###################################################
# Reads the individual Pre-Termainal Files
###################################################
def readPT(filename,preTerminal):
	#topValue is the range the replacement takes up. So if the first replacement had a prob of 0.2, its range would be 1.0 to 0.8
	#if the next replacement had a prob of 0.1, its range would be 0.8 to 0.7.
	#Note, some of the complexity here was I originally was trying to optimize this along the lines of the cracker, and then
	#realized I really didn't need to. Aka I didn't need to combine replacments that had the same probability together
	topValue=1.0
	preValue=1.0
	file = open(filename, 'r')
	for x in file:
		line = x.split('\t')
		if len(preTerminal)==0:
			preTerminal.append([topValue,1-float(line[1]),line[0]])
			topValue=topValue-float(line[1])
			preValue=float(line[1])
		else:
			preTerminal.append([topValue,topValue-float(line[1]),line[0]])
			topValue=topValue-float(line[1])
			preValue=float(line[1])

	#There is usually a rounding issue, aka never adds up to exactly 1.0
	#Assigning it -1 since to avoid collisions the search checks that the number is greater than the lowerbound.
	#Aka, could have set it to be -0.0000000001, but -1 was easier
	preTerminal[-1][1]=-1
	return 0


######################################################
# Actually "reads" in the dictionary from file
# Also cleans up the dictionary words so they only contain
# lower-alpha characters, and removes duplicate words
######################################################
def readRawWordlists(fileInfo,rawList):

	file = open(fileInfo[0], 'r')
	rawList.append((0,[]))
	maxLength=0

	for origString in file:
		x=''
		#Lowercase the letter
		origString= origString.lower()
		#Strip digits and special characters
		origString= origString.rstrip()
		for y in origString:
                        if y.isalpha():
                                x+=y
		curLength=len(x)

		#If a longer word is found than the previous longest word
		if (curLength>maxLength) and (curLength!=0) and (x!=''):         
			#Create empty slots to fill in additional words later if needed for shorter than maxlength words
			for y in range(curLength-maxLength-1):
				rawList.append((y+maxLength+1,[]))
			rawList.append((curLength,[x]))
			maxLength=curLength
		else:
			rawList[curLength][1].append(x)

	return 0


######################################################
# Reads in the dictionary files
######################################################
def readWordlists(wordlists,dictionaryPT):
	
	#First, normalize the dictionary probability values
	preSum=0.0
	for x in wordlists:
		preSum+=float(x[1])
	for x in wordlists:
		x[1]=x[1]/preSum

	#Note, since I keep thinking about it, it doesn't matter what order the dictionaries are in
	#Since we don't care about probability order. Aka it doesn't matter if a less probable dictionary
	#is parsed "first"

	#Now read in the dictionary files
	rawList1=[]
	rawList2=[]
	if readRawWordlists(wordlists[0],rawList1)!=0:
		print "Problem reading dictionary file"
		return -1
	if len(wordlists)==2:
		if readRawWordlists(wordlists[1],rawList2)!=0:
                	print "Problem reading dictionary file"
                	return -1
	#Add it to the master wordlist
	#First find out the max length and add extra nodes to the shorter list
	if len(rawList1)>len(rawList2):
		maxLen =len(rawList1)
		for x in range(maxLen-len(rawList2)):
			rawList2.append((len(rawList2)+x+1,[]))
	else:
		maxLen =len(rawList2)
		for x in range(maxLen-len(rawList1)):
			rawList1.append((len(rawList1)+x+1,[]))

	#next add each length
	for x in range(maxLen):
		if (len(rawList1[x][1])!=0) and (len(rawList2[x][1])!=0):  #There is a node in both lists
			rawList1[x][1].insert(0,1.0)
			rawList1[x][1].insert(1,1.0-wordlists[0][1])

			rawList2[x][1].insert(0,1.0-wordlists[0][1])
			rawList2[x][1].insert(1,0.0)
			
			dictionaryPT.append((x,[rawList1[x][1],rawList2[x][1]]))

		elif (len(rawList1[x][1])!=0):   #The node only exists in the first list
			rawList1[x][1].insert(0,1.0)
			rawList1[x][1].insert(1,0.0)
			dictionaryPT.append((x,[rawList1[x][1]]))

		elif (len(rawList2[x][1])!=0):    #The node only exists in the second list
			rawList2[x][1].insert(0,0.0)
			rawList2[x][1].insert(1,0.0)
			dictionaryPT.append((x,[rawList2[x][1]]))

		else:  #The node doesn't exist
			dictionaryPT.append((x,[[]]))
	return 0


###########################################################
# Reads in the different length pre-terminal replacements
###########################################################
def readLenPT(ruleName,filename,preTerminal):
	#First get a list of all files in the directory, (ignorning NotFound.txt for now)
	files = glob.glob('Rules/'+ruleName[0]+filename+'[0-9]*.txt')

	#Next initialize the holding datastructure, [(len,[[top_prob,lower_prob,words],[top_prob,lower_prob,words]]),(len,[top_prob,lower_prob,words])]
	#To do this, we need to find the maximum length
	maxLength=0
	for x in files:
		tempString = x.split('/')
		curLength=int(tempString[-1].split('.')[0])
		if curLength>maxLength:
			maxLength = curLength

	#Now really initialize the datastructure
	#Yeah, there'll never be anything in 0, but it makes the logic easier later on
	for x in range(maxLength+1):
		preTerminal.append((x,[]))

	#Now read the file
	for x in files:
		tempString = x.split('/')
                curLength=int(tempString[-1].split('.')[0])
		if readPT(x,preTerminal[curLength][1])!=0:
			print "Error reading " + x
			return -1
	return 0


####################################################
# Reads in the PCFG Grammar
####################################################
def readGrammar(ruleName,basePT, specialPT, digitPT, capPT, keyboardPT):
	if (readPT('Rules/'+ruleName[0]+'/Grammar/Grammar.txt',basePT)!=0):
		print "Error reading in the grammar file"
		return -1
	if (readLenPT(ruleName,"/Special/",specialPT)!=0):
		print "Error reading in the special char files"
		return -1
	if (readLenPT(ruleName,"/Digits/",digitPT)!=0):
                print "Error reading in the digits char files"
                return -1
	if (readLenPT(ruleName,"/Capitalization/",capPT)!=0):
                print "Error reading in the capitaliztion char files"
                return -1
	if (readLenPT(ruleName,"/Keyboard/",keyboardPT)!=0):
                print "Error reading in the keyboard char files"
                return -1
	return 0



#########################################################
# Modified Binary Search
#########################################################
def binary_search(a, x, lo=0, hi=None):
	if hi is None:
		hi = len(a)
	while lo < hi:
		mid = (lo+hi)//2
		midval = a[mid]
		if midval[1] >= x:
			lo = mid+1
		elif midval[0] < x: 
			hi = mid
		else:
			return mid
	return -1

########################################################
# Finds a random replacement, is weighted by probability
########################################################
def findRandom(preTerminal):
	randValue = random.uniform(0.0,1.0)
	returnValue=binary_search(preTerminal,randValue)

	#Since there may be many preTerminals with the same probability
	if len(preTerminal[returnValue])!=3:
		randValue=randrange(0,len(preTerminal[returnValue])-2)
		return preTerminal[returnValue][randValue+2]

	#print str(preTerminal[returnValue][2]) + '\t' + str(preTerminal[returnValue][0] - preTerminal[returnValue][1])
	return preTerminal[returnValue][2]
	

##############################################################
# Breaks up the base structure into the individual components
##############################################################
def splitBase(preTerminal):
	returnValue=[]
	curChar=''
	curSize=0
	for x in preTerminal:
		if x==curChar:
			curSize=curSize+1
		else:
			if curChar!='':
				returnValue.append([curChar,curSize])
			curSize=1
			curChar=x
	returnValue.append([curChar,curSize])

	return returnValue


####################################################
# Applies a capitalization mask to a dictionary word
####################################################
def applyMask(word,mask):
	returnValue=''
	#print word + " " + mask
	for x in range(len(word)):
		if mask[x]=='L':
			returnValue+=word[x]
		else:
			returnValue+=word[x].upper()
	return returnValue

#################################################################
# Checks to see if word meets the complexity requirement
##################################################################
def checkComplexity(word):
	hasLower=0
	hasUpper=0
	hasSpecial=0
	hasDigit=0
	if len(word)<6:
		return False 
	for x in word:
		if x.isdigit():
			hasDigit=1
		if x.islower():
			hasLower=1
		if x.isupper():
			hasUpper=1
		if not x.isalnum():
			hasSpecial=1

	if (hasLower + hasUpper+ hasSpecial + hasDigit)>=3:
		return True
	return False

			

###################################################
# Main function to generate honeyords
###################################################
def createHoney(numHoneyWords,basePT,specialPT,digitPT,capPT,keyboardPT,dictionaryPT,honeyWords):
	for x in range(int(numHoneyWords[0])):
		valid_guess=0
		while valid_guess==0:
			valid_guess=1 #Assume the guess is valid unless some error condition is detected
			#first select the base structure
			baseValue = findRandom(basePT)
			while len(baseValue) > 32:
				baseValue = findRandom(basePT) 		
			
			#next break up the base structure
			parsedBase = splitBase(baseValue)
			newHoneyWord=''
			#Now apply the individual replacements
			for y in parsedBase:
				if y[0]=='L':
					#Need to handle the cases where there may not be an appropriately sized dictionary word in the input dictionary
					if y[1]>=len(dictionaryPT):
						valid_guess=0
						break
                                        if len(dictionaryPT[y[1]][1][0])<3:
                                                valid_guess=0
                                                break

					orig_word = findRandom(dictionaryPT[y[1]][1])
					if len(orig_word)==0:
						valid_guess=0
						break
					cap_mask = findRandom(capPT[y[1]][1])
					terminal = applyMask(orig_word,cap_mask)
					#terminal = "password"
				if y[0]=='D':
					#Since the training program has a limit on the max size digits and special chars to save
					if y[1]>=len(digitPT):
						valid_guess=0
						break
					terminal = findRandom(digitPT[y[1]][1])
				if y[0]=='S':
					if y[1]>=len(specialPT):
						valid_guess=0
						break
					terminal = findRandom(specialPT[y[1]][1])
				if y[0]=='K':
					#Keyboad ignores length requirements, weird but has been more effective in tests
					terminal = findRandom(keyboardPT[1][1])
				newHoneyWord+=terminal
			
			if not checkComplexity(newHoneyWord):
				valid_guess=0

		honeyWords.append(newHoneyWord)

	return 0

def main():
	print "starting"
	ruleName=[]
	outputFile=[]
	wordlists=[]
	numHoneyWords=[]
	
	#The diffrent Pre-Terminal replacements
	basePT=[]
	specialPT=[]
	digitPT=[]
	capPT=[]
	keyboardPT=[]
	dictionaryPT=[]

	#The final list of honeywords
	honeyWords=[]

	parseCommandLine(ruleName,outputFile,numHoneyWords,wordlists)
	if readGrammar(ruleName,basePT, specialPT, digitPT, capPT, keyboardPT)!=0:
		exit()
	if readWordlists(wordlists,dictionaryPT)!=0:
		exit()
	createHoney(numHoneyWords,basePT,specialPT,digitPT,capPT,keyboardPT,dictionaryPT,honeyWords)

	#Write the output
	file = open(outputFile[0], 'w')
	for x in honeyWords:
		file.write(x + '\n')
	print "Finished generating " + str(numHoneyWords) + " honeywords"	

if __name__ == "__main__":
        main()
