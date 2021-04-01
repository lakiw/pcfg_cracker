#!/usr/bin/env python3


"""

This file contains the functionality to detect websites

"""


## Local Imports
from .tld_list import get_tld_list


def detect_website(section):
    """
    Looks for websites in a section

    For example passwordwww.rockyou.com123 will extract www.rockyou.com

    Variables:

        section: The current section of the password to process

    Returns:
        The following are the return values:

        parsing: A list of the sections to return
        E.g. input password is 'rockyou.com123'
        parsing should return:
        [('rockyou.com','W'),('123',None)]

        url: The full url found, (unformatted)

        host: The base website found, lowercased. E.g. 'google.com'

        prefix: The prefix at the front of the website. E.g. 'http://', 'www.', ...

    """

    # List of valid URL-safe special characters
    # Not using them now, but may want to add this in later
    # valid_special = "-._~:/?#[]@!$&'()*+,;="

    tld_list = get_tld_list()
    working_string = section[0].lower()
    parsing = []

    working_string = section[0].lower()

    # Bail out check before looking for TLDs since '.' is not common
    if '.' not in working_string:
        return section, None, None, None

    # Look to find the tld in the url
    #
    # Note, tempted to use urlextract, but that would add another required
    # python library that users would have to install. Still identifying
    # urls is one of those "easy" problems that has a lot of tricky edge cases
    #
    for tld in tld_list:
        end_index = working_string.find(tld)
        total_index = end_index

        # Found a tld
        #
        # Will perform checks and loop to identify a valid at the end of the section
        # Otherwise there will be false positives such as 'mr.chicken'
        #
        # It loops because we don't want to get stuck on false positives like
        # www.COMmunity.COM
        #
        while end_index != -1:

            # Check to make sure that the tld is at the end of the section
            # or that it ends in a valid characters
            if total_index != len(working_string) - len(tld):

                # Currently making sure the next character isn't a letter
                # Also checking to make sure it isn't a '.' to indicate nested
                # TLDs (such as org.com)
                #
                # Letters following URLs have a high false positive rate from
                # my testing to date
                #
                # It'd be nice to check to make sure that the following character
                # was a valid URL character, ['/',':'], but surprisingly
                # people don't always use valid URLs in their password but will
                # append digits/special chars to meet pw creation requriements
                #
                # Therefore, this check will absolutly have false positives
                # but currently I view the false positives worth it for avoiding
                # false negatives for passwords I find interesting to parse
                #
                if (working_string[total_index + len(tld)].isalpha()) or (working_string[total_index + len(tld)] == '.'):

                    # This is a false positive

                    # Update the search string so we don't find the same false
                    # positive and search again
                    total_index += len(tld)
                    end_index = working_string[total_index:].find(tld)
                    total_index += end_index

                    continue

            # Looks like a URL was used in the password. Identify the end of the
            # URL. This is a quick check and has significant potential to
            # include data that isn't part of the URL

            # Making a pointer the current end of the URL to the TLD
            end_index = total_index + len(tld)

            # The TLD is the end of the string, so nothing is after it
            if end_index == len(working_string):
                end_of_url = end_index

            # Looks like the URL continues becasue there is the '/'
            elif working_string[end_index] == '/':
                end_of_url = len(working_string)

            # Just going to assume the rest of the string is mangling vs a URL
            else:
                end_of_url = end_index

            # Now identify the host of the URL
            #
            # Note, can't just use python's urlparse since once again, people
            # don't always use valid urls in their passwords
            #

            # Find the host, this will either be up to the previous '.' to the
            # TLD, the '/', or the begining of the password

            # Note, this will misparse IP addresses. Not sure if I care enough
            # to add handling for that at this time.
            start_index = working_string[:total_index].rfind('.') + 1

            # No '.' found. Now look for the /
            if start_index == -1:
                start_index = working_string[:total_index].rfind('/') + 1

            # No '/' found. Now look for a ':'
            if start_index == -1:
                start_index = working_string[:total_index].rfind(':') + 1

            # Look for spaces too since they appear in passphrases
            if start_index == -1:
                start_index = working_string[:total_index].rfind(' ') + 1

            # Note, if the start character wasn't found, start_index will be
            # '-1' so adding +1 to it will set the host to the begining of the
            # string
            host = working_string[start_index:total_index+len(tld)]

            ## Find the prifix if it exists
            #
            prefix = None
            start_of_url = -1

            # If the host wasn't found, assume there will not be a prefix
            if start_index == -1:
                start_of_url = 0

            # Look for a prefix
            if start_of_url == -1:
                prefix_index = working_string[:start_index+1].rfind('http://www.')
                if prefix_index != -1:
                    prefix = 'http://www.'
                    start_of_url = prefix_index

            if start_of_url == -1:
                prefix_index = working_string[:start_index].rfind('http://')
                if prefix_index != -1:
                    prefix = 'http://'
                    start_of_url = prefix_index

            if start_of_url == -1:
                prefix_index = working_string[:start_index].rfind('www.')
                if prefix_index != -1:
                    prefix = 'www.'
                    start_of_url = prefix_index

            # No prefix found
            if start_of_url == -1:
                start_of_url = 0

            # Save the *full* URL string
            full_url = working_string[start_of_url:end_of_url]

            ## Create the parsing
            #

            # Add the non-url portion at the start of the password if exists
            if start_of_url != 0:
                # Using the section vs working_section to preserve capitalization
                parsing.append((section[0][0:start_of_url],None))

            # Add the URL to the parsing
            parsing.append((working_string[start_of_url:end_of_url],'W'))

            # Add the non-url portion at the end of the password if exists
            if end_of_url != len(section[0]):
                # Using the section vs working_section to preserve capitalization
                parsing.append((section[0][end_of_url:],None))

            return parsing, full_url, host, prefix

    return section, None, None, None


def website_detection(section_list):
    """
    Finds likely websites in the password

    Returns:
        Returns several lists: url_list, website_list, prefix_list

        url_list: the raw URLs that are detected

        host_list: The base website. For example google.com

        prefix_list: What prefixes, (if any) are put in the website, 'www', 'http:'

    """

    url_list = []
    host_list = []
    prefix_list = []

    ## Do a pass through and detect websites
    #
    # Walk through each section and parse it individually
    # Using an index since it lets me split items up while parsing the
    # whole list
    #
    index = 0
    while index < len(section_list):

        # Skip sections that have been processed earlier, for example
        # by keyboard walk detection
        if section_list[index][1] is None:

            parsing, url, website, prefix = detect_website(section_list[index])

            # If a website was detected
            if url:
                url_list.append(url)
                host_list.append(website)
                prefix_list.append(prefix)

                # This is a trick to use the list extend but at an index
                del section_list[index]
                section_list[index:index] = parsing

        index += 1

    return url_list, host_list, prefix_list
