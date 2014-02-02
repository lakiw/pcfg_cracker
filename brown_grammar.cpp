#include "brown_grammar.h"


//////////////////////////////////////////////////////////////////
//Controlls all the logic for loading the passphrase dictionaries and initializing everything
//
bool main_load_passphrase(deque <ntGenTopType> *phraseValues, list <pqReplacementType> *baseStructures, deque <fileInfoType> *fileInfo, pqueueType *pqueue, double probLimit) {
  deque <ppPointerType> phraseList;
//  brown_initialize(phraseValues);
  simplified_initialize(phraseValues);
  orderPointers(phraseValues, &phraseList);
  read_dic_config("config.txt",fileInfo);
  add_user_dics(&phraseList, fileInfo);
  add_default_dics(&phraseList);
  load_all_dics(phraseValues);
  load_passphrase_grammar(pqueue,baseStructures, &phraseList,"Passphrase_Default", probLimit);
  cout << "pqueue size now is " << pqueue->size() << endl;
  return true;
}

////////////////////////////////////////////////////////////////////
// The simplified typing vs the complex typing in the Brown dataset
// More datasets support this, and it in fact might be more effective
// for passphrase cracking.
int simplified_initialize(deque <ntGenTopType> *phraseValues) {
  ntGenTopType tempHolder;

  tempHolder.names.push_back("ADJ");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("ADV");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("CNJ");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("DET");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("EX");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("FW");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("MOD");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("N");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("NP");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("NUM");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("PRO");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("P");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("TO");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("UH");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("V");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("VB");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("VBZ");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("VD");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("VG");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("VN");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("WH");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();
}

int brown_initialize(deque <ntGenTopType> *phraseValues) {
  ntGenTopType tempHolder;

  //Initially set up all of the possible replacements via the Brown Typing/Corpus
  //Aka this data will be used when parsing the base structures to figure out what replacements to use
  //For example, if it see's 'NP VS NN' we know to use 'ProperNoun Verb Noun' as replacements.
  //Multiple strings can have the same transforms due to limitations of the dictionaries as implimented
  //Aka right now I don't expect to have different dicionaries for nominal pronouns and possessive nominal pronouns

  //This part only groups the replacements together, aka so the various Nouns will all be classified as nouns

  tempHolder.names.push_back(".");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("(");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back(")");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("*");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("--");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back(",");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back(":");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("ABL");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("ABN");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("ABX");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("AP");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("AT");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("BE");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("BED");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("BEDZ");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();
 
  tempHolder.names.push_back("BEG");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("BEM");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("BEN");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("BER");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("BEZ");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("CC");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();
  
  //numbers, (one, 1, first)
  tempHolder.names.push_back("CD");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("OD");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("CS");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("DO");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("DOD");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("DOZ");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("DT");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("DTI");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("DTS");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("DTX");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("EX");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("FW");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("HV");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("HVD");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("HVG");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("HVN");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("IN");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //Adjective types
  tempHolder.names.push_back("JJ");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("JJR");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("JJS");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("JJT");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("MD");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("NC");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //Noun types
  tempHolder.names.push_back("NN");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("NNP");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("NN$");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("NNS");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("NNS$");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("NR");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //Proper noun types, (names, places, pets, etc)
  tempHolder.names.push_back("NP");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("NP$");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("NPS");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("NPS$");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //Pronoun types
  tempHolder.names.push_back("PN");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("PN$");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("PP$");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("PP$$");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("PPL");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("PPLS");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("PPO");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("PPS");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("PPSS");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("PRP");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("PRP$");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //Qualifiers, (very, fairly)
  tempHolder.names.push_back("QL");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("QLP");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //Adverbs
  tempHolder.names.push_back("RB");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("RBR");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("RBT");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("RN");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("RP");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("TO");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("UH");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //Verb types
  tempHolder.names.push_back("VB");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("VBD");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("VBG");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("VBN");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("VBP");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("VBZ");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //wh- types, (who which, when, etc)
  tempHolder.names.push_back("WDT");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("WP$");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("WPO");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("WPS");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("WQL");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  tempHolder.names.push_back("WRB");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  return 0;
}

bool compare_ppPointer (ppPointerType first, ppPointerType second) {
  int result = first.name.compare(second.name);
  if (result ==0) {
    return false;
  } 
  else if (result < 0) {
    return true;
  }
  return false;
}

int pp_binary_search(deque <ppPointerType> * A, string key, int imin, int imax) {
  // test if array is empty
  if (imax < imin) {
    // set is empty, so return value showing not found
    return -1;
  }
  else
    {
       
      // calculate midpoint to cut set in half
      int imid = imin + ((imax - imin) / 2);
      // three-way comparison
      if (A->at(imid).name.compare(key) > 0) {
        // key is in lower subset
        return pp_binary_search(A, key, imin, imid-1);
      }
      else if (A->at(imid).name.compare(key) < 0) {
        // key is in upper subset
        return pp_binary_search(A, key, imid+1, imax);
      }
      else
        // key has been found
        return imid;
    }
}


