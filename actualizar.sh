#!/usr/bin/env bash
# ==============================================================================
# Script de actualización automatizada para Sinergia Repo
# Uso: ./actualizar.sh /ruta/a/carpeta_del_paquete
# ==============================================================================

set -e

REPO_DIR="/home/nacho/sinergia-repo"
TARGET_DIR="$1"
GPG_KEY="4CBFA5A14BB153A7"

if [ -z "$TARGET_DIR" ] || [ ! -d "$TARGET_DIR" ]; then
    echo "❌ Error: Debes indicar una carpeta válida con el PKGBUILD y el archivo compilado."
    echo "Uso: $0 /ruta/al/directorio_de_compilacion"
    exit 1
fi

cd "$TARGET_DIR"

# 1. Buscar binario y PKGBUILD
PKG_FILE=$(ls -t *.pkg.tar.zst 2>/dev/null | head -n 1)

if [ -z "$PKG_FILE" ] || [ ! -f "PKGBUILD" ]; then
    echo "❌ Error: No se encontró .pkg.tar.zst o PKGBUILD en $TARGET_DIR"
    exit 1
fi

# Validar que el paquete sea un archivo .tar.zst estructurado correctamente
echo "🔍 Verificando integridad del paquete $PKG_FILE..."
if ! tar -tf "$PKG_FILE" .PKGINFO >/dev/null 2>&1; then
    echo "❌ Error: El archivo $PKG_FILE no es un paquete válido de Arch Linux (inválido o corrupto)."
    exit 1
fi

PKG_NAME=$(grep -E "^pkgname=" PKGBUILD | cut -d'=' -f2 | tr -d "'\"")

echo "📦 Paquete detectado: $PKG_FILE"
echo "📄 Receta: $PKG_NAME"

# 2. Copiar binario a x86_64/
echo "➡ Copiando binario a x86_64/..."
cp -f "$PKG_FILE" "$REPO_DIR/x86_64/"

# 3. Firmar paquete con GPG
echo "🔏 Firmando paquete con GPG..."
cd "$REPO_DIR/x86_64"
gpg --batch --yes --detach-sign --default-key "$GPG_KEY" "$PKG_FILE"

# 4. Actualizar la base de datos y firmarla
echo "🔄 Actualizando base de datos sinergia.db..."
repo-add --sign --key "$GPG_KEY" sinergia.db.tar.gz "$PKG_FILE"

# 5. Sincronizar la receta en PKGBUILDs/
echo "📋 Actualizando receta en PKGBUILDs/$PKG_NAME/..."
mkdir -p "$REPO_DIR/PKGBUILDs/$PKG_NAME"
cp -f "$TARGET_DIR/PKGBUILD" "$REPO_DIR/PKGBUILDs/$PKG_NAME/PKGBUILD"

# 6. Actualizar la grilla en index.html de forma dinámica
cd "$REPO_DIR"
echo "🌐 Actualizando listado en index.html..."

TOTAL_PKGS=$(ls -1 x86_64/*.pkg.tar.zst | wc -l)
sed -i "s/Aplicaciones Disponibles ([0-9]*)/Aplicaciones Disponibles ($TOTAL_PKGS)/g" index.html

GRID_CONTENT="            <div class=\"app-grid\">\n"
for pkg in $(ls -1 x86_64/*.pkg.tar.zst | sed 's|x86_64/||g' | sed -E 's/-[0-9].*//g' | sort -u); do
    GRID_CONTENT="${GRID_CONTENT}                <div class=\"app-item\"><i class=\"fa-solid fa-cube\"></i> ${pkg}</div>\n"
done
GRID_CONTENT="${GRID_CONTENT}            </div>"

sed -i "/<div class=\"app-grid\">/,/<\/div>/c\\${GRID_CONTENT}" index.html

# 7. Asegurar LFS y Subir a GitHub
echo "🚀 Sincronizando con GitHub..."
git lfs track "*.pkg.tar.zst" >/dev/null 2>&1 || true
git add .gitattributes x86_64/ PKGBUILDs/ index.html
git commit -m "feat(repo): add/update $PKG_NAME ($PKG_FILE)"
git push origin main

echo "=========================================================================="
echo "✅ ¡$PKG_NAME ($TOTAL_PKGS paquetes en total) publicado con éxito!"
echo "=========================================================================="
