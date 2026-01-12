#!/bin/bash

# 1. Cargar el secreto desde el archivo .env
# Buscamos el archivo .env en el directorio actual
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: No se encontró el archivo .env con el token."
    exit 1
fi

# 2. Definir rutas dinámicamente
# Usamos $(pwd) para asegurarnos de que estamos en la carpeta correcta
PROJECT_DIR=$(pwd)
HIST_DIR="$PROJECT_DIR/history"
HIST_FILE="$HIST_DIR/last-100-history.txt"

# Usamos la variable cargada desde .env (Asegúrate que en el .env diga borednomore3_TOKEN=tu_token)
REPO_URL="https://${borednomore3_TOKEN}@github.com/nepamuceno/borednomore3.git"

# 3. Configuración de Tags (Formato: stable-DD_MM_YYYY_HH_MM)
BASE_TAG="stable-$(date +'%d_%m_%Y_%H_%M')"
mkdir -p "$HIST_DIR"

# Intentamos guardar el historial (esto puede fallar si el archivo de origen no existe)
if [ -f "$HOME/.bash_history" ]; then
    tail -n 100 "$HOME/.bash_history" > "$HIST_FILE"
fi

echo "--- Subiendo cambios a GitHub (borednomore3 - Modo Seguro) ---"
read -p "Ingresa mensaje del commit: " COMMIT_MSG

# Si el mensaje está vacío, usar uno por defecto
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Update: $(date +'%Y-%m-%d %H:%M')"
fi

read -p "Nota extra para el tag (opcional): " EXTRA_NOTE

# Limpiar espacios en la nota extra para que el tag sea válido en git
EXTRA_NOTE_CLEAN=$(echo "$EXTRA_NOTE" | tr ' ' '_')

if [ -n "$EXTRA_NOTE_CLEAN" ]; then
    TAG_MSG="${BASE_TAG}-${EXTRA_NOTE_CLEAN}"
else
    TAG_MSG="$BASE_TAG"
fi

# 4. Operaciones de Git
git add -A
git commit -m "$COMMIT_MSG"
git tag "$TAG_MSG"

# Push usando la URL con el token inyectado
echo "Enviando a GitHub..."
git push "$REPO_URL" main --tags

echo "✅ Subida completada con éxito como tag: $TAG_MSG"
