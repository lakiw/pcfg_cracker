# Welcome to the Probabilistic Context Free Grammar Password Research Project

## Python PCFG Cracker Re-Write Status:
1. Training Program's Core Functionality: Done
2. Training Program's Testing Status:
  1. Windows: Initial tests done
  2. MacOSX: Initial tests done
  3. Linux: Not started
3. Training Program's Documentation Status: TBD
4. PCFG Manager Core Functionality: In progress
5. Core PCFG and "Next" algorithm: Done
6. Reading in grammar and parsing it correctly: In progres

Long story short, it doesn't work yet but progress is being made!!


## Overview

This is a major area of research for me, and something that I truly believe in. For years, we have been applying probability models to help speed up brute force attacks, (aka letter frequency analysis and Markov Models). At the same time though, our approach to dictionary based attacks has been fairly ad-hoc. John the Ripper’s default, (and single mode), rules while built based on their creators experiences with cracking passwords, are still extremely subjective. For example I’ve found very few passwords in my cracking attacks that were created by reversing an input dictionary word. Cain and Able, while a great product, probably has the most bizarre rule selection in that it focuses on capitalization mangling at the expense of just about everything else, (though it will also add two numbers to the end of words and replace letters with numbers). AccessData orders their default rule set not on how effective the rules are but by how large the search space is for each rule. This is not a slam on these approaches but I do think that as passwords become stronger and stronger, (either through user training or password creation policies), we need to improve how we generate and use word mangling rules.

The main goal of this project is to see if we can assign probabilities to different word mangling rules and then generate password guesses in probability order. There are several advantages I feel this approach offers us.  First, by designing a way to measure the probability of word mangling rules, we can quickly generate new rules by training our password cracker on known passwords that we feel are similar to the target. This way, we will be able to train our cracker to go against English speakers, Russian speakers, passwords created for social networking sites, passwords created with a strong password creation strategy, etc. If you’ve ever spent time editing a John the Ripper config file, you know that ability to automatically generate rules is very nice. Second, it allows us to more effectively target strong passwords. Just like with letter frequency analysis, the letter “z” may be uncommon, but the string “aaaaz” may be more probable than the string “dfttp” since it takes into account the probability of all the letters. Likewise, by using a probability model of how passwords are created, we can better balance the order of how multiple word mangling rules are applied to password guesses. For example, the guess “$$password63” may be more probable than “!*password12”. Not only does this technique apply to word mangling rules, but also to the input words themselves. We know that the word “password” is more probable than the word “zebra”. Using a probabilistic approach gives us a framework to make use of this knowledge.

## Special Thanks and Acknowledgements:

The original version of the program was written Bill Glodek, another graduate student at Florida State University. The original idea for using probabilistic context free grammars to represent how people create passwords was Dr. Sudhir Aggarwal’s and Professor Breno de Medeiros’s. Basically I was lucky enough to come in at the right time to assist with the start of the program and help carry it on once Bill graduated.


## Code Layout

I'm currently in the process of restructing this git repo, but for now you can find the semi-woring code under "traditional_pcfg_cracker". I broke a lot of things when adding passphrase support so I'll probably upload an older more stable version at some point. I created a directory specifically for passphrase cracking where I expect I'll create a seperate branch of the code tailored for that use case. Finally on the defensive side, the honeyword geeration code is available under the honeywords directory.