CC=g++
XFLAG =-Wall -ansi -pedantic
CFLAG =
main: pcfg_manager 


pcfg_manager: pcfg_manager.o tty.o brown_grammar.o
	$(CC) $(CFLAG) pcfg_manager.o tty.o brown_grammar.o -03 -o pcfg_manager
	
pcfg_manager.o: pcfg_manager.cpp
	$(CC) $(CFLAG) -c pcfg_manager.cpp

tty.o: tty.c
	$(CC) $(CFLAG) -c tty.c

brown_grammar.o: brown_grammar.cpp
	$(CC) $(CFLAG) -c brown_grammar.cpp

clean:
	rm -f pcfg_manager 
	rm -f *.o
