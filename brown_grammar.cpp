#include "brown_grammar.h"

int test() {

 return 0;
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

  tempHolder.names.push_back("CC");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();
  
  //numbers, (one, 1, first)
  tempHolder.names.push_back("CD");
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
  tempHolder.names.push_back("JJR");
  tempHolder.names.push_back("JJS");
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
  tempHolder.names.push_back("NN$");
  tempHolder.names.push_back("NNS");
  tempHolder.names.push_back("NNS$");
  tempHolder.names.push_back("NR");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //Proper noun types, (names, places, pets, etc)
  tempHolder.names.push_back("NP");
  tempHolder.names.push_back("NP$");
  tempHolder.names.push_back("NPS");
  tempHolder.names.push_back("NPS$");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //Pronoun types
  tempHolder.names.push_back("PN");
  tempHolder.names.push_back("PN$");
  tempHolder.names.push_back("PP$");
  tempHolder.names.push_back("PP$$");
  tempHolder.names.push_back("PPL");
  tempHolder.names.push_back("PPLS");
  tempHolder.names.push_back("PPO");
  tempHolder.names.push_back("PPS");
  tempHolder.names.push_back("PPSS");
  tempHolder.names.push_back("PRP");
  tempHolder.names.push_back("PRP$");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //Qualifiers, (very, fairly)
  tempHolder.names.push_back("QL");
  tempHolder.names.push_back("QLP");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //Adverbs
  tempHolder.names.push_back("RB");
  tempHolder.names.push_back("RBR");
  tempHolder.names.push_back("RBT");
  tempHolder.names.push_back("RN");
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
  tempHolder.names.push_back("VBD");
  tempHolder.names.push_back("VBG");
  tempHolder.names.push_back("VBN");
  tempHolder.names.push_back("VBP");
  tempHolder.names.push_back("VBZ");
  phraseValues->push_back(tempHolder);
  tempHolder.names.clear();

  //wh- types, (who which, when, etc)
  tempHolder.names.push_back("WDT");
  tempHolder.names.push_back("WP$");
  tempHolder.names.push_back("WPO");
  tempHolder.names.push_back("WPS");
  tempHolder.names.push_back("WQL");
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
  if (imax < imin)
    // set is empty, so return value showing not found
    return -1;
  else
    {
      // calculate midpoint to cut set in half
      int imid = imin + ((imax - imin) / 2);
 
      // three-way comparison
      if (A->at(imid).name.compare(key))
        // key is in lower subset
        return pp_binary_search(A, key, imin, imid-1);
      else if (A->at(imid).name.compare(key))
        // key is in upper subset
        return pp_binary_search(A, key, imid+1, imax);
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


////////////////////////////////////////////////////////////////////////////////
// Associate the user specified dicionaries with the types
int add_user_dics(deque <ppPointerType> *phraseList, deque <fileInfoType> *fileInfo) {
  
  //---Cycle through all the user specified dictionaries-------------//
  for (int i=0; i < fileInfo->size(); i++) {
    
    //--Next find the transform this dictionary is associated with--------------//
    int index = pp_binary_search(phraseList, fileInfo->at(i).type, 0, phraseList->size());
    if (index != -1) { //it exists
      ntGenTopType * tempNtGen = phraseList->at(index).pointer;
      tempNtGen->fileInfo.push_front(fileInfo->at(i));
    }
    else {
      std::cerr << "You specified a passphrase dictionary type where the type doesn't exist\n";
      std::cerr << "The type was: " << fileInfo->at(i).type << endl;
      return 1;
    }

  }

  return 0;
}
