#!/bin/bash
# =====================================================================
# run.sh - Script de inicio automatico de CampusAI (Linux/Mac)
# =====================================================================
# Uso:
#     chmod +x run.sh
#     ./run.sh
#
# Este script:
#   1. Verifica que Python 3 este instalado
#   2. Crea un entorno virtual si no existe
#   3. Instala todas las dependencias
#   4. Verifica que .env tenga la clave de Groq
#   5. Arranca el servidor uvicorn
# =====================================================================

set -e  # Detener al primer error

# Colores para mensajes (opcional, solo estetica)
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # Sin color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   CampusAI - Inicio automatico${NC}"
echo -e "${GREEN}========================================${NC}"

# Cambiar al directorio del backend (donde esta este script + /backend)
cd "$(dirname "$0")/backend"

# ---------- 1. Verificar Python ----------
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 no esta instalado.${NC}"
    echo "Descargalo desde: https://www.python.org/downloads/"
    exit 1
fi
echo -e "${GREEN}[OK] Python detectado: $(python3 --version)${NC}"

# ---------- 2. Crear entorno virtual ----------
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[INFO] Creando entorno virtual...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}[OK] Entorno virtual creado${NC}"
else
    echo -e "${GREEN}[OK] Entorno virtual ya existe${NC}"
fi

# Activar el entorno virtual
source venv/bin/activate

# ---------- 3. Instalar dependencias ----------
echo -e "${YELLOW}[INFO] Instalando dependencias (puede tardar la primera vez)...${NC}"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo -e "${GREEN}[OK] Dependencias instaladas${NC}"

# ---------- 4. Verificar .env ----------
if [ ! -f ".env" ]; then
    echo -e "${RED}[ERROR] No existe el archivo .env${NC}"
    exit 1
fi

# Verificar si la clave sigue como placeholder
if grep -q "GROQ_API_KEY=TU_API_KEY_AQUI" .env; then
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}   AVISO: Configura tu clave de Groq${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo "Edita el archivo: backend/.env"
    echo "Reemplaza TU_API_KEY_AQUI por tu clave real."
    echo "Obtenla GRATIS en: https://console.groq.com/keys"
    echo ""
    echo "El servidor arrancara igual, pero el chat IA no funcionara"
    echo "hasta que pongas tu clave (las FAQ si funcionan)."
    echo ""
    read -p "Presiona ENTER para continuar..."
fi

# ---------- 5. Arrancar servidor ----------
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Iniciando servidor en puerto 8000${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Chat:           http://localhost:8000"
echo "Documentacion:  http://localhost:8000/docs"
echo ""
echo "Presiona Ctrl+C para detener el servidor."
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
