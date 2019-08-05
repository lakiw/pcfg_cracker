#!/usr/bin/env python3

#########################################################################################################
# Used to create and increment guesses for a particular length + IP + target level with OMEN
##########################################################################################################


import sys
import os 


#########################################################################################################
# Will attempt to create a guess for a particular length + IP + target level
# Based on OMEN
#
# Seperating this out to clean up the markov_cracker code
#########################################################################################################
class GuessStructure:
    
    ############################################################################################
    # Initializes the guess structure
    # If no valid guess is available, set is_valid to False
    ############################################################################################
    def __init__(self, cp, max_level, ip, cp_length, target_level, optimizer):
        
        ##--If this is the first guess
        self.first_guess = True
        
        ##--The CP structures--##
        self.cp = cp
        
        ##--The maximum level an item can be--##
        self.max_level = max_level
        
        ##--The IP string to use
        self.ip = ip
        
        ##--The length of the IP to use
        self.ip_length = len(self.ip)
        
        ##--The number of cps to add after the IP
        self.cp_length = cp_length
        
        ##--The target level for this item
        self.target_level = target_level
        
        ##--Initialize the parse_tree
        self.parse_tree = []       

        ##--The optimizer
        self.optimizer = optimizer        
        
            
    ################################################################################################
    # Get the next guess for this guess structure
    # Returns None if no valid guess is left
    ################################################################################################
    def next_guess(self):
        ##--First Guess
        if not self.parse_tree:
            self.parse_tree = self._fill_out_parse_tree(self.ip,self.cp_length, self.target_level)
            if not self.parse_tree:
                return None

            return self._format_guess()
        
        ##--Every guess after the first guess
        
        ##--Shortcut deal with the last item
        last_item = self.parse_tree[-1]
        if last_item[2] + 1 < len(self.cp[last_item[0]][last_item[1]]):
            self.parse_tree[-1][2] += 1
            return self._format_guess()
        
        ##--Pop the last element off
        element = self.parse_tree.pop()
        
        ##--Quick bail out since there is nothing else to increment, (the parse tree was only one cp long)
        if not self.parse_tree:
            return None
        
        ##--The number of CP we need to fill in after this depth
        req_length = 1
        
        ##--The number of levels we have to fill for the final password from this depth
        req_level = element[1] + self.parse_tree[-1][1]           
        
        #print("element: " + str(element))
        #print("parse tree: " + str(self.parse_tree))
        #print("req_level: " + str(req_level))
        #input("debug")        
            
        ##--Now loop through all the possible items at this depth
        while self.parse_tree:
            
            ##--Simplifying some of the code by assigning this pointer
            last_item = self.parse_tree[-1]
            
            ##--Start it out by incrementing the index of the last item
            last_item[2] += 1
                        
            ##--The level we are workng from for this current depth
            depth_level = last_item[1]          
            
            ##--Levels for depth start off at the max and go down to 0
            while True:
                
                while last_item[2] < len(self.cp[last_item[0]][depth_level]):
                    new_ip = element[0][0:-1] + self.cp[last_item[0]][depth_level][last_item[2]]
                    new_elements = self._fill_out_parse_tree(new_ip, req_length, req_level-depth_level)
                    
                    ##--Found a match!!
                    if new_elements != None: 
                        self.parse_tree += new_elements                      
                        return self._format_guess()
                    
                    ##--Otherwise, increase the index and try again at this depth level                    
                    last_item[2] += 1
                
                ##--No lower level, exit out of this
                if depth_level == 0:
                    break
                    
                ##--Try a lower level 
                cp_index, depth_level = self._find_cp(last_item[0], depth_level-1, 0)

                ##--No lower level, exit
                if cp_index == None:
                    break
                
                last_item[1] = depth_level
                
                ##--Reset the index to the start
                last_item[2] = 0
            
            ##-No match, go deeper
            element = self.parse_tree.pop()
            req_length += 1

            if self.parse_tree:
                req_level += self.parse_tree[-1][1]                
        
        return None
            

    ##################################################################################################
    # Takes the parse tree and the IP and generates an actual guess to return
    ##################################################################################################
    def _format_guess(self):

        guess = self.ip
        for item in self.parse_tree:
            guess += self.cp[item[0]][item[1]][item[2]]        
        
        ##--This seems slower
        #guess = ''.join([self.ip] + [self.cp[item[0]][item[1]][item[2]] for item in self.parse_tree])       
        
        return guess
            
            
    ##################
    # Fills out a parse tree
    ####################
    def _fill_out_parse_tree(self, ip, length, target_level):
        if length == 1:
            cp_index, cp_level = self._find_cp(ip, target_level, target_level)
            if cp_index == None:
                return None
            return [[ip, cp_level, 0]]

        ###--Check to see if the optimizer has an answer
        if length <= self.optimizer.max_length:
            found, result = self.optimizer.lookup(ip, length, target_level)
            
            ##--If a previous result was stored in the optimizer, return it
            if found:
                return result
            
        cur_level = target_level
        
        ##--Need to save these off for updating the optimizer
        optimize_level_target = target_level
        
        while cur_level >= 0:
            ##--Find the top level CP for the current level
            cp_index, cp_level = self._find_cp(ip, cur_level, 0)
            if cp_index == None:
                if length <= self.optimizer.max_length:
                    self.optimizer.update(ip, length, optimize_level_target, None)
                return None
            
            next_length = length - 1            
            top_index = len(cp_index)
            cur_index = 0
            while cur_index < top_index:
                next_ip = ip[1:]+cp_index[cur_index]
                working_parse_tree = self._fill_out_parse_tree(
                    ip = next_ip, 
                    length = next_length,
                    target_level = target_level - cp_level
                    )
                    
                if working_parse_tree != None:
                    result = [[ip, cp_level, cur_index]] + working_parse_tree
                    if length <= self.optimizer.max_length:
                        self.optimizer.update(ip, length, optimize_level_target, result)
                    return result
                    
                cur_index += 1
            
            ##--Need to go one less than the returned cp level so we don't loop forever
            cur_level = cp_level - 1
            
        if length <= self.optimizer.max_length:
            self.optimizer.update(ip, length, optimize_level_target, None)
        return None
        
        
    ################################################################################################
    # Returns a pointer to the highest possible transition
    # [ip, level, index]
    # Returns None if none is possible  
    ################################################################################################    
    def _find_cp(self, ip, top_level, bottom_level):
        
        ##--Quick bail out if the ip is not present
        if ip not in self.cp:
            return None, None
        
        ##--Set the maximum level we're going to check        
        if self.max_level < top_level:
            top_level = self.max_level
            
        ##--Attempt to find the highest transition possible    
        while top_level >= bottom_level:
            if top_level in self.cp[ip]:
                return self.cp[ip][top_level], top_level
                
            top_level -= 1

        return None, None
            