
#Note this still doesn't work    
    
##--Version 2--##
def recursive_function(cur_pt, min_prob, max_prob, max_return_size)
    ret_value = []
    
    #check if the prob is too lower
    if prob(cur_pt) < min prob:
        return []
        
    #check if this node falls within the range
    if prob(cur_pt) <= max_prob:
        ret_value.append({'pt':cur_pt, prob = prob(cur_pt)})
        
    #check transitions
    if len (transitions) == 0 and not is_terminal:   
        possible_transitions = []
        for x in transitions:
            possible_transitions.append(recursive_function(x, min_prob / prob(cur_pt), max_prob * prob(cur_pt), max_return_size - len(ret_value)))
        
        ##--Combine transitions and add to ret_value
        #create_big_list of ret_values, and update min probability here if ret_values > max_return_size
    
    if can increment cur_pt:
        recursive_results = recursive_function(cur_pt incremented, min_prob, max_prob, max_return_size)
        #Add results to ret_values, and update min probability here if ret_values > max_return_size
        
            
    return ret_values
        

    