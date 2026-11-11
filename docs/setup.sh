##!/bin/bash

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
# Crear un archivo de configuración temporal limpio exclusivamente para instalar los paquetes de Chaotic
TEMP_CONF=$(mktemp)
echo "SigLevel = Never" > "$TEMP_CONF"
echo "DBPath = /var/lib/pacman/" >> "$TEMP_CONF"
echo "CacheDir = /var/cache/pacman/pkg/" >> "$TEMP_CONF"

# Instalar keyring y mirrorlist sin tocar el pacman.conf principal todavía
pacman -U --config "$TEMP_CONF" --noconfirm --needed \
  'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' \
  'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'
rm -f "$TEMP_CONF"

# Poblar la clave de Chaotic
pacman-key --populate chaotic

# Añadir el repositorio a pacman.conf SOLAMENTE si el mirrorlist ya existe en el sistema
if [ -f /etc/pacman.d/chaotic-mirrorlist ] && ! grep -q "\[chaotic-aur\]" /etc/pacman.conf; then
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

# Instalar componentes de Sinergia, yay-bin y utilidades base
echo "[+] Instalando componentes de Sinergia, yay y utilidades base..."
pacman -S --noconfirm --needed \
  base-devel \
  git \
  wget \
  curl \
  yay-bin \
  sinergia-keyring \
  sinergia-welcome

echo "[+] ¡Instalación y configuración completa de Sinergia finalizada con éxito! 🐧🚀"
