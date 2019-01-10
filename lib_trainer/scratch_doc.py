## Not a real python file. Just using this to hold various scratch pieces of code I'm pasting around

# TODO: Remove this test code
            # test multiword
            cur_run = []
            for x in password:
                if x.isalpha():
                    cur_run.append(x)
                else:
                    if cur_run:
                        multiword_parsed, result = multiword.detect_multiword("".join(cur_run))
                        if len(result) > 1:
                            num_multi_words +=1
                            #if len(result) > 2:                       
                            #    print("Original pw: " + "".join(password))
                            #   print("Multi-word : " + str(result))
                            #    print()
                        else:
                            num_single_words +=1
                            if not multiword_parsed:
                                leet_parsed, leet_result = leet_detector.detect_leet(password)
                                if leet_parsed:
                                    print("Original pw: " + "".join(password))
                                    print("L33t Word : " + str(leet_result))
                                    print()
                                    continue
                            
                            
                        cur_run = []
                        
            if cur_run:
                multiword_parsed, result = multiword.detect_multiword("".join(cur_run))
                if len(result) > 1:
                    num_multi_words +=1
                    
                else:
                    num_single_words +=1