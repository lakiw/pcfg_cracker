import collections
import functools
import re
from typing import Tuple, List

import sys
import traceback

import itertools

from .speedup import load_l33t_ign, load_l33t_found
from .trainer_file_input import TrainerFileInput

"""
The principle of L33t detector is as follows:
Firstly, we find whether a whole password follows l33t transformation or not.
Then, we will find some l33ts.
Next, we use found l33ts to detect l33ts which appear as part of a password.
Finally, we can find as many as possible l33ts in passwords.

"""


def get_mask(seg):
    """
    get corresponding upper/lower tag of given seg
    Hello -> ULLLL
    :param seg:
    :return:
    """
    mask = ""
    for e in seg:
        if e.isupper():
            mask += "U"
        elif e.islower():
            mask += "L"
        else:
            mask += "L"
    return mask


def get_ado(word: str):
    """
    split word according to A, D, O tag
    hello123world -> [(hello, A, 5), (123, D, 3), (world, A, 5)]
    :param word:
    :return:
    """
    prev_chr_type = None
    acc = ""
    parts = []
    for c in word:
        if c.isalpha():
            cur_chr_type = "A"
        elif c.isdigit():
            cur_chr_type = "D"
        else:
            cur_chr_type = "O"
        if prev_chr_type is None:
            acc = c
        elif prev_chr_type == cur_chr_type:
            acc += c
        else:
            parts.append((acc, prev_chr_type, len(acc)))
            acc = c
        prev_chr_type = cur_chr_type
    parts.append((acc, prev_chr_type, len(acc)))
    return parts


# this is a hack
re_invalid = re.compile(
    r"^("
    r"[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e0-9]{1,3}[a-z]{1,3}"  # except (S or D) + L
    r"|[0-9]+[a-z]{1,2}|[a-z]{1,2}[0-9]+"  # remove m150, 
    r"|[a-z]{1,3}[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e0-9]{1,3}"  # except L + (S or D)
    r"|[02356789@]{1,2}[a-z]+"  # except 5scott
    r"|[a-z0-9]4(ever|life)"  # except a4ever, b4ever
    r"|1[a-z]{1,4}[^u]"  # except 1hateu, 1loveu
    r"|1il(ov|uv).+"  # except 1iloveyou
    r"|[a-z]{3,}[0-9$]+"
    r"|(000)?we?bh(o?st)?)$")

# ignore words in this set
ignore_set = load_l33t_ign()
# words in this set will be treated as l33t and will not detect again.
# to speedup
valid_set = load_l33t_found()


def limit_alpha(word: str):
    """
    word is not composed of pure alphas
    word should have at last one alpha
    word.isdigit() is a speedup for pure digits
    :param word:
    :return:
    """
    return word.isalpha() or word.isdigit() or all([not c.isalpha() for c in word])


def invalid(word: str):
    """
    whether this word can be treated as l33t
    There are many trade-offs, to reject false positives
    :param word:
    :return:
    """
    lower = word.lower()
    wlen = len(word)
    if lower in ignore_set:
        return True
    # length ~ [4, 20]
    if len(word) < 4 or len(word) > 20:
        return True
    # pure alphas, pure digits, or pure others
    if limit_alpha(word):
        return True
    if word.startswith("#1") or word.endswith("#1"):
        return True
    counter = collections.Counter(lower)
    # 5i5i5i5i, o00oo0o
    if len(counter) < 3 or max(counter.values()) >= len(word) / 2:
        return True
    # li1li1li1, o0po0po0p
    if len(counter) == 3 and len(word) >= 6 and max(counter.values()) >= len(word) / 3:
        return True
    # xxx!
    if lower[:-1].isalpha() and lower[-1:] == '!':
        return True
    # xxx4ever
    if 9 > wlen > 5 and lower[-5:] == '4ever' and (lower[:-5].isalpha() or lower[:-5].isdigit()):
        return True
    return re_invalid.search(lower)


