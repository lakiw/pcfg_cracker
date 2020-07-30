"""
This is to get the segments of a password.
"""
from collections import defaultdict
from typing import TextIO

from lib_trainer.alpha_detection import alpha_detection
from lib_trainer.digit_detection import digit_detection
from lib_trainer.keyboard_walk import detect_keyboard_walk
from lib_trainer.multiword_detector import MultiWordDetector
from lib_trainer.context_sensitive_detection import context_sensitive_detection
from lib_trainer.my_context_detection import detect_context_sections
from lib_trainer.my_leet_detector import AsciiL33tDetector
from lib_trainer.my_multiword_detector import MyMultiWordDetector
from lib_trainer.other_detection import other_detection
from lib_trainer.year_detection import year_detection


def v41seg(training: TextIO, test_set: TextIO, save2: TextIO):
    if not save2.writable():
        raise Exception(f"{save2.name} is not writable")

    multiword_detector = MultiWordDetector()
    for password in training:
        password = password.strip("\r\n")
        multiword_detector.train(password)
    training.close()

    pwd_counter = defaultdict(int)
    for password in test_set:
        password = password.strip("\r\n")
        pwd_counter[password] += 1
    test_set.close()

    for password, num in pwd_counter.items():
        section_list, found_walks = detect_keyboard_walk(password)
        _ = year_detection(section_list)
        _ = context_sensitive_detection(section_list)
        _, _ = alpha_detection(section_list, multiword_detector)
        _ = digit_detection(section_list)
        _ = other_detection(section_list)
        info = [password, f"{num}"]
        npass = ""
        for sec, tag in section_list:
            npass += sec
            info.append(sec)
            info.append(tag)
        if password.lower() != npass.lower():
            raise Exception("neq")
        print("\t".join(info), end="\n", file=save2)
    pass


def l33tseg(training: TextIO, test_set: TextIO, save2: TextIO):
    if not save2.writable() or not training.seekable():
        raise Exception(f"{save2.name} is not writable")

    multiword_detector = MyMultiWordDetector()
    for password in training:
        password = password.strip("\r\n")
        multiword_detector.train(password)
    training.close()
    l33t_detector = AsciiL33tDetector(multiword_detector)
    l33t_detector.init_l33t(training.name, "ascii")
    pwd_counter = defaultdict(int)
    for password in test_set:
        password = password.strip("\r\n")
        pwd_counter[password] += 1
    test_set.close()
    for password, num in pwd_counter.items():
        section_list = [(password, None)]
        _ = year_detection(section_list)
        section_list, _ = detect_context_sections(section_list)
        section_list, _, _ = l33t_detector.parse_sections(section_list)
        section_list, _, _, _, _ = multiword_detector.parse_sections(section_list)
        info = [password, f"{num}"]
        npass = ""
        for sec, tag in section_list:
            npass += sec
            info.append(sec)
            info.append(tag)
        if password.lower() != npass.lower():
            # Note that we'll not lower X
            # therefore, the best way is to compare password.lower
            # with npass.lower
            print(password)
            print(section_list)
            raise Exception("neq")
        print("\t".join(info), end="\n", file=save2)
    pass


def main():
    pass


if __name__ == '__main__':
    main()
