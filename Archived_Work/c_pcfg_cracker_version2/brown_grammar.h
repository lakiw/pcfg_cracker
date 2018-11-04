#ifndef _BROWN_GRAMMAR_H
#define _BROWN_GRAMMAR_H

#include <algorithm>
#include "pcfg_manager.h"


bool main_load_passphrase(deque <ntGenTopType> *phraseValues, list <pqReplacementType> *baseStructures, deque <
fileInfoType> *fileInfo, pqueueType *pqueue, double probLimit);
int brown_initialize(deque <ntGenTopType> *phraseValues);
int simplified_initialize(deque <ntGenTopType> *phraseValues);
int orderPointers(deque <ntGenTopType> *phraseValues, deque <ppPointerType> *phraseList);
int add_user_dics(deque <ppPointerType> *phraseList, deque <fileInfoType> *fileInfo);
int add_default_dics(deque <ppPointerType> *phraseList);
int load_all_dics(deque <ntGenTopType> *phraseValues);
int load_passphrase_grammar(pqueueType *pqueue, list <pqReplacementType> *baseStructures,deque <ppPointerType> *phraseList,string ruleName, double probLimit);
int read_dic_config(string configName, deque <fileInfoType> *fileInfo);
#endif