class AsciiL33tDetector:

    def __init__(self, multi_word_detector):
        """
        multi_word detector should be instance of my_multiword_detector.py
        :param multi_word_detector: instance of my_multiword_detector.py
        """
        self.multi_word_detector = multi_word_detector

        self.replacements = {
            '/-\\': ['a'],
            "/\\": ['a'],
            "|3": ['b'],
            "|o": ['b'],
            "(": ['c', 'g'],
            "<": ['c'],
            "k": ['c', 'k'],
            "s": ['c', 's'],
            "|)": ['d'],
            "o|": ["d"],
            "|>": ['d'],
            "<|": ["d"],
            "|=": ['f'],
            "ph": ['f', 'ph'],
            "9": ['g'],
            "|-|": ['h'],
            "]-[": ['h'],
            '}-{': ['h'],
            "(-)": ['h'],
            ")-(": ['h'],
            "#": ['h'],
            "l": ['i', 'l'],
            "|": ['i', 'l'],
            "!": ['i'],
            "][": ['i'],
            "i": ['l'],
            "_|": ['j'],
            "|<": ['k'],
            "/<": ['k'],
            "\\<": ['k'],
            "|{": ['k'],
            "|_": ['l'],
            "|v|": ['m'],
            "/\\/\\": ['m'],
            "|'|'|": ['m'],
            "(v)": ['m'],
            "/\\\\": ['m'],
            "/|\\": ['m'],
            '/v\\': ['m'],
            '|\\|': ['n'],
            "/\\/": ['n'],
            "|\\\\|": ['n'],
            "/|/": ['n'],
            "()": ['o'],
            "[]": ['o'],
            "{}": ['o'],
            "|2": ['p', 'r'],
            "|D": ["p"],
            "(,)": ['q'],
            "kw": ['q', 'kw'],
            "|z": ['r'],
            "|?": ['r'],
            "+": ['t'],
            "']['": ['t'],
            "|_|": ['u'],
            "|/": ['v'],
            "\\|": ['v'],
            "\\/": ['v'],
            "/": ['v'],
            "\\/\\/": ['w'],
            "\\|\\|": ['w'],
            "|/|/": ['w'],
            "\\|/": ['w'],
            "\\^/": ['w'],
            "//": ['w'],
            "vv": ['w'],
            "><": ['x'],
            "}{": ['x'],
            "`/": ['y'],
            "'/": ['y'],
            "j": ['y', 'j'],
            "(\\)": ['z'],
            '@': ['a'],
            '8': ['b', 'ate'],
            '3': ['e'],
            '6': ['b', 'g'],
            '1': ['i', 'l'],
            '0': ['o'],
            # '9': ['q'],
            '5': ['s'],
            '7': ['t'],
            '2': ['z', 'too', 'to'],
            '4': ['a', 'for', 'fore'],
            '$': ['s']
        }
        # to speedup match, not necessary
        repl_dict_tree = {}
        for repl, convs in self.replacements.items():
            tmp_d = repl_dict_tree
            for c in repl:
                if c not in tmp_d:
                    tmp_d[c] = {}
                tmp_d = tmp_d[c]
            tmp_d["\x02"] = convs
        self.repl_dict_tree = repl_dict_tree
        self.max_len_repl = len(max(self.replacements, key=lambda x: len(x)))
        # to speedup query
        self.l33t_map = {}
        # dict tree, to speedup detection
        self.dict_l33ts = {}
        # max len of l33t
        self.__min_l33ts = 4
        # min len of l33t
        self.__max_l33ts = 8
        # lower string

    def unleet(self, word: str) -> itertools.product:
        """
        1 may be converted to l and i, therefore at least one unleet word will be found
        this func will find all possible transformations.
        However, here is a hack to reject word with 256+ transformations
        :param word: l33t word
        :return: unleeted list
        """
        unleeted = []
        repl_dtree = self.repl_dict_tree
        i = 0
        while i < len(word):
            max_m = word[i]
            if max_m not in repl_dtree:
                unleeted.append([max_m])
                i += 1
                continue
            add_on = 1
            for t in range(2, self.max_len_repl + 1):

                n_key = word[i:i + t]
                if n_key not in self.replacements:
                    continue
                max_m = n_key
                add_on = t
            if max_m not in self.replacements:
                repl_list = [max_m]
            else:
                repl_list = self.replacements.get(max_m)
            i += add_on
            unleeted.append(repl_list)
        all_num = functools.reduce(lambda x, y: x * y, [len(p) for p in unleeted])
        # a hack, to early reject
        if all_num >= 256:
            return []
        all_possibles = itertools.product(*unleeted)
        return all_possibles

    def find_l33t(self, word: str) -> (bool, str):
        """
        whether a word is l33t or not
        return true if found.
        if you want, you can find all possible unleeted words
        :param word:
        :return: is l33t or not, unleeted word
        """

        unleeted_list = self.unleet(word)
        for unleeted in unleeted_list:
            unleeted = "".join(unleeted)
            count = self.multi_word_detector.get_count(unleeted)
            if count >= self.multi_word_detector.threshold:
                return True, unleeted
                # valid.append((unleeted, count))
        return False, ""

    def detect_l33t(self, pwd: str):
        """
        whether a given password is l33t.
        this is a hack, because I detect whether whole password is a l33t.
        Best way is to detect whether a password contains l33t part.
        this may be optimized later.
        :param pwd:
        :return:
        """
        lower_pwd = pwd.lower()
        if lower_pwd in valid_set and lower_pwd not in ignore_set:
            if lower_pwd not in self.l33t_map:
                self.l33t_map[lower_pwd] = 0
            self.l33t_map[lower_pwd] += 1
        if invalid(pwd):
            return
        is_l33t, leet = self.find_l33t(lower_pwd)
        if is_l33t:
            if lower_pwd not in self.l33t_map:
                self.l33t_map[lower_pwd] = 0
            self.l33t_map[lower_pwd] += 1
            pass
        pass

    def init_l33t(self, training_set, encoding):
        """
        find l33ts from a training set
        :param training_set:
        :param encoding:
        :return:
        """
        if encoding.lower() != 'ascii':
            raise Exception("l33t detector can be used in ASCII-encoded passwords")
        file_input = TrainerFileInput(training_set, encoding)
        num_parsed_so_far = 0
        try:
            for password in file_input.read_password():
                # Print status indicator if needed
                num_parsed_so_far += 1
                if num_parsed_so_far % 1000000 == 0:
                    print(str(num_parsed_so_far // 1000000) + ' Million')
                # pcfg_parser.parse(password)
                self.detect_l33t(password)

        except Exception as msg:
            traceback.print_exc(file=sys.stdout)
            print("Exception: " + str(msg))
            print("Exiting...")
            return
        print(f"init l33t done", file=sys.stderr)
        self.gen_l33t_dtree()
        pass

    def gen_l33t_dtree(self):
        """
        generate a dict tree, to speedup detection of part of l33t in a password
        :return:
        """
        l33ts = sorted(self.l33t_map.keys(), key=lambda x: len(x), reverse=True)
        if len(l33ts) == 0:
            return
        self.__min_l33ts = len(l33ts[-1])
        self.__max_l33ts = len(l33ts[0])
        for l33t in l33ts:
            # early return, a hack
            if len(l33t) < 2 * self.__min_l33ts:
                break
            for i in range(self.__min_l33ts, len(l33t) - self.__min_l33ts + 1):
                left = l33t[:i]
                right = l33t[i:]
                """
                some l33t may be composed of several short l33ts, remove them
                """
                if left in self.l33t_map and self.multi_word_detector.get_count(right) >= 5:
                    del self.l33t_map[l33t]
                    break
                if right in self.l33t_map and self.multi_word_detector.get_count(left) >= 5:
                    del self.l33t_map[l33t]
                    break
        for l33t in self.l33t_map:
            dict_l33t = self.dict_l33ts
            for c in l33t:
                if c not in dict_l33t:
                    dict_l33t[c] = {}
                dict_l33t = dict_l33t[c]
            dict_l33t["\x03"] = True
        pass

    def extract_l33t(self, pwd) -> List[Tuple[int, int, bool]]:
        """
        find the longest match of l33t, using DFS
        :param pwd:  password to be identified
        :return: list of [start_idx, len_of_seg, is_l33t]
        """
        l33t_list = []
        # candidate for a l33t
        a_l33t = ""
        # dict tree for l33ts, to speedup
        dict_l33ts = self.dict_l33ts
        lower_pwd = pwd.lower()
        len_pwd = len(pwd)
        i = 0
        cur_i = i
        len_l33ted = 0
        while i < len_pwd and cur_i < len_pwd:
            c = lower_pwd[cur_i]
            if c in dict_l33ts:
                a_l33t += c
                dict_l33ts = dict_l33ts[c]
                if "\x03" in dict_l33ts:
                    add_a_l33t = ""
                    bak_add_a_l33t = ""
                    for addi in range(cur_i + 1, min(cur_i + self.__max_l33ts - len(a_l33t) + 1, len_pwd)):
                        addc = lower_pwd[addi]
                        if addc not in dict_l33ts:
                            break
                        dict_l33ts = dict_l33ts[addc]
                        add_a_l33t += addc
                        if "\x03" in dict_l33ts:
                            bak_add_a_l33t = add_a_l33t
                        pass
                    if bak_add_a_l33t != "":
                        a_l33t += bak_add_a_l33t
                        cur_i += len(bak_add_a_l33t)
                    # find a l33t
                    len_a_l33t = len(a_l33t)
                    l33t_list.append((cur_i - len_a_l33t + 1, len_a_l33t, True))
                    # if len_l33ted == pwd_len, return, else, add not_l33t parts
                    len_l33ted += len_a_l33t
                    # successfully find a l33t, move forward i
                    i += len_a_l33t
                    cur_i = i
                    # used to find not_l33t
                    a_l33t = ""
                    dict_l33ts = self.dict_l33ts
                cur_i += 1
            else:
                i += 1
                cur_i = i
                a_l33t = ""
                dict_l33ts = self.dict_l33ts
        if len_l33ted == len_pwd:
            return l33t_list
        elif len(l33t_list) == 0:
            return [(0, len_pwd, False)]
        else:
            n_list = set()
            is_l33t_set = set()
            n_list.add(0)
            for i, sl, is_l33t in l33t_list:
                n_list.add(i)
                n_list.add(i + sl)
                is_l33t_set.add(i)
            n_list.add(len_pwd)
            n_list = sorted(n_list)
            n_l33t_list = []
            for n_i, pwd_i in enumerate(n_list[:-1]):
                n_l33t_list.append((pwd_i, n_list[n_i + 1] - pwd_i, pwd_i in is_l33t_set))
            return n_l33t_list
        pass

    def parse(self, password):
        """
        parsing a password, may be a section of password
        :param password:
        :return: section tag, l33ts, masks
        """
        if password in self.l33t_map:
            return [(password, f"A{len(password)}")], [password], [get_mask(password)]

        l33t_list = self.extract_l33t(password)
        if len(l33t_list) == 0:
            return [(password, None)], [], []
        l33t_list = sorted(l33t_list, key=lambda x: x[0])
        section_list = []
        leet_list = []
        mask_list = []
        for idx, len_l33t, is_l33t in l33t_list:
            leet = password[idx:idx + len_l33t]
            if is_l33t:
                lower_leet = leet.lower()
                section_list.append((lower_leet, f"A{len(lower_leet)}"))
                leet_list.append(lower_leet)
                mask = get_mask(leet)
                mask_list.append(mask)
            else:
                section_list.append((leet, None))
        return section_list, leet_list, mask_list

    def parse_sections(self, sections):
        """
        given a sections list, find and tag possible l33ts, and return a new sections list
        :param sections:
        :return:
        """
        parsed_sections = []
        parsed_l33t = []
        parsed_mask = []
        for section, tag in sections:
            if tag is not None:
                parsed_sections.append((section, tag))
                continue
            if len(section) < self.__min_l33ts or limit_alpha(section):
                parsed_sections.append((section, None))
                continue
            section_list, leet_list, mask_list = self.parse(section)
            parsed_sections.extend(section_list)
            parsed_l33t.extend(leet_list)
            parsed_mask.extend(mask_list)
        return parsed_sections, parsed_l33t, parsed_mask
