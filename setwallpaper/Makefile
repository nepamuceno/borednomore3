CC = gcc
CFLAGS = -Wall -O3 -fPIC
LIBS = -lX11 -lImlib2
PREFIX = /usr/local

TARGETS = native-setwallpaper native-setwallpaper.so

all: $(TARGETS)

native-setwallpaper: native-setwallpaper.c
	$(CC) $(CFLAGS) -o native-setwallpaper native-setwallpaper.c $(LIBS)

native-setwallpaper.so: native-setwallpaper.c
	$(CC) $(CFLAGS) -shared -o native-setwallpaper.so native-setwallpaper.c $(LIBS)

test: native-setwallpaper
	./native-setwallpaper ../wallpapers/wallpaper_00001.jpg

bench: native-setwallpaper native-setwallpaper.so
	./benchmark.py -f "../wallpapers/*.jpg" -l 5

install: native-setwallpaper native-setwallpaper.so
	install -Dm755 native-setwallpaper $(DESTDIR)$(PREFIX)/bin/native-setwallpaper
	install -Dm755 native-setwallpaper.so $(DESTDIR)$(PREFIX)/lib/native-setwallpaper.so

clean:
	rm -f native-setwallpaper native-setwallpaper.so *.o

.PHONY: all test bench install clean
