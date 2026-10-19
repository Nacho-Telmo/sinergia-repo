#!/usr/bin/env bash
set -e

REPO_DIR="$HOME/sinergia-repo"
DB_NAME="sinergia.db.tar.gz"

cd "$REPO_DIR"

echo "==> Buscando nuevos paquetes (.pkg.tar.zst)..."
for pkg in *.pkg.tar.zst; do
    if [ -f "$pkg" ]; then
        echo "==> Agregando $pkg a la base de datos..."
        repo-add "$DB_NAME" "$pkg"
    fi
done

echo "==> Base de datos actualizada con éxito."
