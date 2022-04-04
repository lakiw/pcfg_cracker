#!/usr/bin/env python3

"""

Creates lookup tables for OMEN ngrams using the specified alphabet

Basically this handles the initial counts and telling if 'abcd' shows
in a password

"""


from .smoothing import smooth_grammar, smooth_length


class AlphabetLookup:
    """
    Holds all the OMEN NGRAM lookup information and statistics

    Responsible for performing lookups against it

    """

    def __init__(self, alphabet, ngram, min_length = 1, max_length = 21):
        """
        Basic initialization function

        Warning, setting too long of an alphabet and/or too high of ngrams
        can cause severe memory/disk space issues.

        Variables:
            alphabet = the string alphabet to generate, aka 'abcdefABCDEF123'

            ngrams = The length of markov chains.

            min_length = The minimum length password to train on

            max_length = The maximum length password to train on

        """
        # Save input options
        self.alphabet = alphabet
        self.ngram = ngram
        self.max_length = max_length
        self.min_length = min_length

        # Min length can't be less than ngram
        if self.min_length < ngram:
            self.min_length = ngram

        ## The grammar has the format (example for ngram=4)
        #
        #   {
        #       'aaa': {       //the starting charaters
        #           ip_count: 5,    //the number of times they have shown up in the ip (begining)
        #           ep_count: 3,    //the number of times they have shown up in the ep (end)
        #           cp_count: 100,  //the number of times they have shown up total in passwords (for cp)
        #           next_letter:{   //the next letter for cp
        #             a:5           //represents the cp 'aaaa' with the count of the times that cp has been seen
        #             b:12,         //represents the cp 'aaab'
        #             ...,
        #           },
        #       },
        #       ...,
        #   }
        #
        self.grammar = {}

        ## Initialize the counters

        # Initial probability counter
        self.ip_counter = 0

        # end probability counter
        #
        # Not actually used for OMEN, but might help with targeted MASK attacks
        #
        self.ep_counter = 0

        # length counter
        self.ln_counter = 0

        # Intitialize the length table
        # Since we can do a lookup directly based on length, saving this
        # as a simple list vs dictionary
        self.ln_lookup = [0]* max_length

    def parse(self, password):
        """
        Parses the input password and updates the global counts
        """

        # Reject if too short or too long
        pw_len = len(password)
        if pw_len < self.min_length or pw_len > self.max_length:
            return

        # Update the length counts
        # List is 0 indexed so subtract -1 from actual length
        self.ln_lookup[pw_len - 1] += 1
        self.ln_counter += 1

        ## Loop through the entire password
        #
        # Going to go through every ngram-1 combo so we can grab the end prob as well
        # in this loop. For example if ngram = 3 and the password is 'abcd' we want
        # 'ab', 'bc', 'cd'. For the loop it goes 0 to 3, so 0 to pw_len(4) - ngram(3) + 2
        #
        for i in range(0,pw_len - self.ngram + 2):
            # Grab the ngram-1 section to key off of
            cur_start_ngram = password[i:i+self.ngram-1]

            # Check if this ngram has been seen before
            if cur_start_ngram  not in self.grammar:
                # If not, check if it falls within our alphabet
                if self.is_in_alphabet(cur_start_ngram):
                    # Initialize the entry for this items
                    self.grammar[cur_start_ngram] = {
                        'ip_count':0,
                        'ep_count':0,
                        'cp_count':0,
                        'next_letter':{},
                        }
                # Not in alphabet, skip and go on to the next one
                else:
                    continue

            # Declaring this pointer here to clean up the folloiwng code
            index = self.grammar[cur_start_ngram]

            ## Handle if it is the IP
            #
            if i == 0:
                index['ip_count'] += 1
                self.ip_counter += 1

            ## Handle the CP info
            #
            if i != pw_len - (self.ngram -1):
                end_char = password[i+self.ngram-1]
                # Check if this character has been seen before
                if end_char not in index['next_letter']:
                    # Check if this char is in the alphabet
                    if self.is_in_alphabet(end_char):
                        index['next_letter'][end_char] = 1
                        index['cp_count'] += 1
                # Have seen this before
                else:
                    index['next_letter'][end_char] += 1
                    index['cp_count'] += 1

            ##Handle the EP info
            #
            else:
                index['ep_count'] += 1
                self.ep_counter +=1

        return

    def is_in_alphabet(self, cur_ngram):
        """
        Checks if a ngram can be constructed with the alphabet

        Returns:
            True: if ngram is composed of valid characters
            False: if any character in the ngram is not valid

        """
        for letter in cur_ngram:
            if letter not in self.alphabet:
                return False

        return True

    def apply_smoothing(self):
        """
        Applies probability smoothing to the grammar

        Also calculates the OMEN "levels" for the different counters

        """
        smooth_length(self.ln_lookup, self.ln_counter)
        smooth_grammar(self.grammar, self.ip_counter, self.ep_counter)
