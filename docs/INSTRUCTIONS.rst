.. image:: image/getty_2.jpg
  :width: 400
  :alt: Getty the Goblin Picture 2

How to build/update the Developer's Guide
------------------------------------------

Sphinx is used to create the Developer's Guide. To install Sphinx:

`python -m pip install sphinx`

To create an HTML viewable version of the Developer's Guide run:

`sphinx-build -b html docs\source docs\build`

Then you can view the Developer's Guide at docs\build\index.html

To create a PDF of the Developer's Guide you will need a LaTeX distribuion, the latexmk package, and likely PERL as well.

Building Docs on Windows:
~~~~~~~~~~~~~~~~~~~~~~~~~

One option is to install https://miktex.org/. There is a bunch of spammy links on the website. My apologies. Click on the download link. Do NOT click on the "START NOW" link. Once you have it installed, open the Miktex program, click packages button and then select latexmk to install that package. Around this point you might realize that building the html documentation might have been easier. Let me apologize on behalf of the academic community. The next step is you'll need to install perl. https://www.perl.org/get.html. I use strawberryperl simply because the install process was less annoying. A quick link to that is https://strawberryperl.com/. 

Ok, if you had any command prompt windows open, you'll now need to close and reopen them for the links to latexmk to work. Now you should hopefully be able to build a PDF of the document.

Now in a terminal or command prompt navigate to the ./docs directory and run: `make latexpdf`. The build may require installing additional LaTeX packages. I had to install what felt like 50 of them for the basic "hello world" pdf example. I swear I am not knowingly installing any malware or backdoors on your computer with this. If all of this worked you should now be able to view the pdf in docs\\build\\latex\\pcfgdevelopersguide.pdf