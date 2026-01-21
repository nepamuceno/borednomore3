count=0
for i in ../debian/src/lxqt/wallpapers/*.jpg; do 
    ./native-setwallpaper "$i"
    sleep 0.7
    count=$((count+1))
    [ $count -ge 10 ] && break
done

# Sync only final wallpaper to pcmanfm-qt
last=$(ls ../debian/src/lxqt/wallpapers/*.jpg | head -n10 | tail -n1)
./native-setwallpaper "$last" --sync-config
