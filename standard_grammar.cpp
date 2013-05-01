#include "standard_grammar.h"

//---Note, these are optimized by analyzing letter frequency analysis. Quite honestly I don't remember the dataset I used for that...---//
string alpha = "aeoirlnstmcudbpghyvfkjzxwq";
string digits = "0l29837654";
//string digits = "0123456789";
string special = "!._-*@/+,\\$&!=?'#\")(%^<> ;";

//--Used for storing Brute Force Data------------//
list <unsigned long> allDigits[MAXWORDSIZE+1];  //used to store all the digit values in dictionary order
list <unsigned long> allSpecial[MAXWORDSIZE+1]; //used to store all the special values in dictioanry order

///////////////////////////////////////////////////
// Compares two dictionary words
// Used for sorting the lists
bool compareDicWords(mainDicHolderType first, mainDicHolderType second) {
  int compareValue = first.word.compare(second.word);
  if (compareValue<0) {
    return true;
  }
  else if (compareValue>0) {
    return false;
  }
  else if (first.probability>second.probability) {
    return true;
  }
  return false;
}


////////////////////////////////////////////////////
// Simply detects duplicate dictionary words
// Used for cleaning up an input dictionary and removing
// duplicates from multiple input dictionaries
bool duplicateDicWords(mainDicHolderType first, mainDicHolderType second) {
  if (first.word.compare(second.word)==0) {
    return true;
  }
  return false;
}


