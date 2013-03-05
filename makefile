proxy : proxy.o
	cc -g -pg -o proxy proxy.o

proxy.o: proxy.c
	cc -g -pg -c proxy.c

clean:
	rm *.o proxy
