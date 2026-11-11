#!/bin/bash

# ==========================================
# CONFIGURACIÓN DE REPOSITORIOS (SINERGIA + CHAOTIC-AUR)
# ==========================================
REPO_URL="https://nacho-telmo.github.io/sinergia-repo/x86_64"
KEY_URL="https://nacho-telmo.github.io/sinergia-repo/x86_64/sinergia-key.asc"
KEY_ID="33986859CBA9A0329EE9321E1AA165CC95EBE1F1"
REPO_NAME="sinergia"
# ==========================================

# 1. Verificar privilegios de root[cite: 3]
if [ "$EUID" -ne 0 ]; then
  echo "[-] Este script debe ejecutarse con sudo o como root."[cite: 3]
  exit 1
fi

echo "[+] Configurando repositorios para Sinergia..."[cite: 3]

# 2. Configurar Chaotic-AUR con reintentos automáticos de servidores de llaves
echo "[+] Añadiendo Chaotic-AUR (Keyring y Mirrorlist)..."[cite: 3]
for server in hkps://keyserver.ubuntu.com:443 hkp://keyserver.ubuntu.com pgp.mit.edu keys.openpgp.org; do
  if pacman-key --recv-key 3056513887B78AEB --keyserver "$server"; then
    break
  fi
  echo "[!] Servidor $server no disponible, intentando con el siguiente..."
done

pacman-key --lsign-key 3056513887B78AEB[cite: 3]
pacman -U --noconfirm 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst'[cite: 3]
pacman -U --noconfirm 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'[cite: 3]

if ! grep -q "\[chaotic-aur\]" /etc/pacman.conf; then[cite: 3]
  echo "" >> /etc/pacman.conf[cite: 3]
  echo "[chaotic-aur]" >> /etc/pacman.conf[cite: 3]
  echo "Include = /etc/pacman.d/chaotic-mirrorlist" >> /etc/pacman.conf[cite: 3]
  echo "[+] Chaotic-AUR añadido a /etc/pacman.conf"[cite: 3]
fi

# 3. Importar y firmar la clave GPG oficial del repositorio Sinergia[cite: 3]
echo "[+] Descargando e importando la clave GPG de Sinergia..."[cite: 3]
curl -s "$KEY_URL" | pacman-key --add -[cite: 3]

echo "[+] Otorgando confianza local a la clave ($KEY_ID)..."[cite: 3]
pacman-key --lsign-key "$KEY_ID"[cite: 3]

# 4. Añadir el repositorio Sinergia a /etc/pacman.conf si no está presente[cite: 3]
if ! grep -q "\[$REPO_NAME\]" /etc/pacman.conf; then[cite: 3]
  echo "" >> /etc/pacman.conf[cite: 3]
  echo "[$REPO_NAME]" >> /etc/pacman.conf[cite: 3]
  echo "SigLevel = Required DatabaseOptional" >> /etc/pacman.conf[cite: 3]
  echo "Server = $REPO_URL/" >> /etc/pacman.conf[cite: 3]
  echo "[+] Repositorio Sinergia añadido correctamente a /etc/pacman.conf"[cite: 3]
else
  echo "[i] El repositorio Sinergia ya estaba configurado en /etc/pacman.conf"[cite: 3]
fi

# 5. Sincronizar bases de datos e instalar yay, keyring y la tienda[cite: 3]
echo "[+] Sincronizando bases de datos con pacman -Syy..."[cite: 3]
pacman -Syy --noconfirm[cite: 3]

echo "[+] Instalando yay, sinergia-keyring y sinergia-welcome..."[cite: 3]
pacman -S --noconfirm yay sinergia-keyring sinergia-welcome[cite: 3]

echo "¡Listo! El sistema ya cuenta con Chaotic-AUR, Sinergia Repo y la Sinergia Welcome operativa. 🐧🚀"[cite: 3]
