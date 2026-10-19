#!/usr/bin/env bash
set -e

REPO_DIR="$HOME/sinergia-repo"
ARCH_DIR="$REPO_DIR/x86_64"
DB_NAME="sinergia.db.tar.gz"

cd "$ARCH_DIR"

echo "==> Moviendo nuevos paquetes desde la raíz si existen..."
mv "$REPO_DIR"/*.pkg.tar.zst "$ARCH_DIR"/ 2>/dev/null || true

echo "==> Actualizando base de datos de Pacman en x86_64..."
repo-add "$DB_NAME" *.pkg.tar.zst

echo "==> Reemplazando symlinks por archivos físicos para GitHub Pages..."
rm -f sinergia.db sinergia.files
cp sinergia.db.tar.gz sinergia.db
cp sinergia.files.tar.gz sinergia.files

cd "$REPO_DIR"

echo "==> Subiendo cambios a GitHub..."
git add .
git commit -m "Actualización automática del repositorio Sinergia (x86_64)" || true
git pull --rebase origin main
git push origin main

echo "==> ¡Repositorio Sinergia actualizado y publicado con éxito en GitHub Pages!"
