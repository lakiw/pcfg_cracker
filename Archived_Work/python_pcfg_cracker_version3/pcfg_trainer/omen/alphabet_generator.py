#############################################################################
# Learns an Alphabet from an input training set
# Another way of saying it returns the N most common characters it sees
# for valid passwords in the trianing set
#############################################################################


#####################################################################################
# Making this a class so I can re-use trainer_file_io to read the passwords one
# at a time, and pass them into this
#####################################################################################
class AlphabetGenerator:
    
    
    #####################################################
    # Initialize the alphabet generator
    # 
    # Values:
    #   alphabet_size: The number of characters to save
    #                  to the alphabet
    #   ngram: The ngram count for this grammar
    #          Used to identify the minimum size of passwords
    #          to train on
    #####################################################
    def __init__(self, alphabet_size, ngram):
        self.alphabet_size = alphabet_size
        self.ngram = ngram
        
        ##--Dictionary used for quick lookups during training
        ##  Indexed by letter, value is count seen
        ##  aka:
        ##  { 'a':10, 'c': 15, 'z': 1}
        self.dictionary = {}
        
        
    ##########################################################################################
    # Parse one password
    ##########################################################################################    
    def process_password(self, password):
        ##--Make sure it is long enough
        ##--This is to weed out things like weird one character line breaks
        if len(password) < self.ngram:
            return
            
        ##--Loop through every letter in the password    
        for letter in password:
     
            ##--Skip blacklisted characters. Currently just skipping tabs since that can cause problems with other programs.
            if letter in ['\t']:
                continue
            ##--If we have seen this letter before
            elif letter in self.dictionary:
                self.dictionary[letter] += 1
            ##--If this is the first time we've seen this letter
            else:
                self.dictionary[letter] = 1      
        return
        
    
    ##############################################################################################
    # Returns a string of the most common N characters
    ##############################################################################################
    def get_alphabet(self):
        
        ##--Sort the dictionary by the keys.  Keeping the key/value pairs here for debugging purposes
        sorted_alphabet = [(k,self.dictionary[k]) for k in sorted(self.dictionary, key=self.dictionary.get, reverse=True)]
        
        ##--Generate the final alphabet string
        count = 0
        final_alphabet = ''
        for item in sorted_alphabet:
            ##--Bail out if we have grabbed the N most common items so far
            if count >= self.alphabet_size:
                return final_alphabet

            ##--Append item to our final alphabet
            final_alphabet += item[0]
            count += 1
    
        return final_alphabet