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
#include <ctype.h>

#include "global_def.h"

using namespace std;


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
}pqReplacementType;


////////////////////////////////////////////////////
//Used to sort the probability queue
class queueOrder {
  public:
    queueOrder() {
    }
  bool operator() (const pqReplacementType& lhs, const pqReplacementType& rhs) const{
    return (lhs.probability<rhs.probability);
  }
};

///////////////////////////////////////////
//Main priority queue definition
typedef priority_queue <pqReplacementType,vector <pqReplacementType>,queueOrder> pqueueType;


/////////////////////////////////////////
//Holds info about a dictionary
typedef struct fileInfoStruct {
  int id;   //The id for this file, used to process info from the user's command line
  string type; //The grammar type. Aka L = letters, D = digits.
  string filename; //the file where the actual dictioanry is stored;
  double probability;     //The total probability of the dictionary. Default is 100%, eg 1.0.
  bool isUserDic;  //Simply a flag to print out an error if a user dic does not load vs a defalt dic
}fileInfoType;

///////////////////////////////////////////
//Non-Terminal Generic Top Container
//Basically a container that holds generic non-terminal types
//Used to abstract away a lot of the hardcoded logic previously, (aka LDS non-terminals)
//Hopefully will allow the easier inclusion of new types of non-terminals
typedef struct ntGenTopStruct {
  deque <string> names;  //the names as seen in the grammar. Aka L = letters, D = Digits. Can have multiple names if some replacements go to the same terminals.
  deque <fileInfoType> fileInfo;  //Information about the various dictioanries;
  deque <ntContainerType> data;  //The actual dictionaries
    

}ntGenTopType;


//////////////////////////////////////////////
//Eventually thrown into a list to have an ordered pointer to every possible
//replacement type based on the string info
//Makes loading a new session faster
typedef struct ppPointerStruct {
  string name;
  ntGenTopType * pointer;
}ppPointerType;

short findSize(string input);  //used to find the length of a possible non-ascii string, used because MACOSX had problems with wstring

#endif

