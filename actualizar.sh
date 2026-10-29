#!/usr/bin/env bash
# ==============================================================================
# Script de actualización automatizada para Sinergia Repo
# División automática en partes de 45MB (Límite limpio para GitHub Pages)
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

if [ "$FILE_SIZE_MB" -gt 45 ]; then
    echo "⚡ El paquete supera los 45 MB. Dividiendo en fragmentos de 45 MB para GitHub Pages..."
    
    cp -f "$PKG_FILE" "$REPO_DIR/x86_64/"
    cd "$REPO_DIR/x86_64"
    
    # Dividir el archivo binario en bloques de 45MB
    split -b 45M "$PKG_FILE" "${PKG_FILE}.part-"
    
    # Firmar paquete original y actualizar base de datos pacman
    gpg --batch --yes --detach-sign --default-key "$GPG_KEY" "$PKG_FILE"
    repo-add --sign --key "$GPG_KEY" sinergia.db.tar.gz "$PKG_FILE"
    
    # Eliminar el archivo unificado gigante local para evitar el push de >100MB
    rm -f "$PKG_FILE"
else
    echo "➡ Copiando binario estándar a x86_64/..."
    cp -f "$PKG_FILE" "$REPO_DIR/x86_64/"
    cd "$REPO_DIR/x86_64"
    gpg --batch --yes --detach-sign --default-key "$GPG_KEY" "$PKG_FILE"
    repo-add --sign --key "$GPG_KEY" sinergia.db.tar.gz "$PKG_FILE"
fi

# 2. Sincronizar la receta en PKGBUILDs/
echo "📋 Actualizando receta en PKGBUILDs/$PKG_NAME/..."
mkdir -p "$REPO_DIR/PKGBUILDs/$PKG_NAME"
cp -f "$TARGET_DIR/PKGBUILD" "$REPO_DIR/PKGBUILDs/$PKG_NAME/PKGBUILD"

# 3. Actualizar la grilla en index.html de forma dinámica
cd "$REPO_DIR"
echo "🌐 Actualizando listado en index.html..."

TOTAL_PKGS=$(ls -1 x86_64/*.pkg.tar.* 2>/dev/null | grep -v '\.part-' | grep -v '\.sig' | wc -l)
sed -i "s/Aplicaciones Disponibles ([0-9]*)/Aplicaciones Disponibles ($TOTAL_PKGS)/g" index.html

GRID_CONTENT="            <div class=\"app-grid\">\n"
for pkg in $(ls -1 x86_64/*.pkg.tar.* 2>/dev/null | grep -v '\.part-' | grep -v '\.sig' | sed 's|x86_64/||g' | sed -E 's/-[0-9].*//g' | sort -u); do
    GRID_CONTENT="${GRID_CONTENT}                <div class=\"app-item\"><i class=\"fa-solid fa-cube\"></i> ${pkg}</div>\n"
done
GRID_CONTENT="${GRID_CONTENT}            </div>"

sed -i "/<div class=\"app-grid\">/,/<\/div>/c\\${GRID_CONTENT}" index.html

# 4. Git commit y push
echo "🚀 Sincronizando con GitHub Pages..."
git add x86_64/ PKGBUILDs/ index.html
git commit -m "refactor(script): split packages >45MB into clean 45MB chunks for GitHub Pages"
git push origin main

echo "=========================================================================="
echo "✅ ¡Script actualizado y sincronizado con éxito!"
echo "=========================================================================="
