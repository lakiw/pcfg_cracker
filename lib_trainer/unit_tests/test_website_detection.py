#!/usr/bin/env python3


#######################################################
# Unit tests for email_detection
#
#######################################################


import unittest
import unittest.mock


## Functions and classes to tests
#
from ..detection_rules.website_detection import website_detection


## Responsible for testing the website detection
#
# Note:
# + = positive test, (valid input handling)
# - = stress test, (invalid input handling) 
#
# ==Current Tests==
# + Test whole password being a website
# + Test false positive with .com starting at the begining of a password
# + Test false positive + true positive with two .coms
# + Test positive which has text after the .com
# + Test host detection with multiple subdomains
# + Test extanded url detection with data after the '/'
# + Test two different urls for tlds
#
class Test_Website_Checks(unittest.TestCase):

    ## Test whole password being a website
    #
    def test_whole_password_is_a_website(self):
    
        section_list = [('http://www.google.com',None)]
        url_list, host_list, prefix_list = website_detection(section_list)
        
        assert url_list == ['http://www.google.com']
        assert host_list == ['google.com']
        assert prefix_list == ['http://www.']
        assert section_list == [('http://www.google.com','W')]
        
        
    ## Test false positive of early .com
    #
    def test_false_positive(self):
    
        section_list = [('horSe.community',None)]
        url_list, host_list, prefix_list = website_detection(section_list)
        
        assert url_list == []
        assert host_list == []
        assert prefix_list == []
        assert section_list == [('horSe.community',None)]
        
        
    ## Test false positive followed by true positive .coms
    #
    def test_false_positive_followed_by_true_positive(self):
    
        section_list = [('http://www.community.horse.com',None)]
        url_list, host_list, prefix_list = website_detection(section_list)
        
        assert url_list == ['http://www.community.horse.com']
        assert host_list == ['horse.com']
        assert prefix_list == ['http://www.']
        assert section_list == [('http://www.community.horse.com','W')]
        
        
    ## Test positive followed by text after it
    #
    def test_positive_followed_by_text(self):
    
        section_list = [('http://www.google.com123',None)]
        url_list, host_list, prefix_list = website_detection(section_list)
        
        assert url_list == ['http://www.google.com']
        assert host_list == ['google.com']
        assert prefix_list == ['http://www.']
        assert section_list == [('http://www.google.com','W'),('123',None)]
        
        
    ## Test host detection when there are mulitple subdomains
    #
    def test_host_detection_multiple_subdomains(self):
        section_list = [('http://www.subdomain.anothersub.google.com',None)]
        url_list, host_list, prefix_list = website_detection(section_list)
        
        assert url_list == ['http://www.subdomain.anothersub.google.com']
        assert host_list == ['google.com']
        assert prefix_list == ['http://www.']
        assert section_list == [('http://www.subdomain.anothersub.google.com','W')]
        
        
    ## Test url continuing after the '/'
    #
    def test_extended_url(self):
        section_list = [('http://www.google.com/data.html',None)]
        url_list, host_list, prefix_list = website_detection(section_list)
        
        assert url_list == ['http://www.google.com/data.html']
        self.assertEqual(host_list, ['google.com'])
        self.assertEqual(prefix_list,['http://www.'])
        assert section_list == [('http://www.google.com/data.html','W')]
    