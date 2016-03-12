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
//   Contact Info: weir@cs.fsu.edu
//
//   pcfg_manager.cpp
//

#include "pcfg_manager.h"
#include "tty.h"
#include "brown_grammar.h"
#include "standard_grammar.h"


//-----------Crash restore specific variables-----------------//
fstream crashFile;  //the crashfile to save the current status to
int saveLoc;  //the position in the crashfile to save the current location to, (saves time so we don't have to rewrite the entire thing
//-----------End Crash restore specific varibles-------------//

//----------------Variables Made Global for User Status Reports While Running--------------------//
pqReplacementType curQueueItem;  //The current item being worked on
//--End variables----------------------//


//---Debugging values, DO NOT USE IN ACTUAL WORK-------------//
unsigned long long totalGuesses=0;
int debugPQSize;
double debugMinProbLimit;

//--End debugging values--------------------------------------//


//----Checks status and exits gracefully if cntl-c is triggered----------//
void sig_alrm(int signo)
{
  if (signo==SIGALRM) {
     int c = tty_getchar();
     if (c>=0) {
       std::cerr << "Current PQueue Size = " << debugPQSize << endl;
       std::cerr << "Current minimum allowed probability in PQueue is = " << debugMinProbLimit << endl;
       std::cerr << "Currently trying guesses from: ";
       for (int i=0;i<curQueueItem.replacement.size();i++) {
          list <string>::iterator it;
          list <string>::iterator it2;
          if (!curQueueItem.replacement[i]->isBruteForce) { //the section is not a brute force replacement
            it = curQueueItem.replacement[i]->word.begin();
            if ((curQueueItem.replacement[i]->replaceRule==1)||(curQueueItem.replacement[i]->replaceRule==2)) { //it's a capitalization rule
              it2 = curQueueItem.replacement[i+1]->word.begin();
              for (int j=0;j<it->size();j++) {
                if (it->at(j)=='L') {
                  std::cerr << it2->at(j);
                }
                else {
                  std::cerr << (char)toupper(it2->at(j));
                }
              }
              i++;
            }
            else {
              std::cerr << *it;
            }
          }
          else { //--Is brute force-----//
            if (curQueueItem.replacement[i]->bruteForceType==1) { //digits
              std::cerr << "<Brute Digits:" << curQueueItem.replacement[i]->bruteForceSize <<">";
            }
            else if (curQueueItem.replacement[i]->bruteForceType==2) { //special
              std::cerr << "<Brute Special:" << curQueueItem.replacement[i]->bruteForceSize <<">";
            }
            else {
              std::cerr << "<Brute Alpha:" << curQueueItem.replacement[i]->bruteForceSize <<">";
            }
          }
        }
        std::cerr << "\t to \t";
        for (int i=0;i<curQueueItem.replacement.size();i++) {
          list <string>::iterator it;
          list <string>::iterator it2;
          if (!curQueueItem.replacement[i]->isBruteForce) { //the section is not a brute force replacement
            it = curQueueItem.replacement[i]->word.end();
            it--;
            if ((curQueueItem.replacement[i]->replaceRule==1)||(curQueueItem.replacement[i]->replaceRule==2)) { //it's a capitalization rule
              it2 = curQueueItem.replacement[i+1]->word.end();
              it2--;
              for (int j=0;j<it->size();j++) {
                if (it->at(j)=='L') {
                  std::cerr << it2->at(j);
                }
                else {
                  std::cerr << (char)toupper(it2->at(j));
                }
              }
              i++;
            }
            else {
              std::cerr << *it;
            }
          }
          else { //--Is brute force-----// 
            if (curQueueItem.replacement[i]->bruteForceType==1) { //digits
              std::cerr << "<Brute Digits:" << curQueueItem.replacement[i]->bruteForceSize <<">";
            }
            else if (curQueueItem.replacement[i]->bruteForceType==2) { //special
              std::cerr << "<Brute Special:" << curQueueItem.replacement[i]->bruteForceSize <<">";
            }
            else {
              std::cerr << "<Brute Alpha:" << curQueueItem.replacement[i]->bruteForceSize <<">";
            }
          }
        }
        std::cerr << endl;
        std::cerr << "Current Probability: "<< curQueueItem.probability << endl;
     }  

     struct itimerval tout_val;

     tout_val.it_interval.tv_sec = 0;
     tout_val.it_interval.tv_usec = 0;
     tout_val.it_value.tv_sec = CHECKINPUTTIME;  //check for status output every 10 seconds
     tout_val.it_value.tv_usec = 0;
     setitimer(ITIMER_REAL, &tout_val,0);
  }
  else { //time to exit
    std::cerr << "exiting\n";
    std::cerr << "Current probability of guesses is " << curQueueItem.probability << endl;
    crashFile.seekg(saveLoc);
    crashFile << fixed << curQueueItem.probability;
    crashFile.close();
    exit(0);
  }
}

bool generateGuesses(pqueueType *pqueue, list <pqReplacementType> *baseStructures, long long maxGuesses, double probLimit, long maxPQueueSize);
bool generateRules(pqueueType *pqueue, list <pqReplacementType> *baseStructures, long long maxGuesses, double probLimit, long maxPQueueSize);
int createTerminal(pqReplacementType *curQueueItem, long long  *maxGuesses, int workingSection, string *curOutput);
void help();  //prints out the usage info
unsigned long generateBruteForce(unsigned long cuPos, string *curBrtueForceType,int size, string * bruteGuess);  //generates brute force guesses
bool calculateBrutePos(string input, string *charset,unsigned long *returnValue);
bool areYouMyDad(pqReplacementType *childNode,int curParent, double curProb);
bool pushDeadbeat(pqueueType *pqueue, pqReplacementType *curQueueItem, double &probLimit, long maxPQueueSize);
int trimPQueue(pqueueType *pqueue, double &probLimit, long maxPQueueSize); // removes 1/2 the structures from the pqueue and sets a new probLimit
int rebuildPQueue(pqueueType *pqueue, list <pqReplacementType> *baseStructures, double baseLimit, double &probLimit, long maxPQueueSize);
int recursiveBuildQueue(pqueueType *pqueue, double &minProbLimit,double maxProbLimit, long maxPQueueSize, pqReplacementType curWorker, int size, int pos,double curProbability);
bool onlyChild(pqReplacementType *childNode, double maxProbLimit, double curProbability, int size);
int precomputeInit(bool isRestoreSession, string baseDir, string sessionName,string rules, bool keepUpper, bool keepSpecial, bool keepDigits,string * dicName, double * dicProb, bool * dicExists);
int consumeRules(ntContainerType **dicWords,ntContainerType **numWords, ntContainerType **specialWords, ntContainerType **capWords, ntContainerType **keyboardWords);  //generate guesses in client mode


