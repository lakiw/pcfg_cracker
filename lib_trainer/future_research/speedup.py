"""
Note: This code still has not been integrated with the core PCFG code
"""

import os
import pickle
from typing import Dict, Set

path_found_l33t = os.path.join(os.path.dirname(__file__), "l33t.found")
path_ignore_l33t = os.path.join(os.path.dirname(__file__), "l33t.ignore")


def load_l33t_found() -> Set[str]:
    """
    words in this set will be treated as l33t and will not be parsed again
    :return: set of l33ts
    """
    
    if not os.path.exists(path_found_l33t):
        return set()
    fd = open(path_found_l33t, "r")
    l33ts = set()
    for line in fd:
        l33ts.add(line.strip("\r\n"))
    fd.close()
    return l33ts


def load_l33t_ign() -> Set[str]:
    """
    l33t.ignore, one instance per line
    :return: set of ignored l33ts
    """
    if not os.path.exists(path_ignore_l33t):
        return set()
    fd = open(path_ignore_l33t, "r")
    ign = set()
    for line in fd:
        ign.add(line.strip("\r\n"))
    return ign


def save_l33t_found(l33ts: Dict[str, int]) -> None:
    """
    give me a dict of l33ts, save it
    :param l33ts: l33ts got
    :return:
    """
    fd = open(path_found_l33t, "wb")
    l33ts = set(l33ts.keys())
    pickle.dump(l33ts, fd)

