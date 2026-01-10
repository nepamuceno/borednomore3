#!/bin/bash

# 1. Cargar el secreto desde el archivo .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: No se encontró el archivo .env con el token."
    exit 1
fi

# Define las rutas
PROJECT_DIR="$HOME/borednomore3"
HIST_DIR="$PROJECT_DIR/history"
HIST_FILE="$HIST_DIR/last-100-history.txt"

# Usamos la variable $borednomore3_TOKEN cargada desde .env
REPO_URL="https://${borednomore3_TOKEN}@github.com/nepamuceno/borednomore3.git"

# Configuración de Tags
BASE_TAG="stable-$(date +'%d_%m_%Y_%H_%M')"
mkdir -p "$HIST_DIR"
tail -n 100 "$HOME/.bash_history" > "$HIST_FILE"

echo "--- Subiendo cambios a GitHub (borednomore3 - Modo Seguro) ---"
read -p "Ingresa mensaje del commit: " COMMIT_MSG
read -p "Nota extra para el tag (opcional): " EXTRA_NOTE

[ -n "$EXTRA_NOTE" ] && TAG_MSG="${BASE_TAG}-${EXTRA_NOTE}" || TAG_MSG="$BASE_TAG"

cd "$PROJECT_DIR" || exit 1

git add -A
git commit -m "$COMMIT_MSG"
git tag "$TAG_MSG"

# Push usando la URL con la variable enmascarada
git push "$REPO_URL" main --tags

echo "✅ Subida completada con éxito."
