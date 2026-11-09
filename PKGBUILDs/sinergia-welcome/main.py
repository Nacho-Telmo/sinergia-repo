#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess

# Forzar plataforma xcb para evitar bloqueos del servidor gráfico
os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QCheckBox, QFrame, QGridLayout,
    QMessageBox
)
from PyQt6.QtCore import Qt, QUrl, pyqtSlot, QEvent
from PyQt6.QtGui import QFont, QDesktopServices

AUTOSTART_PATH = os.path.expanduser("~/.config/autostart/sinergia-welcome.desktop")

class SinergiaWelcome(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sinergia Welcome - Centro de Control")
        self.setFixedSize(540, 750)
        self.init_ui()
        # Aplicar el tema inicial según la configuración del sistema
        self.actualizar_estilo_segun_tema()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(12)

        # Encabezado
        title = QLabel("🚀 Sinergia Comunidad Linuxera")
        title.setFont(QFont("Sans Serif", 15, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("margin-top: 5px;")
        main_layout.addWidget(title)

        subtitle = QLabel("Bienvenido a tu entorno optimizado para Arch Linux")
        subtitle.setFont(QFont("Sans Serif", 10))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        # Separador visual 1
        line = QFrame()
        line.setObjectName("separator")
        line.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(line)

        # Grilla de Accesos Directos
        grid = QGridLayout()
        grid.setSpacing(8)

        # Sección: Mantenimiento y Sistema (Botones compactos y texto centrado)
        lbl_sys = QLabel("🛠️ Mantenimiento y Sistema")
        lbl_sys.setFont(QFont("Sans Serif", 10, QFont.Weight.Bold))
        lbl_sys.setStyleSheet("margin-top: 2px;")
        grid.addWidget(lbl_sys, 0, 0, 1, 2)

        btn_update = QPushButton("🔄 Actualizar Sistema")
        btn_update.setFixedHeight(30)
        btn_update.clicked.connect(self.on_update_clicked)
        grid.addWidget(btn_update, 1, 0, 1, 2)

        btn_store = QPushButton("🛍️ Sinergia Store (Tienda de Apps)")
        btn_store.setFixedHeight(30)
        btn_store.clicked.connect(self.on_store_clicked)
        grid.addWidget(btn_store, 2, 0, 1, 2)

        btn_mirrors = QPushButton("⚡ Refrescar Mirrors")
        btn_mirrors.setFixedHeight(30)
        btn_mirrors.clicked.connect(self.on_mirrors_clicked)
        grid.addWidget(btn_mirrors, 3, 0, 1, 2)

        btn_clean = QPushButton("🧹 Limpiar Caché / Huérfanos")
        btn_clean.setFixedHeight(30)
        btn_clean.clicked.connect(self.on_clean_clicked)
        grid.addWidget(btn_clean, 4, 0, 1, 2)

        # Guardar referencias para actualizar estilos dinámicamente
        self.top_buttons = [btn_update, btn_store, btn_mirrors, btn_clean]

        # Sección: Diagnóstico y Herramientas Novato
        lbl_diag = QLabel("🔍 Diagnóstico y Herramientas")
        lbl_diag.setFont(QFont("Sans Serif", 10, QFont.Weight.Bold))
        lbl_diag.setStyleSheet("margin-top: 6px;")
        grid.addWidget(lbl_diag, 5, 0, 1, 2)

        btn_info = QPushButton("💻 Información del Sistema")
        btn_info.setFixedHeight(34)
        btn_info.clicked.connect(self.on_info_clicked)
        grid.addWidget(btn_info, 6, 0)

        btn_net = QPushButton("🌐 Probar Conexión Red")
        btn_net.setFixedHeight(34)
        btn_net.clicked.connect(self.on_net_clicked)
        grid.addWidget(btn_net, 6, 1)

        btn_burner = QPushButton("🔥 Grabar ISO (DD Burner)")
        btn_burner.setFixedHeight(34)
        btn_burner.clicked.connect(self.on_burner_clicked)
        grid.addWidget(btn_burner, 7, 0)

        btn_services = QPushButton("⚙️ Gestor de Servicios")
        btn_services.setFixedHeight(34)
        btn_services.clicked.connect(self.on_services_clicked)
        grid.addWidget(btn_services, 7, 1)

        btn_aur = QPushButton("📦 Gestor AUR Helper")
        btn_aur.setFixedHeight(34)
        btn_aur.clicked.connect(self.on_aur_clicked)
        grid.addWidget(btn_aur, 8, 0)

        btn_logs = QPushButton("📋 Ver Logs de Errores")
        btn_logs.setFixedHeight(34)
        btn_logs.clicked.connect(self.on_logs_clicked)
        grid.addWidget(btn_logs, 8, 1)

        self.grid_buttons = [btn_info, btn_net, btn_burner, btn_services, btn_aur, btn_logs]

        main_layout.addLayout(grid)

        # Separador visual 2
        line2 = QFrame()
        line2.setObjectName("separator")
        line2.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(line2)

        # Comunidad
        lbl_com = QLabel("🌐 Comunidad")
        lbl_com.setFont(QFont("Sans Serif", 10, QFont.Weight.Bold))
        main_layout.addWidget(lbl_com)

        com_layout = QHBoxLayout()
        btn_yt = QPushButton("📺 YouTube")
        btn_yt.setFixedHeight(34)
        btn_yt.clicked.connect(self.open_yt)
        com_layout.addWidget(btn_yt)

        btn_tg = QPushButton("💬 Telegram")
        btn_tg.setFixedHeight(34)
        btn_tg.clicked.connect(self.open_tg)
        com_layout.addWidget(btn_tg)

        btn_repo = QPushButton("💻 Repo Web")
        btn_repo.setFixedHeight(34)
        btn_repo.clicked.connect(self.open_repo)
        com_layout.addWidget(btn_repo)

        self.comm_buttons = [btn_yt, btn_tg, btn_repo]

        main_layout.addLayout(com_layout)
        main_layout.addStretch()

        # Checkbox autostart
        self.chk_autostart = QCheckBox("Mostrar esta ventana al iniciar el sistema")
        self.chk_autostart.setChecked(os.path.exists(AUTOSTART_PATH))
        self.chk_autostart.toggled.connect(self.toggle_autostart)
        main_layout.addWidget(self.chk_autostart)

    def changeEvent(self, event):
        # Detecta cambios en la paleta del sistema operativo en tiempo real
        if event.type() == QEvent.Type.ApplicationPaletteChange:
            self.actualizar_estilo_segun_tema()
        super().changeEvent(event)

    def actualizar_estilo_segun_tema(self):
        palette = QApplication.palette()
        bg_color = palette.color(palette.ColorRole.Window)
        is_light_mode = bg_color.lightness() > 128

        if is_light_mode:
            # Estilos Modo Claro
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                    color: #222222;
                }
                QLabel {
                    color: #222222;
                }
                QCheckBox {
                    color: #333333;
                    font-size: 10pt;
                }
                QFrame#separator {
                    background-color: #cccccc;
                    border: none;
                    max-height: 2px;
                }
            """)
            top_bg, top_hover = "#ffffff", "#eaeaea"
            grid_bg, grid_hover = "#ffffff", "#eaeaea"
            comm_bg, comm_hover = "#ffffff", "#eaeaea"
        else:
            # Estilos Modo Oscuro (Ecosistema Sinergia)
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #121212;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QCheckBox {
                    color: #dddddd;
                    font-size: 10pt;
                }
                QFrame#separator {
                    background-color: #333333;
                    border: none;
                    max-height: 2px;
                }
            """)
            top_bg, top_hover = "#1e1e1e", "#2d2d2d"
            grid_bg, grid_hover = "#1e1e1e", "#2d2d2d"
            comm_bg, comm_hover = "#1e1e1e", "#2d2d2d"

        # Aplicar estilos dinámicos a los botones superiores
        top_style = f"""
            QPushButton {{
                background-color: {top_bg};
                color: {'#222222' if is_light_mode else '#ffffff'};
                border: 1px solid #00acc1;
                border-radius: 6px;
                font-weight: bold;
                font-size: 9pt;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {top_hover};
                border: 1px solid {'#00838f' if is_light_mode else '#ffffff'};
            }}
        """
        for btn in self.top_buttons:
            btn.setStyleSheet(top_style)

        # Aplicar estilos a la grilla central
        grid_style = f"""
            QPushButton {{
                background-color: {grid_bg};
                color: {'#222222' if is_light_mode else '#ffffff'};
                border: 1px solid #7e57c2;
                border-radius: 6px;
                font-weight: bold;
                font-size: 9pt;
                text-align: left;
                padding-left: 10px;
            }}
            QPushButton:hover {{
                background-color: {grid_hover};
                border: 1px solid {'#5e35b1' if is_light_mode else '#ffffff'};
            }}
        """
        for btn in self.grid_buttons:
            btn.setStyleSheet(grid_style)

        # Aplicar estilos a los botones de comunidad
        comm_style = f"""
            QPushButton {{
                background-color: {comm_bg};
                color: {'#222222' if is_light_mode else '#ffffff'};
                border: 1px solid #ffb74d;
                border-radius: 6px;
                font-weight: bold;
                font-size: 9pt;
                text-align: left;
                padding-left: 10px;
            }}
            QPushButton:hover {{
                background-color: {comm_hover};
                border: 1px solid {'#f57c00' if is_light_mode else '#ffffff'};
            }}
        """
        for btn in self.comm_buttons:
            btn.setStyleSheet(comm_style)

    @pyqtSlot()
    def on_update_clicked(self):
        comando = "sudo pacman -Syu --noconfirm && yay -Syu --noconfirm; echo ''; echo '¡Actualización completada con éxito!'; sleep 8"
        self.run_in_terminal(comando)

    @pyqtSlot()
    def on_store_clicked(self):
        self.run_app("sinergia-store")

    @pyqtSlot()
    def on_mirrors_clicked(self):
        self.run_app("sinergia-reflector-top")

    @pyqtSlot()
    def on_clean_clicked(self):
        self.run_app("sinergia-cleaner")

    @pyqtSlot()
    def on_burner_clicked(self):
        self.run_app("sinergia-dd-burner")

    @pyqtSlot()
    def on_services_clicked(self):
        self.run_app("sinergia-service-manager")

    @pyqtSlot()
    def on_aur_clicked(self):
        self.run_app("sinergia-aur-helper")

    @pyqtSlot()
    def on_info_clicked(self):
        fetch_cmd = "fastfetch" if shutil.which("fastfetch") else ("neofetch" if shutil.which("neofetch") else "uname -a && lscpu")
        self.run_in_terminal(fetch_cmd)

    @pyqtSlot()
    def on_net_clicked(self):
        self.run_in_terminal("ping -c 4 1.1.1.1 && ping -c 4 google.com")

    @pyqtSlot()
    def on_logs_clicked(self):
        self.run_in_terminal("journalctl -p 3 -xb")

    @pyqtSlot()
    def open_yt(self):
        QDesktopServices.openUrl(QUrl("https://www.youtube.com/@Sinergia-Comunidad-Linuxera"))

    @pyqtSlot()
    def open_tg(self):
        QDesktopServices.openUrl(QUrl("https://t.me/Guias_NovumSinergia"))

    @pyqtSlot()
    def open_repo(self):
        QDesktopServices.openUrl(QUrl("https://nacho-telmo.github.io/sinergia-repo/"))

    def run_in_terminal(self, command_str):
        term = shutil.which("alacritty")
        if not term:
            QMessageBox.warning(self, "Terminal no encontrada", "El emulador 'alacritty' no está instalado.")
            return

        args = [term, "-e", "bash", "-c", command_str + "; read"]
        try:
            subprocess.Popen(args, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error al abrir terminal: {e}")

    def run_app(self, app_name):
        if not shutil.which(app_name):
            QMessageBox.warning(
                self,
                "Herramienta no encontrada",
                f"El ejecutable '{app_name}' no está instalado en el sistema."
            )
            return

        try:
            subprocess.Popen([app_name], start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error al lanzar app: {e}")

    @pyqtSlot(bool)
    def toggle_autostart(self, checked):
        if checked:
            os.makedirs(os.path.dirname(AUTOSTART_PATH), exist_ok=True)
            content = """[Desktop Entry]
Type=Application
Name=Sinergia Welcome
Exec=sinergia-welcome
Icon=sinergia-welcome
Terminal=false
Categories=Utility;
"""
            with open(AUTOSTART_PATH, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            if os.path.exists(AUTOSTART_PATH):
                os.remove(AUTOSTART_PATH)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SinergiaWelcome()
    window.show()
    sys.exit(app.exec())