////////////////////////////////////////////////////////////////////////////////
//Build an ordered list of all the type info, makes loading new sessions faster
//Also I learned O(N) searches *always* seem to bite me in the butt, no matter
//how rare I expect them to be.
int orderPointers(deque <ntGenTopType> *phraseValues, deque <ppPointerType> *phraseList) {

  for (int i=0; i < phraseValues->size(); i++) {
    for (int j=0; j < phraseValues->at(i).names.size(); j++) {
       ppPointerType tempPointer;
       tempPointer.name = phraseValues->at(i).names[j];
       tempPointer.pointer = &phraseValues->at(i);
       phraseList->push_front(tempPointer);
    }
  }
  sort(phraseList->begin(),phraseList->end(),compare_ppPointer);
  return 0;
}


int read_dic_config(string configName, deque <fileInfoType> *fileInfo) {
  ifstream inputFile;
  size_t curPos;
  string inputLine;
  string inputType;
  string inputPath;
  double prob;
  size_t marker;

  inputFile.open(configName.c_str());
  if (!inputFile.is_open()) {  //--If it failed to open the dictionary
    std::cerr << "Could not open file " << configName << endl;
    return -1;
  }
  std::getline(inputFile,inputLine);
  while (!inputFile.eof()) {
    marker=inputLine.find("\t");
    if (marker!=string::npos) {
      inputType = inputLine.substr(0,marker).c_str();
    }
    else {
      std::cerr << "Malformed dictionary config file\n";
      return -1;
    }
    inputLine = inputLine.substr(marker+1,inputLine.size());
    marker=inputLine.find("\t");
    if (marker!=string::npos) {
      inputPath = inputLine.substr(0,marker).c_str();
    }
    else {
      std::cerr << "Malformed dictionary config file\n";
      return -1;
    }
    inputLine = inputLine.substr(marker+1,inputLine.size());
    prob=atof(inputLine.c_str());
    if (prob<=0) {
      std::cerr << "Malformed dictionary config file\n";
      return -1;
    }

    //---Now add the dictionaries----------//
    fileInfoType tempFile;
    tempFile.type = inputType;
    tempFile.filename = inputPath;
    tempFile.probability = prob;
    tempFile.isUserDic = true;
    fileInfo->push_back(tempFile);
    std::getline(inputFile,inputLine);
  }
  return 0;
}

////////////////////////////////////////////////////////////////////////////////
// Associate the user specified dicionaries with the types
int add_user_dics(deque <ppPointerType> *phraseList, deque <fileInfoType> *fileInfo) {
  //---Cycle through all the user specified dictionaries-------------//
  for (int i=0; i < fileInfo->size(); i++) {
    //--Next find the transform this dictionary is associated with--------------//
    int index = pp_binary_search(phraseList, fileInfo->at(i).type, 0, phraseList->size()-1);
    if (index != -1) { //it exists
      ntGenTopType * tempNtGen = phraseList->at(index).pointer;
      tempNtGen->fileInfo.push_front(fileInfo->at(i));
    }
    else {
      std::cerr << "You specified a passphrase dictionary type where the type doesn't exist\n";
      std::cerr << "The type was: " << fileInfo->at(i).type << endl;
      //return 1;
    }

  }

  return 0;
}

///////////////////////////////////////////////////////////////////////////////////
// Add default dictionaries if no user dictionary was specified
int add_default_dics(deque <ppPointerType> *phraseList) {
  string basepath="Passphrase_Wordlists/";
  //---Go through all the pre-terminal to terminal replacements------//
  for (int i=0; i<phraseList->size();i++) {
    if (phraseList->at(i).pointer->fileInfo.size()==0) { //No existing dictionaries
      for (int j=0; j<phraseList->at(i).pointer->names.size();j++) {
        //---Only try default dictionaries for replacements that start with alphanum letters------//
        if (isalpha(phraseList->at(i).pointer->names.at(j).at(0))){
          fileInfoType tempFile;
          tempFile.isUserDic=false;
          tempFile.type=phraseList->at(i).pointer->names.at(j);
          tempFile.filename=basepath + phraseList->at(i).pointer->names.at(j) + ".txt";
          ///--For now, assign 100% to each dictionary. If multiple dictionaires are used for a
          ///--replacement then normalization will take care of that to get them at the correct prob
          ///--In the future if multiple default dictionaries are added with different probabilities
          ///--For example "BobLovesAlice" types of replacements, I may include a custom default prob info
          ///--in the dictioanry file itself
          tempFile.probability = 1.0 + (rand() % 100)/100.0;
	  phraseList->at(i).pointer->fileInfo.push_front(tempFile);
        }
      }
    }
  }
  return 0;
}

