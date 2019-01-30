######################################################################################
# Responsible for turning a pre-terminal into a series of guesses
# Uses a *next* function so it can be called repeatedly for each next guess
# I did this to get away from a "generate all the guesses and return them as a list"
# That approach worked great for a bit but as some of these pre-terminals can generate
# millions of guesses it started to break down
#######################################################################################

import random ##--Used for honeyword generation

from .markov_cracker import MarkovCracker, MarkovIndex


########################################################################################
# GuessIndex should only be created/manipulated by the GuessGeneration class
# Used to keep track of the individual replacements
# There are a *ton* of performance improvements that can be made here FYI
# For example, pretty much all of the "if/else" statements could be removed
#########################################################################################
class GuessIndex:
    def __init__(self,cur_dic, end_of_guess, markov_cracker = None):
        
        ## The pre-terminal section that this represents
        self.cur_dic = cur_dic
        
        ## The mangling rule being applied
        ## Yes this is also in self.cur_dic but seperating it out makes the code easier to read
        self.function = cur_dic['function']
        
        ## The current index into the replacements, for example for ['cat', 'hat', 'bat'] if 1, it means 'hat' is the current item
        self.top_index = 0
        
        ## Need to have a link to all the markov probabilities if this is a Markov repacement
        self.markov_cracker = markov_cracker  
        
        ## Where in the actual guess this mangling rule will be applied. Important since things like case mangling
        ## can occur on a previous dictionary word        
        self.guess_pointer = end_of_guess 
        
        ## Assign functions for the transform options here so we don't have to keep checking 'if' statements
        ##
        ## Reset is the function to call when reseting this GuessIndex
        ## function takes the form 
        ##     def reset(self, guess, new = False)
        ##
        ## Next is the function to call when generating the 'next' terminal for this GuessIndex
        ## function takes the form
        ##     def next(self, guess)
        if self.function in ['Copy','Shadow']:
            self.reset = self.__reset_copy_shadow
            self.next = self.__next_copy_shadow
        elif self.function == 'Capitalization':
            self.reset = self.__reset_capitalization
            self.next = self.__next_capitalization
        elif self.function == 'Markov':
            self.reset = self.__reset_markov
            self.next = self.__next_markov
        ##--This should not happen
        else:
            raise    

     
    ##================================================================================================================
    # The next several functions are assigned to self.reset() depending on what the transition rule is
    # General description of function's task:
    # Start this particular mangling rule from scratch
    # For example for ['cat', 'hat', 'bat'] go back and start from 'cat' again 
    # The 'new' variable is if this is being called the first time, (and needs to create all the datastructures)
    ##==================================================================================================================    
    
    #################################################################################################
    # Mini function that replaces the parent reset function
    # For [Copy, Shadow] transforms
    #################################################################################################
    def __reset_copy_shadow(self, guess, new = False):
        self.top_index = 0
        #--If there are no replacements
        if not self.cur_dic['values']:
            return False
        
        value = self.cur_dic['values'][0]
        if new:
            guess.append(value)
        else:
            guess[self.guess_pointer] = value
    
        return True
     
     
    #################################################################################################
    # Mini function that replaces the parent reset function
    # For [Capitalization] transforms
    #################################################################################################
    def __reset_capitalization(self, guess, new = False):
        self.top_index = 0
        
        #--If there are no replacements
        if not self.cur_dic['values']:
            return False
        
        rule = self.cur_dic['values'][0]            
        temp_string = []
        base_word = guess[self.guess_pointer]
        
        for letterPos in range(0,len(base_word)):
            if rule[letterPos]=='U':
                temp_string.append(base_word[letterPos].upper())
            else:
                temp_string.append(base_word[letterPos])
        
        guess[self.guess_pointer] = ''.join(temp_string)
        
        return True
        
    
    #################################################################################################
    # Mini function that replaces the parent reset function
    # For [Markov] transforms
    #################################################################################################
    def __reset_markov(self, guess, new = False):
        self.top_index = 0
        
        #--If there are no replacements
        if not self.cur_dic['values']:
            return False
        
        first_range = self.cur_dic['values'][0]
        levels = first_range.split(":")
        self.markov_index = MarkovIndex(min_level = int(levels[0]), max_level = int(levels[1]))
        value = self.markov_cracker.next_guess(self.markov_index)
        
        if new:
            guess.append(value)
        else:
            guess[self.guess_pointer] = value 
        
        return True
               
    
    ##================================================================================================================
    # The next several functions are assigned to self.next() depending on what the transition rule is
    # General description of function's task:
    # Modify the guess by the next mangling rule in the chain
    # Return True if there is a "next" guess
    # Return False if there is no more guesses to created/manipulated
    # 
    # For example for ['cat', 'hat', 'bat'], if the previous guess was 'cat', now create the guess 'hat'.
    ##==================================================================================================================    
    
    #################################################################################################
    # Mini function that replaces the parent reset function
    # For [Guess, Shadow] transforms
    # -Copy = It is a direct copy of values. For example instert '123456'
    # -Shadow = If you are copying over values that aren't terminals. For example L3=>['cat','hat']. 
    #  They are not terminals since you still need to apply capitalization rules to them
    #################################################################################################
    def __next_copy_shadow(self, guess):
        
        self.top_index += 1
        #--If there are no replacements
        if self.top_index >= len(self.cur_dic['values']):
            return False
        
        value = self.cur_dic['values'][self.top_index]
        guess[self.guess_pointer] = value   
        
        return True
            
            
    #################################################################################################
    # Mini function that replaces the parent reset function
    # For [Capitalization] transforms
    # -Capitalize the value passed in from the previous section----
    #################################################################################################
    def __next_capitalization(self, guess):
        
        self.top_index += 1
        #--If there are no replacements
        if self.top_index >= len(self.cur_dic['values']):
            return False
            
        rule = self.cur_dic['values'][self.top_index]            
        temp_string = []
        base_word = guess[self.guess_pointer]
        
        for letterPos in range(0,len(base_word)):
            if rule[letterPos]=='U':
                temp_string.append(base_word[letterPos].upper())
            else:
                temp_string.append(base_word[letterPos].lower())
        
        guess[self.guess_pointer] = ''.join(temp_string)       
        
        return True
            
            
    #################################################################################################
    # Mini function that replaces the parent reset function
    # For [Markov] transforms
    # -Add Markov expansion. Currently using the same logic as JtR's --Markov Mode. Will print out all terminals
    # -falling below the min prob rank and max prob rank
    #################################################################################################
    def __next_markov(self, guess):
        
        value = self.markov_cracker.next_guess(self.markov_index)

        ##--In case there are multiple Markov ranges with the same probability in this list--##
        ##--I don't expect this to happen. aka the first if statement will fail and return False
        ##--but I'm adding it in for future proofing in case I ever decide to do probability smoothing
        ##--on those Markov ranges
        while value == None:
            self.top_index += 1
            #--If there are no replacements
            if self.top_index >= len(self.cur_dic['values']):
                return False
    
            first_range = self.cur_dic['values'][0]
            levels = first_range.split(":")
            self.markov_index = MarkovIndex(min_level = int(levels[0]), max_level = int(levels[1]))
            value = self.markov_cracker.next_guess(self.markov_index)

        guess[self.guess_pointer] = value 
         
        return True

              
    ####################################################################################################
    # Returns a random guess for this particular terminal
    # Mostly used for honeyword generation
    #####################################################################################################
    def get_random(self, guess):
        
        ##--Copy = It is a direct copy of values. For example instert '123456'
        ##--Shadow = If you are copying over values that aren't terminals. For example L3=>['cat','hat']. They are not terminals since you still need to apply capitalization rules to them
        if self.function in ['Copy','Shadow']:
            try:    
                guess[self.guess_pointer] = random.choice(self.cur_dic['values'])
            
            ##--If the list is empty it will raise an exception--##
            except:            
                return False
            
        ##----Capitalize the value passed in from the previous section----
        elif self.function == 'Capitalization':
            try:    
                rule = random.choice(self.cur_dic['values'])
                
            ##--If the list is empty it will raise an exception--##
            except:            
                return False  
                          
            temp_string = []
            base_word = guess[self.guess_pointer]
            
            for letterPos in range(0,len(base_word)):
                if rule[letterPos]=='U':
                    temp_string.append(base_word[letterPos].upper())
                else:
                    temp_string.append(base_word[letterPos].lower())
            
            guess[self.guess_pointer] = ''.join(temp_string)

        ##--Add Markov expansion. Currently using the same logic as JtR's --Markov Mode. Will print out all terminals
        ##--falling below the min prob rank and max prob rank
        elif self.function == 'Markov':
            
            ##--If there are multiple Markov ranges then all of their values should be equal probability for this pre-terminal--##
            ##--Aka it doesn't matter which one we pick--##
            rule = random.choice(self.cur_dic['values'])
            
            levels = rule.split(":")
            
            ##--Note, try a "best effort" to quickly find a random guess that falls within the target Markov range
            ##--The probability of this guess might be less then the range specifies
            ##--for honeywords I figure that's good enough since there is not a fast index option for the current Markov
            ##--algorithm. Users might be annoyed if it takes two weeks to generate an accurate Markov guess vs one that is "close"
            guess[self.guess_pointer] =self.markov_cracker.get_random(min_level = levels[0], suggested_max_level = levels[1])
                
        return True
            
            
