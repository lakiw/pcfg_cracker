.. image:: image/getty_7.jpg
  :width: 400
  :alt: Getty the Goblin Picture 7
  
I felt it may be helpful to lay out some design principles for this particular PCFG implementation. None of these are hard rules, but they will influence any merge requests I accept. I also hope they explain certain architectural choices I've made when developing this code. Note, these policies only apply to this particular PCFG implementation. For example in the C compiled version of the PCFG is by its very nature going to be harder to install and run than the Python version in this repository.

1. The code should be easy to install and run

  - A good number of the people who use this code-base are researchers and students new to security research. I'm convinced one of the reasons why this work has been able to have the impact it has is that researchers can download it and use it within minutes. Let's face it, security research is hard and most tools out there have a steep learning curve. Making something easy for people is often worth a lot more than a new feature provided by a hard to install package.
  
  - As a corollary to this point, I am extremely resistant to include **numpy** as a required library. The versioning issues numpy has, along with the platform specific compiler needed makes it much more difficult to create portable and easy to install tools.
  
  - I'm also resistant to adding any other additional required Python packages to this code-base. If there is a good reason and it's not numpy I'm open to hearing about adding new features that require additional libraries but will need a pretty good justification to accept a merge request. I will also try to ensure that the codebase can run without that package/feature. An example of how an optional library is currently treated in the codebase is the **chardet** library. chardet is pretty common and installed in most Python environments, but if people don't have it they can still train rulesets. They just have to manually detect and specify the encoding used in the training set themselves.
  
  - This toolset should work on both Windows and most Linux variants. So for example, if you need to reference a file path, make sure you use `os.path.join()` vs. hardcoding in an OS specific backslash or forward-slash.
  
2. Whenever possible, the program should learn from the training set vs. having regexs or strings pre-defined

  - This is a rule which I've broken a lot. For example the "Context Sensitive" X replacements are all pre-defined. Also things like e-mail and website TLDs are hard-coded in. Hence the weaselly word "whenever possible"
  
  - An example of this approach in practice is how multi-word detection is handled. There is no predefined list of words to identify what is a multi-word and what is not. It learns all the base words during training.
  
  - Learning from the training set is the desired approach because it makes the tools more language agnostic, and more importantly, pre-defined lists are really hard to maintain and often have frequent gaps. Also there are hidden benefits. For example, people often put words such as "Fall" or "June" at the end of passwords where there is a mandatory password change policy in place. The PCFG currently doesn't have any logic tailored to this specific mangling technique, but it gets it partially for "free" with the way it currently learns multi-words from the training set.
  
3. When possible, there should be a clear delimitation between the training phase and the running phase of tools in this repo

  - This is another way of saying when training, save the output and then process that output with other tools when you want to use it.
  
  - The reasoning behind this is that I've found it extremely useful to have the training set available to manually tweak or to make available for other tools and uses. 