bool processDic(string *inputDicFileName, bool *inputDicExists, double *inputDicProb,ntContainerType **dicWords, bool removeUpper, bool removeSpecial, bool removeDigits) {
  ifstream inputFile;
  bool atLeastOneDic=false;  //just checks to make sure at least one input dictionary was specified
  mainDicHolderType tempWord;  
  list <mainDicHolderType> allTheWords;
  size_t curPos;
  int numWords[MAXINPUTDIC][MAXWORDSIZE+1];
  double wordProb[MAXINPUTDIC][MAXWORDSIZE+1];
  ntContainerType *tempContainer;  
  ntContainerType *curContainer; 
  bool goodWord=true;

  //-initilize the variables--//
  for (int i=0;i<MAXINPUTDIC;i++) {
    for (int j=0; j<=MAXWORDSIZE;j++) {
      numWords[i][j]=0;
    }
  }
  //-normalize the probability of all the dictionaries so they add up to 1.0----//
  double normalizedProb=0.0;
  for (int i=0; i<MAXINPUTDIC;i++) { //for every input dictionary
    if (inputDicExists[i]) {
      normalizedProb=normalizedProb + inputDicProb[i];
    }
  }
  for (int i=0; i<MAXINPUTDIC;i++) { //now modify the probability
    if (inputDicExists[i]) {
      inputDicProb[i]=inputDicProb[i]/normalizedProb;
    }
  }
  for (int i=0; i<MAXINPUTDIC;i++) {  //for every input dictionary
    if (inputDicExists[i]) {
      inputFile.open(inputDicFileName[i].c_str());
      if (!inputFile.is_open()) {
        std::cerr << "Could not open file " << inputDicFileName[i] << endl;
        return false;
      }
      tempWord.category=i;
      while (!inputFile.eof()) {
        std::getline(inputFile,tempWord.word);
        curPos=tempWord.word.find("\r");  //remove carrige returns
        if (curPos!=string::npos) {
          tempWord.word.resize(curPos);
        }
        tempWord.word_size=findSize(tempWord.word);
        if ((tempWord.word_size>0)&&(tempWord.word_size<=MAXWORDSIZE)) {
          if ((removeUpper)||(removeSpecial)||(removeDigits)) {
            goodWord=true;
            if (removeUpper) {   //check to see if there are any uppercase letters
              for (int j=0;j<tempWord.word.size();j++) {
                if (((int)tempWord.word[j]>64)&&((int)tempWord.word[j]<91)) {
                  goodWord=false;
                  break;
                }
              }
            }
            if (removeSpecial) { //check to see if there are any special characters in the word
              for (int j=0;j<tempWord.word.size();j++) {
                if (((int)tempWord.word[j]<48)||(((int)tempWord.word[j]>57)&&((int)tempWord.word[j]<65))||(((int)tempWord.word[j]>90)&&((int)tempWord.word[j]<97))||(((int)tempWord.word[j]>122)&&((int)tempWord.word[j]<127))) {
                  goodWord=false;
                  break;
                }
              }
            }
            if (removeDigits) {
              for (int j=0;j<tempWord.word.size();j++) {
                if (((int)tempWord.word[j]>47)&&((int)tempWord.word[j]<58)) {
                  goodWord=false;
                  break;
                }
              }
            }
            if (goodWord) {
              allTheWords.push_front(tempWord);
              numWords[i][tempWord.word_size]++;
            }
            else {
//              cout <<"bad word = " << tempWord.word << endl;
            }
          } 
          else {
            allTheWords.push_front(tempWord);
            numWords[i][tempWord.word_size]++;
          }
        }
      }
      atLeastOneDic=true;
      inputFile.close();
    }
  }
  if (!atLeastOneDic) {
    return false;
  }
  //--Calculate probabilities --//
  for (int i=0; i<MAXINPUTDIC;i++) {
    for (int j=0; j<=MAXWORDSIZE;j++) {
      if (numWords[i][j]==0) {
        wordProb[i][j]=0;
      }
      else {
        wordProb[i][j]= inputDicProb[i] * (1.0/numWords[i][j]);
      }
    }
  }
  list <mainDicHolderType>::iterator it;
  for (it=allTheWords.begin();it!=allTheWords.end();++it) {
    (*it).probability = wordProb[(*it).category][(*it).word_size]; 
  }
  
  allTheWords.sort(compareDicWords);
  allTheWords.unique(duplicateDicWords);

  //------Now divide the words into their own ntStructures-------//
  for (int i=0;i<=MAXWORDSIZE;i++) {
    dicWords[i]=NULL;
    for (int j=0;j<MAXINPUTDIC;j++) {
      if (wordProb[j][i]!=0) {
        tempContainer = new ntContainerType;
        tempContainer->next=NULL;
        tempContainer->prev=NULL;
        tempContainer->isBruteForce=false;
        tempContainer->probability=wordProb[j][i];
        tempContainer->replaceRule=0;
        tempContainer->rainbowCategory=3;
        tempContainer->rainbowLength=i;
        if (dicWords[i]==NULL) {
          dicWords[i]= tempContainer;
        }
        else if (dicWords[i]->probability<tempContainer->probability) {
          tempContainer->next = dicWords[i];
          dicWords[i]->prev=tempContainer;
          dicWords[i]=tempContainer;
        }
        else {
          curContainer=dicWords[i];
          while ((curContainer->next!=NULL)&&(curContainer->next->probability>tempContainer->probability)) {
            curContainer=curContainer->next;
          }
          if (tempContainer->probability!=curContainer->probability) {
            tempContainer->next=curContainer->next;
            if (curContainer->next!=NULL) {
              curContainer->next->prev=tempContainer;
            }
            tempContainer->prev=curContainer;
            curContainer->next=tempContainer;
          }
        }
      }
    }
  }
  
  //faster than resorting the words again to sort them in probability order, since there is usually only one or two dictionaries 
  for (it=allTheWords.begin();it!=allTheWords.end();++it) {
    tempContainer=dicWords[(*it).word_size];
    while ((tempContainer!=NULL)&&(tempContainer->probability!=(*it).probability)) {
      tempContainer=tempContainer->next;
    }
    if (tempContainer==NULL) {
      std::cerr << "Error with processing input dictionary\n";  
      std::cerr << "Word " <<(*it).word << " prob " <<(*it).probability << endl;
      return false;
    }
    tempContainer->word.push_back((*it).word);
  }

  //--Used for precomputation of rules --//
  for (int i=1;i<=MAXWORDSIZE;i++) {
    tempContainer=dicWords[i];
    unsigned short rIndex=0;
    while (tempContainer!=NULL) {
      tempContainer->rainbowIndex=rIndex;
      rIndex++;
      tempContainer=tempContainer->next;
    }
  }

  return true;
}



