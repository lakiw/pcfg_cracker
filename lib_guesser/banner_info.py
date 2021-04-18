#!/usr/bin/env python3


"""
Contains banner ascii art and displays for the training program

Note: Need to print everything out to stderr since the output/guesses of
this program will be sent to stdout
"""


import sys


def print_banner():
    """
    ASCII art for the banner
    """
    print()
    print('''    ____            __  __           ______            __   ''',file=sys.stderr)
    print('''   / __ \________  / /_/ /___  __   / ____/___  ____  / /  ''',file=sys.stderr)
    print('''  / /_/ / ___/ _ \/ __/ __/ / / /  / /   / __ \/ __ \/ /   ''',file=sys.stderr)
    print(''' / ____/ /  /  __/ /_/ /_/ /_/ /  / /___/ /_/ / /_/ / /     ''',file=sys.stderr)
    print('''/_/ __/_/_  \___/\__/\__/\__, /   \__________/\____/_/     ''',file=sys.stderr)
    print('''   / ____/_  __________  __/_/_   / ____/_  _____  _____________  _____''',file=sys.stderr)
    print('''  / /_  / / / /_  /_  / / / / /  / / __/ / / / _ \/ ___/ ___/ _ \/ ___/''',file=sys.stderr)
    print(''' / __/ / /_/ / / /_/ /_/ /_/ /  / /_/ / /_/ /  __(__  |__  )  __/ /    ''',file=sys.stderr)
    print('''/_/    /__,_/ /___//__/\__, /   \____/\__,_/\___/____/____/\___/_/     ''',file=sys.stderr)
    print('''                         /_/''',file=sys.stderr)
    print('',file=sys.stderr)


def print_error():
    """
    ASCII art for displaying an error state before quitting
    """
    print('',file=sys.stderr)
    print('An error occured, shutting down',file=sys.stderr)
    print('',file=sys.stderr)
    print(r' \__/      \__/      \__/      \__/      \__/      \__/          \__/',file=sys.stderr)
    print(r' (oo)      (o-)      (@@)      (xx)      (--)      (  )          (OO)',file=sys.stderr)
    print(r'//||\\    //||\\    //||\\    //||\\    //||\\    //||\\        //||\\',file=sys.stderr)
    print(r'  bug      bug       bug/w     dead      bug       blind      bug after',file=sys.stderr)
    print(r'         winking   hangover    bug     sleeping    bug     whatever you did',file=sys.stderr)
    print('',file=sys.stderr)