/////////////////////////////////////////////////////////////////////////////////////
//  Loads the words for a single dictionary
//  Note, right now I'm not lowercaseing the input or removing special characters
//  Aka that info for passphrases might be important, (vs mostly creating junk in regular password
//  cracking attacks.) For example, I don't want to change "don't" into "dont".
//  Later on it might be useful to revisit this and only leave in certain types of special characters
//
int load_dic(fileInfoType *fileInfo, ntContainerType *data) {
  ifstream inputFile;
  size_t curPos;
  string inputWord;
  inputFile.open(fileInfo->filename.c_str());
  if (!inputFile.is_open()) {  //--If it failed to open the dictionary
    if (fileInfo->isUserDic) { //--Only print out if it can't open user dics
      std::cerr << "Could not open file " << fileInfo->filename << endl;
    }
    return -1;
  }

  //--------Now process the input dictionary-------------//
  while (!inputFile.eof()) {
    std::getline(inputFile,inputWord);
    curPos=inputWord.find("\r");  //remove carrige returns
    if (curPos!=string::npos) {
      inputWord.resize(curPos);
    }
    if (inputWord.size()>0) {
      data->word.push_back(inputWord);
    }
  }
  if (data->word.size() == 0) { //No words were loaded
    std::cerr << "Warning: No words loaded for " << fileInfo->filename << endl;
    return -1;
  }

  return 0;
}

/////////////////////////////////////////////////////////////////////////////////////
// Sets all of the values for a passphrase dictionary except for actual words
// Most of these values could be removed if I actually forked the passphrase and password
// cracking portions of this program into different programs
int set_passphrase_dic_values(fileInfoType *fileInfo, ntContainerType *data) {
  if (data->word.size()==0) {
    std::cerr << "Weird, there is an empty dictionary even though that should have been removed earlier\n";
    return -1;
  }
  data->replaceRule=0; //final terminal
  data->next = NULL; //will set these later but might as well be careful
  data->prev = NULL;
  data->isBruteForce = false; //not a brute force guess
  data->rainbowCategory = 3; //dictionary word
  //---Other rainbow values don't really fit into passphrases, need to revisit that later--//
  data->probability = fileInfo->probability; //not the final probability, but need to save the prob of the dictionary here so it follows the datastructure
  return 0;
}

bool ntCompare(ntContainerStruct a, ntContainerStruct b) {
  return (a.probability > b.probability);
}

//////////////////////////////////////////////////////////////////////////////////////
// Load all the dictionairies. 
// Includes logic for normalizing the probability between multiple dictionaries and then
// sorting the replacements in probability order
int load_all_dics(deque <ntGenTopType> *phraseValues) {
  for (int i=0; i<phraseValues->size(); i++) {
    //--Load up all the dictionaries------//
    for (int j=0; j< phraseValues->at(i).fileInfo.size();j++) {
      ntContainerType data;
      if (load_dic(&phraseValues->at(i).fileInfo.at(j),&data)==0) {
        if (set_passphrase_dic_values(&phraseValues->at(i).fileInfo.at(j),&data)==0) {
          phraseValues->at(i).data.push_back(data);
        }
      }
    }
    //---Now calculate the probability of each dictionary so all the replacements for a pre-terminal add up t  1.0---//
    ///---First find the current sum of all the probabilities---------//
    double totalProb = 0.0;
    for (int j=0; j< phraseValues->at(i).data.size();j++) {
      totalProb = totalProb + phraseValues->at(i).data.at(j).probability;
    }
    ///---Now calculate the true probability of a final terminal value--------------//
    for (int j=0; j< phraseValues->at(i).data.size();j++) {
      //--first find the normalizd probability for the full dictionary
      phraseValues->at(i).data.at(j).probability = (phraseValues->at(i).data.at(j).probability * (1.0)) / totalProb;
      //--next find the true probability of each word based on the size of the dictionary---//
      phraseValues->at(i).data.at(j).probability = (phraseValues->at(i).data.at(j).probability * (1.0)) / phraseValues->at(i).data.at(j).word.size();
    }
    //---Now sort them by probability-----//
    sort(phraseValues->at(i).data.begin(), phraseValues->at(i).data.end(), ntCompare);
    //---Now establish the links for the values when they are pushed into base structures--------//
    for (int j=0; j< int(phraseValues->at(i).data.size()-1);j++) {
      //cout << "DEBUG: " << j << " : " << int(phraseValues->at(i).data.size() -1)<< endl;
      phraseValues->at(i).data.at(j).next = &phraseValues->at(i).data.at(j+1);
    }
  }
  return 0;
}

