#!/usr/init/env python3
import sys
import subprocess
import shutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QScrollArea, QFrame, QMessageBox,
    QTabWidget, QDialog, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class AppDetailDialog(QDialog):
    def __init__(self, name, description, pkg_name, origin, category, install_cmd, remove_cmd, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detalles - {name}")
        self.setFixedSize(440, 340)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        # Título
        lbl_title = QLabel(name)
        lbl_title.setFont(QFont("Sans", 15, QFont.Weight.Bold))
        layout.addWidget(lbl_title)

        # Categoría y Origen
        lbl_meta = QLabel(f"Categoría: <b>{category}</b> | Origen: <span style='color: #00acc1;'>{origin}</span>")
        lbl_meta.setFont(QFont("Sans", 10))
        layout.addWidget(lbl_meta)

        # Descripción completa
        lbl_desc = QLabel(description)
        lbl_desc.setFont(QFont("Sans", 10))
        lbl_desc.setStyleSheet("color: #cccccc;")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        # Info técnica (Paquete)
        lbl_pkg = QLabel(f"Nombre del paquete: <span style='color: #81c784;'>{pkg_name}</span>")
        lbl_pkg.setFont(QFont("Sans", 10))
        layout.addWidget(lbl_pkg)

        layout.addStretch()

        # Botón de cerrar
        btn_close = QPushButton("Cerrar")
        btn_close.setFixedHeight(36)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)