bool processProbFromFile(ntContainerType **mainContainer,string fileDir, int type) {  //processes the number probabilities
  bool atLeastOneValue=false;
  ifstream inputFile;
  list <string>::iterator it;  
  char fileName[256];
  ntContainerType * curContainer;
  string inputLine;
  size_t marker;
  double prob;

  for (int i=1; i<=MAXWORDSIZE;i++) {
    sprintf(fileName,"%s%i.txt",fileDir.c_str(),i);
    inputFile.open(fileName);
    if (inputFile.is_open()) { //a file exists for that string length
      curContainer=new ntContainerType;
      curContainer->isBruteForce=false;
      curContainer->next=NULL;
      curContainer->prev=NULL;
      if (type==0) { //capitalization
        curContainer->replaceRule=1; //Default, capitalization
      }
      else {  //not a capitalization
        curContainer->replaceRule=0;
      }
      mainContainer[i]=curContainer;
      mainContainer[i]->probability=0;
      while (!inputFile.eof()) {
        getline(inputFile,inputLine);
        marker=inputLine.find("\t");
        if (marker!=string::npos) {
          prob=atof(inputLine.substr(marker+1,inputLine.size()).c_str());
          if ((curContainer->probability==0)||(curContainer->probability==prob)) {
            curContainer->probability=prob;
            curContainer->word.push_back(inputLine.substr(0,marker));
            if (type==0) { //--Optimization for speed if the only value in the container is all lowercase mangling----//
              if (curContainer->word.size()>1) {
                curContainer->replaceRule=1; // do word mangling rules
              }
              else if (inputLine.substr(0,marker).find("U")==string::npos) { //all lowercase
                curContainer->replaceRule=2;
              }
            } 
          }
          else {
            curContainer->next=new ntContainerType;
            curContainer->next->prev=curContainer;
            curContainer=curContainer->next;
            curContainer->next=NULL;
            curContainer->isBruteForce=false;
            if (type==0) { // capitalization
              if (inputLine.substr(0,marker).find("U")==string::npos) { //all lowercase
                curContainer->replaceRule=2;
              }
              else { //contains an uppercase character
                curContainer->replaceRule=1;
              }
            }
            else {  //non capitalization rule
              curContainer->replaceRule=0;
            }
            curContainer->probability=prob;
            curContainer->word.push_back(inputLine.substr(0,marker));
          }
        }

      }
      atLeastOneValue=true; 
      inputFile.close();         
    }
    else {
      mainContainer[i]=NULL; 
    }
  }
  if (!atLeastOneValue) {
    std::cerr << "Error trying to open the probability values from the training set\n";
    std::cerr << "The file was " << fileName << endl;
    return false;
  }
  //------------------Now read in the probability for values that were not in the training set---------------//
  sprintf(fileName,"%sNotFound.txt",fileDir.c_str());
  inputFile.open(fileName);
  if (!inputFile.is_open()) {
    std::cerr << "Error, could not open the probability smoothing file " << fileName <<"\n";
    return false;
  }
  getline(inputFile,inputLine);
  int curPos=1;
  while (!inputFile.eof()) {
    marker=inputLine.rfind("\t");
    if (marker!=string::npos) {
      prob = atof(inputLine.substr(marker+1,inputLine.size()).c_str());
      if (prob!=0) {
        if (mainContainer[curPos]==NULL) { 
          curContainer=new ntContainerType;
          mainContainer[curPos]=curContainer;
        }
        else {
          curContainer=mainContainer[curPos];          
          while (curContainer->next!=NULL) {
            curContainer=curContainer->next;
          }
          curContainer->next =new ntContainerType;
          curContainer->next->prev = curContainer;
          curContainer=curContainer->next;
        }
        curContainer->next=NULL;
        curContainer->isBruteForce=true;
        curContainer->bruteForceType=type;
        marker=inputLine.find("\t");
        curContainer->bruteForceSize=curPos;
        if (type==0) {
          curContainer->replaceRule=0;
        }
        else {
          curContainer->replaceRule=1;
        }
        curContainer->probability=prob;
        string tempHolder;
        tempHolder.append(atoi(inputLine.substr(0,marker).c_str()),'0');
        curContainer->word.push_back(tempHolder);
      }
    }
    getline(inputFile,inputLine);
    curPos++;
  }
  //--Now apply the precomute info to the structures--------//
  for (int i=1;i<=MAXWORDSIZE;i++) {
    unsigned short rIndex=0;
    curContainer=mainContainer[i];
    while (curContainer!=NULL) {
      curContainer->rainbowCategory=type;
      curContainer->rainbowLength=i;
      curContainer->rainbowIndex=rIndex;
      rIndex++;
      curContainer=curContainer->next;
    }
  }
  
  return true;
}


