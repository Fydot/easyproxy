proxy : proxy.o
	cc -Werror -g -pg -o proxy proxy.o

proxy.o: proxy.c
	cc -Werror -g -pg -c proxy.c

clean:
	rm *.o proxy
