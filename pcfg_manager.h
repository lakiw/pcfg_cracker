//////////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  PCFG Password Cracker
//  --Probabilistic Context Free Grammar (PCFG) Password Guessing Program
//
//  Written by Matt Weir
//  Backend algorithm developed by Matt Weir, Sudhir Aggarwal, and Breno de Medeiros
//  Special thanks to Bill Glodek for work on an earlier version
//  Special thanks to the National Institute of Justice and the NW3C for support with the initial reasearch
//  Special thanks to the John the Ripper community where some of the code was copied from
//  Huge thanks to Florida State University's ECIT lab where this was developed
//  And the list goes on and on... And thank you whoever is reading this. Be good!
//
//  Copyright (C) 2013  Matt Weir, Sudhir Aggarwal, and Breno de Medeiros at Florida State University.
//
//  This program is free software; you can redistribute it and/or
//  modify it under the terms of the GNU General Public License
//  as published by the Free Software Foundation; either version 2
//  of the License, or (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program; if not, write to the Free Software
//  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
//   
//
//   pcfg_manager.h
//
//


#ifndef _PCFG_MANAGER_H
#define _PCFG_MANAGER_H

#include <sys/types.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <signal.h>
#include <math.h>
#include <iostream>
#include <iomanip>
#include <fstream>
#include <deque>
#include <list>
#include <queue>
#include <iterator>

using namespace std;

#define MAXWORDSIZE 18 //Maximum size of a word from the input dictionaries
#define MAXINPUTDIC 10  //Maximum number of user inputed dictionaries
#define CHECKINPUTTIME 5 //Time to check to see if the user wants a status update

//---Note, these are optimized by analyzing letter frequency analysis. Quite honestly I don't remember the dataset I used for that...---//
string alpha = "aeoirlnstmcudbpghyvfkjzxwq";
string digits = "0l29837654";
//string digits = "0123456789";
string special = "!._-*@/+,\\$&!=?'#\")(%^<> ;";

///////////////////////////////////////////
//Used for initially parsing the dictionary words
typedef struct mainDicHolderStruct {
  string word;
  int category;
  double probability;
  short word_size;
}mainDicHolderType;


///////////////////////////////////////////
//Non-Terminal Container Struct
//Holds all the base information used for non-terminal to terminal replacements
typedef struct ntContainerStruct {
  list <string> word;           //the replacement group. Can be a word, a number or a special character set
  double probability;    //the probability of this group
  short replaceRule;            //0=final terminal; 1=capitalization rule; 2=all_lower(optimization); 3=replacement; 4=replacement(blank);
  ntContainerStruct *next;        //The next highest probable replacement for this type
  ntContainerStruct *prev;
  bool isBruteForce;           //false = no, true=yes do brute force
  short bruteForceType;          //1=digits, 2=special, 3=alpha characters
  short bruteForceSize;          //How long a string of characters/digits/etc it should brute force
  unsigned short rainbowCategory; //0=capitalization,1=number, 2=special, 3=dictionary,4=keyboard for rule precomputation
  unsigned short rainbowLength;	//the length, used for precomputing rules
  unsigned short rainbowIndex;		//the particular index of this node, used for precomputing rules
}ntContainerType;

//////////////////////////////////////////
//PriorityQueue Replacement Type
//Basically a pointer
typedef struct pqReplacementStruct {
  deque <ntContainerStruct *> replacement;    //the actual containers and mangling rules to apply
  double probability;       //the preterminal probability
  double base_probability;  //the probability of the base structure
  int pivotPoint;           //not used anymore, keeping it in for some comparison tests
}pqReplacementType;



///////////////////////////////////////////
//Non-Terminal Generic Top Container
//Basically a container that holds generic non-terminal types
//Used to abstract away a lot of the hardcoded logic previously, (aka LDS non-terminals)
//Hopefully will allow the easier inclusion of new types of non-terminals
typedef struct ntGenTopStruct {
  

}ntGenTopType;


#endif