bool processBasicStruct(pqueueType *pqueue, list <pqReplacementType> *baseStructures, ntContainerType **dicWords, ntContainerType **numWords, ntContainerType **specialWords, ntContainerType **capWords, ntContainerType **keyboardWords, string ruleName, double probLimit) {
  ifstream inputFile;
  string inputLine;
  size_t marker;
  double prob;
  int valueLen;
  pqReplacementType inputValue;
  char pastCase='!';
  int curSize=0;
  bool badInput=false;
  #ifdef _WIN32
  inputFile.open(string(".\\Rules\\"+ruleName+"\\Grammar\\Grammar.txt").c_str());
  #else
  inputFile.open(string("./Rules/"+ruleName+"/Grammar/Grammar.txt").c_str());
  #endif
  
  if (!inputFile.is_open()) {
    std::cerr << "Could not open the grammar file\n";
    return false;
  }
  getline(inputFile,inputLine);
  while (!inputFile.eof()) {
    badInput=false;
    marker=inputLine.find("\t");
    if (marker!=string::npos) {
      prob=atof(inputLine.substr(marker+1,inputLine.size()).c_str());
      inputLine.resize(marker);
      inputValue.probability=prob;
      inputValue.base_probability=prob;
      pastCase='!';
      curSize=0;
      for (int i=0;i<inputLine.size();i++) {
        if (curSize==MAXWORDSIZE) {
          badInput=true;
          break;
        }
        if (pastCase=='!') { 
          pastCase=inputLine[i];
          curSize=1;
        }
        else if (pastCase==inputLine[i]) {
          curSize++;
        }
        else {
          if (pastCase=='L') {
            if (dicWords[curSize]==NULL) {
              badInput=true;
              break;
            }
            inputValue.replacement.push_back(capWords[curSize]);
            inputValue.probability=inputValue.probability*capWords[curSize]->probability;
            inputValue.replacement.push_back(dicWords[curSize]);
            inputValue.probability=inputValue.probability*dicWords[curSize]->probability;
          }
          else if (pastCase=='D') {
            if ((numWords[curSize]==NULL)||(capWords[curSize]==NULL)) {
              badInput=true;
              break;
            }
            inputValue.replacement.push_back(numWords[curSize]);
            inputValue.probability=inputValue.probability*numWords[curSize]->probability;
          }
          else if (pastCase=='S') {
            if (specialWords[curSize]==NULL) {
              badInput=true;
              break;
            }
            inputValue.replacement.push_back(specialWords[curSize]);
            inputValue.probability=inputValue.probability*specialWords[curSize]->probability;
          }
          else if (pastCase=='K') {
            if (keyboardWords[1]==NULL) {
              badInput=true;
              break;
            }
            inputValue.replacement.push_back(keyboardWords[1]);
            inputValue.probability=inputValue.probability*keyboardWords[1]->probability;
          }
          else {
            std::cerr << "WTF Weird Error Occured\n";
            return false;
          }
          curSize=1;
          pastCase=inputLine[i];
        }
      }
      if (badInput==true) { //NOOP
      }
      else if (pastCase=='L') {
        if ((curSize>=MAXWORDSIZE)||(dicWords[curSize]==NULL)||(capWords[curSize]==NULL)) {
          badInput=true;
        }
        else {
          inputValue.replacement.push_back(capWords[curSize]);
          inputValue.probability=inputValue.probability*capWords[curSize]->probability;
          inputValue.replacement.push_back(dicWords[curSize]);
          inputValue.probability=inputValue.probability*dicWords[curSize]->probability;
        }
      }
      else if (pastCase=='D') {
        if ((curSize>=MAXWORDSIZE)||(numWords[curSize]==NULL)) {
          badInput=true;
        }
        else {
          inputValue.replacement.push_back(numWords[curSize]);
          inputValue.probability=inputValue.probability*numWords[curSize]->probability;
        }
      }
      else if (pastCase=='S') {
        if ((curSize>=MAXWORDSIZE)||(specialWords[curSize]==NULL)) {
          badInput=true;
        }
        else {
          inputValue.replacement.push_back(specialWords[curSize]);
          inputValue.probability=inputValue.probability*specialWords[curSize]->probability;
        }
      }
      else if (pastCase=='K') {
        if (keyboardWords[1]==NULL) {
          badInput=true;
        }
        else {
          inputValue.replacement.push_back(keyboardWords[1]);
          inputValue.probability=inputValue.probability*keyboardWords[1]->probability;
        }
      }
      if (!badInput) {
        if (inputValue.probability==0) {
          std::cerr << "Error, we are getting some values with 0 probability\n";
          return false;
        }
        if (inputValue.probability >=probLimit) {
          pqueue->push(inputValue);
          baseStructures->push_back(inputValue);
        }
      }
      inputValue.probability=0;
      inputValue.replacement.clear();      
    }
    getline(inputFile,inputLine);
  } 


  inputFile.close(); 
  return true;
}


