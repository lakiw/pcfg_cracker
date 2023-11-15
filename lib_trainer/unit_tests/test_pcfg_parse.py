#!/usr/bin/env python3


#######################################################
# Unit tests pcfg parser
#
#######################################################

import unittest
import unittest.mock
from collections import Counter

## Functions and classes to tests
#
from ..pcfg_password_parser import PCFGPasswordParser
from ..detection_rules.multiword_detector import MultiWordDetector
## Responsible for testing the prefix count
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test simple password with a prefixcount
#

class Test_PCFGPasswordParser_prefixcount(unittest.TestCase):
    # Setup test MultiWord
    multiword_detector = MultiWordDetector(
                            threshold = 5,
                            min_len = 4,
                            max_len = 21,
                            prefixcount=True)
    # While we are here, lets test the multiword aswell
    multiword_detector.train('500 Password123!')
    assert multiword_detector.lookup == {'p': {'a': {'s': {'s': {'w': {'o': {'r': {'d': {'count': 500}}}}}}}}}

    pcfg_parser = PCFGPasswordParser(multiword_detector, prefixcount=True)
    pcfg_parser.parse('500 Password123!')

    assert pcfg_parser.count_alpha[8] == Counter({'password': 500})
