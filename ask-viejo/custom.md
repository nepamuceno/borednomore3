for i in ../debian/src/lxqt/wallpapers/*.jpg; do ./native-setwallpaper "$i" --sync-config;sleep 0.7;done
deb@deb-hp205g3aio:~/borednomore3/borednomore3/setwallpaper$ ls
ai-engine.md    benchmark.py  Makefile             native-setwallpaper.c   prompt.md       wallpaper_adapter.py
app_state.json  custom.md     native-setwallpaper  native-setwallpaper.so  setwallpaper.c

problem pacmanfm-qt gets corrupted

still i broke pacmanfm-qt, goes to a blank desktop randomly

deb@deb-hp205g3aio:~/borednomore3/borednomore3/setwallpaper$ ./native-setwallpaper --slideshow 0.7 ../debian/src/lxqt/wallpapers/*.jpg --sync-config
X Error of failed request:  BadGC (invalid GC parameter)
  Major opcode of failed request:  130 (MIT-SHM)
  Minor opcode of failed request:  3 (X_ShmPutImage)
  Resource id in failed request:  0x1600002
  Serial number of failed request:  13
  Current serial number in output stream:  14