#!/usr/bin/env python3
import os
import re
import glob
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
PKG_DIR = os.path.join(DOCS_DIR, "x86_64")
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

METADATA = {
    "sinergia-welcome": ("Centro de control y bienvenida para Sinergia Linux", "🚀"),
    "sinergia-dd-burner": ("Herramienta gráfica para grabar imágenes ISO en USB", "🔥"),
    "sinergia-cleaner": ("Limpiador de sistema, caché de pacman y archivos huérfanos", "🧹"),
    "sinergia-reflector-top": ("Optimizador gráfico de mirrors pacman más rápidos", "⚡"),
    "sinergia-webapp-manager": ("Gestor gráfico de aplicaciones web para el escritorio", "🌐"),
    "sinergia-appimage-manager": ("Gestor e integrador de paquetes AppImage", "📦"),
    "sinergia-aur-helper": ("Asistente de compilación e instalación para AUR", "🛠️"),
    "sinergia-conky": ("Widgets y monitoreo de sistema Conky preconfigurados", "📊"),
    "sinergia-keyring": ("Claves GPG oficiales del repositorio Sinergia", "🔑"),
    "sinergia-plasma-full": ("Meta-paquete de configuración de escritorio KDE Plasma", "💻"),
    "sddm-theme-sinergia": ("Tema visual Sinergia para el gestor de inicio SDDM", "🎨"),
    "flextile-git": ("Gestor de distribución de ventanas flexible", "🪟"),
    "konvi": ("Utilidad de conversión y herramientas de sistema", "⚙️"),
    "stacer-bin": ("Optimizador y monitor de recursos de sistema", "📈"),
    "vortex-dark-icons": ("Tema de íconos oscuros Vortex para el escritorio", "🖼️"),
}

PKG_PATTERN = re.compile(r"^(.+)-([^-]+-[0-9]+)-([^-]+)\.pkg\.tar\.zst$")

def get_file_size(filepath):
    size_bytes = os.path.getsize(filepath)
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    return f"{size_bytes / 1024:.1f} KB"