/////////////////////////////////////////////////////////////////////////////////////////
// Load Passphrase Grammar
//
int load_passphrase_grammar(pqueueType *pqueue, list <pqReplacementType> *baseStructures, deque <ppPointerType> *phraseList,string ruleName, double probLimit) {
  ifstream inputFile;
  string inputLine;
  string tempLine;
  pqReplacementType inputValue;
  bool badInput=false;
  size_t marker;
  size_t cleanMark;
  double prob;

  #ifdef _WIN32
  inputFile.open(string(".\\Rules\\"+ruleName+"\\Grammar\\Grammar.txt").c_str());
  #else
  inputFile.open(string("./Rules/"+ruleName+"/Grammar/Grammar.txt").c_str());
  #endif
  if (!inputFile.is_open()) {
    std::cerr << "Could not open the rules file " << ruleName << endl;
    return -1;
  }
  getline(inputFile,inputLine);
  while (!inputFile.eof()) {
    badInput=false;
    marker=inputLine.find("\t");
    if (marker!=string::npos) {
      prob=atof(inputLine.substr(0,marker).c_str());
      inputValue.probability=prob;
      inputValue.base_probability=prob;
      //---------Now process the structure---------------//
      inputLine = inputLine.substr(marker+1,inputLine.size());
      while (marker!=string::npos) {
        marker = inputLine.find('\t');
        //--Process the individual part of the structure here--------//
        tempLine = inputLine.substr(0,marker);

        //------------For now clean up input to exclude types this doesn't support yet-------//
        cleanMark = tempLine.find("-");
        if (cleanMark!=string::npos) {
          tempLine = tempLine.substr(0,cleanMark);
        }
        cleanMark = tempLine.find(",");
        if (cleanMark!=string::npos) {
          tempLine = tempLine.substr(0,cleanMark);
        }
        cleanMark = tempLine.find("*");
        if (cleanMark!=string::npos) {
          tempLine = tempLine.substr(0,cleanMark);
        }
        cleanMark = tempLine.find("+");
        if (cleanMark!=string::npos) {
          tempLine = tempLine.substr(0,cleanMark);
        }
        cleanMark = tempLine.find("(");
        if (cleanMark!=string::npos) {
          tempLine = tempLine.substr(0,cleanMark);
        }
        cleanMark = tempLine.find(")");
        if (cleanMark!=string::npos) {
          tempLine = tempLine.substr(0,cleanMark);
        }
        cleanMark = tempLine.find(":");
        if (cleanMark!=string::npos) {
          tempLine = tempLine.substr(0,cleanMark);
        }
        //----------End cleanup code----------------------//
        std::transform(tempLine.begin(), tempLine.end(),tempLine.begin(), ::toupper);
        int index = pp_binary_search(phraseList, tempLine, 0, phraseList->size()-1);

        //----Could Not Parse Input Line-----------------//
        if ((index == -1)&& (tempLine.size()>0)) {
          //Used to catch errors with my parsing script
          //cout << "notfound:" << tempLine << ":" << endl;
        } 
        if (index == -1) {
          //cout << "Did not find :" << tempLine << ": in :" << inputLine<<endl; 
          badInput = true;
          break;
        } 
        
        //----Add subsectin-------------------------------//
        if (phraseList->at(index).pointer->data.size()==0) {
          //cout << "Dictionary " << tempLine << " is empty\n";
          badInput = true;
          break; 
        }
        inputValue.replacement.push_back(&phraseList->at(index).pointer->data.at(0));
        inputValue.probability=inputValue.probability*phraseList->at(index).pointer->data.at(0).probability;

        inputLine =inputLine.substr(marker+1,inputLine.size());
      }
    }
    else {
      badInput = true;
    }

    if (!badInput) {
      if (inputValue.probability==0) {
        std::cerr << "Error, we are getting some values with 0 probability\n";
        //return false;
      }
      else if (inputValue.probability >=probLimit) {
        /////////////////////////////////////////////////////////////////////////////////////////
        //--DEBUG TAKE THIS CHECK OUT LATER WHEN THERE ARE BETTER BASE STURUCTURES AVAILABLE---//
        /////////////////////////////////////////////////////////////////////////////////////////
        if (inputValue.replacement.size() > 4) {
          pqueue->push(inputValue);
          baseStructures->push_back(inputValue);
        }
	//------End Debug------//
      }
    }
    inputValue.probability=0;
    inputValue.replacement.clear();

    getline(inputFile,inputLine);
  }

  return 0;
}




