@echo off
echo ============================================
echo  AI Music Detector - Backend Starter
echo ============================================
echo.

REM Verificar si existe el entorno virtual
if not exist "venv\" (
    echo [1/3] Creando entorno virtual...
    python -m venv venv
    echo     Entorno virtual creado!
) else (
    echo [1/3] Entorno virtual ya existe
)

echo.
echo [2/3] Activando entorno virtual...
call venv\Scripts\activate

echo.
echo [3/3] Instalando/Verificando dependencias...
pip install -r requirements.txt --quiet

echo.
echo ============================================
echo  Iniciando servidor Flask...
echo ============================================
echo.
python app.py

pause
