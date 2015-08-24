#ifndef _STANDARD_GRAMMAR_H
#define _STANDARD_GRAMMAR_H

#include "pcfg_manager.h"

bool processBasicStruct(pqueueType *pqueue,list <pqReplacementType> *baseStructures, ntContainerType **dicWords,  ntContainerType **numWords, ntContainerType **specialWords, ntContainerType **capWords, ntContainerType **keyboardWords, string ruleName, double probLimit);

//--Process Input Dictionaries---------//
bool processDic(string *inputDicFileName,bool *inputDicExists, double *inputDicProb, ntContainerType **dicWords,bool removeUpper, bool removeSpecial, bool removeDigits);

//--Proces Probabilities from a File------//
bool processProbFromFile(ntContainerType **numWords, string filePath,int type);  //processes the number probabilities

//-------Responsible for building brute force dictionaries-----//
bool buildBruteForce(ntContainerType **specialWords, ntContainerType **numWords);

#endif