//Restore from saved session functions
bool restoreSession(pqueueType *pqueue, list <pqReplacementType> *baseStructures, long maxPQueueSize, double rPoint, double &probLimit); //restores the priority queue to the correct values
int writeCrashFile(string baseDir, string sessionName,string rules, bool keepUpper, bool keepSpecial, bool keepDigits,string * dicName, double * dicProb, bool * dicExists, double restorePoint, short precomputeMode);
//comment for above - writes the initial crashFile
int loadCrashFile(string baseDir, string sessionName,string &rules, bool &keepUpper, bool &keepSpecial, bool &keepDigits,string * dicName, double * dicProb, bool * dicExists, double &restorePoint, short &precomputeMode);
//comment for above, restores settings from the crashFile, closes the crashfile afterwards.
int loadClientMode(string baseDir, string sessionName,string &rules, bool &keepUpper, bool &keepSpecial, bool &keepDigits,string * dicName, double * dicProb, bool * dicExists);
//comment for above, loads all of the settings for the client mode.

int updateCrashFile();  //updates the crash file with the current progress


int queueItemMemSize;  //Used to dynamically determine the average size of a queueitem at runtime, (safer than checking to see if a 64bit operating system).


bool memoryTest=false;  //if the session is only testing memory usage and not actually cracking passwords


