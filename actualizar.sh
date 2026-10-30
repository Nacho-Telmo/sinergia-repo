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

# 3. Actualizar la grilla en public/index.html de forma limpia
cd "$REPO_DIR"
echo "🌐 Actualizando listado en public/index.html..."

python3 -c '
import os, tarfile, re

repo_dir = "/home/nacho/sinergia-repo"
db_path = os.path.join(repo_dir, "x86_64", "sinergia.db.tar.gz")
html_path = os.path.join(repo_dir, "public", "index.html")

names = set()
if os.path.exists(db_path):
    with tarfile.open(db_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith("/desc"):
                f = tar.extractfile(member)
                if f:
                    lines = [line.decode("utf-8", errors="ignore").strip() for line in f.readlines()]
                    for i, line in enumerate(lines):
                        if line == "%NAME%" and i + 1 < len(lines):
                            names.add(lines[i + 1])

pkgs = sorted(list(names))

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find("<div class=\"app-grid\">")
if start_idx != -1:
    header_part = content[:start_idx]
    items_html = "\n".join([f"                <div class=\"app-item\"><i class=\"fa-solid fa-cube\"></i> {p}</div>" for p in pkgs])
    grid_html = f"<div class=\"app-grid\">\n{items_html}\n            </div>\n"
    
    end_part = "\n        </section>\n    </main>\n</body>\n</html>"
    if "</section>" in content:
        end_part = content[content.rfind("</section>"):]
        
    full_clean_html = header_part + grid_html + "    " + end_part
    full_clean_html = re.sub(r"Aplicaciones Disponibles \([0-9]+\)", f"Aplicaciones Disponibles ({len(pkgs)})", full_clean_html)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_clean_html)
'

# 4. Git commit y push
echo "🚀 Sincronizando con GitHub Pages..."
git add x86_64/ PKGBUILDs/ public/index.html actualizar.sh
git commit -m "update(repo): add/update $PKG_NAME"
git push origin main

echo "=========================================================================="
echo "✅ ¡Repositorio y sitio web actualizados con éxito!"
echo "=========================================================================="
