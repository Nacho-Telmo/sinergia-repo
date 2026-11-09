#!/usr/bin/env python3
import sys
import os
import subprocess

os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QListWidget,
    QMessageBox
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QFont

SYSTEM_THEMES_DIR = "/usr/share/sinergia-conky/themes"
AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")

class SinergiaConkyManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sinergia Conky Manager")
        self.setFixedSize(650, 530)
        self.init_ui()
        self.actualizar_estilo_segun_tema()
        self.cargar_temas()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Título
        title = QLabel("📊 Sinergia Conky Manager")
        title.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Gestor de widgets de escritorio minimalistas para X11 y Wayland")
        subtitle.setFont(QFont("Sans Serif", 9))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        # Layout horizontal principal
        content_layout = QHBoxLayout()

        # Lista de temas disponibles
        self.list_widget = QListWidget()
        self.list_widget.setFixedWidth(240)
        self.list_widget.currentRowChanged.connect(self.on_theme_selected)
        content_layout.addWidget(self.list_widget)

        # Panel derecho
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)

        self.lbl_selected = QLabel("Seleccioná un tema")
        self.lbl_selected.setFont(QFont("Sans Serif", 11, QFont.Weight.Bold))
        right_layout.addWidget(self.lbl_selected)

        self.lbl_info = QLabel("Ruta: -")
        self.lbl_info.setWordWrap(True)
        right_layout.addWidget(self.lbl_info)

        right_layout.addStretch()

        # Botones de control
        self.btn_start = QPushButton("▶ Iniciar este Tema")
        self.btn_start.setFixedHeight(34)
        self.btn_start.setStyleSheet(self.get_btn_style("#00acc1", "#00838f"))
        self.btn_start.clicked.connect(self.start_selected_conky)
        right_layout.addWidget(self.btn_start)

        self.btn_autostart = QPushButton("🔄 Autostart: Desactivado")
        self.btn_autostart.setFixedHeight(34)
        self.btn_autostart.setStyleSheet(self.get_btn_style("#7e57c2", "#5e35b1"))
        self.btn_autostart.clicked.connect(self.toggle_autostart)
        right_layout.addWidget(self.btn_autostart)

        self.btn_stop_selected = QPushButton("⏹ Detener este Tema")
        self.btn_stop_selected.setFixedHeight(32)
        self.btn_stop_selected.setStyleSheet(self.get_btn_style("#ffb74d", "#f57c00"))
        self.btn_stop_selected.clicked.connect(self.stop_selected_conky)
        right_layout.addWidget(self.btn_stop_selected)

        self.btn_stop_all = QPushButton("🛑 Detener Todos los Conkys")
        self.btn_stop_all.setFixedHeight(32)
        self.btn_stop_all.setStyleSheet(self.get_btn_style("#e53935", "#c62828"))
        self.btn_stop_all.clicked.connect(self.stop_all_conky)
        right_layout.addWidget(self.btn_stop_all)

        content_layout.addLayout(right_layout)
        main_layout.addLayout(content_layout)

        # Botón cerrar
        self.btn_close = QPushButton("Cerrar")
        self.btn_close.setFixedHeight(30)
        self.btn_close.clicked.connect(self.close)
        main_layout.addWidget(self.btn_close)

    def get_btn_style(self, bg_color, hover_color):
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 9pt;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ApplicationPaletteChange:
            self.actualizar_estilo_segun_tema()
        super().changeEvent(event)

    def actualizar_estilo_segun_tema(self):
        palette = QApplication.palette()
        is_light_mode = palette.color(palette.ColorRole.Window).lightness() > 128

        if is_light_mode:
            self.setStyleSheet("""
                QMainWindow { background-color: #f5f5f5; color: #222222; }
                QLabel { color: #222222; }
                QListWidget { background-color: #ffffff; color: #222222; border: 1px solid #cccccc; border-radius: 6px; padding: 5px; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #121212; color: #ffffff; }
                QLabel { color: #ffffff; }
                QListWidget { background-color: #1e1e1e; color: #00ff00; border: 1px solid #282828; border-radius: 6px; padding: 5px; font-family: monospace; }
            """)

    def cargar_temas(self):
        self.list_widget.clear()
        search_dir = SYSTEM_THEMES_DIR if os.path.exists(SYSTEM_THEMES_DIR) else "themes"

        if os.path.exists(search_dir):
            for theme_name in sorted(os.listdir(search_dir)):
                theme_path = os.path.join(search_dir, theme_name)
                if os.path.isdir(theme_path) and os.path.exists(os.path.join(theme_path, "conky.conf")):
                    self.list_widget.addItem(theme_name)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def on_theme_selected(self, row):
        item = self.list_widget.item(row)
        if item:
            self.current_theme_name = item.text()
            search_dir = SYSTEM_THEMES_DIR if os.path.exists(SYSTEM_THEMES_DIR) else "themes"
            self.current_conf_path = os.path.abspath(os.path.join(search_dir, self.current_theme_name, "conky.conf"))
            self.lbl_selected.setText(f"Tema: {self.current_theme_name}")
            self.lbl_info.setText(f"Config:\n{self.current_conf_path}")
            self.check_autostart_status()

    def get_autostart_file_path(self):
        if not hasattr(self, 'current_theme_name'):
            return None
        return os.path.join(AUTOSTART_DIR, f"sinergia-conky-{self.current_theme_name}.desktop")

    def check_autostart_status(self):
        desktop_file = self.get_autostart_file_path()
        if desktop_file and os.path.exists(desktop_file):
            self.btn_autostart.setText("✅ Autostart: Activado")
            self.btn_autostart.setStyleSheet(self.get_btn_style("#43a047", "#2e7d32"))
        else:
            self.btn_autostart.setText("🔄 Autostart: Desactivado")
            self.btn_autostart.setStyleSheet(self.get_btn_style("#7e57c2", "#5e35b1"))

    def toggle_autostart(self):
        if not hasattr(self, 'current_conf_path'):
            return

        os.makedirs(AUTOSTART_DIR, exist_ok=True)
        desktop_file = self.get_autostart_file_path()

        if os.path.exists(desktop_file):
            try:
                os.remove(desktop_file)
                QMessageBox.information(self, "Autostart", "Se desactivó el inicio automático para este tema.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo quitar el autostart: {e}")
        else:
            desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Sinergia Conky - {self.current_theme_name}
