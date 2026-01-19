# Makefile para setwallpaper
CC = gcc
CFLAGS = -Wall -O2
LIBS = -lX11 -lImlib2

TARGET = setwallpaper
SRC = setwallpaper.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LIBS)

clean:
	rm -f $(TARGET) *.o
