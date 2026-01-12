#!/bin/bash

# 1. Cargar el secreto desde el archivo .env
if [ -f .env ]; then
    # Exportamos las variables (esto cargará NEPA_TOKEN)
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ Error: No se encontró el archivo .env"
    exit 1
fi

# 2. Validación de Token y Definición de URL
# Cambiamos borednomore3_TOKEN por NEPA_TOKEN para que coincida con tu archivo .env
if [ -z "$NEPA_TOKEN" ]; then
    echo "❌ Error: La variable NEPA_TOKEN está vacía en el archivo .env"
    exit 1
fi

# Definimos la URL usando tu usuario y el token cargado
GITHUB_USER="nepamuceno"
REPO_URL="https://${GITHUB_USER}:${NEPA_TOKEN}@github.com/${GITHUB_USER}/borednomore3.git"

# 3. Configuración de Rutas e Historial
PROJECT_DIR=$(pwd)
HIST_DIR="$PROJECT_DIR/history"
HIST_FILE="$HIST_DIR/last-100-history.txt"
mkdir -p "$HIST_DIR"

if [ -f "$HOME/.bash_history" ]; then
    tail -n 100 "$HOME/.bash_history" > "$HIST_FILE"
fi

# 4. Preparación de Mensajes y Tags
echo "--- Subiendo cambios a GitHub (borednomore3 - Modo Seguro) ---"
read -p "Ingresa mensaje del commit: " COMMIT_MSG

if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Update: $(date +'%Y-%m-%d %H:%M')"
fi

read -p "Nota extra para el tag (opcional): " EXTRA_NOTE
EXTRA_NOTE_CLEAN=$(echo "$EXTRA_NOTE" | tr ' ' '_')

BASE_TAG="stable-$(date +'%d_%m_%Y_%H_%M')"
if [ -n "$EXTRA_NOTE_CLEAN" ]; then
    TAG_MSG="${BASE_TAG}-${EXTRA_NOTE_CLEAN}"
else
    TAG_MSG="$BASE_TAG"
fi

# 5. Operaciones de Git
git add -A

# Solo hace commit si hay cambios detectados
if ! git diff-index --quiet HEAD --; then
    git commit -m "$COMMIT_MSG"
else
    echo "ℹ️ No hay cambios nuevos, solo se actualizarán tags si es necesario."
fi

git tag "$TAG_MSG"

# 6. Push con verificación de errores
echo "Enviando a GitHub..."
if git push "$REPO_URL" main --tags; then
    echo "✅ Subida completada con éxito como tag: $TAG_MSG"
else
    echo "❌ Error: Falló la subida. Eliminando tag local fallido..."
    git tag -d "$TAG_MSG"
    exit 1
fi