class SinergiaStore(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sinergia Store")
        # Fijamos las dimensiones para mantener una proporción limpia y evitar roturas al maximizar
        self.setFixedSize(920, 720)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background: #1e1e1e;
                color: #aaaaaa;
                padding: 10px 14px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #00acc1;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background: #2a2a2a;
                color: #ffffff;
            }
        """)

        # Lista de aplicaciones actualizada con Heroic Games Launcher
        self.apps = [
            ("🌐 Vivaldi", "Navegador web avanzado y personalizable", "vivaldi", "sudo pacman -S --noconfirm vivaldi", "sudo pacman -Rns --noconfirm vivaldi", "Internet", "Arch Extra"),
            ("🌐 Chromium", "Navegador web rápido y de código abierto basado en Blink", "chromium", "sudo pacman -S --noconfirm chromium", "sudo pacman -Rns --noconfirm chromium", "Internet", "Arch Extra"),
            ("🦁 Brave", "Navegador web enfocado en la privacidad", "brave-bin", "sudo pacman -S --noconfirm brave-bin", "sudo pacman -Rns --noconfirm brave-bin", "Internet", "Chaotic-AUR"),
            ("🔒 Signal", "Mensajería privada rápida y segura", "signal-desktop", "sudo pacman -S --noconfirm signal-desktop", "sudo pacman -Rns --noconfirm signal-desktop", "Internet", "Arch Extra"),
            ("💬 Discord", "Chat de voz y comunidades gamer/dev", "discord", "sudo pacman -S --noconfirm discord", "sudo pacman -Rns --noconfirm discord", "Gamer", "Arch Extra"),
            ("🎮 Heroic Launcher", "Lanzador de juegos de Epic, GOG y Amazon", "heroic-games-launcher-bin", "yay -S --noconfirm heroic-games-launcher-bin", "yay -R --noconfirm heroic-games-launcher-bin", "Gamer", "AUR"),
            ("🎵 Spotify", "Música y streaming en línea", "spotify", "yay -S --noconfirm spotify", "yay -R --noconfirm spotify", "Multimedia", "Chaotic-AUR"),
            ("🎬 Haruna", "Reproductor multimedia basado en mpv", "haruna", "sudo pacman -S --noconfirm haruna", "sudo pacman -Rns --noconfirm haruna", "Multimedia", "Arch Extra"),
            ("📥 Sinergia YT-DLP", "Interfaz gráfica en PyQt6 para yt-dlp", "sinergia-ytdlp-gui", "sudo pacman -S --noconfirm sinergia-ytdlp-gui", "sudo pacman -Rns --noconfirm sinergia-ytdlp-gui", "Multimedia", "Sinergia Repo"),
            ("📝 Visual Studio Code", "Editor de código y extensiones", "visual-studio-code-bin", "yay -S --noconfirm visual-studio-code-bin", "yay -R --noconfirm visual-studio-code-bin", "Desarrollo", "Chaotic-AUR"),
            ("📊 OnlyOffice", "Suite de oficina compatible con Office", "onlyoffice-bin", "sudo pacman -S --noconfirm onlyoffice-bin", "sudo pacman -Rns --noconfirm onlyoffice-bin", "Oficina", "Chaotic-AUR"),
            ("📥 qBitTorrent", "Cliente de torrents rápido y liviano", "qbittorrent", "sudo pacman -S --noconfirm qbittorrent", "sudo pacman -Rns --noconfirm qbittorrent", "Internet", "Arch Extra"),
            ("🎨 GIMP", "Editor y manipulador de imágenes", "gimp", "sudo pacman -S --noconfirm gimp", "sudo pacman -Rns --noconfirm gimp", "Multimedia", "Arch Extra"),
            ("🎮 Steam", "Plataforma de videojuegos", "steam", "sudo pacman -S --noconfirm steam", "sudo pacman -Rns --noconfirm steam", "Gamer", "Arch Extra"),
            ("⚡ Stacer", "Optimizador y monitor de sistema", "stacer-bin", "sudo pacman -S --noconfirm stacer-bin", "sudo pacman -Rns --noconfirm stacer-bin", "Sistema", "Sinergia Repo")
        ]

        self.app_cards = []
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Encabezado (Limpio, solo título)
        header_layout = QHBoxLayout()
        title_label = QLabel("🚀 Sinergia Store - Centro de Software")
        title_label.setFont(QFont("Sans", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Pestañas de Categorías
        self.tabs = QTabWidget()
        categories = ["Todas", "Internet", "Multimedia", "Gamer", "Desarrollo", "Oficina", "Sistema"]
        for cat in categories:
            tab = QWidget()
            self.tabs.addTab(tab, cat)
        self.tabs.currentChanged.connect(self.filter_by_category)
        main_layout.addWidget(self.tabs)

        # Área de Scroll para las tarjetas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Crear todas las tarjetas de forma estática una sola vez
        for name, desc, pkg_name, install_cmd, remove_cmd, category, origin in self.apps:
            card_info = self.create_app_card(name, desc, pkg_name, install_cmd, remove_cmd, category, origin)
            self.app_cards.append(card_info)

        # Botón unificado de acciones por lote
        batch_layout = QHBoxLayout()
        self.btn_batch_action = QPushButton("🚀 Ejecutar lote (0 para instalar, 0 para desinstalar)")
        self.btn_batch_action.setFixedHeight(42)
        self.btn_batch_action.setEnabled(False)
        self.btn_batch_action.setStyleSheet("""
            QPushButton {
                background-color: #00acc1;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666666;
                border: 1px solid #3d3d3d;
            }
            QPushButton:hover:enabled {
                background-color: #00838f;
            }
        """)
        self.btn_batch_action.clicked.connect(self.run_batch_action)
        batch_layout.addWidget(self.btn_batch_action)
        main_layout.addLayout(batch_layout)

        # Rellenamos la grilla y actualizamos estados
        self.populate_grid("Todas")

        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll)

    def create_app_card(self, name, desc, pkg_name, install_cmd, remove_cmd, category, origin):
        card = QFrame()
        card.setFixedSize(260, 210)
        card.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 10px;
                border: 1px solid #282828;
            }
            QFrame:hover {
                border: 1px solid #00acc1;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(8)

        # Cabecera de la tarjeta: Nombre y Botón de Info
        top_row = QHBoxLayout()
        lbl_name = QLabel(name)
        lbl_name.setFont(QFont("Sans", 11, QFont.Weight.Bold))
        lbl_name.setStyleSheet("color: #ffffff; border: none;")
        top_row.addWidget(lbl_name)
        top_row.addStretch()

        btn_info = QPushButton("ℹ️")
        btn_info.setFixedSize(28, 28)
        btn_info.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border-radius: 4px;
                border: none;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        btn_info.setToolTip("Ver detalles de la aplicación")
        btn_info.clicked.connect(lambda: self.show_app_details(name, desc, pkg_name, origin, category, install_cmd, remove_cmd))
        top_row.addWidget(btn_info)
        card_layout.addLayout(top_row)

        # Etiqueta de Origen (Repositorio)
        origin_color = "#00acc1" if origin == "Arch Extra" else ("#7e57c2" if origin == "Chaotic-AUR" else "#ffb74d")
        lbl_origin = QLabel(f"<b>{origin}</b>")
        lbl_origin.setFont(QFont("Sans", 8))
        lbl_origin.setStyleSheet(f"color: {origin_color}; border: none;")
        card_layout.addWidget(lbl_origin)

        # Descripción corta
        lbl_desc = QLabel(desc)
        lbl_desc.setFont(QFont("Sans", 9))
        lbl_desc.setStyleSheet("color: #999999; border: none;")
        lbl_desc.setWordWrap(True)
        card_layout.addWidget(lbl_desc)

        card_layout.addStretch()

        # Checkbox para lote y Botón de acción individual
        bottom_row = QHBoxLayout()
        chk_select = QCheckBox("Seleccionar")
        chk_select.setStyleSheet("color: #aaaaaa; border: none; font-size: 9pt;")
        chk_select.stateChanged.connect(self.update_batch_button_state)
        bottom_row.addWidget(chk_select)
        bottom_row.addStretch()

        btn_action = QPushButton("Instalar")
        btn_action.setFixedSize(85, 30)
        btn_action.setStyleSheet("""
            QPushButton {
                background-color: #00acc1;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                border: none;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #00838f;
            }
        """)
        btn_action.clicked.connect(lambda: self.execute_action(pkg_name, install_cmd, remove_cmd))
        bottom_row.addWidget(btn_action)

        card_layout.addLayout(bottom_row)

        return {
            'name': name,
            'desc': desc,
            'pkg_name': pkg_name,
            'install_cmd': install_cmd,
            'remove_cmd': remove_cmd,
            'category': category,
            'origin': origin,
            'card_widget': card,
            'btn_action': btn_action,
            'chk': chk_select
        }

    def show_app_details(self, name, desc, pkg_name, origin, category, install_cmd, remove_cmd):
        dialog = AppDetailDialog(name, desc, pkg_name, origin, category, install_cmd, remove_cmd, self)
        dialog.exec()

    def check_if_installed(self, pkg_name):
        try:
            result = subprocess.run(["pacman", "-Q", pkg_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return result.returncode == 0
        except Exception:
            return False

    def populate_grid(self, category_filter):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        row = 0
        col = 0
        max_cols = 3

        for info in self.app_cards:
            if category_filter == "Todas" or info['category'] == category_filter:
                self.grid_layout.addWidget(info['card_widget'], row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

        self.update_card_states()

    def filter_by_category(self, index):
        cat_name = self.tabs.tabText(index)
        self.populate_grid(cat_name)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == event.Type.ActivationChange and self.isActiveWindow():
            self.update_card_states()

    def update_card_states(self):
        for info in self.app_cards:
            installed = self.check_if_installed(info['pkg_name'])
            btn = info['btn_action']

            if installed:
                btn.setText("Desinstalar")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #d32f2f;
                        color: white;
                        border-radius: 4px;
                        font-weight: bold;
                        border: none;
                        font-size: 9pt;
                    }
                    QPushButton:hover {
                        background-color: #b71c1c;
                    }
                """)
            else:
                btn.setText("Instalar")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #00acc1;
                        color: white;
                        border-radius: 4px;
                        font-weight: bold;
                        border: none;
                        font-size: 9pt;
                    }
                    QPushButton:hover {
                        background-color: #00838f;
                    }
                """)
        self.update_batch_button_state()

    def update_batch_button_state(self):
        installs = 0
        removals = 0
        for info in self.app_cards:
            if info['chk'].isChecked():
                if self.check_if_installed(info['pkg_name']):
                    removals += 1
                else:
                    installs += 1

        total = installs + removals
        if total == 0:
            self.btn_batch_action.setText("🚀 Ejecutar lote (0 para instalar, 0 para desinstalar)")
            self.btn_batch_action.setEnabled(False)
        else:
            parts = []
            if installs > 0:
                parts.append(f"{installs} para instalar")
            if removals > 0:
                parts.append(f"{removals} para desinstalar")
            self.btn_batch_action.setText(f"🚀 Ejecutar lote ({', '.join(parts)})")
            self.btn_batch_action.setEnabled(True)

    def execute_action(self, pkg_name, install_cmd, remove_cmd):
        installed = self.check_if_installed(pkg_name)
        cmd = remove_cmd if installed else install_cmd
        action_name = "Desinstalación" if installed else "Instalación"

        term = shutil.which("alacritty")
        if not term:
            QMessageBox.warning(self, "Terminal no encontrada", "El emulador 'alacritty' no está instalado.")
            return

        full_cmd = f"{cmd}; echo ''; echo '¡{action_name} finalizada! Cerrando terminal en 3 segundos...'; sleep 3"
        args = [term, "-e", "bash", "-c", full_cmd]

        try:
            subprocess.Popen(args, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo iniciar el proceso: {e}")

    def run_batch_action(self):
        installs = []
        removals = []
        for info in self.app_cards:
            if info['chk'].isChecked():
                if self.check_if_installed(info['pkg_name']):
                    removals.append(info['remove_cmd'])
                else:
                    installs.append(info['install_cmd'])

        all_cmds = []
        if installs:
            all_cmds.append(" && ".join(installs))
        if removals:
            all_cmds.append(" && ".join(removals))

        if not all_cmds:
            return

        combined_cmd = " && ".join(all_cmds)
        term = shutil.which("alacritty")
        if not term:
            QMessageBox.warning(self, "Terminal no encontrada", "El emulador 'alacritty' no está instalado.")
            return

        full_cmd = f"{combined_cmd}; echo ''; echo '¡Operación por lote finalizada! Cerrando terminal en 3 segundos...'; sleep 3"
        args = [term, "-e", "bash", "-c", full_cmd]

        try:
            subprocess.Popen(args, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Destildar todas las casillas tras lanzar la acción
            for info in self.app_cards:
                info['chk'].setChecked(False)
            self.update_card_states()
        except Exception as e:
            print(f"Error al ejecutar operaciones por lote: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SinergiaStore()
    window.show()
    sys.exit(app.exec())
