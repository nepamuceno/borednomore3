CC = gcc
CFLAGS = -Wall -O2
LIBS = -lX11 -lImlib2

all: setwallpaper benchmark

setwallpaper: setwallpaper.c
	$(CC) $(CFLAGS) -o setwallpaper setwallpaper.c $(LIBS)

benchmark: benchmark.py
	chmod +x benchmark.py

clean:
	rm -f setwallpaper
