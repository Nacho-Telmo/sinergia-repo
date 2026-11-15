#!/usr/bin/env python3
import sys
import psutil
import subprocess
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QMessageBox,
    QFrame,
)

class SinergiaFreeRam(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sinergia Free RAM")
        self.setFixedSize(480, 420)
        self.setProperty("class", "sinergia-free-ram")

        self.init_ui()

        # Timer para actualizar las estadísticas de RAM cada 1.5 segundos
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ram_stats)
        self.timer.start(1500)

        self.update_ram_stats()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Título
        title = QLabel("🧠 Sinergia Free RAM")
        title.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Monitoreo y optimización de memoria en tiempo real")
        subtitle.setFont(QFont("Sans Serif", 9))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #313244; max-height: 2px; border: none;")
        main_layout.addWidget(line)

        # Widgets de RAM
        self.ram_label = QLabel("RAM: Calculando...")
        self.ram_label.setFont(QFont("Sans Serif", 10, QFont.Weight.Bold))
        main_layout.addWidget(self.ram_label)

        self.ram_bar = QProgressBar()
        self.ram_bar.setRange(0, 100)
        self.ram_bar.setFixedHeight(18)
        main_layout.addWidget(self.ram_bar)

        # Widgets de SWAP
        self.swap_label = QLabel("SWAP: Calculando...")
        self.swap_label.setFont(QFont("Sans Serif", 10, QFont.Weight.Bold))
        main_layout.addWidget(self.swap_label)

        self.swap_bar = QProgressBar()
        self.swap_bar.setRange(0, 100)
        self.swap_bar.setFixedHeight(18)
        main_layout.addWidget(self.swap_bar)

        main_layout.addStretch()

        # Botón de Liberar Memoria
        self.btn_clean = QPushButton("🧹 Liberar Caché y Memoria RAM")
        self.btn_clean.setFixedHeight(40)
        self.btn_clean.setFont(QFont("Sans Serif", 10, QFont.Weight.Bold))
        self.btn_clean.clicked.connect(self.liberar_memoria)
        main_layout.addWidget(self.btn_clean)

        # Estilo visual base (Catppuccin Dark adaptado)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
            }
            QProgressBar {
                background-color: #11111b;
                border: 1px solid #313244;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #89b4fa;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #313244;
                color: #89b4fa;
                border: 1px solid #89b4fa;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45475a;
                color: #ffffff;
            }
        """)

    def update_ram_stats(self):
        ram = psutil.virtual_memory()
        used_gb = ram.used / (1024**3)
        total_gb = ram.total / (1024**3)
        self.ram_label.setText(f"RAM: {used_gb:.2f} GB / {total_gb:.2f} GB ({ram.percent}%)")
        self.ram_bar.setValue(int(ram.percent))

        swap = psutil.swap_memory()
        if swap.total > 0:
            swap_used_gb = swap.used / (1024**3)
            swap_total_gb = swap.total / (1024**3)
            self.swap_label.setText(f"SWAP: {swap_used_gb:.2f} GB / {swap_total_gb:.2f} GB ({swap.percent}%)")
            self.swap_bar.setValue(int(swap.percent))
        else:
            self.swap_label.setText("SWAP: Desactivada / No disponible")
            self.swap_bar.setValue(0)

    @pyqtSlot()
    def liberar_memoria(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Liberar Memoria")
        msg.setText("¿Deseas liberar la caché de páginas, dentries e inodos del sistema?")
        msg.setInformativeText("Esta acción requiere permisos de administrador y liberará memoria RAM inactiva.")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                cmd = "pkexec sh -c 'sync && echo 3 > /proc/sys/vm/drop_caches'"
                resultado = subprocess.run(cmd, shell=True, capture_output=True, text=True)

                if resultado.returncode == 0:
                    QMessageBox.information(self, "Éxito", "¡Memoria caché liberada correctamente con éxito!")
                    self.update_ram_stats()
                else:
                    QMessageBox.warning(self, "Aviso", "La operación fue cancelada o no se otorgaron permisos de superusuario.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo ejecutar la limpieza: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SinergiaFreeRam()
    window.show()
    sys.exit(app.exec())
