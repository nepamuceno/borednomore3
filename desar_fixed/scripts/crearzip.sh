#!/bin/bash
# /desar2/scripts/crearzip.sh - Empaqueta solo codigo fuente

SALIDA="desar_src.zip"

rm -f "$SALIDA"

zip -r "$SALIDA" \
  lib/ \
  pubspec.yaml \
  pubspec.lock \
  android/app/src/main/AndroidManifest.xml \
  android/app/build.gradle \
  android/build.gradle.kts \
  android/settings.gradle.kts \
  android/gradle.properties \
  assets/fonts/ \
  assets/sonidos/ \
  scripts/ \
  --exclude "*/build/*" \
  --exclude "*/.dart_tool/*" \
  --exclude "*/.gradle/*" \
  --exclude "*/.git/*" \
  --exclude "*.apk" \
  --exclude "*.aab" \
  --exclude "*.zip" \
  --exclude "*.class" \
  --exclude "*.jar" \
  --exclude "*.lock" \
  --exclude "*/cache/*" \
  --exclude "*/.cache/*" \
  --exclude "*/generated/*" \
  --exclude "*/.plugin_symlinks/*" \
  --exclude "*/ephemeral/*" \
  --exclude "*.g.dart" \
  --exclude "*.freezed.dart"

echo ""
echo "Generado: $SALIDA ($(du -sh $SALIDA | cut -f1))"
echo "Archivos: $(unzip -l $SALIDA | tail -1 | awk '{print $2}')"
