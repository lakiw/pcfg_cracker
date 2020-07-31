#!/usr/bin/env python3


#########################################################################
# Tries to detect Multi-words in the training dataset
#
# Aka CorrectBatteryStaple = Correct Battery Staple
#
# There's multiple ways to do this. 
# For example https://github.com/s3inlc/CorrectStaple
#
# The current method attempts to learn multiwords from the training set
# directly, with a small list of assist multi words to aid in this.
#
# Aka if 'cat' and 'dog' is seen multiple times in the training set
# but 'catdog' is only seen once, attempt to break it into a multi-word
#
#########################################################################


# Attempts to identify and split up multiwords
#
# Current works by creating a base word list from the training data of
# words that occur multiple times. Once this base set is genreated will
# then attempt to break up low occurence words into smaller base words
#
import copy
from typing import List, TextIO

"""
Note that catdog will not be treated as (cat, dog) 
because both of them of length less than 4.

helloabc will be treated as (hello, abc) 
because one of multiword should be of length larger than of equal to 4
"""


def split_ado(string):
    """
    a replacement for re
    :param string: any string
    :return: alpha, digit, other parts in a list
    """
    prev_chr_type = None
    acc = ""
    parts = []
    for c in string:
        if c.isalpha():
            cur_chr_type = "alpha"
        elif c.isdigit():
            cur_chr_type = "digit"
        else:
            cur_chr_type = "other"
        if prev_chr_type is None:
            acc = c
        elif prev_chr_type == cur_chr_type:
            acc += c
        else:
            parts.append(acc)
            acc = c
        prev_chr_type = cur_chr_type
    parts.append(acc)
    return parts


