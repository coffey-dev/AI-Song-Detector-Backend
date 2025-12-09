#!/bin/bash

echo "============================================"
echo " AI Music Detector - Backend Starter"
echo "============================================"
echo ""

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "[1/3] Creando entorno virtual..."
    python3 -m venv venv
    echo "    ✓ Entorno virtual creado!"
else
    echo "[1/3] Entorno virtual ya existe"
fi

echo ""
echo "[2/3] Activando entorno virtual..."
source venv/bin/activate

echo ""
echo "[3/3] Instalando/Verificando dependencias..."
pip install -r requirements.txt --quiet

echo ""
echo "============================================"
echo " Iniciando servidor Flask..."
echo "============================================"
echo ""
python app.py
