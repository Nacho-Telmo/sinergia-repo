#!/bin/bash
set -e

KEY_ID="4CBFA5A14BB153A7"
REPO_DIR="$HOME/sinergia-repo/x86_64"

echo "==> Entrando a la carpeta del repositorio..."
cd "$REPO_DIR"

echo "==> Firmando paquetes .pkg.tar.zst no firmados..."
for pkg in *.pkg.tar.zst; do
    if [ -f "$pkg" ] && [ ! -f "${pkg}.sig" ]; then
        echo "Firmando $pkg..."
        gpg --detach-sign --use-agent -u "$KEY_ID" "$pkg"
    fi
done

echo "==> Actualizando base de datos firmada con repo-add..."
repo-add -s -k "$KEY_ID" sinergia.db.tar.gz *.pkg.tar.zst

echo "==> Reestructurando archivos para servidores web..."
rm -f sinergia.db sinergia.files
mv sinergia.db.tar.gz sinergia.db
mv sinergia.db.tar.gz.sig sinergia.db.sig
mv sinergia.files.tar.gz sinergia.files
mv sinergia.files.tar.gz.sig sinergia.files.sig

echo "==> Exportando clave pública actualizada..."
gpg --export --armor "$KEY_ID" > sinergia.gpg

echo "==> Sincronizando con Git y GitHub Pages..."
cd "$HOME/sinergia-repo"
read -p "Mensaje de commit: " commit_msg
commit_msg=${commit_msg:-"Actualización de paquetes y firmas GPG"}
git add .
git commit -m "$commit_msg"
git push

echo "==> ¡Repositorio de Sinergia actualizado y firmado correctamente!"
