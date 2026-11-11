#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "[-] Este script debe ejecutarse como root (sudo)."
  exit 1
fi

echo "[+] Limpiando configuraciones previas de Chaotic en pacman.conf..."
sed -i '/\[chaotic-aur\]/{N;N;d}' /etc/pacman.conf
sed -i '/chaotic-mirrorlist/d' /etc/pacman.conf

echo "[+] Inicializando llaveros de Pacman..."
pacman-key --init
pacman-key --populate archlinux

# Asegurar keyring oficial actualizado primero
pacman -S --noconfirm --needed archlinux-keyring

echo "[+] Configurando Chaotic-AUR..."
TEMP_CONF=$(mktemp)
echo "[options]" > "$TEMP_CONF"
echo "SigLevel = Never" >> "$TEMP_CONF"
echo "DBPath = /var/lib/pacman/" >> "$TEMP_CONF"
echo "CacheDir = /var/cache/pacman/pkg/" >> "$TEMP_CONF"

pacman -U --config "$TEMP_CONF" --noconfirm --needed \
  'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' \
  'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'
rm -f "$TEMP_CONF"

pacman-key --populate chaotic

if [ -f /etc/pacman.d/chaotic-mirrorlist ]; then
  echo "" >> /etc/pacman.conf
  echo "[chaotic-aur]" >> /etc/pacman.conf
  echo "Include = /etc/pacman.d/chaotic-mirrorlist" >> /etc/pacman.conf
fi

echo "[+] Añadiendo repositorio personalizado de Sinergia..."
if ! grep -q "\[sinergia-repo\]" /etc/pacman.conf; then
  cat << 'EOF' >> /etc/pacman.conf

[sinergia-repo]
SigLevel = Optional TrustAll
Server = https://Nacho-Telmo.github.io/sinergia-repo/\$arch
EOF
fi

echo "[+] Sincronizando bases de datos (con reintentos por estabilidad)..."
# Bucle de reintento en caso de error 503 temporal de GitHub Pages
retries=5
success=0
while [ $retries -gt 0 ]; do
  if pacman -Syu --noconfirm; then
    success=1
    break
  fi
  echo "[-] Sincronización falló (posible 503 de GitHub). Reintentando en 5 segundos... ($retries intentos restantes)"
  sleep 5
  retries=$((retries - 1))
done

if [ $success -eq 0 ]; then
  echo "[-] Error crítico: No se pudieron sincronizar las bases de datos tras varios intentos."
  exit 1
fi

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
