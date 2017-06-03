from .markov_cracker import MarkovCracker, MarkovIndex

class GuessIndex:
    def __init__(self,cur_dic, end_of_guess, markov_cracker = None):
        self.cur_dic = cur_dic
        self.function = cur_dic['function']
        self.top_index = 0
        self.running_index = 0
        self.markov_cracker = markov_cracker
        
        self.guess_pointer = end_of_guess 
          
          
    def reset(self, guess, new = False):
        self.top_index = 0
        self.running_index = 0
        
        ##--Copy = It is a direct copy of values. For example instert '123456'
        ##--Shadow = If you are copying over values that aren't terminals. For example L3=>['cat','hat']. They are not terminals since you still need to apply capitalization rules to them
        if self.function in ['Copy','Shadow']:
            #--If there are no replacements
            if not self.cur_dic['values']:
                return False
            
            value = self.cur_dic['values'][0]
            if new:
                guess.append(value)
            else:
                guess[self.guess_pointer] = value   
            
        ##----Capitalize the value passed in from the previous section----
        elif self.function == 'Capitalization':
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
        
        ##--Add Markov expansion. Currently using the same logic as JtR's --Markov Mode. Will print out all terminals
        ##--falling below the min prob rank and max prob rank
        elif self.function == 'Markov':
            
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
        
        
    def next(self, guess):
        
        ##--Copy = It is a direct copy of values. For example instert '123456'
        ##--Shadow = If you are copying over values that aren't terminals. For example L3=>['cat','hat']. They are not terminals since you still need to apply capitalization rules to them
        if self.function in ['Copy','Shadow']:
            self.top_index += 1
            #--If there are no replacements
            if self.top_index >= len(self.cur_dic['values']):
                return False
            
            value = self.cur_dic['values'][self.top_index]
            guess[self.guess_pointer] = value   
            
        ##----Capitalize the value passed in from the previous section----
        elif self.function == 'Capitalization':
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

        ##--Add Markov expansion. Currently using the same logic as JtR's --Markov Mode. Will print out all terminals
        ##--falling below the min prob rank and max prob rank
        elif self.function == 'Markov':
            
            value = self.markov_cracker.next_guess(self.markov_index)

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
            
#########################################################################################################
# Used to generate all the guesses for a given pre-terminal
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
    # Walks through all of the transistions and buidls out the list of terminals to use
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
    ######################################################################################################
    def get_first_guess(self):
        for item in self.structures: 
            if not item.reset(self.guess, new=True):
                return None
        
        return ''.join(self.guess)
    
    ###########################################################################################################
    # Returns the "next" guess
    ###########################################################################################################
    def get_next_guess(self):
        for index in range(len(self.structures)-1,-1, -1):
            if self.structures[index].next(self.guess):
                ##--Update everything after this
                for forward_index in range(index+1, len(self.structures)):
                    self.structures[forward_index].reset(self.guess, new=False)
                
                return ''.join(self.guess)
            
        return None