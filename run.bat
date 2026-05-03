@echo off
REM =====================================================================
REM run.bat - Script de inicio automatico de CampusAI (Windows)
REM =====================================================================
REM Uso:
REM     Doble clic en run.bat
REM     o desde CMD:  run.bat
REM
REM Este script:
REM   1. Verifica que Python este instalado
REM   2. Crea un entorno virtual si no existe
REM   3. Instala todas las dependencias
REM   4. Verifica que .env tenga la clave de Groq
REM   5. Arranca el servidor uvicorn
REM =====================================================================

setlocal enabledelayedexpansion

echo ========================================
echo    CampusAI - Inicio automatico
echo ========================================

REM Cambiar al directorio del backend
cd /d "%~dp0backend"

REM ---------- 1. Verificar Python ----------
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo Descargalo desde: https://www.python.org/downloads/
    echo IMPORTANTE: Marca "Add Python to PATH" en el instalador.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo [OK] Python detectado: !PYVER!

REM ---------- 2. Crear entorno virtual ----------
if not exist "venv\" (
    echo [INFO] Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado
) else (
    echo [OK] Entorno virtual ya existe
)

REM Activar el entorno virtual
call venv\Scripts\activate.bat

REM ---------- 3. Instalar dependencias ----------
echo [INFO] Instalando dependencias (puede tardar la primera vez)...
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas

REM ---------- 4. Verificar .env ----------
if not exist ".env" (
    echo [ERROR] No existe el archivo .env
    pause
    exit /b 1
)

findstr /C:"GROQ_API_KEY=TU_API_KEY_AQUI" .env >nul
if not errorlevel 1 (
    echo.
    echo ========================================
    echo    AVISO: Configura tu clave de Groq
    echo ========================================
    echo Edita el archivo: backend\.env
    echo Reemplaza TU_API_KEY_AQUI por tu clave real.
    echo Obtenla GRATIS en: https://console.groq.com/keys
    echo.
    echo El servidor arrancara igual, pero el chat IA no funcionara
    echo hasta que pongas tu clave ^(las FAQ si funcionan^).
    echo.
    pause
)

REM ---------- 5. Arrancar servidor ----------
echo.
echo ========================================
echo    Iniciando servidor en puerto 8000
echo ========================================
echo.
echo Chat:           http://localhost:8000
echo Documentacion:  http://localhost:8000/docs
echo.
echo Presiona Ctrl+C para detener el servidor.
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
