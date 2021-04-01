#!/usr/bin/env python3


#######################################################
# Unit tests for email_detection
#
#######################################################


import unittest
import unittest.mock


## Functions and classes to tests
#
from ..detection_rules.email_detection import email_detection


## Responsible for testing the E-mail detection
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test whole password being an e-mail
# + Test two e-mails in password
# + Test other data after the e-mail
# + Test TLD but not an e-mail, no @
#
class Test_Email_Checks(unittest.TestCase):

    ## Test whole password being a e-mail
    #
    def test_whole_password_is_an_email(self):
    
        section_list = [('cweir@vt.edu',None)]
        found_emails, found_providers = email_detection(section_list)
        
        assert found_emails == ['cweir@vt.edu']
        assert found_providers == ['vt.edu']
        assert section_list == [('cweir@vt.edu','E')]
    
    
    ## Test two e-mails in passwords
    #
    def test_two_emails_in_password(self):
    
        section_list = [('cweir@vt.educweir@vt.edu',None)]
        found_emails, found_providers = email_detection(section_list)
        
        assert found_emails == ['cweir@vt.edu','cweir@vt.edu']
        assert found_providers == ['vt.edu','vt.edu']
        assert section_list == [('cweir@vt.edu','E'),('cweir@vt.edu','E')]
        
        
    ## Test data after the e-mail
    #
    def test_data_after_email(self):
    
        section_list = [('cweir@vt.eduTest123',None)]
        found_emails, found_providers = email_detection(section_list)
        
        assert found_emails == ['cweir@vt.edu']
        assert found_providers == ['vt.edu']
        assert section_list == [('cweir@vt.edu','E'),('Test123',None)]
        
        
    ## Test tld but no @ so not an e-mail
    #
    def test_tld_but_not_an_email(self):
    
        section_list = [('cweirvt.edu',None)]
        found_emails, found_providers = email_detection(section_list)
        
        assert found_emails == []
        assert found_providers == []
        assert section_list == [('cweirvt.edu',None)]