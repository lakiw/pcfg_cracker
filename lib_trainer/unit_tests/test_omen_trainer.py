#!/usr/bin/env python3


#######################################################
# Unit tests omen trainer
#
#######################################################

import unittest
import unittest.mock
from collections import Counter

## Functions and classes to tests
#
from ..omen.alphabet_generator import AlphabetGenerator
## Responsible for testing the prefix count
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test simple password with a prefixcount
#

class Test_AlphabetGenerator_prefixcount(unittest.TestCase):
    # Setup generator
    ag = AlphabetGenerator(100, 4, prefixcount=True)
    ag.process_password('500 Password123!')
    assert ag.dictionary['P'] == 500
