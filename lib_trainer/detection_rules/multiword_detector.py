#!/usr/bin/env python3


"""
Tries to detect Multi-words in the training dataset

Aka CorrectBatteryStaple = Correct Battery Staple

There's multiple ways to do this.
For example https://github.com/s3inlc/CorrectStaple

The current method attempts to learn multiwords from the training set
directly, with a small list of assist multi words to aid in this.

Aka if 'cat' and 'dog' is seen multiple times in the training set
but 'catdog' is only seen once, attempt to break it into a multi-word

"""


class MultiWordDetector:
    """
    Attempts to identify and split up multiwords

    Current works by creating a base word list from the training data of
    words that occur multiple times. Once this base set is genreated will
    then attempt to break up low occurence words into smaller base words

    """

    def __init__(self, threshold = 5, min_len = 4, max_len = 21):
        """
        Initialize the Multi-word detector

        Variables:
            threshold = the minimum number of times that a word can be seen to be
            classified as a base word

            min_len = miminum length for a base word from the training set.
            Don't want to have one letter matches or everything will be a
            multi-word. Note, there is a seperate list of high value base
            words such as 'love' and 'cat', that may be below the min_len

            max_len = maximum lenght of a multi-word to parse. This is to prevent
            getting hung up on 500 character passwords.

        """
        self.threshold = threshold
        self.min_len = min_len
        self.max_len = max_len

        # No sense checking an input word if it is too small to be made up of
        # two base words
        #
        # Saving this value to reduce multiplications later on since this
        # will need to be checked to parse input passwords
        self.min_check_len = min_len * 2

        ## This is the lookup table where base words are saved
        #
        # Rather than save all the words directly with counts, it saves a nested
        # dictionary with each level being a character. That way when parsing
        # a multiword we can walk down it trying to find matches
        #
        self.lookup = {}

    def train(self, input_password):
        """
        Trains on an input passwords

        One "weird" note about the lookup table. To speed things up, I'm not
        checking mimimum length of strings before I insert them into the lookup
        table. Therefore there will almost certainly be one, two character strings
        in the lookup table that aren't valid base words. That's ok though since
        their "count" wont' be recorded so they will not be treated as valid
        base words, and since they are short and most will be parts of other
        words, they shouldn't take up a lot of space

        """

        # Quick bail out if the input password is too short or too long
        if len(input_password) < self.min_len:
            return

        if len(input_password) > self.max_len:
            return

        # pointer to the current position in the lookup table
        index = self.lookup

        # The length of the current run
        run_len = 0

        # Lowercase the password since multiword training is not being done
        # on capitalization or CamelCase
        password = input_password.lower()

        # Walk through each character in the password
        for letter in password:

            # It is a letter
            if letter.isalpha():

                # Increment the run length
                run_len += 1

                # Check to see if we need to create an entry for this letter
                if letter not in index:
                    index[letter] = {}

                # update the pointer
                index = index[letter]

            # Not a letter
            else:

                # Deal with closing up a current run
                if run_len != 0:

                    # If the run isn't too short
                    if run_len >= self.min_len:
                        # If the word hasn't been seen before
                        if "count" not in index:
                            index["count"] = 1

                        else:
                            index["count"] += 1

                    # Reset the index and run length
                    run_len = 0
                    index = self.lookup

        # Finish up the last run if the word ends on a alpha character
        if run_len != 0:
            # If the run isn't too short
            if run_len >= self.min_len:
                # If the word hasn't been seen before
                if "count" not in index:
                    index["count"] = 1

                else:
                    index["count"] += 1

            # Reset the index and run length
            run_len = 0
            index = self.lookup

    def _get_count(self, alpha_string):
        """
        Gets the number of times the alpha_string has been seen in training

        Variables:
            alpha_string: Note making this explicit that only alpha strings should
            be passed in. The goal of this function is *not* to parse
            out digits, special characters, etc

        Returns:
            Int: The number of times the string was seen during training

        """

        index = self.lookup

        # In how it's currently being used in the pcfg trainer, it should
        # have seen every word at least once, but I could see myself re-using
        # this code in a different way, so throw an exception and catch it
        # if the alpha_string hasn't been seen before
        try:
            # Walk the alpha string
            for value in alpha_string:
                value = value.lower()

                # Reminder, that Index is basically a tree, so we're walking
                # the tree here
                index = index[value]

            # Now get the count
            return index["count"]

        # Haven't seen this alpha string before
        except KeyError:
            return 0

    def _identify_multi(self, alpha_string):
        """
        Recusivly attempts to identify multiword parsing

        Starts with the minimum len base word it can find, and then calls itself
        recursivly with the rest of the password until one does not return None.

        Returns None if no match can be made.

        Returns
            None: If no parsing could be found

            [base1, base2, ...] if parsing was found

        """

        # Stop looking for multiwords if there is not enough letters left
        # to create a second base word
        #
        max_index = len(alpha_string) - self.min_len

        # Tries to create the largest base word possible
        #
        # Subtract 1 to min_len so that we continue through the minimum length
        for index in range(max_index, self.min_len - 1, -1):

            # If this is a valid base word
            if self._get_count(alpha_string[0:index]) >= self.threshold:

                # Check to see if the remainder is a valid base word
                if self._get_count(alpha_string[index:]) >= self.threshold:
                    # It was, so return the two items as a list
                    return [alpha_string[0:index], alpha_string[index:]]

                # Need to recursivly look for a multiword in the remainder
                results = self._identify_multi(alpha_string[index:])

                # If results indicate a parsing for the end of the alpha_string
                # It was a successful multi_word so return it as a list
                if results:
                    results.insert(0,alpha_string[0:index])
                    return results

        # Could not parse out multi-words
        return None

    def parse(self, alpha_string):
        """
        Detects if the input is a multi-word and if so, returns the base words

        I'm overloading the multiword detector usage to also be able to detect
        base words as well. This can be useful for things like l33t mangling.

        Because of that it returns two variables. The first one is a True/False
        of it the multiword detector could parse the word, the second is the
        parsing of the multiword itself.

        Variables:
            alpha_string: Note making this explicit that only alpha strings should
            be passed in. The goal of this function is *not* to parse
            out digits, special characters, etc
            Note: This can be a string OR a list of one character items.

        Returns:
            Two variables, are returned, If_Parsed and [Parsing of word]

            If_Parsed:
                True if the parsing found a multi-word or a base word

                False if no parsing or base word was found

            [alpha_string]: if the alpha_string was not a multi-word
            [base_word,base_word,...]: List of base words making up the multi-word

        """

        # Quick bail out if the input password is too short or too long

        # Checking the base len so that we can still check if the string
        # is a base word.
        if len(alpha_string) < self.min_len:
            return False, [alpha_string]

        if len(alpha_string) >= self.max_len:
            return False, [alpha_string]

        # If the alpha_string has been seen enough to not be categorized as
        # a multi-word
        if self._get_count(alpha_string) >= self.threshold:
            return True, [alpha_string]

        # Bail out if the input password is too short to be a multi-word
        if len(alpha_string) < self.min_check_len:
            return False, [alpha_string]

        # May be a multi-word. Need to parse it for possible base strings
        result = self._identify_multi(alpha_string)

        # No multiword parsing found
        if not result:
            return False, [alpha_string]

        # A multi-word parsing was found
        return True, result
