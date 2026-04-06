#!/bin/bash
# /desar2/scripts/compilar.sh - DESAR v0.0.1-beta
# Compilacion sin flutter clean - solo recompila lo que cambio

APP="desar-0.0.1-beta"
MODO="${1:-debug}"
SALIDA="build/app/outputs/flutter-apk"
BUNDLE_DIR="build/app/outputs/bundle/release"
HTTP_PORT=8080

ok()    { echo "  OK: $1"; }
warn()  { echo "  AVISO: $1"; }
error() { echo "  ERROR: $1"; }

duracion() { echo "$((($1)/60))m $((($1)%60))s"; }

notificar() {
  notify-send "DESAR" "$1" 2>/dev/null || true
  paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || \
  aplay  /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || true
}

compilar() {
  local log=$(mktemp)
  local T=$SECONDS

  eval "$1" 2>&1 | tee "$log" | grep -E \
    "Compiling|Linking|Built|error:|Error|warning:|Running|Gradle" \
    --line-buffered || true

  local EXIT=${PIPESTATUS[0]}
  local DUR=$(duracion $((SECONDS - T)))

  if [ $EXIT -eq 0 ]; then
    ok "Listo en $DUR"
    notificar "Compilacion OK en $DUR"
  else
    error "Fallo en $DUR"
    echo ""
    error "Ultimas lineas:"
    tail -20 "$log" | grep -i "error\|exception\|failed" || tail -10 "$log"
    notificar "Compilacion FALLO"
    rm -f "$log"
    exit 1
  fi
  rm -f "$log"
}

# Verificaciones
echo "DESAR $MODO - $(date '+%H:%M:%S')"

[ ! -f "pubspec.yaml" ] && error "Ejecuta desde la raiz del proyecto" && exit 1
[ ! -f "assets/modelos_ia/facenet.tflite" ] && warn "Falta facenet.tflite - reconocimiento facial no funcionara"

# Firma
export KEYSTORE_PASSWORD="${KEYSTORE_PASSWORD:-Desar2026!}"
export KEY_ALIAS="${KEY_ALIAS:-desar}"
export KEY_PASSWORD="${KEY_PASSWORD:-Desar2026!}"

# Dependencias
flutter pub get

# Compilar
case "$MODO" in
  debug)
    compilar "flutter build apk --debug --target-platform android-arm64"
    cp "$SALIDA/app-debug.apk" "$SALIDA/${APP}-debug.apk" 2>/dev/null || true
    ;;
  release)
    compilar "flutter build apk --release --target-platform android-arm64"
    cp "$SALIDA/app-arm64-v8a-release.apk" "$SALIDA/${APP}-release.apk" 2>/dev/null || true
    ;;
  release-all)
    compilar "flutter build apk --release --split-per-abi"
    find "$SALIDA" -name "app-*-release.apk" | while read f; do
      arch=$(echo "$f" | sed 's/.*app-\(.*\)-release.apk/\1/')
      cp "$f" "$SALIDA/${APP}-release-${arch}.apk" 2>/dev/null || true
    done
    ;;
  bundle)
    compilar "flutter build appbundle --release"
    cp "$BUNDLE_DIR/app-release.aab" "$BUNDLE_DIR/${APP}.aab" 2>/dev/null || true
    ;;
  web)
    compilar "flutter build web --release"
    ;;
  linux)
    compilar "flutter build linux --release"
    ;;
  all)
    bash "$0" debug
    bash "$0" release
    bash "$0" bundle
    ;;
  *)
    echo "Uso: ./scripts/compilar.sh [debug|release|release-all|bundle|web|linux|all]"
    exit 1
    ;;
esac

# Archivos generados
echo ""
echo "Archivos:"
find "$SALIDA" "$BUNDLE_DIR" -name "${APP}*" 2>/dev/null | while read f; do
  SIZE=$(du -sh "$f" | cut -f1); ok "$(basename $f)  ($SIZE)"
done

# Servidor HTTP
echo ""
IP=$(ip addr show | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | cut -d/ -f1 | head -1)
echo "Descarga el APK en: http://${IP}:${HTTP_PORT}"
echo "Ctrl+C para detener"
echo ""
cd "$SALIDA" 2>/dev/null || cd "build/app/outputs" 2>/dev/null || cd build
python3 -m http.server $HTTP_PORT
