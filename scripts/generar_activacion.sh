#!/bin/bash
# /desar/scripts/generar_activacion.sh
# Generador de codigos de activacion DESAR
# Uso: bash scripts/generar_activacion.sh [anio] [mes]
# Ejemplo: bash scripts/generar_activacion.sh 26 3
# (c) 2026 zSoft - Alex Rogelio Rodriguez Castañeda

SEMILLA1="matacuaz"
SEMILLA2="tecoman"

AZUL='\033[0;34m'
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
NC='\033[0m'

# Hash simple igual al algoritmo Dart
hash_semilla() {
  local semilla="$1"
  local hash=0
  local len=${#semilla}
  for ((i=0; i<len; i++)); do
    local char="${semilla:$i:1}"
    local code=$(printf '%d' "'$char")
    hash=$(( (hash * 31 + code) & 0xFFFFFFFF ))
  done
  echo ${hash#-}  # valor absoluto
}

generar_codigo() {
  local anio="$1"
  local mes="$2"

  # Validar entradas
  if [[ $anio -lt 25 || $anio -gt 35 ]]; then
    echo "Error: Año debe ser 25-35 (ej: 26 para 2026)" >&2
    exit 1
  fi
  if [[ $mes -lt 1 || $mes -gt 12 ]]; then
    echo "Error: Mes debe ser 1-12" >&2
    exit 1
  fi

  local s1hash=$(hash_semilla "$SEMILLA1")
  local s2hash=$(hash_semilla "$SEMILLA2")

  local b1=$(( s1hash % 9000 + 1000 ))
  local b2=$(( s2hash % 9000 + 1000 ))
  local b3=$(( anio * 100 + mes ))
  local b4=$(( (b1 + b2 + b3) % 9000 + 1000 ))

  printf "%04d%04d%04d%04d" $b1 $b2 $b3 $b4
}

# ─── Main ────────────────────────────────────────────────────
echo -e "${AZUL}╔══════════════════════════════════════════╗${NC}"
echo -e "${AZUL}║  DESAR - Generador de Activaciones       ║${NC}"
echo -e "${AZUL}║  (c) 2026 zSoft                          ║${NC}"
echo -e "${AZUL}╚══════════════════════════════════════════╝${NC}"
echo ""

if [[ $# -eq 2 ]]; then
  # Modo: argumento directo
  ANIO="$1"
  MES="$2"
  RAW=$(generar_codigo "$ANIO" "$MES")
  FORMATEADO="${RAW:0:4}-${RAW:4:4}-${RAW:8:4}-${RAW:12:4}"
  echo -e "  Año: 20${ANIO}  Mes: ${MES}"
  echo -e "  ${VERDE}Código RAW:        $RAW${NC}"
  echo -e "  ${VERDE}Código formateado: $FORMATEADO${NC}"
else
  # Modo interactivo: generar todos los meses del año especificado
  if [[ $# -eq 1 ]]; then
    ANIO="$1"
  else
    echo -n "  Año (25-35, ej 26 para 2026): "
    read ANIO
  fi

  echo ""
  echo -e "  ${AMARILLO}Códigos de activación para año 20${ANIO}:${NC}"
  echo -e "  ──────────────────────────────────────────"
  printf "  %-10s %-22s %-22s\n" "Mes" "Código RAW" "Código Formateado"
  echo -e "  ──────────────────────────────────────────"
  for mes in {1..12}; do
    RAW=$(generar_codigo "$ANIO" "$mes")
    FMT="${RAW:0:4}-${RAW:4:4}-${RAW:8:4}-${RAW:12:4}"
    NOMBRE_MES=$(date -d "2000-$(printf '%02d' $mes)-01" "+%B" 2>/dev/null || echo "Mes $mes")
    printf "  %-10s ${VERDE}%-22s${NC} ${VERDE}%s${NC}\n" "$NOMBRE_MES" "$RAW" "$FMT"
  done
  echo -e "  ──────────────────────────────────────────"
  echo ""
  echo -e "  ${AMARILLO}Uso: bash scripts/generar_activacion.sh <anio> <mes>${NC}"
  echo -e "  Ejemplo: bash scripts/generar_activacion.sh 26 6"
fi

echo ""
