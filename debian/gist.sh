#!/bin/bash

OUTPUT="gist.txt"
> "$OUTPUT"
BASE_DIR=$(pwd)

echo "Generando $OUTPUT..."

# Find only source code files
find "$BASE_DIR" -type f \
    \( -name "*.py" -o -name "*.sh" -o -name "*.md" -o -name "*.txt" \
       -o -name "*.conf" -o -name "*.list" -o -name "*.desktop" \
       -o -name "Makefile" -o -name "*.env" -o -name "*.1" \) \
    -not -path '*/.*' \
    -not -path '*/__pycache__/*' \
    -not -path '*/dist/*' \
    -not -path '*/wallpapers/*' \
    -not -name "$OUTPUT" \
    -not -name "gist.sh" | while read -r file; do
    
    # Additional check to exclude binary/compiled files
    if [[ "$file" != *.pyc ]] && [[ "$file" != *.so ]] && [[ "$file" != *.o ]]; then
        echo "=== $file ===" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
        
        # Add file content
        if [ -s "$file" ]; then
            cat "$file" >> "$OUTPUT"
        else
            echo "(empty file)" >> "$OUTPUT"
        fi
        
        echo -e "\n\n" >> "$OUTPUT"
    fi
done

# --- NUEVA PARTE: COPIAR AL PORTAPAPELES ---
if command -v xclip &> /dev/null; then
    cat "$OUTPUT" | xclip -selection clipboard
    echo "✅ Archivo generado y COPIADO al portapapeles. ¡Dale Ctrl+V en GitHub!"
else
    echo "✅ Archivo generado en: $BASE_DIR/$OUTPUT"
    echo "⚠️  xclip no está instalado. Instálalo con 'sudo apt install xclip' para copiar automáticamente."
fi