bool calculateBrutePos(string input, string *charset,unsigned long *returnValue) {
  int len = input.length();
  int charSize=charset->length();
  size_t charPos;
  *returnValue=0;
  for (int i=0;i<len;i++) {
    charPos = charset->find(input.at(i));
    if (charPos==string::npos) {
//      cout << "error parsing the rules values for brute force: "<< input << " pos:" << i << " char:" << input.at(i)<< " charset:" << *charset <<"\n";
      return false;
    }
    (*returnValue)=(*returnValue) + (charPos * pow(charSize,i));
  }
  return true;
}

bool buildBruteForce(ntContainerType **specialWords, ntContainerType **numWords) {
  //--First create a list of all the sorted digits and special characters, to prevent duplicate guesses from being generated-------//
  for (int i=1;i<MAXWORDSIZE+1;i++) {
    ntContainerType *tempContainer = specialWords[i];
    unsigned long pushValue;
    while (tempContainer!=NULL) {
      if (!tempContainer->isBruteForce) {
        for (list<string>::iterator it=tempContainer->word.begin();it!=tempContainer->word.end();++it) {
          if (calculateBrutePos((*it),&special,&pushValue)) {
            allSpecial[i].push_back(pushValue);
          }
        }
      }
      tempContainer=tempContainer->next;
    }
    tempContainer=numWords[i];
    while (tempContainer!=NULL) {
      if (!tempContainer->isBruteForce) {
        for (list<string>::iterator it=tempContainer->word.begin();it!=tempContainer->word.end();++it) {
          if (calculateBrutePos((*it),&digits,&pushValue)) {
            allDigits[i].push_back(pushValue);
          }
        }
      }
      tempContainer=tempContainer->next;
    }
    allDigits[i].sort();
    allSpecial[i].sort();
  }
  return true;
}
