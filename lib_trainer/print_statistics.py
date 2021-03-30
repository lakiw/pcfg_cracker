#!/usr/bin/env python3


"""

This file contains functionality to print "interesting results" to stdout
after a training session is run.

These results are currently geared to items that will help identify
the source of an unknown training dataset/leak

"""

def print_statistics(pcfg_parser):
    """
    Prints interesting statistics from the training set

    Currently just prints top e-main providers, top URL domains and top years

    Variables:
        pcfg_parser: Of type PCFGPasswordParser. Contains the statistics to
        print out

    Returns:
        Null
    """

    print()
    print("-------------------------------------------------")
    print("Top 5 e-mail providers")
    print("-------------------------------------------------")
    print()
    top5 = pcfg_parser.count_email_providers.most_common(5)
    for item in top5:
        print(item[0] + " : " + str(item[1]))

    print()
    print("-------------------------------------------------")
    print("Top 5 URL domains")
    print("-------------------------------------------------")
    print()
    top5 = pcfg_parser.count_website_hosts.most_common(5)
    for item in top5:
        print(item[0] + " : " + str(item[1]))

    print()
    print("-------------------------------------------------")
    print("Top 10 Years found")
    print("-------------------------------------------------")
    print()
    top10 = pcfg_parser.count_years.most_common(10)
    for item in top10:
        print(item[0] + " : " + str(item[1]))