def build_catalog():
    packages = []
    pkg_files = glob.glob(os.path.join(PKG_DIR, "*.pkg.tar.zst"))

    for filepath in sorted(pkg_files):
        filename = os.path.basename(filepath)
        match = PKG_PATTERN.match(filename)
        if match:
            name, version, arch = match.groups()
            desc, icon = METADATA.get(name, ("Paquete binario oficial del repositorio Sinergia", "📦"))
            size = get_file_size(filepath)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%d/%m/%Y")
            packages.append({
                "name": name,
                "version": version,
                "arch": arch,
                "filename": filename,
                "desc": desc,
                "icon": icon,
                "size": size,
                "mtime": mtime
            })

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    cards_html = ""
    for p in packages:
        cards_html += f"""
        <div class="card">
            <div class="card-header">
                <span class="icon">{p['icon']}</span>
                <div>
                    <h3>{p['name']}</h3>
                    <span class="badge">{p['version']}</span>
                </div>
            </div>
            <p class="desc">{p['desc']}</p>
            <div class="meta">
                <span>📁 {p['size']}</span>
                <span>🏷️ {p['arch']}</span>
                <span>📅 {p['mtime']}</span>
            </div>
            <a href="x86_64/{p['filename']}" class="btn-download" download>Descargar .pkg.tar.zst</a>
        </div>"""

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sinergia - Repositorio Oficial Arch Linux</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text: #f8fafc;
            --muted: #94a3b8;
            --accent: #38bdf8;
            --accent-hover: #0284c7;
            --border: #334155;
            --badge-bg: #0369a1;
            --telegram: #0088cc;
            --telegram-hover: #006699;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem 1rem;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}

        header {{
            text-align: center;
            margin-bottom: 2.5rem;
            padding-bottom: 1.5rem;
            border-bottom: 1px solid var(--border);
        }}
        .logo-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 0.75rem;
        }}
        .repo-logo {{
            width: 192px;
            height: 192px;
            object-fit: contain;
            border-radius: 16px;
        }}
        header h1 {{ font-size: 2.3rem; color: var(--accent); font-weight: 800; }}
        .header-desc {{
            color: var(--muted);
            font-size: 1.05rem;
            max-width: 780px;
            margin: 0.5rem auto 1.25rem;
        }}
        .nav-buttons {{
            display: flex;
            justify-content: center;
            gap: 1rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }}
        .btn-telegram {{
            background: var(--telegram);
            color: #ffffff;
            font-weight: bold;
            text-decoration: none;
            padding: 0.6rem 1.3rem;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: background 0.15s ease;
        }}
        .btn-telegram:hover {{ background: var(--telegram-hover); }}
        .btn-secondary {{
            background: #334155;
            color: #ffffff;
            font-weight: bold;
            text-decoration: none;
            padding: 0.6rem 1.3rem;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            transition: background 0.15s ease;
        }}
        .btn-secondary:hover {{ background: #475569; }}

        /* Guía en diseño vertical con botón de copiar */
        .steps-box {{
            background: #1e293b;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1.75rem;
            margin-bottom: 2.5rem;
        }}
        .steps-box h2 {{
            font-size: 1.25rem;
            color: var(--accent);
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .steps-list {{
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }}
        .step-card {{
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}
        .step-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        .step-number {{
            display: inline-block;
            background: var(--badge-bg);
            color: #fff;
            font-weight: bold;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .step-title {{
            font-weight: bold;
            font-size: 1.05rem;
            color: #f8fafc;
        }}
        .step-desc {{
            font-size: 0.9rem;
            color: var(--muted);
        }}
        .code-wrapper {{
            position: relative;
        }}
        pre {{
            background: #090d16;
            padding: 0.85rem 3.5rem 0.85rem 1rem;
            border-radius: 6px;
            overflow-x: auto;
            font-family: monospace;
            color: #38bdf8;
            font-size: 0.85rem;
            border: 1px solid var(--border);
            white-space: pre-wrap;
            word-break: break-all;
        }}
        .btn-copy {{
            position: absolute;
            top: 8px;
            right: 8px;
            background: #334155;
            color: #f8fafc;
            border: none;
            border-radius: 4px;
            padding: 0.3rem 0.6rem;
            font-size: 0.75rem;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.15s ease;
        }}
        .btn-copy:hover {{
            background: var(--accent);
            color: #0f172a;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1.5rem;
        }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.15s ease, border-color 0.15s ease;
        }}
        .card:hover {{
            transform: translateY(-3px);
            border-color: var(--accent);
        }}
        .card-header {{ display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }}
        .card-header .icon {{ font-size: 1.8rem; }}
        .card-header h3 {{ font-size: 1.15rem; word-break: break-word; }}
        .badge {{
            display: inline-block;
            background: var(--badge-bg);
            color: #e0f2fe;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: bold;
            margin-top: 4px;
        }}
        .desc {{ color: var(--muted); font-size: 0.92rem; margin-bottom: 1rem; flex-grow: 1; }}
        .meta {{
            display: flex;
            gap: 1rem;
            font-size: 0.8rem;
            color: var(--muted);
            margin-bottom: 1rem;
            border-top: 1px solid var(--border);
            padding-top: 0.5rem;
        }}
        .btn-download {{
            display: block;
            text-align: center;
            background: var(--accent);
            color: #0f172a;
            font-weight: bold;
            text-decoration: none;
            padding: 0.5rem;
            border-radius: 6px;
            transition: background 0.15s ease;
        }}
        .btn-download:hover {{ background: var(--accent-hover); color: #fff; }}
        footer {{
            text-align: center;
            margin-top: 3rem;
            color: var(--muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
            padding-top: 1.5rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-container">
                <img src="https://raw.githubusercontent.com/Nacho-Telmo/sinergia-repo/main/logo.png" alt="Logo Sinergia" class="repo-logo">
                <h1>Sinergia Comunidad Linuxera</h1>
            </div>
            <p class="header-desc">
                Repositorio oficial de paquetes binarios para Arch Linux, mantenido de forma colaborativa por los integrantes de la Comunidad de Sinergia. Optimizado para ofrecer herramientas personalizadas, mantenimiento simplificado y máximo rendimiento en el escritorio.
            </p>
            <div class="nav-buttons">
                <a href="https://t.me/Guias_NovumSinergia" target="_blank" class="btn-telegram">
                    ✈️ Canal de Telegram
                </a>
                <a href="https://www.youtube.com/@Sinergia-Comunidad-Linuxera" target="_blank" class="btn-secondary">
                    📺 Canal de YouTube
                </a>
            </div>
        </header>

        <!-- Sección de 4 Pasos Verticales con Botón Copiar -->
        <div class="steps-box">
            <h2>🛠️ 4 Pasos para agregar el repositorio a tu sistema</h2>
            <div class="steps-list">

                <div class="step-card">
                    <div class="step-header">
                        <div>
                            <span class="step-number">PASO 1</span>
                            <span class="step-title">Importar la clave GPG del repositorio</span>
                        </div>
                    </div>
                    <div class="step-desc">Descarga e importa la clave pública oficial directamente al llavero de tu sistema:</div>
                    <div class="code-wrapper">
                        <pre id="code-1">curl -s https://nacho-telmo.github.io/sinergia-repo/x86_64/sinergia-key.asc | sudo pacman-key --add -</pre>
                        <button class="btn-copy" onclick="copyCode('code-1', this)">Copiar</button>
                    </div>
                </div>

                <div class="step-card">
                    <div class="step-header">
                        <div>
                            <span class="step-number">PASO 2</span>
                            <span class="step-title">Firmar localmente la clave</span>
                        </div>
                    </div>
                    <div class="step-desc">Otorga confianza local a la clave importada para que pacman valide las firmas de forma segura:</div>
                    <div class="code-wrapper">
                        <pre id="code-2">sudo pacman-key --lsign-key 33986859CBA9A0329EE9321E1AA165CC95EBE1F1</pre>
                        <button class="btn-copy" onclick="copyCode('code-2', this)">Copiar</button>
                    </div>
                </div>

                <div class="step-card">
                    <div class="step-header">
                        <div>
                            <span class="step-number">PASO 3</span>
                            <span class="step-title">Agregar el repositorio a tu configuración</span>
                        </div>
                    </div>
                    <div class="step-desc">Abre el archivo de configuración con tu editor de texto favorito y añade las líneas al final:</div>
                    <div class="code-wrapper">
                        <pre id="code-3">sudo nano /etc/pacman.conf

[sinergia]
SigLevel = Required DatabaseOptional
Server = https://nacho-telmo.github.io/sinergia-repo/x86_64/</pre>
                        <button class="btn-copy" onclick="copyCode('code-3', this)">Copiar</button>
                    </div>
                </div>

                <div class="step-card">
                    <div class="step-header">
                        <div>
                            <span class="step-number">PASO 4</span>
                            <span class="step-title">Sincronizar las bases de datos</span>
                        </div>
                    </div>
                    <div class="step-desc">Fuerza el refresco de los repositorios para comenzar a utilizar el repositorio de Sinergia:</div>
                    <div class="code-wrapper">
                        <pre id="code-4">sudo pacman -Syy</pre>
                        <button class="btn-copy" onclick="copyCode('code-4', this)">Copiar</button>
                    </div>
                </div>

            </div>
        </div>

        <div class="grid">
            {cards_html}
        </div>

        <footer>
            <p>Catálogo generado automáticamente el {now_str} • Sinergia Repo ({len(packages)} paquetes)</p>
        </footer>
    </div>

    <script>
        function copyCode(elementId, btn) {{
            const codeText = document.getElementById(elementId).innerText;
            navigator.clipboard.writeText(codeText).then(() => {{
                const originalText = btn.innerText;
                btn.innerText = "¡Copiado!";
                btn.style.background = "#38bdf8";
                btn.style.color = "#0f172a";
                setTimeout(() => {{
                    btn.innerText = originalText;
                    btn.style.background = "#334155";
                    btn.style.color = "#f8fafc";
                }}, 2000);
            }}).catch(err => {{
                console.error('Error al copiar: ', err);
            }});
        }}
    </script>
</body>
</html>
"""

    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    with open(os.path.join(PUBLIC_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Catálogo web generado exitosamente ({len(packages)} paquetes procesados).")

if __name__ == "__main__":
    build_catalog()
