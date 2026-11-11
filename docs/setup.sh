#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "[-] Este script debe ejecutarse como root (sudo)."
  exit 1
fi

echo "[+] Inicializando llaveros de Pacman..."
pacman-key --init
pacman-key --populate archlinux

# Asegurar keyring oficial actualizado primero
pacman -S --noconfirm --needed archlinux-keyring

echo "[+] Configurando Chaotic-AUR..."
TEMP_CONF=$(mktemp)
grep -v '^SigLevel' /etc/pacman.conf > "$TEMP_CONF"
echo "SigLevel = Never" >> "$TEMP_CONF"

pacman -U --config "$TEMP_CONF" --noconfirm --needed \
  'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' \
  'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'
rm -f "$TEMP_CONF"

pacman-key --populate chaotic

if ! grep -q "\[chaotic-aur\]" /etc/pacman.conf; then
  echo "" >> /etc/pacman.conf
  echo "[chaotic-aur]" >> /etc/pacman.conf
  echo "Include = /etc/pacman.d/chaotic-mirrorlist" >> /etc/pacman.conf
fi

# Configurar el repositorio oficial de Sinergia (sinergia-repo)
echo "[+] Añadiendo repositorio personalizado de Sinergia..."
if ! grep -q "\[sinergia-repo\]" /etc/pacman.conf; then
  cat << 'EOF' >> /etc/pacman.conf

[sinergia-repo]
SigLevel = Optional TrustAll
Server = https://Nacho-Telmo.github.io/sinergia-repo/\$arch
EOF
fi

echo "[+] Sincronizando bases de datos..."
pacman -Syu --noconfirm

# Instalar componentes de Sinergia y utilidades base
echo "[+] Instalando componentes de Sinergia y utilidades base..."
pacman -S --noconfirm --needed \
  base-devel \
  git \
  wget \
  curl \
  sinergia-keyring \
  sinergia-welcome

# Instalar yay (AUR Helper) de forma automatizada
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
