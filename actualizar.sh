#!/bin/bash
# ==============================================================================
# Script de automatización total para sinergia-repo
# Huella GPG: 33986859CBA9A0329EE9321E1AA165CC95EBE1F1
# Destino binarios: docs/x86_64/
# Destino web pública: docs/
# ==============================================================================

set -e

REPO_DIR="/home/nacho/sinergia-repo"
DOCS_DIR="$REPO_DIR/docs/x86_64"
KEY_ID="33986859CBA9A0329EE9321E1AA165CC95EBE1F1"

echo "=================================================="
echo " 🚀 Automatizador de Repositorio y Web - Sinergia"
echo "=================================================="

# 1. Asegurar directorios requeridos
mkdir -p "$DOCS_DIR"

# 2. Determinar qué compilar
if [ -n "$1" ]; then
    TARGETS=("$1")
else
    echo "--> No se especificó paquete individual. Procesando todos los PKGBUILDs..."
    TARGETS=($(ls -d "$REPO_DIR"/PKGBUILDs/*/ | xargs -n 1 basename))
fi

# 3. Compilar y trasladar binarios
for pkg in "${TARGETS[@]}"; do
    PKG_PATH="$REPO_DIR/PKGBUILDs/$pkg"
    if [ -d "$PKG_PATH" ]; then
        echo ""
        echo "--------------------------------------------------"
        echo "📦 Compilando y firmando: $pkg"
        echo "--------------------------------------------------"
        cd "$PKG_PATH"

        # Compilar y firmar con la clave GPG oficial
        makepkg -cf --sign --key "$KEY_ID"

        # Eliminar versión anterior del mismo paquete en docs/x86_64 si existe
        rm -f "$DOCS_DIR/${pkg}"-*.pkg.tar.zst* 2>/dev/null || true

        # Mover nuevos binarios y firmas a docs/x86_64/
        echo "🚚 Moviendo nuevo binario a $DOCS_DIR..."
        mv -f *.pkg.tar.zst* "$DOCS_DIR/" 2>/dev/null || true
    else
        echo "⚠️  El directorio PKGBUILDs/$pkg no existe. Se omite."
    fi
done

# 4. Actualizar la base de datos de Pacman
echo ""
echo "--------------------------------------------------"
echo "⚙  Actualizando base de datos pacman en docs/x86_64..."
echo "--------------------------------------------------"
cd "$DOCS_DIR"

if ! compgen -G "*.pkg.tar.zst" > /dev/null; then
    echo "❌ ERROR CRÍTICO: No se encontraron paquetes *.pkg.tar.zst en $DOCS_DIR" >&2
    exit 1
fi

rm -f sinergia-repo.db* sinergia-repo.files* sinergia.db* sinergia.files*
repo-add -n -s --key "$KEY_ID" sinergia-repo.db.tar.gz ./*.pkg.tar.zst
ln -sf sinergia-repo.db.tar.gz sinergia-repo.db
ln -sf sinergia-repo.files.tar.gz sinergia-repo.files
ln -sf sinergia-repo.db.tar.gz.sig sinergia-repo.db.sig

for pkg_file in ./*.pkg.tar.zst; do
    real_size=$(stat -c "%s" "$pkg_file")
    base_name=$(basename "$pkg_file")
    pkg_id=$(echo "$base_name" | sed -E 's/^([^-]+(-[^-]+)*)-[^-]+\.pkg\.tar\.zst$/\1/')
    db_csize=$(tar -xOzf sinergia-repo.db.tar.gz "${pkg_id}/desc" 2>/dev/null | awk '/^%CSIZE%$/{getline; print $0}')
    if [ -z "$db_csize" ] || [ "$real_size" -ne "$db_csize" ]; then
        echo "❌ ERROR CRÍTICO: Desfase de tamaño en $base_name (real=$real_size vs %CSIZE%=${db_csize:-ninguno})" >&2
        exit 1
    fi
done

echo "✅ Base de datos re-generada, firmada y verificada al byte (%CSIZE% OK)."
# 5. Actualizar la web / catálogo de aplicaciones público
echo ""
echo "--------------------------------------------------"
echo "🌐 Actualizando catálogo web en docs/..."
echo "--------------------------------------------------"
cd "$REPO_DIR"

# Si existe un script de generación de la web (en public/ o raíz), lo ejecuta:
if [ -f "public/generate.py" ]; then
    python3 public/generate.py
elif [ -f "public/build.sh" ]; then
    bash public/build.sh
elif [ -d "public" ]; then
    # Sincronizar activos estáticos de public/ a docs/ sin borrar la carpeta x86_64
    rsync -av --exclude='x86_64' public/ docs/
fi

echo "✅ Sitio web y catálogo de aplicaciones sincronizados."

# 6. Confirmación para Git
echo ""
read -p "¿Deseás hacer git add, commit y push a GitHub ahora mismo? (s/N): " CONFIRM
if [[ "$CONFIRM" =~ ^[Ss]$ ]]; then
    cd "$REPO_DIR"
    git add .
    read -p "Mensaje del commit (Enter para valor por defecto): " MSG
    if [ -z "$MSG" ]; then
        MSG="chore(repo): actualizar paquetes binarios, base de datos limpia y catálogo web"
    fi
    git commit -m "$MSG"
    git push origin main
    echo ""
    echo "🚀 ¡Todo publicado correctamente en GitHub Pages!"
fi
