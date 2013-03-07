#ifndef _BROWN_GRAMMAR_H
#define _BROWN_GRAMMAR_H

#include "pcfg_manager.h"



int brown_initialize(deque <ntGenTopType> *phraseValues);
int orderPointers(deque <ntGenTopType> *phraseValues, deque <ppPointerType> *phraseList);
int add_user_dics(deque <ppPointerType> *phraseList, deque <fileInfoType> *fileInfo);

#endif
