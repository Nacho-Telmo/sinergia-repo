#!/usr/bin/env bash
# ==============================================================================
# Script de actualización automatizada para Sinergia Repo
# Uso: ./actualizar.sh /ruta/a/carpeta_del_paquete
# Ejemplo: ./actualizar.sh ~/Proyectos/pkg-sinergia-webapp-manager
# ==============================================================================

set -e

REPO_DIR="/home/nacho/sinergia-repo"
TARGET_DIR="$1"

if [ -z "$TARGET_DIR" ] || [ ! -d "$TARGET_DIR" ]; then
    echo "❌ Error: Debes indicar una carpeta válida que contenga el PKGBUILD y el paquete compilado."
    echo "Uso: $0 /ruta/al/directorio_de_compilacion"
    exit 1
fi

cd "$TARGET_DIR"

# 1. Buscar el paquete .pkg.tar.zst más reciente en el directorio
PKG_FILE=$(ls -t *.pkg.tar.zst 2>/dev/null | head -n 1)

if [ -z "$PKG_FILE" ]; then
    echo "❌ Error: No se encontró ningún archivo .pkg.tar.zst en $TARGET_DIR"
    echo "Asegúrate de haber ejecutado 'makepkg -s' previamente."
    exit 1
fi

if [ ! -f "PKGBUILD" ]; then
    echo "❌ Error: No se encontró el archivo PKGBUILD en $TARGET_DIR"
    exit 1
fi

# Extraer el nombre base del paquete desde el PKGBUILD
PKG_NAME=$(grep -E "^pkgname=" PKGBUILD | cut -d'=' -f2 | tr -d "'\"")

echo "📦 Paquete detectado: $PKG_FILE"
echo "📄 Receta: $PKG_NAME"

# 2. Copiar binario a la carpeta x86_64/ del repo
echo "➡️  Copiando binario a x86_64/..."
cp -f "$PKG_FILE" "$REPO_DIR/x86_64/"

# 3. Firmar el paquete binario con GPG
echo "🔏 Firmando paquete con GPG..."
cd "$REPO_DIR/x86_64"
gpg --batch --yes --detach-sign --no-armor "$PKG_FILE"

# 4. Actualizar la base de datos sinergia.db y firmarla
echo "🔄 Actualizando base de datos sinergia.db..."
repo-add -s -n -R sinergia.db.tar.gz "$PKG_FILE"

# 5. Sincronizar el PKGBUILD en la carpeta PKGBUILDs/
echo "📋 Actualizando receta en PKGBUILDs/$PKG_NAME/..."
mkdir -p "$REPO_DIR/PKGBUILDs/$PKG_NAME"
cp -f "$TARGET_DIR/PKGBUILD" "$REPO_DIR/PKGBUILDs/$PKG_NAME/PKGBUILD"

# 6. Git Add, Commit y Push a GitHub
echo "🚀 Sincronizando con GitHub..."
cd "$REPO_DIR"
git add x86_64/ PKGBUILDs/
git commit -m "Update: $PKG_FILE y actualización de base de datos"
git push origin main

echo "=========================================================================="
echo "✅ ¡Actualización de $PKG_NAME completada y publicada con éxito en GitHub!"
echo "=========================================================================="
