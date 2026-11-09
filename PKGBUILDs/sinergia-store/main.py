#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess

# Forzar plataforma xcb para evitar bloqueos del servidor gráfico
os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QPushButton, QScrollArea, QGridLayout,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QFont

class SinergiaStore(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sinergia Store - Aplicaciones Esenciales")
        self.setFixedSize(800, 720)

        self.app_cards = []  # Lista para guardar referencias a las tarjetas
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 20, 25, 20)

        # Encabezado
        title = QLabel("🛍️ Sinergia Store")
        title.setFont(QFont("Sans", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Gestión rápida de software curado para tu Arch Linux")
        subtitle.setFont(QFont("Sans", 10))
        subtitle.setStyleSheet("color: #888;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        # Separador visual
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        # Área desplazable para las tarjetas de aplicaciones
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_content = QWidget()
        grid = QGridLayout(scroll_content)
        grid.setSpacing(15)

        # Lista de aplicaciones curadas (Nombre, Descripción, Paquete real, Comando Instalar, Comando Desinstalar)
        self.apps = [
            ("🌐 Vivaldi", "Navegador web avanzado y altamente personalizable", "vivaldi", "sudo pacman -S --noconfirm vivaldi", "sudo pacman -Rns --noconfirm vivaldi"),
            ("🦁 Brave", "Navegador web enfocado en la privacidad", "brave-bin", "sudo pacman -S --noconfirm brave-bin", "sudo pacman -Rns --noconfirm brave-bin"),
            ("🔒 Signal", "Mensajería privada rápida y segura", "signal-desktop", "sudo pacman -S --noconfirm signal-desktop", "sudo pacman -Rns --noconfirm signal-desktop"),
            ("💬 Discord", "Chat de voz y comunidades gamer/dev", "discord", "sudo pacman -S --noconfirm discord", "sudo pacman -Rns --noconfirm discord"),
            ("🎵 Spotify", "Música y streaming en línea", "spotify", "yay -S --noconfirm spotify", "yay -R --noconfirm spotify"),
            ("🎬 Haruna", "Reproductor multimedia moderno basado en mpv", "haruna", "sudo pacman -S --noconfirm haruna", "sudo pacman -Rns --noconfirm haruna"),
            ("📝 Visual Studio Code", "Editor de código y extensiones", "visual-studio-code-bin", "yay -S --noconfirm visual-studio-code-bin", "yay -R --noconfirm visual-studio-code-bin"),
            ("📊 OnlyOffice", "Suite de oficina compatible con documentos Office", "onlyoffice-bin", "sudo pacman -S --noconfirm onlyoffice-bin", "sudo pacman -Rns --noconfirm onlyoffice-bin"),
            ("📥 qBitTorrent", "Cliente de torrents rápido y liviano", "qbittorrent", "sudo pacman -S --noconfirm qbittorrent", "sudo pacman -Rns --noconfirm qbittorrent"),
            ("🎨 GIMP", "Editor y manipulador de imágenes", "gimp", "sudo pacman -S --noconfirm gimp", "sudo pacman -Rns --noconfirm gimp"),
            ("🎮 Steam", "Plataforma de videojuegos", "steam", "sudo pacman -S --noconfirm steam", "sudo pacman -Rns --noconfirm steam"),
            ("⚡ Stacer", "Optimizador y monitor de sistema", "stacer-bin", "sudo pacman -S --noconfirm stacer-bin", "sudo pacman -Rns --noconfirm stacer-bin")
        ]

        row = 0
        col = 0
        for name, desc, pkg_name, install_cmd, remove_cmd in self.apps:
            card_info = self.create_app_card(name, desc, pkg_name, install_cmd, remove_cmd)
            grid.addWidget(card_info['card'], row, col)
            self.app_cards.append(card_info)
            col += 1
            if col > 1:
                col = 0
                row += 1

        # Estado inicial de los botones y colores
        self.update_card_states()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def changeEvent(self, event):
        """Detecta cuando la ventana recupera el foco (ej: al cerrar alacritty) y actualiza estados."""
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                self.update_card_states()
        super().changeEvent(event)

    def update_card_states(self):
        """Actualiza el diseño y los comandos de cada tarjeta en el lugar sin perder el scroll."""
        for info in self.app_cards:
            is_installed = self.check_if_installed(info['pkg_name'])

            bg_color = "#253329" if is_installed else "#2d2d2d"
            btn_color = "#d32f2f" if is_installed else "#00acc1"
            btn_hover = "#c62828" if is_installed else "#00838f"
            btn_text = "Desinstalar" if is_installed else "Instalar"
            target_cmd = info['remove_cmd'] if is_installed else info['install_cmd']

            info['card'].setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border-radius: 8px;
                    padding: 12px;
                }}
                QLabel {{
                    color: #ffffff;
                    border: none;
                }}
                QPushButton {{
                    background-color: {btn_color};
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                    padding: 6px;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {btn_hover};
                }}
            """)

            info['btn'].setText(btn_text)

            # Desconectar señales anteriores para evitar acumulación de eventos
            try:
                info['btn'].clicked.disconnect()
            except TypeError:
                pass

            info['btn'].clicked.connect(lambda _, c=target_cmd: self.run_action(c))

    def check_if_installed(self, pkg_name):
        try:
            result = subprocess.run(["pacman", "-Q", pkg_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return result.returncode == 0
        except Exception:
            return False

    def create_app_card(self, name, description, pkg_name, install_cmd, remove_cmd):
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(card)

        lbl_name = QLabel(name)
        lbl_name.setFont(QFont("Sans", 11, QFont.Weight.Bold))
        layout.addWidget(lbl_name)

        lbl_desc = QLabel(description)
        lbl_desc.setFont(QFont("Sans", 9))
        lbl_desc.setStyleSheet("color: #b0b0b0;")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        btn_action = QPushButton("...")
        layout.addWidget(btn_action)

        return {
            'pkg_name': pkg_name,
            'card': card,
            'btn': btn_action,
            'install_cmd': install_cmd,
            'remove_cmd': remove_cmd
        }

    def run_action(self, command_str):
        term = shutil.which("alacritty")
        if not term:
            QMessageBox.warning(self, "Terminal no encontrada", "El emulador 'alacritty' no está instalado.")
            return

        full_cmd = f"{command_str}; echo ''; echo '¡Operación finalizada! Cerrando terminal en 3 segundos...'; sleep 3"
        args = [term, "-e", "bash", "-c", full_cmd]

        try:
            subprocess.Popen(args, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error al ejecutar comando: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SinergiaStore()
    window.show()
    sys.exit(app.exec())
