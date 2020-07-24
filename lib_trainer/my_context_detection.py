"""
This is detector of Fixed Collocations, or conteXt sensitive
"""

"""
letters and digits
"""
all_letters = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
all_digits = set("0123456789")
"""
Context sensitive instances
"""
context_dict = [
    ";p",
    ":p",
    "*0*",
    "#1",
    "No.1",
    "no.1",
    "No.",
    "i<3",
    "I<3",
    "<3",
    "Mr.",
    "mr.",
    "MR.",
    "MS.",
    "Ms.",
    "ms.",
    "Mz.",
    "mz.",
    "MZ.",
    "St.",
    "st.",
    "Dr.",
    "dr.",

]


def detect_context(section: str):
    """
    find the context sensitive instance in a section
    :param section: a sub-string of a password
    :return: [(sec, tag)] list and [context] list
    """
    ret = []
    len_sec = len(section)

    for context in context_dict:
        len_x = len(context)
        idx = section.find(context)
        # not found
        if idx < 0:
            continue
        # first chr of context of same class with previous chr
        if idx + len_x < len_sec \
                and ((context[-1] in all_letters and section[idx + len_x] in all_letters)
                     or (context[-1] in all_digits and section[idx + len_x] in all_digits)):
            continue
        # last chr of context of same class with
        if idx > 0 and (((context[0] in all_letters) and (section[idx - 1] in all_letters))
                        or ((context[0] in all_digits) and (section[idx - 1] in all_digits))):
            continue
        if idx > 0:
            ret.append((section[:idx], None))
        ret.append((section[idx: idx + len_x], "X1"))
        if idx + len_x < len_sec:
            ret.append((section[idx + len_x:], None))
        return ret, [context]
    return [(section, None)], []


def detect_context_sections(sections_list):
    """
    tagging given sections, and return tagged sections
    :param sections_list: List[(section, tag)]
    :return: List[(section, tag)], List[context]
    """
    parsed_sections = []
    contexts = []
    for section, tag in sections_list:
        if len(section) < 2:
            parsed_sections.append((section, None))
        else:
            parsed_s, cont_s = detect_context(section)
            parsed_sections.extend(parsed_s)
            contexts.extend(cont_s)
    return parsed_sections, contexts


pass

