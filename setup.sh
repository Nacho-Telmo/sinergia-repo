#!/bin/bash

# ==========================================
# CONFIGURACIÓN DEL REPOSITORIO SINERGIA
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

echo "[+] Configurando el repositorio $REPO_NAME..."

# 2. Importar y firmar la clave GPG oficial del repositorio
echo "[+] Descargando e importando la clave GPG..."
curl -s "$KEY_URL" | pacman-key --add -

echo "[+] Otorgando confianza local a la clave ($KEY_ID)..."
pacman-key --lsign-key "$KEY_ID"

# 3. Añadir el repositorio a /etc/pacman.conf si no está presente
if ! grep -q "\[$REPO_NAME\]" /etc/pacman.conf; then
  echo "" >> /etc/pacman.conf
  echo "[$REPO_NAME]" >> /etc/pacman.conf
  echo "SigLevel = Required DatabaseOptional" >> /etc/pacman.conf
  echo "Server = $REPO_URL/" >> /etc/pacman.conf
  echo "[+] Repositorio añadido correctamente a /etc/pacman.conf"
else
  echo "[i] El repositorio ya estaba configurado en /etc/pacman.conf"
fi

# 4. Sincronizar bases de datos e instalar el keyring y la tienda
echo "[+] Sincronizando bases de datos con pacman -Syy..."
pacman -Syy --noconfirm

echo "[+] Instalando sinergia-keyring y sinergia-store..."
pacman -S --noconfirm sinergia-keyring sinergia-store

echo "¡Listo! El repositorio de Sinergia ya está activo y operativo en tu sistema. 🐧🚀"