#########################################################################################################
# Used to generate all the guesses for a given pre-terminal
# The main function is the "next" function that returns the next guess
# It will return None when there are no more guesses to create
#########################################################################################################
class GuessGeneration:
    
    ############################################################################################
    # Initialize the session
    ############################################################################################
    def __init__(self, grammar, markov_cracker, pre_terminal):
        
        ##--guess is kept as a list so we can update individual parts
        self.guess = []
        
        ##--The structures that keeps track of all the items
        self.structures = []
        
        ##--The grammar this is built on
        self.grammar = grammar
        
        ##--The Markov grammar
        self.markov_cracker = markov_cracker
        
        ##--Initilaize the terminal structures
        self.__initialize(pre_terminal, 0)
                
    
    ##################################################################################################
    # Walks through all of the transistions and builds out the list of terminals to use
    # Basically sets up all of the data structures so it is ready to start creating guesses
    # This is a private function, no one else should call it
    ##################################################################################################    
    def __initialize(self,  cur_section, end_of_guess):
        cur_dic = self.grammar[cur_section[0]]['replacements'][cur_section[1]]
        
        ##---Potentially adding a new replacement. aka S->ABC. This is more of a traditional PCFG "non-terminal"
        if cur_dic['function']=='Transparent':
            for rule in cur_section[2]:
                self.__initialize(rule, end_of_guess)
                end_of_guess = self.structures[-1].guess_pointer +1  
        
        else:
            self.structures.append(GuessIndex(cur_dic, end_of_guess, self.markov_cracker))
            
            ##--Need to expand the Shadow rules so case manling is applied
            if cur_dic['function'] == 'Shadow':
                self.__initialize(cur_section[2][0], end_of_guess)
             
        
    ######################################################################################################
    # Returns the first guess
    # Seperating this out so that I don't have to check if it is the first guess every time I call the 
    # "get_next_guess" function
    ######################################################################################################
    def get_first_guess(self):
        for item in self.structures:
            try:
                if not item.reset(self.guess, new=True):
                    return None
            except:
                print(item)
                print(item.function)
                input("hit enter")
        return ''.join(self.guess)
    
    
    ###########################################################################################################
    # Returns the "next" guess
    # This and the get_first_guess are the core of this class
    # Returns None if there are no more guesses to generate
    ###########################################################################################################
    def get_next_guess(self):
        for index in range(len(self.structures)-1,-1, -1):
            if self.structures[index].next(self.guess):
                ##--Update everything after this
                for forward_index in range(index+1, len(self.structures)):
                    self.structures[forward_index].reset(self.guess, new=False)
                
                return ''.join(self.guess)
            
        return None
        
    
    ################################################################################################################
    # As the name implies, returns a *random* guess generated by the pre-terminal
    # I expect this mostly to be used in honeywords
    # Returns None if there are no possible guesses to generate
    ################################################################################################################
    def get_random_guess(self):
        ##--Initialize the guess with the first terminal--##
        ##--Yes it's added overhead since we just throw the guess away but it initializes the structure so it avoids having
        ##--to write additional code
        for item in self.structures: 
            item.reset(self.guess, new=True)
        
        ##--Now get a random guess
        for item in self.structures: 
            if not item.get_random(self.guess):
                return None
            
        return ''.join(self.guess)