int main(int argc, char *argv[]) {

  string inputDicFileName[MAXINPUTDIC];   //Filenames for the input dictionaries
  string ruleName = "Default";            //Name of rules to use
  string sessionName = "save";            //Session name used to save/restore cracking sessions
  string clientName = "import";           //Session name used when in client mode
  bool inputDicExists[MAXINPUTDIC];       //Keeps track of which input dictionaries were specified, in case the user did something like dic1 and dic8
  double inputDicProb[MAXINPUTDIC];       //Total probability of input dictionaries. Aka if a dic would crack 60% of passwords it will be .6
  double restorePoint;                    //Probability of guesses to restore a session at.

  ntContainerType *dicWords[MAXWORDSIZE+1];   //Holds the actual dictionary words
  ntContainerType *numWords[MAXWORDSIZE+1];   //Holds all the digits
  ntContainerType *specialWords[MAXWORDSIZE+1];  //holds all the special characters
  ntContainerType *capWords[MAXWORDSIZE+1];      //holds all the capitalization info
  ntContainerType *keyboardWords[MAXWORDSIZE+1];    //holds all the keyboard combinations
  long long maxGuesses=0;
  pqueueType pqueue;
  list <pqReplacementType> baseStructures;   //used to rebuild the prioirty queue from scratch. Aka for memory management to lower the min probability
  bool isRestoreSession=false; //if we should restore the session;
  
  bool removeUpper=true;   //if we should not include dictionary words that contain uppercase letters
  bool removeSpecial=true; //if we should not include dictionary words that contain special characters
  bool removeDigits=true;  //if we should not include dictionary words that contain digits
  bool crashRecovery=false;
  string baseDir;   //the directory the password cracker is located, (used to find the rules folder)
  short precomputeMode=0;  //if it should precompute and save mangling rules vs. generating guesses

  //---------Passphrase Variable-----------------//
  //---Note, if I had my act together I could treat passphrases/passwords exactly the same---------------//
  //---I'm keeping them seperate for now though since named dictionaries are more important for passphrases--------//
  //---Aka dictionaties for Verbs, Nouns, Adjectives, etc-----------------------------------//
  //---Also I plan on playing/experimenting with passphrase specific mangling rules that have some context-sensitive info----------//
  bool isPassphrase=false;  //if it is a passphrase attack

  //---------End Passphrase Variables------------//

  double probLimit=0; //The minimum probability allowed for a pre-terminal to be insterted into the pqueue
  long maxPQueueSize=200000;

  struct sigaction action;         //The signal handler. Used to make sure the most current progess is saved if the user exits the program


  queueItemMemSize= 2 *(sizeof(pqueueType) + sizeof(pqReplacementType) + (5*sizeof(deque<ntContainerStruct *>))); //Yes I assume that there are on average, 5 replacments for each pre-terminal
  std::cerr << "queueitemsize = " << queueItemMemSize << endl;
//---------Parse the command line------------------------//

  //--Initilize the command line variables -- //
  for (int i=0;i<MAXINPUTDIC;i++) {
    inputDicExists[i]=false;
    inputDicProb[i]=1;
  } 
  if (argc == 1) {
    help();
    return 0;
  }
  for (int i=1;i<argc;i++) {
    string commandLineInput = argv[i];
    string tempString = commandLineInput;
    int currentDic;
    if (commandLineInput.find("-dname")==0) { //reading in an input dictionary 
      tempString=commandLineInput.substr(6,commandLineInput.size());
      if (isdigit(tempString[0])) {
        currentDic=atoi(tempString.c_str());
        if (currentDic >=MAXINPUTDIC) {
          std::cerr << "\nSorry, but the category of input dictionaries must fall between 0 and " << MAXINPUTDIC -1 << "\n";
          help();
          return 0;
        }
      }
      else {
        help();
        return 0;
      }
      i++;
      if (i<argc) {
        commandLineInput=argv[i];
        inputDicExists[currentDic]=true;
        inputDicFileName[currentDic]=commandLineInput;
      }
      else {
        std::cerr << "\nSorry, but you need to include the filename after the -dname option\n";
        help();
        return 0;
      }
    }
    else if (commandLineInput.find("-dprob")==0) { //reading in a dictionary's probability
      tempString=commandLineInput.substr(6,commandLineInput.size());
      if (isdigit(tempString[0])) {
        currentDic=atoi(tempString.c_str());
        if (currentDic >=MAXINPUTDIC) {
          std::cerr << "\nSorry, but the category of input dictionaries must fall between 0 and " << MAXINPUTDIC -1 << "\n";
          help();
          return 0;
        }
      }
      else {
        help();
        return 0;
      }
      i++;
      if (i<argc) {
        inputDicProb[currentDic]=atof(argv[i]);
        if ((inputDicProb[currentDic]>1.0)||(inputDicProb[currentDic]<=0)) {
          std::cerr << "\nSorry, but the input dictionary probability must fall between 1.0 and 0, and not equal 0.\n";
          help();
          return 0;
        }
      }
      else {
        std::cerr << "\nSorry, but you need to include the filename after the -dname option\n";
        help();
        return 0;
      }
    }
    else if (commandLineInput.find("-rules")==0) { //the ruleset to use
      i++;
      if (i<argc) {
        ruleName = argv[i];
      }
      else {
        std::cerr << "\nSorry, but you need to include the rule name you want to use\n";
        help();
        return 0;
      }
    }
    else if (commandLineInput.find("-session")==0) { //the session name to use
      i++;
      if (i<argc) {
        sessionName = argv[i];
      }
      else {
        std::cerr << "\nSorry, but you need to include the name of the session you want to use\n";
        help();
        return 0;
      }
    }
    else if (commandLineInput.find("-restore")==0) { //restore a halted session, all of the other config options are then ignored
      i++;
      if (i<argc) {
        sessionName = argv[i];
        isRestoreSession=true;
      }
      else {
        std::cerr << "\nSorry, but you need to include the name of the session you want to restore. Default is 'Save'\n";
        help();
        return 0;
      }
    }
    else if (commandLineInput.find("-memCap")!=string::npos) {
      i++;
      if ((i<argc)&&(isdigit(argv[i][0]))) {
        int baseMemLimit;
        baseMemLimit = atof(argv[i]);
	if (baseMemLimit<0) {
          std::cerr << "\nSorry, the -memCap limit must be a positive number\n";
          help();
          return 0;
        }
        char memUnit;
        memUnit = argv[i][strlen(argv[i])-1];
        if ((memUnit!='m')&&(memUnit!='M')&&(memUnit!='g')&&(memUnit!='G')) {
          std::cerr << "\nSorry, you need to specify the unit, either 'G|g' for Gigs or 'M|m' for Megs. For example '-memCap 1G'\n";
          help();
          return 0;
        }
        if ((memUnit=='m')||(memUnit=='M')) {   //keeping it real with 1048576 byts in a Megabyte
          maxPQueueSize = (1048576*baseMemLimit) / queueItemMemSize;
        }
        else {
          maxPQueueSize = (1073741824*baseMemLimit) / queueItemMemSize;
        }
        std::cerr << "baseMemLimit = " << baseMemLimit << " type = " << memUnit << "queuesize = " << maxPQueueSize << endl;
      }
      else {
        std::cerr <<"\nSorry, but you need to include a value for the probabilty limit between 1.0 and 0.0. The default is 0.0000000001\n";
        help();
        return 0;
      }
    }          
        
    else if (commandLineInput.find("-keepUpper")!=string::npos) {
      removeUpper=false;
    }
    else if (commandLineInput.find("-keepSpecial")!=string::npos) {
      removeSpecial=false;
    }
    else if (commandLineInput.find("-keepDigits")!=string::npos) {
      removeDigits=false;
    }
    else if (commandLineInput.find("-memTest")!=string::npos) {
      memoryTest=true;
    }
    else if (commandLineInput.find("-pregen")!=string::npos) {
      i++;
      if (i<argc) {
        sessionName = argv[i];
        precomputeMode=1;
      }
      else {
        std::cerr << "\nSorry, but you need to include the filename to save the precomputed file to, or you can select 'stdout'\n";
        help();
        return 0;
      }
    }
    else if (commandLineInput.find("-client")!=string::npos) {
      i++;
      if (i<argc) {
        clientName = argv[i];
        precomputeMode=2;
      }
      else {
        std::cerr << "\nSorry, but you need to include a file to read the rules from, or you can select 'stdin'\n";
        help();
        return 0;
      }
    }
    else if (commandLineInput.find("-passphrase")!=string::npos) {
      isPassphrase = true;
    }
      
    else {
      std::cerr << "\nSorry, unknown command line option entered:" << commandLineInput << endl;
      help();
      return 0;
    }
  }
  string tempString = argv[0];
  #ifdef _WIN32
  if (tempString.find("\\")!=string::npos) {
    baseDir=tempString.substr(0,tempString.find_last_of("\\")+1);
  }
  else {
    baseDir=".\\";
  }
  #else 
  if (tempString.find("/")!=string::npos) {
    baseDir=tempString.substr(0,tempString.find_last_of("/")+1);
  }
  else {
    baseDir="./";
  }
  #endif

  //----------End Parsing the command line--------------------//

  //--Haven't fully integrated passphrases with other options so process that first and then exit------//
  if (isPassphrase) {
    deque <ntGenTopType> phraseValues;
    deque <fileInfoType> fileInfo;
    main_load_passphrase(&phraseValues, &baseStructures, &fileInfo, &pqueue, probLimit);
    if (generateGuesses(&pqueue,&baseStructures, maxGuesses, probLimit, maxPQueueSize)==false) {
      std::cerr<< "\nError generating guesses\n";
      return 0;
    }
    return 0;
  }
  //---------Restore Settings From File if it is a Restore Session-----------------//
  if (isRestoreSession) {
    if (loadCrashFile(baseDir, sessionName, ruleName, removeUpper, removeSpecial, removeDigits,inputDicFileName, inputDicProb, inputDicExists, restorePoint, precomputeMode)) {
      std::cerr << "\nThere was a problem opening the recovery file, Exiting\n";
      return 0;
    }
  }

  //----------If in client mode, load up the settings from the input file or stdin as defined by the user---------//
  if (precomputeMode==2) {
    if (loadClientMode(baseDir, clientName, ruleName, removeUpper, removeSpecial, removeDigits,inputDicFileName, inputDicProb, inputDicExists)) {
      std::cerr << "\nThere was a problem opening the precomputed rules file, Exiting\n";
      return 0;
    }
  } 

  //---------Process all the Dictioanry Words------------------//
  if (processDic(inputDicFileName, inputDicExists, inputDicProb,dicWords,removeUpper,removeSpecial,removeDigits)==false) {
    std::cerr << "\nThere was a problem opening the input dictionaries\n";
    help();
    return 0;
  }

  #ifdef _WIN32
  if (processProbFromFile(numWords,baseDir+"Rules\\"+ruleName+"\\Digits\\",1)==false) {
  #else
  if (processProbFromFile(numWords,baseDir+"Rules/"+ruleName+"/Digits/",1)==false) {
  #endif
    std::cerr << "\nCould not open the number probability files\n";
    return 0;
  }
  #ifdef _WIN32
  if (processProbFromFile(specialWords,baseDir+"Rules\\"+ruleName+"\\Special\\",2)==false) {
  #else
  if (processProbFromFile(specialWords,baseDir+"Rules/"+ruleName+"/Special/",2)==false) {
  #endif
    std::cerr << "\nCould not open the special character probability files\n";
    return 0;
  }
  #ifdef _WIN32
  if (processProbFromFile(capWords,baseDir+"Rules\\"+ruleName+"\\Capitalization\\",0)==false) {
  #else
  if (processProbFromFile(capWords,baseDir+"Rules/"+ruleName+"/Capitalization/",0)==false) {
  #endif
    std::cerr << "\nCould not open the capitalization probability files\n";
    return 0;
  }
  #ifdef _WIN32
  if (processProbFromFile(keyboardWords,baseDir+"Rules\\"+ruleName+"\\Keyboard\\",4)==false) {
  #else
  if (processProbFromFile(keyboardWords,baseDir+"Rules/"+ruleName+"/Keyboard/",4)==false) {
  #endif
    std::cerr << "\nCould not open the keyboard probability files\n";
    return 0;
  }

  if (processBasicStruct(&pqueue, &baseStructures, dicWords, numWords, specialWords,capWords, keyboardWords, ruleName, probLimit)==false) {
    std::cerr << "\nError, could not open structure file from the training set\n";
    return 0;
  }
 

  //--------Now build the brute force data----------------//
    
  if (isRestoreSession) {  //restore the priority queue of a previously stopped cracking session
    restoreSession(&pqueue, &baseStructures,maxPQueueSize,restorePoint,probLimit);
  }
  writeCrashFile(baseDir, sessionName, ruleName, removeUpper, removeSpecial, removeDigits,inputDicFileName, inputDicProb, inputDicExists,restorePoint, precomputeMode);

  //--initialize the output for pregen mode if that is turned on-------//
  if (precomputeMode==1) {
    if (precomputeInit(isRestoreSession,baseDir,sessionName,ruleName, removeUpper, removeSpecial, removeDigits,inputDicFileName, inputDicProb, inputDicExists)!=0) {
      std::cerr << "Error starting precompute Mode, exiting\n";
      return 1;
    }
  }


  //-----------------Signal Initilization--------------
  //------------Initilize user status output----------------//
  tty_init(1);
  struct itimerval tout_val;

  tout_val.it_interval.tv_sec = 0;
  tout_val.it_interval.tv_usec = 0;
  tout_val.it_value.tv_sec = CHECKINPUTTIME;  //check for status output every 10 seconds
  tout_val.it_value.tv_usec = 0;
  setitimer(ITIMER_REAL, &tout_val,0);

  action.sa_handler = sig_alrm;
  sigemptyset(&action.sa_mask);
  action.sa_flags = 0;
  sigaction(SIGINT, &action, 0);
  sigaction(SIGKILL, &action, 0);
  sigaction(SIGTERM, &action, 0);
  sigaction(SIGALRM, &action, 0);

  //signal(SIGALRM, sig_alrm);

  //-----------------End Signal Initilization----------


  if (precomputeMode==0) {  //generate Guesses
    if (generateGuesses(&pqueue,&baseStructures, maxGuesses, probLimit, maxPQueueSize)==false) {
      std::cerr<< "\nError generating guesses\n";
      return 0;
    }
  }
  else if (precomputeMode==1) { //Just generate the rules
    if (generateRules(&pqueue,&baseStructures, maxGuesses, probLimit, maxPQueueSize)==false) {
      std::cerr<< "\nError generating the precomputed rules\n";
      return 0;
    }
  }
  else if (precomputeMode==2) { //work in client mode
    if (consumeRules(dicWords, numWords, specialWords, capWords, keyboardWords)==false) {
      std::cerr<< "\nError generating guesses\n";
      return 0;
    }
  }
  return 0;
}     


void help() {
  std::cerr<< endl << endl << endl;
  std::cerr << "PCFG CRACKER - A password guess generator based on probablistic context free grammars\n";
  std::cerr << "Version 0.?? - Updated March-2013 ... Still very much a proof of concept\n";
  std::cerr << "Written by Matt Weir, weir@cs.fsu.edu\n";
  std::cerr << "Special thanks to Florida State University for supporting this work\n";
  std::cerr << "----------------------------------------------------------------------------------------------------------\n";
  std::cerr << "Usage Info:\n";
  std::cerr << "./pcfg_manager <options>\n";
  std::cerr << "\tOptions:\n";
  std::cerr << "\t-dname[0-" << MAXINPUTDIC-1 << "] <dictionary name>\t<REQUIRED>: The input dictionary name\n";
  std::cerr << "\t\t\t\t\tExample: -dname0 common_words.txt\n";
  std::cerr << "\t-dprob[0-" << MAXINPUTDIC-1 << "] <dictionary probability>\t<OPTIONAL>: The input dictionary's probability, if not specified set to 1.0\n";
  std::cerr << "\t\t\t\t\t\tExample: -dprob0 0.75\n";
  std::cerr << "\t-rules <rulefile>\t<OPTIONAL>: The rules to use. If none specified, 'Default' is used\n";
  std::cerr << "\t-session <session name>\t<OPTIONAL>: The name to assign the recovery file. By default it is 'save'\n";
  std::cerr << "\t-restore <session name>\t<OPTIONAL>: Restore a halted session. Note, this is the only option you need as all other\n\t\t\t\tconfig settings are in the restore file\n";
  std::cerr << "\t-memCap <approximite memory limit>[M,G]\t<OPTIONAL>: Limits memory usage though this is a \"approximite\" value \n\t\t\t\t\t\tthat does not take into account loaded dictionaries.\n\t\t\t\t\t\tInclude either a 'M' or a 'G' afterwards to specify Megs or Gigs.\n\t\t\t\t\t\tExample: -memCap 200M\n";
  std::cerr << "\t-keepUpper\t\t<OPTIONAL>: don't lowercase all the words in the dictionary file - not recommended\n";
  std::cerr << "\t-keepSpecial\t\t<OPTIONAL>: don't strip special characters from the dictionary file - not recommended\n";
  std::cerr << "\t-keepDigits\t\t<OPTIONAL>: don't strip digits from the dictionary file -not recommended\n";
  std::cerr << "\t-memTest\t\t<DIAGNOSTIC>: Output memory usage instead of password guesses\n";
  std::cerr << "\n";
  std::cerr << "\tPassphrase Specific Options:\n";
  std::cerr << "\t-passphrase\t\t<REQURIED IF PASSPHRASE>: Tells the tool to perform a passphrase attack instead of a dictionary attack\n";;
  
  std::cerr << endl << endl;
  return;
}


////----Inititialize the precompute stream if needed---------------//
int precomputeInit(bool isRestoreSession,string baseDir, string sessionName, string rules, bool keepUpper, bool keepSpecial, bool keepDigits,string * dicName, double * dicProb, bool * dicExists) {
  if (sessionName.compare("stdout")!=0) {  //print results to a file instead of cout
    if (isRestoreSession) {
      freopen(sessionName.c_str(),"a",stdout);
    }
    else {
      freopen(string(baseDir+sessionName).c_str(),"w",stdout);
    }
  }
  cout.setf(ios::fixed,ios::floatfield);
  cout.precision(16); 
  if ((!isRestoreSession)||(sessionName.compare("stdout")==0)) {  //print out the file initilization info
    cout << "Version:\t1.75" << endl;
    cout <<  "Rules:\t" << rules << endl;
    cout << "KeepUpper:\t" << keepUpper << endl;
    cout << "KeepSpecial:\t" <<keepSpecial << endl;
    cout << "KeepDigits:\t" << keepDigits << endl;
    for (int i=0;i<MAXINPUTDIC;i++) {
      if (dicExists[i]) {
        cout << dicName[i] << endl;
        cout << dicProb[i] << endl;
      }
    }
    cout << "---End_of_Dictionaries---\n";
  }
  return 0;
}


//////////////////////////////////////////////////////////////////
//Initiliazes client mode, aka 'dumbterminal mode'
int loadClientMode(string baseDir, string sessionName,string &rules, bool &keepUpper, bool &keepSpecial, bool &keepDigits,string * dicName, double * dicProb, bool * dicExists)  {
  string inputLine;
  double version;
  string junk;
  int curDictionary=0;
  if (sessionName.compare("stdin")!=0) {  //read results from a file instead of cin
    freopen(sessionName.c_str(),"r",stdin);
  }
  //--first read in the version info---//
  cin >> junk >> version;
  if (junk.compare("Version:")!=0) {
    std::cerr << "Error, malformed precompute file, may be caused if you are trying to load an older, (pre- version 1.73), crashfile" << endl;
    return -1;
  }
  if (version<1.75) {
    std::cerr << "Error, the precompute file is from an older version that is no longer supported. If you really need to restore the session either use an older version of this program, or contact the author at weir@cs.fsu.edu and let him know this is a feature you want" << endl;
    return -1;
  }
  //--
  cin >> junk >> rules;
  if (rules.size()==0) {
    std::cerr << "Error, could not open the precompute file\n";
    return -1;
  }
  if (cin.fail()) {
    std::cerr << "Error, malformed precomputefile\n";
    return -1;
  }
  cin >> junk >> keepUpper;
   if (cin.fail()) {
    std::cerr << "Error, malformed precomputefile\n";
    return -1;
  }
  cin >> junk >> keepSpecial;
  if (cin.fail()) {
    std::cerr << "Error, malformed precomputefile\n";
    return -1;
  }
  cin >> junk >> keepDigits;
  if (cin.eof()) {
    std::cerr << "Error, malformed precomputefile\n";
    return -1;
  }
  cin >> inputLine;
  while ((inputLine.compare("---End_of_Dictionaries---")!=0)&&(!cin.fail())&&(curDictionary<MAXINPUTDIC)) {
    dicExists[curDictionary]=true;
    dicName[curDictionary]=inputLine;
    if (cin.fail()) {
      std::cerr << "Error, malformed precomputefile\n";
      return -1;
    }
    cin >> dicProb[curDictionary];
    if ((dicProb[curDictionary]<=0)||(cin.fail())||(dicProb[curDictionary]>1)) {
      std::cerr << "Error, malformed precomputefile\n";
      return -1;
    }
    curDictionary++;
    cin >> inputLine;
  }
  if (cin.fail()) {
    std::cerr << "Error, malformed precomputefile\n";
    return -1;
  }
  return 0;
}



////--handle all of the loading/saving of crash files----------//
int writeCrashFile(string baseDir, string sessionName,string rules, bool keepUpper, bool keepSpecial, bool keepDigits,string * dicName, double * dicProb, bool * dicExists, double restorePoint,short  precomputeMode) {
  
  crashFile.open(string(baseDir+sessionName+".rec").c_str(), fstream::out);
  crashFile.setf(ios::fixed,ios::floatfield);
  crashFile.precision(16);
  crashFile << "Version:\t1.75" << endl;
  crashFile << "Rules:\t" <<rules << endl;
  crashFile << "KeepUpper:\t" << keepUpper << endl;
  crashFile << "KeepSpecial:\t" <<keepSpecial << endl;
  crashFile << "KeepDigits:\t" << keepDigits << endl;
  crashFile << "PreComputeMode:\t";
  crashFile <<precomputeMode << endl;
  for (int i=0;i<MAXINPUTDIC;i++) {
    if (dicExists[i]) {
      crashFile << dicName[i] << endl;
      crashFile << dicProb[i] << endl;
    }
  }
  crashFile << "---End_of_Dictionaries---\n";
  saveLoc=crashFile.tellg();
  crashFile << fixed << restorePoint;
  return 0;
}

int updateCrashFile() {
  crashFile.seekg(saveLoc);
  crashFile << fixed << curQueueItem.probability << endl;
  return 0;
}

//////////////////////////////////////////////////////////////////
//Loads the crashfile
int loadCrashFile(string baseDir, string sessionName,string &rules, bool &keepUpper, bool &keepSpecial, bool &keepDigits,string * dicName, double * dicProb, bool * dicExists, double &restorePoint, short &precomputeMode)  {
  string inputLine;
  double version;
  string junk;
  int curDictionary=0;
  crashFile.open(string(baseDir+sessionName+".rec").c_str(),fstream::in);
  if (crashFile==NULL) {
    std::cerr << "Error, could not open the crash recovery file\n";
    return -1;
  }
  //--first read in the version info---//
  crashFile >> junk >> version;
  if (junk.compare("Version:")!=0) {
    std::cerr << "Error, malformed crashfile, may be caused if you are trying to load an older, (pre- version 1.73), crashfile" << endl;
    return -1;
  }
  if (version<1.74) {
    std::cerr << "Error, the crashfile is from an older version that is no longer supported. If you really need to restore the session either use an older version of this program, or contact the author at weir@cs.fsu.edu and let him know this is a feature you want" << endl;
    return -1;
  }
  //--
  crashFile >> junk >> rules;
  if (rules.size()==0) {
    std::cerr << "Error, could not open the crash recovery file\n";
    return -1;
  }
  if (crashFile.eof()) { 
    std::cerr << "Error, malformed crashfile\n";
    return -1;
  }
  crashFile >> junk >> keepUpper;
  if (crashFile.eof()) {
    std::cerr << "Error, malformed crashfile\n";
    return -1;
  }
  crashFile >> junk >> keepSpecial;
  if (crashFile.eof()) {
    std::cerr << "Error, malformed crashfile\n";
    return -1;
  }
  crashFile >> junk >> keepDigits;
  if (crashFile.eof()) {
    std::cerr << "Error, malformed crashfile\n";
    return -1;
  }
  crashFile >> junk >> precomputeMode;
  crashFile >> inputLine;
  while ((inputLine.compare("---End_of_Dictionaries---")!=0)&&(!crashFile.eof())&&(curDictionary<MAXINPUTDIC)) {
    dicExists[curDictionary]=true;
    dicName[curDictionary]=inputLine;
    if (crashFile.eof()) {
      std::cerr << "Error, malformed crashfile\n";
      return -1;
    }
    crashFile >> dicProb[curDictionary];
    if ((dicProb[curDictionary]<=0)||(crashFile.eof())||(dicProb[curDictionary]>1)) {
      std::cerr << "Error, malformed crashfile\n";
      return -1;
    }
    curDictionary++;
    crashFile >> inputLine;
  }
  if (crashFile.eof()) {
    std::cerr << "Error, malformed crashfile\n";
    return -1;
  }
  crashFile >> restorePoint;
  crashFile.close();
  return 0;
}


//////////////////////////////////////////////////////////////////////
//Restores the priority queue to the last popped pre-terminal value, aka restorePoint
bool restoreSession(pqueueType *pqueue, list <pqReplacementType> *baseStructures, long maxPQueueSize, double rPoint, double &probLimit) {
  rebuildPQueue(pqueue, baseStructures, rPoint+0.0000000000000001, probLimit,  maxPQueueSize);
  return true;
}



short findSize(string input) { //used to find the size of a string that may contain wchar info, not using wstrings since MACOSX is being stupid
                               //aka when I built it on Ubuntu it worked with wstring, but mac still reads them in as 8 bit chars
  short size=0;
  for (int i=input.size()-1;i>=0;i--) {
    if ((unsigned int)input[i]>127) { //it is a non-ascii char
      i--;
    }
    size++;
  }
  return size;
}



///////////////////////////////////////////////////////////////////////////////
// Main function for managing the priority queue. Pops values and calls the next
// function to push new value into the queue
//
bool generateGuesses(pqueueType *pqueue,list <pqReplacementType> *baseStructures,long long maxGuesses, double probLimit, long maxPQueueSize) {
  int returnStatus;
  string curGuess;
  unsigned long long numberOfPreTerminals=1;
  while (!pqueue->empty()) {
    curQueueItem  = pqueue->top();
    debugPQSize = pqueue->size();
    double debugMinProbLimit = probLimit;
    pqueue->pop();
    while ((curQueueItem.probability<probLimit)&&(!pqueue->empty())) { // this loop is a debugging check since I'm dynamically changing probLimit now
      std::cerr << "Wow, this shouldn't have fired off. Check your pqueue structure Matt!\n";
      curQueueItem  = pqueue->top();
      pqueue->pop();
    }
    if (curQueueItem.probability<probLimit) { //Yet another debugging check, will remove these in a later version but right now leaving them just in case I break something again
      std::cerr << "Well that explains a lot, the bug is in your pqueue\n";
      break;
    }
    if (numberOfPreTerminals%100==0) {
      updateCrashFile();
    }

    if (memoryTest) {       //--Print out the current state of the prioirty queue as well as other debug info
      //if (totalGuesses>=1000000000) { exit(0);}
      unsigned long long tempNumGuesses;  //Used to calculate the number of guesses generated by the current preterminal structure
      
      //--First calculate the number of guesses--//
      //--Note, will slightly overestimate the number of guesses since currently the generation code is smart enough to--//
      //--avoid duplicate guesses generated due to brute force attacks--------//
      tempNumGuesses=1;
      for (int i=0;i<curQueueItem.replacement.size();i++) {
        if (!curQueueItem.replacement[i]->isBruteForce) { //the section is not a brute force replacement
          tempNumGuesses=tempNumGuesses * curQueueItem.replacement[i]->word.size();
        }
        else { //--Is brute force-----//
          if (curQueueItem.replacement[i]->bruteForceType==1) { //digits
            tempNumGuesses=tempNumGuesses * pow(10,curQueueItem.replacement[i]->bruteForceSize);
          }
          else if (curQueueItem.replacement[i]->bruteForceType==2) { //special
            tempNumGuesses=tempNumGuesses * pow(28,curQueueItem.replacement[i]->bruteForceSize);
          }
          else {
            tempNumGuesses=tempNumGuesses * pow(26,curQueueItem.replacement[i]->bruteForceSize);
          }
        }
        totalGuesses=totalGuesses + tempNumGuesses;

      }
      std::cerr << "Total_Guesses:\t" << totalGuesses << "\tTotal_PreTerminals_Popped:\t" << numberOfPreTerminals;
      std::cerr << "\tSize_Of_Queue:\t" << pqueue->size();
      std::cerr << "\tProbability:\t" << curQueueItem.probability << "\tbase_struct:\t";
      list <string>::iterator it;
      for (int i=0;i<curQueueItem.replacement.size();i++) {
        it =curQueueItem.replacement[i]->word.begin();
        std::cerr << *it;
      }
      std::cerr << endl;
    } 
    else {  //--Generate and print the actual guesses
      curGuess.clear();
      returnStatus= createTerminal(&curQueueItem, &maxGuesses,0,&curGuess);  //prints out the guesses
      if (returnStatus==1) { //made the maximum number of guesses
        std::cerr << "Made the maximum amount of guesses specified by user for current cracking session, exiting\n";
        return true;
      }
      else if (returnStatus==-1) { //an error occured
        std::cerr << "An error occured in the pqueue, exiting\n";
        return false;
      }
    }

    numberOfPreTerminals++;  //tracks the number of preTerminals.
    pushDeadbeat(pqueue,&curQueueItem, probLimit,maxPQueueSize);    //The deadbeat dad function
    if (pqueue->empty()) {
      double baseLimit=probLimit;
      if (probLimit==0) { std::cerr << "Hey it's 0\n";}
      probLimit=0.0;
      rebuildPQueue(pqueue, baseStructures, baseLimit, probLimit, maxPQueueSize);
      if (pqueue->empty()) {
        std::cerr << "Didn't push any new guesses into the queue, minProbability is " << probLimit << " Max probability is: " << baseLimit << endl;
      }
    }
  }
  std::cerr << "Hmm looks like it is done, but that means an error probably occured\n";
  return true;
}


int consumeRules(ntContainerType **dicWords, ntContainerType **numWords, ntContainerType **specialWords, ntContainerType **capWords, ntContainerType **keyboardWords) {
  deque <ntContainerType*> directLink[5][MAXWORDSIZE +1];

  return 0;
}


///////////////////////////////////////////////////////////////////////////////
// Do all of the work with the priority queue generateing rules, but don't generate guesses
// I could have included this in the generateGuesses function, but I wanted to simplify it a bit from all of the different modes
bool generateRules(pqueueType *pqueue,list <pqReplacementType> *baseStructures,long long maxGuesses, double probLimit, long maxPQueueSize) {
  int returnStatus;
  unsigned long long numberOfPreTerminals=1;
  while (!pqueue->empty()) {
    curQueueItem  = pqueue->top();
    debugPQSize = pqueue->size();
    double debugMinProbLimit = probLimit;
    pqueue->pop();
    while ((curQueueItem.probability<probLimit)&&(!pqueue->empty())) { // this loop is a debugging check since I'm dynamically changing probLimit now
      std::cerr << "Wow, this shouldn't have fired off. Check your pqueue structure Matt!\n";
      curQueueItem  = pqueue->top();
      pqueue->pop();
    }
    if (curQueueItem.probability<probLimit) { //Yet another debugging check, will remove these in a later version but right now leaving them just in case I break something again
      std::cerr << "Well that explains a lot, the bug is in your pqueue\n";
      break;
    }
    if (numberOfPreTerminals%100==0) {
      updateCrashFile();
    }

    ///////////////////////////////////
    //----Now save the info----------//
    //////////////////////////////////

    //Data Structure----3 bytes----------//
    //broken down by bits
    //0=isBrute
    //1-7=length
    //8-10=replaceRule
    //11-13=category
    //14-21=index
    //---End of data structure-------//
    unsigned char size = curQueueItem.replacement.size();
    unsigned char saveData[3];
    cout.write((char*)&size, sizeof(char));
    for (int i=0;i<size;i++) {
      saveData[0]=0;
      saveData[1]=0;
      saveData[2]=0;
      if (curQueueItem.replacement[i]->isBruteForce) {
        saveData[0]=0x80;
      }
      saveData[0]=saveData[0] | curQueueItem.replacement[i]->rainbowLength;
      saveData[1]=curQueueItem.replacement[i]->replaceRule << 5;
      saveData[1]=saveData[1] | (curQueueItem.replacement[i]->rainbowCategory <<2);
      saveData[1]=saveData[1] | (curQueueItem.replacement[i]->rainbowIndex>>6);
      saveData[2]=curQueueItem.replacement[i]->rainbowIndex & 0xFF;
      
      cout.write((char*)&saveData, sizeof(char)*3);
    }

    //----Get back to queue management---------//
    if (numberOfPreTerminals==maxGuesses) { //We've hit the maximum size to store the rules file
      break;
    }
    numberOfPreTerminals++;  //tracks the number of preTerminals.
    pushDeadbeat(pqueue,&curQueueItem, probLimit,maxPQueueSize);    //The deadbeat dad function
    if (pqueue->empty()) {
      double baseLimit=probLimit;
      if (probLimit==0) { std::cerr << "Hey it's 0\n";}
      probLimit=0.0;
      rebuildPQueue(pqueue, baseStructures, baseLimit, probLimit, maxPQueueSize);
      if (pqueue->empty()) {
        std::cerr << "Didn't push any new guesses into the queue, minProbability is " << probLimit << " Max probability is: " << baseLimit << endl;
      }
    }
  }
  std::cerr << "Done pregenerating the rules\n";
  updateCrashFile();  //incase you want to create a bigger rules file later, you can start where you left off
  return true;
}


int createTerminalCap(pqReplacementType *curQueueItem,long long  *maxGuesses, int workingSection, string *curOutput, string capRule) {
  list <string>::iterator it;
  int size = curOutput->size();
  for (it=curQueueItem->replacement[workingSection]->word.begin();it!=curQueueItem->replacement[workingSection]->word.end();++it) {
    curOutput->resize(size);
    for (int i=0;i<capRule.length();i++) {
      if (capRule[i]=='L') { //add a lowercase letter
        curOutput->append(1,(*it).at(i));
      }
      else { //add an uppercase letter
        curOutput->append(1,toupper((*it).at(i)));
      }
    }
    if (workingSection==curQueueItem->replacement.size()-1) {
      if (!memoryTest) {
        cout << *curOutput << endl;
      }
      else {
        totalGuesses++;
      }
    }
    else {
      createTerminal (curQueueItem, maxGuesses, workingSection+1, curOutput);
    }
  }
  return 0;
}

int createTerminal(pqReplacementType *curQueueItem,long long  *maxGuesses, int workingSection, string *curOutput) {
  list <string>::iterator it;
  int size = curOutput->size();
  if (!curQueueItem->replacement[workingSection]->isBruteForce) { //Not a brute force guess
    for (it=curQueueItem->replacement[workingSection]->word.begin();it!=curQueueItem->replacement[workingSection]->word.end();++it) {
      if (curQueueItem->replacement[workingSection]->replaceRule==0) {  //normal replacement, of numbers or special characters or alpha characters
        curOutput->resize(size);
        curOutput->append(*it);
        if (workingSection==curQueueItem->replacement.size()-1) {  //print out the password guess
          printf("%s\n",(*curOutput).c_str());
        }
        else {
          createTerminal (curQueueItem, maxGuesses, workingSection+1, curOutput);
        }
      }
      else if (curQueueItem->replacement[workingSection]->replaceRule==1) { //capitalization mangling rule
        curOutput->resize(size);
        createTerminalCap(curQueueItem, maxGuesses, workingSection+1, curOutput, *it);
      }
      else if (curQueueItem->replacement[workingSection]->replaceRule==2) { //all lowercase mangling rule
        createTerminal(curQueueItem, maxGuesses, workingSection+1,curOutput);
      }
    }
  }
  else { //it is a brute force guess

///--------Commenting this out for now, I want to rework this whole section-----////
/*
    string *curBruteForceType;
    string bruteGuess;
    list <unsigned long> *alreadyDoneList;
    if (curQueueItem->replacement[workingSection]->bruteForceType==1) {
      curBruteForceType=&digits;
      alreadyDoneList=&allDigits[curQueueItem->replacement[workingSection]->bruteForceSize];
    }
    else if (curQueueItem->replacement[workingSection]->bruteForceType==2) {
      curBruteForceType=&special;
      alreadyDoneList=&allSpecial[curQueueItem->replacement[workingSection]->bruteForceSize];
    }
    else {
      curBruteForceType=&alpha;
    }
    unsigned long curPos = 0;
    list <unsigned long>::iterator it = alreadyDoneList->begin();
    while (curPos==*it) {
      curPos++;
      if (it!=alreadyDoneList->end()) {
        ++it;
      }
    }
    curPos = generateBruteForce(curPos,curBruteForceType,curQueueItem->replacement[workingSection]->bruteForceSize,&bruteGuess);
    while (curPos!=-1) {
      curOutput->resize(size);
      curOutput->append(bruteGuess);
      if (workingSection==curQueueItem->replacement.size()-1) {  //print out the password guess
        if (!memoryTest) {
          printf("%s\n",(*curOutput).c_str());
        }
        else {
          totalGuesses++;
        }
      }
      else {
        createTerminal (curQueueItem, maxGuesses, workingSection+1, curOutput);
      }
      while (curPos==*it) {
        curPos++;
        if (it!=alreadyDoneList->end()) {
          ++it;
        }
      }
      curPos =  generateBruteForce(curPos,curBruteForceType,curQueueItem->replacement[workingSection]->bruteForceSize,&bruteGuess);
    }
///////////////////////////////////////////////////////
//End of commented out brute force section////////////////
////////////////////////////////////////////////////////
*/
  }

  return 0;
} 


unsigned long generateBruteForce(unsigned long curPos, string *curBruteForceType,int size, string * bruteGuess) {
  unsigned long curWorking = curPos;
  int keySize=(*curBruteForceType).size();
  (*bruteGuess).clear();
  for (int i=0;i<size;i++) {
    int tempPos=curWorking%keySize;
    (*bruteGuess).append(1,curBruteForceType->at(tempPos));
    curWorking=curWorking/keySize;
  }
  curPos++;
  if (curPos>pow(keySize,size)) {
    return -1;
  }
  return curPos;
}


//////////////////////////////////////////////////////////////
//Alternate way to build the tree based on the deadbeat dad algorithm
//
bool pushDeadbeat(pqueueType *pqueue, pqReplacementType *curQueueItem, double &probLimit, long maxPQueueSize) {
  pqReplacementType insertValue;
  double dadProb = curQueueItem->probability;
  insertValue.base_probability=curQueueItem->base_probability;
  for (int i=0;i<curQueueItem->replacement.size();i++) {
    if (curQueueItem->replacement[i]->next!=NULL) {
      insertValue.replacement.clear();
      insertValue.probability=curQueueItem->base_probability;
      for (int j=0;j<curQueueItem->replacement.size();j++) {
        if (j!=i) {
          insertValue.replacement.push_back(curQueueItem->replacement[j]);
          insertValue.probability=insertValue.probability*curQueueItem->replacement[j]->probability;
        }
        else {
          insertValue.replacement.push_back(curQueueItem->replacement[j]->next);
          insertValue.probability=insertValue.probability*curQueueItem->replacement[j]->next->probability;
        }
      }
      if (insertValue.probability>=probLimit) {
        if (areYouMyDad(&insertValue,i,dadProb)) {
          pqueue->push(insertValue);
          if ((pqueue->size() >= maxPQueueSize)&&(maxPQueueSize!=-1)) {
            trimPQueue(pqueue,probLimit,maxPQueueSize);
            //std::cerr << "Debug: Reducing probability limit\n";       
          }
        }
      }
    }
    insertValue.replacement.clear();  //Note, probably can take this out, just checking for memory leaks
  }
  return true;
}


////////////////////////////////////////////////////////////////
//Returns true if the current popped node is the least probable parent for the child node
//I know, to continue the joke I should find some way so I can use the most probable parent
//
bool areYouMyDad(pqReplacementType *childNode,int curParent, double curProb) {
  double dnaProb=0; //the probability of other parents
  for (int i=0;i<childNode->replacement.size();i++) {
    if (i!=curParent) {
      dnaProb=childNode->base_probability;
      for (int j=0;j<childNode->replacement.size();j++) {
        if (j!=i) {
          dnaProb=dnaProb * childNode->replacement[j]->probability;
        }
        else {
          if (childNode->replacement[j]->prev==NULL) {
            dnaProb=1;
            break;
          }
          else {
            dnaProb=dnaProb * childNode->replacement[j]->prev->probability;
          }
        }
      } 
      if (dnaProb==curProb) {
        if (i>curParent) { //this is a heuristic to resolve ties. Basically the parent furthest to the right on the tree takes care of the kid
          return false;
        }
      }
      else if (dnaProb<curProb) { //there is another parent who will take care of the snotty kids
        return false;
      }
    }
  }
  return true;
}


//////////////////////////////////////////////////////////////
//Temporary, (hah yah we'll see about that), fix to allow deleting the last 1/2 of a priority queue
//Very inefficient, need to come up with a better solution
//
int trimPQueue(pqueueType *pqueue, double &probLimit, long maxPQueueSize) {
   list <pqReplacementType> swapList;
   long newQueueSize = maxPQueueSize/2;
   //--sanity check--------//
   if (maxPQueueSize>pqueue->size()) {
      std::cerr << "Hey you're trying to trim the pqueue even though it isn't full yet. That's a bug\n";
      return 1;
   }
   for (long i=0;i<newQueueSize;i++) {
     swapList.push_back(pqueue->top());
     if (i==(newQueueSize-1)) {  //set the new probability
        //--Handle edge cases-------//
        while (pqueue->top().probability==swapList.back().probability) {
          swapList.push_back(pqueue->top());
          pqueue->pop();
        }
        probLimit = pqueue->top().probability;
     }
     pqueue->pop();
   }
   while (!pqueue->empty()) {
     pqueue->pop();
   }
   for (list<pqReplacementType>::iterator it=swapList.begin() ; it != swapList.end(); it++ ) {
     pqueue->push(*it);
   }
   swapList.clear();
   return 0;
}


///////////////////////////////////////////////////////////////
//Rebuilds the pqueue from scratch to only include values that fall between the probability limits
//
int rebuildPQueue(pqueueType *pqueue, list <pqReplacementType> *baseStructures, double baseLimit, double &probLimit, long maxPQueueSize){
  pqReplacementType curWorker; 
  //cout << "debug : "<< baseLimit << " " << probLimit << endl;
  //std::cerr << "Starting to rebuild the PQueue\n";
  while (!pqueue->empty()) {  //probably don't need to do this since it should be empty. Just a sanity check
    pqueue->pop();
  }
  int j=0;
  for (list<pqReplacementType>::iterator it=baseStructures->begin(); it!=baseStructures->end(); it++) {
      curWorker=*it;
      recursiveBuildQueue(pqueue, probLimit, baseLimit,  maxPQueueSize, curWorker, curWorker.replacement.size(),0,(*it).base_probability);
  } 
  //std::cerr << "Finished rebuilding the PQueue\n";
  return 0;
}

///////////////////////////////////////////////////////////////////////
//Normally I would doublecheck size, but if I use this function properly it will not need to be checked again, and it will speed it up a minute amount
//Another way of saying, hey if you are looking for bugs, look here!!
int recursiveBuildQueue(pqueueType *pqueue, double &minProbLimit, double maxProbLimit, long maxPQueueSize, pqReplacementType curWorker, int size, int pos, double baseProbability) {
  int returnValue;
  bool firstAndOut=true;
  double curProbability=0.0;
  for (int i=0;i<size;i++) {
    if (curWorker.replacement[i]==NULL) {
      std::cerr << "Hey a NULL value was encountered\n";
      std::cerr << "Info size: " << size << " position: " << i << " pivot point: " << pos << endl;
      return 1;
    }
  }
  while (curWorker.replacement[pos]!=NULL) {
     curProbability=baseProbability * curWorker.replacement[pos]->probability;
     if (pos<(size-1)) {
       returnValue = recursiveBuildQueue(pqueue, minProbLimit, maxProbLimit,  maxPQueueSize, curWorker, size,pos+1,curProbability);
       if ((returnValue==1)&&(firstAndOut)) { //No more lower probability preterminals from this pivot point need be inserted into the queue at this point
         return 1;                            //Cascade it to up to the prev pivot point, (aka the previous one might be able to stop as well
       }
       else if (returnValue==1) {             //No lower probability preterminals from this pivot point need be inserted into the queue at this point
         return 0;                            //Do not cascade the results to the prev pivot point
       }
     }
     else {      //this is the point where we consider inserting it into the pqueue
         if (curProbability < minProbLimit) { //too low a probability
           if (firstAndOut) {
             return 1;
           }
           else {
             return 0;
           }
         } 
         else if (curProbability<=maxProbLimit) {  //see if you can push it into the queue
           if (onlyChild(&curWorker,maxProbLimit,curProbability,size)) {    //checks to see if any of it's parents are in the current queue
             pqReplacementType insertValue;
             insertValue.base_probability=curWorker.base_probability;
             insertValue.probability=curProbability;
             insertValue.replacement.clear();
             for (int i=0;i<curWorker.replacement.size();i++) {
               insertValue.replacement.push_back(curWorker.replacement[i]);
             }
             pqueue->push(insertValue);
             if ((pqueue->size() >= maxPQueueSize)&&(maxPQueueSize!=-1)) {
//               std::cerr << "Debug: Reducing probability limit\n";
               trimPQueue(pqueue,minProbLimit,maxPQueueSize);
             }
           }
           if (firstAndOut) {
             return 1;
           }
           else {
             return 0;
           }
         }
         //--------Don't need a case if the current probabilty is more than the maxLimit
           
     }
     curWorker.replacement[pos]=curWorker.replacement[pos]->next; 
     if (curWorker.replacement[pos]!=NULL) {
       firstAndOut=false;
     }
  }
  if (firstAndOut) {
    return 1;
  }
  return 0;
}




////////////////////////////////////////////////////////////////
//Returns true if the child has no parents in the pqueue
//
bool onlyChild(pqReplacementType *childNode, double maxProbLimit, double curProbability, int size) {
  double parentProb=0; //the probability of the parent
  for (int i=0;i<size-1;i++) {
    parentProb=childNode->base_probability;
    for (int j=0;j<childNode->replacement.size();j++) {
      if (j!=i) {
        parentProb=parentProb * childNode->replacement[j]->probability;
      }
      else {
        if (childNode->replacement[j]->prev==NULL) {
          parentProb=1;
          break;
        }
        else {
          parentProb=parentProb * childNode->replacement[j]->prev->probability;
        }
      }
    }
    if (parentProb <= maxProbLimit) {
      return false;
    }
    //--Note, don't have to check to see if the parent is more that minProbLimit, since it's child is, (otherwise this wouldn't be called)
    //--and a parent's prob is always more than or equal to the child.
    //--Also ties always go to the parent
  }
  return true;
}

