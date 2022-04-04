#!/usr/bin/env python3


"""

This file contains the functionality to detect e-mail addresses

"""


from .tld_list import get_tld_list


def detect_email(section):
    """
    Looks for emails in a section

    For example bob@hotmail.com123 will extract bob@hotmail.com

    Variables:

        section: The current section of the password to process
        This function will break up the section into multiple parts
        if an e-mail is found

    Returns:
        There are three return values:
        parsing, found, provider

        parsing: A list of the sections to return
        E.g. input password is 'bob@hotmail.com123'
        parsing should return:
        [('bob@hotmail.com','E'),('123',None)]

        found: The email found parsing this section, or None

        provider: The provider 'e.g. gmail.com' for the e-mail or None

    """

    tld_list = get_tld_list()
    working_string = section[0].lower()
    parsing = []

    # Bail out checks before looking for TLDs to see if it might be an e-mail
    if '.' not in working_string:
        return section, None, None

    if '@' not in working_string:
        return section, None, None

    # Look to find if a tld exists in the e-mail
    for tld in tld_list:
        end_index = working_string.find(tld)

        # Found a tld, now need to see if it is an e-mail
        if end_index != -1:

            # Update the end index to actually point to the end
            end_index += len(tld)


            # Look for an '@' symbol to indicate an e-mail
            # Only search the string before the tld
            #
            marker_index = working_string[0:end_index].find('@')

            # Found the '@'
            if marker_index != -1:

                # Originally was going to try to find the "front" of the email
                # but after looking at several datasets, the false-negative
                # from this would outweigh the benifits. Aka don't see many
                # instances of people adding mangling rules in front of e-mail
                # addresses
                #
                # Note, both found and provider are being normalized to
                # lowercase for now
                #
                found = working_string[0:end_index]

                # Get the provider
                #
                # Exclude the '@' symbol
                #
                provider = working_string[marker_index + 1:end_index]

                # Update the parsing info for the found e-mail
                #
                # Note, using section vs. working_string since working_string
                # was normalized to lowercase and I don't want to lose the
                # capitalization info
                #
                parsing.append((section[0][0:end_index],'E'))

                # If there are items after the e-mail, add remainder to parsing
                if end_index != len(working_string):
                    parsing.append((section[0][end_index:],None))

                return parsing, found, provider

    return section, None, None


def email_detection(section_list):
    """
    Finds likely e-mails in the password

    Returns:
        Returns two lists, email_list and provider_list

        email_list: A list of email addresses that were detected

        provider_list: A list of the providers (after the @). Yes that info
        is avialble in found_emails but might as well identify
        the provider/tld now since it is useful to display

    """

    email_list = []
    provider_list = []

    ## Do a pass through and detect e-mails
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

            parsing, email, provider = detect_email(section_list[index])

            # If an e-mail was detected
            if email:
                email_list.append(email)
                provider_list.append(provider)

                # This is a trick to use the list extend but at an index
                del section_list[index]
                section_list[index:index] = parsing

        index += 1

    return email_list, provider_list