class MyMultiWordDetector:

    # Initialize the Multi-word detector
    #
    # threshold = the minimum number of times that a word can be seen to be
    # classified as a base word
    #
    # min_len = miminum length for a base word from the training set.
    #           Don't want to have one letter matches or everything will be a
    #           multi-word. Note, there is a seperate list of high value base
    #           words such as 'love' and 'cat', that may be below the min_len
    #
    # max_len = maximum lenght of a multi-word to parse. This is to prevent
    #           getting hung up on 500 character passwords.
    #
    def __init__(self, threshold=5, min_len=4, max_len=21):
        self.threshold = threshold
        self.min_len = min_len
        self.max_len = max_len

        # No sense checking an input word if it is too small to be made up of
        # two base words
        #
        # Saving this value to reduce multiplications later on since this
        # will need to be checked to parse input passwords
        self.min_check_len = min_len * 2

        # This is the lookup table where base words are saved
        #
        # Rather than save all the words directly with counts, it saves a nested
        # dictionary with each level being a character. That way when parsing
        # a multiword we can walk down it trying to find matches 
        #
        self.dtree = {"#1": 5}
        self.__min_len_dtree = {}
        self.lendict = {}

        # Trains on an input passwords

    #
    # One "weird" note about the lookup table. To speed things up, I'm not
    # checking mimimum length of strings before I insert them into the lookup
    # table. Therefore there will almost certainly be one, two character strings
    # in the lookup table that aren't valid base words. That's ok though since
    # their "count" wont' be recorded so they will not be treated as valid
    # base words, and since they are short and most will be parts of other
    # words, they shouldn't take up a lot of space
    #
    def train(self, input_password):

        # Quick bail out if the input password is too short or too long
        if len(input_password) < self.min_len:
            return

        if len(input_password) > self.max_len:
            return
        # Lowercase the password since multiword training is not being done
        # on capitalization or CamelCase
        password = input_password.lower()
        parts = split_ado(password)
        for part in parts:
            if len(part) < self.min_len:
                if part not in self.__min_len_dtree:
                    self.__min_len_dtree[part] = 0
                self.__min_len_dtree[part] += 1
                continue
            if part not in self.dtree:
                self.dtree[part] = 0
            self.dtree[part] += 1

    def train_file(self, password_list: TextIO):
        password_list.seek(0)
        for pwd in password_list:
            pwd = pwd.strip("\r\n")
            self.train(pwd)
        self.new_lendict()
        password_list.seek(0)
        pass

    # Gets the number of times the alpha_string has been seen in training
    #
    # alpha_string: Note making this explicit that only alpha strings should
    #               be passed in. The goal of this function is *not* to parse
    #               out digits, special characters, etc
    #
    # Returns:
    #     Int: The number of times the string was seen during training
    #
    def _get_count(self, alpha_string):
        return self.dtree.get(alpha_string.lower(), 0)

    def get_count(self, string):
        return self.dtree.get(string.lower(), 0)

    # Recusivly attempts to identify multiword parsing
    # 
    # Returns
    #    None: If no parsing could be found
    #    [base1, base2, ...] if parsing was found
    #
    # Starts with the minimum len base word it can find, and then calls itself
    # recursivly with the rest of the password until one does not return None. 
    # Returns None if no match can be made.

    #
    def _identify_multi(self, alpha_string):

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
                    results.insert(0, alpha_string[0:index])
                    return results

        # Could not parse out multi-words
        return None

    def __calc_prob(self, container: List):
        prob = 1
        for part in container:
            if len(part) < self.min_len:
                continue
            prob *= self.lendict.get(len(part), {}).get(part, .0)
            if prob < 1e-50:
                break
        return container, prob / len(container)

    def _augmented_identify_multi(self, alpha_string, multi_list: List, container: List, target_len: int,
                                  threshold: int = 0):
        # Tries to create the largest base word possible
        #
        # Subtract 1 to min_len so that we continue through the minimum length
        for index in range(1, len(alpha_string), 1):
            multi_container = container
            left = alpha_string[0:index]
            left_count = self._get_count(left)
            right = alpha_string[index:]
            right_count = self._get_count(right)
            # If this is a valid base word
            if left_count + right_count > threshold:
                multi_container.append(left)
                # Check to see if the remainder is a valid base word
                # It was, so return the two items as a list
                multi_container.append(right)
                if len("".join(multi_container)) == target_len:
                    multi_list.append(self.__calc_prob(copy.deepcopy(multi_container)))
                multi_container.pop()
                # return multi_container

                # Need to recursivly look for a multiword in the remainder

                self._augmented_identify_multi(right, multi_list, multi_container, target_len, threshold)

                if len("".join(multi_container)) == target_len:
                    multi_list.append(self.__calc_prob(copy.deepcopy(multi_container)))
                multi_container.pop()

                # If results indicate a parsing for the end of the alpha_string
                # It was a successful multi_word so return it as a list
                # if results:
                #     results.insert(0, alpha_string[0:index])
                #     return results

        # Could not parse out multi-words
        return
        pass

    # Detects if the input is a multi-word and if so, returns the base words
    #
    # alpha_string: Note making this explicit that only alpha strings should
    #               be passed in. The goal of this function is *not* to parse
    #               out digits, special characters, etc
    #
    #               Note: This can be a string OR a list of one character
    #                     items.
    #
    # I'm overloading the multiword detector usage to also be able to detect
    # base words as well. This can be useful for things like l33t manling.
    #
    # Because of that it returns two variables. The first one is a True/False
    # of it the multiword detector could parse the word, the second is the
    # parsing of the multiword itself.
    #
    # Returns 2 variables:
    #     If_Parsed [Parsing of word]
    #
    #     If_Parsed = True if the parsing found a multi-word or a base word
    #
    #     If_Parsed = False if no parsing or base word was found                 
    #
    #     [alpha_string]: if the alpha_string was not a multi-word
    #     [base_word,base_word,...]: List of base words making up the multi-word
    #
    def parse(self, alpha_string, threshold=0):

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
        # if len(alpha_string) < self.min_check_len:
        #     return False, [alpha_string]

        # May be a multi-word. Need to parse it for possible base strings
        result = []
        self._augmented_identify_multi(alpha_string, result, [], len(alpha_string), threshold=threshold)
        result = sorted(result, key=lambda x: x[1], reverse=True)
        # No multiword parsing found
        if not result:
            return False, [alpha_string]

        # A multi-word parsing was found        
        else:
            return True, result[0][0]

    def parse_sections(self, sections):
        """
        give me a list of sections, I'll find possible multiwords
        Note that Digit, Other will also be parsed
        :param sections:
        :return:
        """
        parsed = []
        extracted_digits = []
        extracted_specials = []
        extracted_letters = []
        extracted_mask = []
        for sec, tag in sections:
            if tag is not None:
                parsed.append((sec, tag))
                continue
            parts = split_ado(sec)
            for part in parts:
                is_multi, multi_words = self.parse(part)
                for t in multi_words:
                    if t.isalpha():
                        lower_t = t.lower()
                        parsed.append((lower_t, f"A{len(lower_t)}"))
                        extracted_letters.append(lower_t)
                        mask = ""
                        for c in t:
                            if c.isupper():
                                mask += "U"
                            else:
                                mask += "L"
                        extracted_mask.append(mask)
                    elif t.isdigit():
                        parsed.append((t, f"D{len(t)}"))
                        extracted_digits.append(t)
                    else:
                        parsed.append((t, f"O{len(t)}"))
                        extracted_specials.append(t)
        return parsed, extracted_letters, extracted_mask, extracted_digits, extracted_specials

    def new_lendict(self):
        """
        generate a dict whose key is len
        helloabc may not be treated as (hello, abc) because len(abc) < min_len
        therefore, I use another dict __min_len_dtree to parse this case
        :return:
        """
        lendict = {}
        for dic in [self.dtree, self.__min_len_dtree]:
            for k, v in dic.items():
                lk = len(k)
                if lk not in lendict:
                    lendict[lk] = {}
                lendict[lk][k] = dic[k]
            for lk, ks in lendict.items():
                total = sum(ks.values())
                for k, v in ks.items():
                    lendict[lk][k] = v / total
            pass

        self.lendict = lendict
        pass


def _test():
    multi = MyMultiWordDetector()
    for _ in range(10):
        multi.train("cat12345")
        multi.train("dog45678")
        multi.train("hello123")
        multi.train("world456")
    for s in ["catdog", "helloabc", "helloworld", "12345999"]:
        r = multi.parse(s)
        print(r)
    pass


if __name__ == '__main__':
    _test()
