#!/usr/bin/env python3

#########################################################################################################
# Uses time memory trade off to speed up guess generation by caching previous results for
# filling out guesses for level + length + starting string combinations
##########################################################################################################


#########################################################################################################
# Creating this as a class so I can easily pass it around
#
# Contains all the logic to speed up guess generation by using tmto tricks
#########################################################################################################
class Optimizer:
    
    ############################################################################################
    # Initializes the optimizer
    # 
    # Input:
    # -max_length: The maximum length of strings to optimize. Increasing this increases memory requirements
    ############################################################################################
    def __init__(self, max_length):
        self.max_length = max_length
        
        ##--The grammar lookup--##
        ## Will be a list indexed on the length
        ## so length 1 will be at position 1
        ## dictionary lookups will be of the format
        ## {
        ##   'ip':{
        ##        'level': 'first result',
        ##        'level2': 'first result',
        ##        ...
        ##   },
        ##   'ip2':{
        ##        'level':'first result',
        ##   }
        ##   ...,
        ## }
        ##
        ## Example (assuming length = 4):
        ## {
        ##   'abc':{
        ##       '0':[[abc, 0],[bcd,0], [cde, 0], [def, 0]],
        ##       '5[[abc, 1],[bc1,1], [c12, 2], [123, 1]],
        ##   },
        ## }
        self.tmto_lookup = []
        for i in range(self.max_length + 1):
            self.tmto_lookup.append({})
        
    
    ##############################################################################################################
    # Look up a previous result
    #
    # Return Values
    # if_found, parse_tree
    # -if_found: True if a result was cahced, False if it was not
    # -parse_tree: The first parse tree to match the lookup criteria. None if no parse tree matches it
    ###############################################################################################################
    def lookup(self, ip, length, target_level):
        try:
            return True, self.custom_copy( self.tmto_lookup[length][ip][target_level] )
        except KeyError:
            return False, None
               
               
    #######################################################################################################
    # Updates the optimizer with a found result
    #######################################################################################################
    def update(self, ip, length, target_level, parse_tree):
        
        ##--If we haven't seen this ip for this length before
        if ip not in self.tmto_lookup[length]:
            self.tmto_lookup[length][ip] = {}
               
        self.tmto_lookup[length][ip][target_level] = self.custom_copy(parse_tree)
        
    
    #########################################################################################################
    # Because copy.deepcopy is overkill for what we want
    #########################################################################################################
    def custom_copy(self, input_list):
        if input_list:
            return [x[:] for x in input_list]
        return None
        