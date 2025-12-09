#!/bin/bash

echo "========================================"
echo "Deploy Backend to GitHub"
echo "========================================"
echo ""

echo "Este script te ayudará a subir el backend a GitHub"
echo ""

echo "PASO 1: Asegúrate de haber creado un repositorio en GitHub"
echo "Nombre sugerido: ai-music-detector-backend"
echo ""
read -p "Presiona Enter para continuar..."

echo ""
echo "PASO 2: Ingresa la URL de tu repositorio"
echo "Ejemplo: https://github.com/tu-usuario/ai-music-detector-backend.git"
echo ""
read -p "URL del repositorio: " REPO_URL

echo ""
echo "Inicializando Git..."
git init

echo ""
echo "Agregando archivos..."
git add .

echo ""
echo "Creando commit..."
git commit -m "Backend inicial para Railway deployment"

echo ""
echo "Conectando con GitHub..."
git remote add origin "$REPO_URL"

echo ""
echo "Subiendo código..."
git branch -M main
git push -u origin main

echo ""
echo "========================================"
echo "¡Listo! Tu código está en GitHub"
echo "========================================"
echo ""
echo "Ahora ve a Railway:"
echo "1. https://railway.app/"
echo "2. New Project"
echo "3. Deploy from GitHub repo"
echo "4. Selecciona tu repositorio"
echo ""
