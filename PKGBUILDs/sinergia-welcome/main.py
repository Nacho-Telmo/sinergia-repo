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
from PyQt6.QtCore import Qt, QUrl, pyqtSlot
from PyQt6.QtGui import QFont, QDesktopServices

AUTOSTART_PATH = os.path.expanduser("~/.config/autostart/sinergia-welcome.desktop")

class SinergiaWelcome(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sinergia Welcome - Centro de Control")
        self.setFixedSize(520, 660)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 20, 25, 20)

        # Encabezado
        title = QLabel("🚀 Sinergia Comunidad Linuxera")
        title.setFont(QFont("Sans", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Bienvenido a tu entorno optimizado para Arch Linux")
        subtitle.setFont(QFont("Sans", 10))
        subtitle.setStyleSheet("color: #888;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        # Separador visual
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        # Grilla de Accesos Directos
        grid = QGridLayout()
        grid.setSpacing(12)

        # Sección: Mantenimiento y Sistema
        lbl_sys = QLabel("🛠️ Mantenimiento y Sistema")
        lbl_sys.setFont(QFont("Sans", 11, QFont.Weight.Bold))
        grid.addWidget(lbl_sys, 0, 0, 1, 2)

        btn_update = QPushButton("🔄 Actualizar Sistema")
        btn_update.setFixedHeight(38)
        btn_update.clicked.connect(self.on_update_clicked)
        grid.addWidget(btn_update, 1, 0, 1, 2)

        btn_mirrors = QPushButton("⚡ Refrescar Mirrors")
        btn_mirrors.setFixedHeight(38)
        btn_mirrors.clicked.connect(self.on_mirrors_clicked)
        grid.addWidget(btn_mirrors, 2, 0, 1, 2)

        btn_clean = QPushButton("🧹 Limpiar Caché / Huérfanos")
        btn_clean.setFixedHeight(38)
        btn_clean.clicked.connect(self.on_clean_clicked)
        grid.addWidget(btn_clean, 3, 0, 1, 2)

        # Sección: Diagnóstico y Herramientas Novato
        lbl_diag = QLabel("🔍 Diagnóstico y Herramientas")
        lbl_diag.setFont(QFont("Sans", 11, QFont.Weight.Bold))
        grid.addWidget(lbl_diag, 4, 0, 1, 2)

        btn_info = QPushButton("💻 Información del Sistema")
        btn_info.setFixedHeight(36)
        btn_info.clicked.connect(self.on_info_clicked)
        grid.addWidget(btn_info, 5, 0)

        btn_net = QPushButton("🌐 Probar Conexión Red")
        btn_net.setFixedHeight(36)
        btn_net.clicked.connect(self.on_net_clicked)
        grid.addWidget(btn_net, 5, 1)

        btn_burner = QPushButton("🔥 Grabar Imagen ISO (DD Burner)")
        btn_burner.setFixedHeight(36)
        btn_burner.clicked.connect(self.on_burner_clicked)
        grid.addWidget(btn_burner, 6, 0, 1, 2)

        btn_aur = QPushButton("📦 Gestor AUR Helper")
        btn_aur.setFixedHeight(36)
        btn_aur.clicked.connect(self.on_aur_clicked)
        grid.addWidget(btn_aur, 7, 0)

        btn_logs = QPushButton("📋 Ver Registro de Errores (Logs)")
        btn_logs.setFixedHeight(36)
        btn_logs.clicked.connect(self.on_logs_clicked)
        grid.addWidget(btn_logs, 7, 1)

        main_layout.addLayout(grid)

        # Separador inferior
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(line2)

        # Comunidad
        lbl_com = QLabel("🌐 Comunidad")
        lbl_com.setFont(QFont("Sans", 11, QFont.Weight.Bold))
        main_layout.addWidget(lbl_com)

        com_layout = QHBoxLayout()
        btn_yt = QPushButton("📺 YouTube")
        btn_yt.setFixedHeight(36)
        btn_yt.clicked.connect(self.open_yt)
        com_layout.addWidget(btn_yt)

        btn_tg = QPushButton("💬 Telegram")
        btn_tg.setFixedHeight(36)
        btn_tg.clicked.connect(self.open_tg)
        com_layout.addWidget(btn_tg)

        btn_repo = QPushButton("💻 Repo Web")
        btn_repo.setFixedHeight(36)
        btn_repo.clicked.connect(self.open_repo)
        com_layout.addWidget(btn_repo)

        main_layout.addLayout(com_layout)

        main_layout.addStretch()

        # Checkbox autostart
        self.chk_autostart = QCheckBox("Mostrar esta ventana al iniciar el sistema")
        self.chk_autostart.setChecked(os.path.exists(AUTOSTART_PATH))
        self.chk_autostart.toggled.connect(self.toggle_autostart)
        main_layout.addWidget(self.chk_autostart)

    @pyqtSlot()
    def on_update_clicked(self):
        comando = "sudo pacman -Syu --noconfirm && yay -Syu --noconfirm; echo ''; echo '¡Actualización completada con éxito!'; sleep 8"
        self.run_in_terminal(comando)

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

    # --- Ejecución desacoplada de subprocesos usando Alacritty ---
    def run_in_terminal(self, command_str):
        term = shutil.which("alacritty")
        if not term:
            QMessageBox.warning(
                self,
                "Terminal no encontrada",
                "El emulador de terminal 'alacritty' no está instalado en el sistema."
            )
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
                f"El ejecutable '{app_name}' no está instalado en el sistema.\n\n"
                f"Podés instalarlo desde la terminal ejecutando:\n"
                f"sudo pacman -S {app_name}"
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
