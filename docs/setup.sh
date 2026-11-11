#!/bin/bash

# ==========================================
# CONFIGURACIÓN DE REPOSITORIOS (SINERGIA + CHAOTIC-AUR)
# ==========================================
REPO_URL="https://nacho-telmo.github.io/sinergia-repo/x86_64"
KEY_URL="https://nacho-telmo.github.io/sinergia-repo/x86_64/sinergia-key.asc"
KEY_ID="33986859CBA9A0329EE9321E1AA165CC95EBE1F1"
REPO_NAME="sinergia"
# ==========================================

# 1. Verificar privilegios de root
if [ "$EUID" -ne 0 ]; then
  echo "[-] Este script debe ejecutarse con sudo o como root."
  exit 1
fi

echo "[+] Configurando repositorios para Sinergia..."

# 2. Configurar Chaotic-AUR (Instalar paquetes PRIMERO para que el mirrorlist exista)
echo "[+] Añadiendo Chaotic-AUR (Keyring y Mirrorlist)..."
pacman-key --init
pacman -U --noconfirm --needed 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'

if ! grep -q "\[chaotic-aur\]" /etc/pacman.conf; then
  echo "" >> /etc/pacman.conf
  echo "[chaotic-aur]" >> /etc/pacman.conf
  echo "Include = /etc/pacman.d/chaotic-mirrorlist" >> /etc/pacman.conf
  echo "[+] Chaotic-AUR añadido a /etc/pacman.conf"
fi

# 3. Importar y firmar la clave GPG oficial del repositorio Sinergia
echo "[+] Descargando e importando la clave GPG de Sinergia..."
curl -s "$KEY_URL" | pacman-key --add -

echo "[+] Otorgando confianza local a la clave ($KEY_ID)..."
pacman-key --lsign-key "$KEY_ID"

# 4. Añadir el repositorio Sinergia a /etc/pacman.conf si no está presente
if ! grep -q "\[$REPO_NAME\]" /etc/pacman.conf; then
  echo "" >> /etc/pacman.conf
  echo "[$REPO_NAME]" >> /etc/pacman.conf
  echo "SigLevel = Required DatabaseOptional" >> /etc/pacman.conf
  echo "Server = $REPO_URL/" >> /etc/pacman.conf
  echo "[+] Repositorio Sinergia añadido correctamente a /etc/pacman.conf"
else
  echo "[i] El repositorio Sinergia ya estaba configurado en /etc/pacman.conf"
fi

# 5. Sincronizar bases de datos e instalar yay, keyring y la tienda
echo "[+] Sincronizando bases de datos con pacman -Syy..."
pacman -Syy --noconfirm

echo "[+] Instalando yay, sinergia-keyring y sinergia-store..."
pacman -S --noconfirm yay sinergia-keyring sinergia-store

echo "¡Listo! El sistema ya cuenta con Chaotic-AUR, Sinergia Repo y la Sinergia Store operativa. 🐧🚀"
