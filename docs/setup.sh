#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "[-] Este script debe ejecutarse como root (sudo)."
  exit 1
fi

echo "[+] Limpiando cualquier rastro previo de Chaotic y Sinergia en pacman.conf..."
sed -i '/\[chaotic-aur\]/,+1d' /etc/pacman.conf
sed -i '/\[sinergia\]/,+3d' /etc/pacman.conf
sed -i '/\[sinergia-repo\]/,+3d' /etc/pacman.conf
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

echo "" >> /etc/pacman.conf
echo "[sinergia]" >> /etc/pacman.conf
echo "SigLevel = Required DatabaseOptional" >> /etc/pacman.conf
echo "Server = https://Nacho-Telmo.github.io/sinergia-repo/\$arch" >> /etc/pacman.conf

echo "[+] Importando y firmando la clave GPG de Sinergia desde el repositorio..."
curl -s https://nacho-telmo.github.io/sinergia-repo/x86_64/sinergia-key.asc | pacman-key --add -
pacman-key --lsign-key 33986859CBA9A0329EE9321E1AA165CC95EBE1F1

echo "[+] Sincronizando bases de datos (con reintentos por estabilidad)..."
retries=5
success=0
while [ $retries -gt 0 ]; do
  if pacman -Syu --noconfirm; then
    success=1
    break
  fi
  echo "[-] Sincronización falló. Reintentando en 5 segundos... ($retries intentos restantes)"
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
  yay \
  sinergia-keyring \
  sinergia-welcome

# Desinstalar aplicaciones y componentes no deseados
echo "[+] Desinstalando componentes y aplicaciones seleccionadas (Discover, KDE Connect, Vim, Plasma Bigscreen)..."
pacman -R --noconfirm \
  discover \
  kdeconnect \
  vim \
  plasma-bigscreen

echo "[+] ¡Instalación y configuración completa de Sinergia finalizada con éxito! 🐧🚀"
