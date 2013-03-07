#ifndef _GLOBAL_DEF_H
#define _GLOBAL_DEF_H

#include <string.h>

#define MAXWORDSIZE 18 //Maximum size of a word from the input dictionaries
#define MAXINPUTDIC 10  //Maximum number of user inputed dictionaries
#define CHECKINPUTTIME 5 //Time to check to see if the user wants a status update

//---Note, these are optimized by analyzing letter frequency analysis. Quite honestly I don't remember the dataset I used for that...---//
string alpha = "aeoirlnstmcudbpghyvfkjzxwq";
string digits = "0l29837654";
//string digits = "0123456789";
string special = "!._-*@/+,\\$&!=?'#\")(%^<> ;";

#endif
