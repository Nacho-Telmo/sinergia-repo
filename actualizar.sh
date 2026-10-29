#!/usr/bin/env bash
# ==============================================================================
# Script de actualización automatizada para Sinergia Repo
# ==============================================================================

set -e

REPO_DIR="/home/nacho/sinergia-repo"
TARGET_DIR="$1"
GPG_KEY="4CBFA5A14BB153A7"

if [ -z "$TARGET_DIR" ] || [ ! -d "$TARGET_DIR" ]; then
    echo "❌ Error: Debes indicar una carpeta válida con el PKGBUILD y el archivo compilado."
    exit 1
fi

cd "$TARGET_DIR"

# 1. Buscar binario (.zst o .xz) y PKGBUILD
PKG_FILE=$(ls -t *.pkg.tar.* 2>/dev/null | grep -E '\.(zst|xz)$' | grep -v '\.part-' | head -n 1)

if [ -z "$PKG_FILE" ] || [ ! -f "PKGBUILD" ]; then
    echo "❌ Error: No se encontró .pkg.tar.zst / .pkg.tar.xz válido o PKGBUILD en $TARGET_DIR"
    exit 1
fi

# Validar integridad del paquete
echo "🔍 Verificando integridad del paquete $PKG_FILE..."
if ! tar -tf "$PKG_FILE" .PKGINFO >/dev/null 2>&1; then
    echo "❌ Error: El archivo $PKG_FILE no es un paquete válido de Arch Linux."
    exit 1
fi

PKG_NAME=$(grep -E "^pkgname=" PKGBUILD | cut -d'=' -f2 | tr -d "'\"")
FILE_SIZE_MB=$(du -m "$PKG_FILE" | cut -f1)

echo "📦 Paquete detectado: $PKG_FILE ($FILE_SIZE_MB MB)"
echo "📄 Receta: $PKG_NAME"

# Limpiar versiones previas del mismo paquete en x86_64/
rm -f "$REPO_DIR/x86_64/$PKG_NAME"-*.pkg.tar.*

# Copiar binario a x86_64/
echo "➡ Copiando binario a x86_64/..."
cp -f "$PKG_FILE" "$REPO_DIR/x86_64/"
cd "$REPO_DIR/x86_64"

# Firmar paquete y actualizar base de datos pacman
gpg --batch --yes --detach-sign --default-key "$GPG_KEY" "$PKG_FILE"
repo-add --sign --key "$GPG_KEY" sinergia.db.tar.gz "$PKG_FILE"

# 2. Sincronizar la receta en PKGBUILDs/
echo "📋 Actualizando receta en PKGBUILDs/$PKG_NAME/..."
mkdir -p "$REPO_DIR/PKGBUILDs/$PKG_NAME"
cp -f "$TARGET_DIR/PKGBUILD" "$REPO_DIR/PKGBUILDs/$PKG_NAME/PKGBUILD"

# 3. Actualizar la grilla en index.html de forma dinámica (sin duplicados)
cd "$REPO_DIR"
echo "🌐 Actualizando listado en index.html..."

PKGS=$(ls -1 x86_64/*.pkg.tar.* 2>/dev/null | grep -v '\.sig' | grep -v '\.part-' | sed 's|x86_64/||g' | sed -E 's/-[0-9].*//g' | sort -u)
TOTAL=$(echo "$PKGS" | grep -c .)

sed -i "s/Aplicaciones Disponibles ([0-9]*)/Aplicaciones Disponibles ($TOTAL)/g" index.html

GRID="            <div class=\"app-grid\">"
for p in $PKGS; do
  GRID="$GRID\n                <div class=\"app-item\"><i class=\"fa-solid fa-cube\"></i> $p</div>"
done
GRID="$GRID\n            </div>"

perl -0777 -i -pe "s|<div class=\"app-grid\">.*?</div>|$GRID|s" index.html

# 4. Git commit y push
echo "🚀 Sincronizando con GitHub Pages..."
git add x86_64/ PKGBUILDs/ index.html actualizar.sh
git commit -m "fix(web): deduplicate package listing in index.html"
git push origin main

echo "=========================================================================="
echo "✅ ¡Script y sitio web sincronizados sin duplicados!"
echo "=========================================================================="
