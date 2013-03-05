proxy : proxy.o
	cc -Werror -o proxy proxy.o

proxy.o: proxy.c
	cc -Werror -c proxy.c

clean:
	rm *.o proxy