Exec=conky -c {self.current_conf_path}
X-GNOME-Autostart-enabled=true
Terminal=false
Categories=System;
"""
            try:
                with open(desktop_file, "w") as f:
                    f.write(desktop_entry)
                QMessageBox.information(self, "Autostart", "¡Listo! Este tema iniciará automáticamente con tu sesión en cualquier entorno.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el archivo de autostart: {e}")

        self.check_autostart_status()

    def start_selected_conky(self):
        if not hasattr(self, 'current_conf_path') or not os.path.exists(self.current_conf_path):
            QMessageBox.warning(self, "Error", "No se seleccionó un archivo de configuración válido.")
            return

        try:
            subprocess.Popen(["conky", "-c", self.current_conf_path], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            QMessageBox.information(self, "Éxito", "¡Widget iniciado en paralelo correctamente!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo iniciar Conky: {e}")

    def stop_selected_conky(self):
        if not hasattr(self, 'current_conf_path'):
            return
        try:
            subprocess.run(["pkill", "-f", f"conky.*{self.current_conf_path}"], stderr=subprocess.DEVNULL)
            QMessageBox.information(self, "Detenido", "Se detuvo el widget seleccionado.")
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"No se pudo detener el proceso: {e}")

    def stop_all_conky(self):
        result = subprocess.run(["killall", "conky"], stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            QMessageBox.information(self, "Detenidos", "Se cerraron todas las instancias de Conky.")
        else:
            QMessageBox.warning(self, "Aviso", "No hay instancias de Conky ejecutándose.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SinergiaConkyManager()
    window.show()
    sys.exit(app.exec())
