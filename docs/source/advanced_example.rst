.. image:: image/getty_5.jpg
  :width: 400
  :alt: Getty the Goblin Picture 5

Overview:
---------

Part of the feature enhancements of Version 4.3 of the PCFG Toolset is enhanced non-ASCII character set support. To demonstrate this, I figured it was time to release a new ruleset trained on non-English passwords to to complement the "Default" ruleset which was trained on a subset of the RockYou passwords. Part of the challenge of training a PCFG ruleset is finding a set of passwords that pairs well with the training process. It helps if the ruleset is created from a set of plaintext passwords. This is because you can't train on passwords you haven't cracked. Duplicate passwords also results in a more effective PCFG Ruleset. Otherwise how will you know that '123456' is more common than '348251'? Also, public password dumps have a lot of ... for lack of a better term ... junk in them. So finding a publicly available password dump that is relatively clean can be challenging. Finally you want to have a training set that resemebles passwords that you are trying to target. One password list that I have that meets many of those requirements is from VK.com which is the Russian equivalent of Facebook. The list I have was supposedly from a 2012 hack, (there's been other reported hacks, including one recently), and it made its way through many different hands before I was able to obtain a copy. To read more about the hack, here is a reference: https://thehackernews.com/2016/06/vk-com-data-breach.html. What's useful is that this list represents a good set of password for Russian speakers, the passwords are in plaintext, it includes duplicate passwords, and the copy I recieved seems to be relatively well formatted.

A quick note on ethics:
-----------------------

The password set I obtained did not include usernames or e-mail addresses. It only included the passwords. This was a bonus for me. I don't want to associate individual passwords with real people. While the PCFG grammar does a decend job of breaking down individual passwords, it does include private data in the generated ruleset that users included in their passwords. That's a big reason why I selected such an old set. All the passwords in the VK password list are at least 10 years old and have been extensively traded in underground circles. Therefore I believe the research use of such a ruleset outweights the privacy impact of making portions of this list partially available in the PCFG code repository. I have also not validated that these passwords are real, and from the actual 2012 vk.com hack. In fact, there's no way for me to truely validate this list. Once again, I view this as a bonus. While there are indicators that this list is in fact legit, (which I'll talk about in the training portion of this chapter), this list could be a fabrication.

Pre-processing the List:
------------------------

Since I'm planning on releasing this ruleset as part of the PCFG code repository, I want to keep the generated grammar relatively small. To this end, I selected a one million password subset of the original vk.com list to use in training. Previous tests have shown that while larger training sets can help improve the effectiveness of PCFG grammars, the value of larger training sets diminishes drastically after the first million passwords. In fact, even training on only 100 thousand password can be quite effective, but one million is a nice pleasing sounding number. An added advantage of this approach is I can then the remaining passwords to run tests against.

One tool that I would highly recommend to clean up password lists before training on is: https://github.com/NetherlandsForensicInstitute/demeuk. If you want to crack passwords like Europol agents, Demeuk is the tool for you. It is very effective at fixing encoding issues, cleaning up weird junk that tends to show up in password lists, as well as tailoring the training set to the password policies you are targeting. I'm going to talk about Demeuk more later, but as some background, I did not use it for the Russian ruleset included in this repo. I went back and forth on this, but in this case the testing I did showed that the code cleanup options in the core-PCFG code were sufficient for processing the training list without using Demeuk.

Training on Vk Passwords:
--------------------------

To create the Russian ruleset, I ran the PCFG trainer and only specified the training list and the ruleset name. I left the rest of the options at their default settings.

.. code-block::

     python3 trainer.py -t vk_1m.txt -r Russian
     
Doing this told me a couple of things. The first thing was that the encoding of this dataset was likely UTF-8, which is really helpful since that makes it more widely applicable for other cracking sessions. Here is an output from my training session that shows that.

.. image:: image/vk_encoding.png
  :width: 400
  :alt: PCFG trainer showing that the VK set was likely UTF-8
  
I've seen a number of other Russian password sets encoded as ISO 8859-5, or MacOS Cyrillic. This means converting your training set to the type of encoding you are targeting is very important. I'll cover that in more detail later. For now though, it's helpful to highlight that the Russian PCFG ruleset included in this code repo is made to target UTF-8 encoded passwords.

You can verify the autodetected encoding by looking at the number of encoding errors encountered when parsing the entire password set. You can see that in the following screenshot that no encoding errors were encountered during the training process.

.. image:: image/vk_encoding_errors.png
  :width: 400
  :alt: PCFG trainer showing no encoding errors were encountered, but it only processed 980k "actual" passwords
  
You might also notice that it only detected around 980 thousand valid passwords even through I passed it a training list of one million passwords. There's a number of reasons a line/password in the training list can be rejected, but the most common reason is the trainer will reject blank lines. This also means that a PCFG based attack will never guess a "blank" password. I've gone back and forth on if this is desired behavior or not, but given how messy training lists tend to be, rejecting blank lines generally seems to be the right call. This also means you might want to run a quick check to validate that a password exists and was not blank before running a PCFG based cracking attack.  Getting back to the VK list, I opened it up the training file troubleshoot this, and yes, it turned out that roughly 2% of the lines were blank. 

The final thin I want to mention about the training process is the statistics the trainer produces at the end. The following picture shows the statistics generated from training on the Vk list.

.. image:: image/vk_stats.png
  :width: 350
  :alt: PCFG trainer showing the statistics generated from the Vk training list
  
Looking at the e-mail list, it certainly appears this training list was created from russian speakers. Side note, bigmir.net is a Kiev based Ukrainian site, which is a good reminder that just because a list is made up of Russian speakers, it doesn't mean they are all Russian users. 

Looking at the top five URLs, you might notice a number of the top e-mail providers there as well. This is a common occurence I've seen across multiple different password dumps. Part of this is a limitation of the trainer. If the trainer parses username@mail.ru, the trainer can tell it is an e-mail account. If the trainer parses mail.ru though, that string without an '@' symbol looks like a URL. Probably the best way to handle this would be to identify e-mail providers during the first pass the trainer runs on the input list, but I haven't gotten around to implimenting that yet. This is all a long way to say you can usually skip past e-mail providers in the URL domains. Looking at the remaining URLs, we can see that vkontakte.ru is highlighted, which gives further credence that this password list came from Vk. This approach is very useful for identifying where random password lists originated from, which is something I end up dealing with quite a bit.

When it comes to years, you'll notice that 2010 is the most common year, despite the fact that this list supposidly was stolen around 2012. This actually matches up with behavior seen in other password disclosures as well. You need to remember that unless a manditory password change policy was in place, most of the passwords will have been created a year or two before the breach. Therefore you should expect a similar distribution. Opening up the Digits/1.txt file in the generated ruleset, I could see that 2012 was actually the 36th most common date found, with 2013 being the 76th most common date. This seems to validate the story that the password list was stolen in early 2012. The other point I'd like to raise is to highlight the prevalance of dates in the early 1990's. Since people tend to use their birthdays in their passwords, this implies that at the time of the theft, the user population skewed to be older teenagers to people in their early 20's.