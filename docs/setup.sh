#!/bin/bash

# Asegurar que el script se ejecute como root
if [ "$EUID" -ne 0 ]; then
  echo "[-] Este script debe ejecutarse como root (sudo)."
  exit 1
fi

echo "[+] Configurando repositorios para Sinergia..."

# 1. Configurar Chaotic-AUR de forma 100% desatendida (sin prompts de claves)
echo "[+] Añadiendo Chaotic-AUR (Keyring y Mirrorlist)..."
pacman-key --init

# Crear un archivo de configuración temporal para pacman sin verificación de firmas en este paso
TEMP_CONF=$(mktemp)
grep -v '^SigLevel' /etc/pacman.conf > "$TEMP_CONF"
echo "SigLevel = Never" >> "$TEMP_CONF"

# Instalar keyring y mirrorlist de Chaotic sin fricción ni preguntas
pacman -U --config "$TEMP_CONF" --noconfirm --needed \
  'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' \
  'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'
rm -f "$TEMP_CONF"

# Poblar la clave de Chaotic recién instalada en el llavero local de pacman
pacman-key --populate chaotic

if ! grep -q "\[chaotic-aur\]" /etc/pacman.conf; then
  echo "" >> /etc/pacman.conf
  echo "[chaotic-aur]" >> /etc/pacman.conf
  echo "Include = /etc/pacman.d/chaotic-mirrorlist" >> /etc/pacman.conf
fi

# 2. Configurar el repositorio oficial de Sinergia (sinergia-repo)
echo "[+] Añadiendo repositorio personalizado de Sinergia..."
if ! grep -q "\[sinergia-repo\]" /etc/pacman.conf; then
  cat << 'EOF' >> /etc/pacman.conf

[sinergia-repo]
SigLevel = Optional TrustAll
Server = https://Nacho-Telmo.github.io/sinergia-repo/\$arch
EOF
fi

echo "[+] Sincronizando bases de datos de paquetes..."
pacman -Syu --noconfirm

# 3. Instalar dependencias base, herramientas y sinergia-keyring / sinergia-welcome
echo "[+] Instalando componentes de Sinergia y utilidades base..."
pacman -S --noconfirm --needed \
  base-devel \
  git \
  wget \
  curl \
  sinergia-keyring \
  sinergia-welcome

# 4. Instalar yay (AUR Helper) de forma automatizada para los paquetes auxiliares
if ! command -v yay &> /dev/null; then
  echo "[+] Instalando yay desde AUR..."
  TEMP_DIR=$(mktemp -d)
  cd "$TEMP_DIR"
  sudo -u ${SUDO_USER:-$(whoami)} git clone https://aur.archlinux.org/yay-bin.git
  cd yay-bin
  sudo -u ${SUDO_USER:-$(whoami)} makepkg -si --noconfirm
  cd ~
  rm -rf "$TEMP_DIR"
fi

echo "[+] ¡Instalación y configuración completa de Sinergia finalizada con éxito! 🐧🚀"
