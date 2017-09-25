CC=g++
XFLAG =-Wall -ansi -pedantic
CFLAG =
main: pcfg_manager 


pcfg_manager: pcfg_manager.o tty.o brown_grammar.o standard_grammar.o
	$(CC) $(CFLAG) pcfg_manager.o tty.o brown_grammar.o standard_grammar.o -O3 -o pcfg_manager
	
pcfg_manager.o: pcfg_manager.cpp
	$(CC) $(CFLAG) -c pcfg_manager.cpp

tty.o: tty.c
	$(CC) $(CFLAG) -c tty.c

brown_grammar.o: brown_grammar.cpp
	$(CC) $(CFLAG) -c brown_grammar.cpp

standard_grammar.o: standard_grammar.cpp
	$(CC) $(CFLAG) -c standard_grammar.cpp

clean:
	rm -f pcfg_manager 
	rm -f *.o
