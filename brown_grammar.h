#ifndef _BROWN_GRAMMAR_H
#define _BROWN_GRAMMAR_H

#include "pcfg_manager.h"



int brown_initialize(deque <ntGenTopType> *phraseValues);
int orderPointers(deque <ntGenTopType> *phraseValues, deque <ppPointerType> *phraseList);
int add_user_dics(deque <ppPointerType> *phraseList, deque <fileInfoType> *fileInfo);
int add_default_dics(deque <ppPointerType> *phraseList);
int load_all_dics(deque <ntGenTopType> *phraseValues);

#endif
