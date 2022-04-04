.. image:: image/getty_2.jpg
  :width: 400
  :alt: Getty the Goblin Picture 2

How to Build/Update the Developer's Guide
------------------------------------------

Sphinx is used to create the Developer's Guide. To install Sphinx (the following assumes that python3 matches your Python 3 environment):

`python3 -m pip install sphinx`

To create an HTML viewable version of the Developer's Guide run:

`sphinx-build -b html docs\source docs\build`

Then you can view the Developer's Guide at docs\build\index.html

To create a PDF of the Developer's Guide you will need a LaTeX distribution, the latexmk package, and likely PERL as well.

Building a PDF Dev Guide on Windows:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First install sphinx as described above. Next you will need to install a LaTeX editor.

One option is to install https://miktex.org/. There is a bunch of spammy links on the website. My apologies. Click on the download link. Do NOT click on the "START NOW" link. Once you have it installed, open the Miktex program, click packages button and then select latexmk to install that package. Around this point you might realize that building the html documentation might have been easier. Let me apologize on behalf of the academic community. The next step is you'll need to install Perl. https://www.perl.org/get.html. I use strawberryperl simply because the install process was less annoying. A quick link to that is https://strawberryperl.com/. 

Ok, if you had any command prompt windows open, you'll now need to close and reopen them for the links to latexmk to work. Now you should hopefully be able to build a PDF of the document.

Next, in a terminal or command prompt navigate to the ./docs directory and run: `make latexpdf`. The build may require installing additional LaTeX packages. I had to install what felt like 50 of them for the basic "hello world" PDF example. I swear I am not knowingly installing any malware or backdoors on your computer with this. If all of this worked you should now be able to view the PDF in docs\\build\\latex\\pcfgdevelopersguide.pdf

If you receive an error saying that an image can not be found while building the PDF, my experience is that MiKTex has gotten confused. In the MiKTex GUI/console, click on Tasks and select "Refresh file name database". If this doesn't fix the problem, update all the packages in MiKTex and then refresh the file name database again.

Building a PDF Dev Guide on Linux:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First install sphinx as described above. If you get an error along the lines of `/bin/sh: 1: sphinx-build: not found` you did not install sphinx to the Python deployment it is trying to use. I'm sorry if that's happening, and while I can refer you to the sphinx documentation: https://www.sphinx-doc.org/en/master/usage/installation.html, your problem may be deeper than that with how Linux distros handle different Python environments. Basically if you were chuckling at the craziness with Windows, well this is the Linux equivalent.

Next you will need to install a LaTeX editor. In this case, the easiest one to install is `latexpdf` which hopefully should be easier to do on most Linux distros than on Windows. For example, on Ubuntu 20.1 you can simply type `sudo apt-get install -y latexmk`. Note, this installs what seems like a million fonts and templates. Once again, you have my word I'm not trying to hack you.

Next you need to install even more LaTeX extras to get cmap.sty. Why do you need cmap.sty? I'm not really sure, but it doesn't work without it. To get it, on Ubuntu you can run `sudo apt install -y texlive-latex-extra`

