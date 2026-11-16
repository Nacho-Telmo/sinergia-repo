#!/usr/bin/env python3
import sys
import subprocess
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QPushButton, QMessageBox, QFrame, QHBoxLayout
)
from PyQt6.QtGui import QIcon

class SinergiaCodecFixer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sinergia Codec Fixer")
        self.setFixedSize(600, 500)

        # Soporte correcto para Wayland y X11
        self.setWindowIcon(QIcon.fromTheme("sinergia-codec-fixer"))
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Título centrado
        title_label = QLabel("Gestor de Codec y fuentes")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2ecc71;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # --- CUADRO 1: LO QUE YA ESTÁ INSTALADO ---
        lbl_installed_title = QLabel("1. Estado actual en tu sistema:")
        lbl_installed_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #bdc3c7;")
        layout.addWidget(lbl_installed_title)

        installed_frame = QFrame()
        installed_frame.setStyleSheet("background: transparent; border: 1px solid rgba(46, 204, 113, 0.4); border-radius: 6px;")
        installed_layout = QVBoxLayout(installed_frame)
        installed_layout.setContentsMargins(14, 12, 14, 12)
        installed_layout.setSpacing(6)

        self.lbl_installed_content = QLabel()
        self.lbl_installed_content.setWordWrap(True)
        self.lbl_installed_content.setStyleSheet("color: #2ecc71; font-size: 12px;")
        installed_layout.addWidget(self.lbl_installed_content)

        layout.addWidget(installed_frame)

        # --- CUADRO 2: RECOMENDACIÓN / FALTANTES A INSTALAR ---
        lbl_recom_title = QLabel("2. Recomendación de componentes para agregar:")
        lbl_recom_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #bdc3c7;")
        layout.addWidget(lbl_recom_title)

        recom_frame = QFrame()
        recom_frame.setStyleSheet("background: transparent; border: 1px solid rgba(41, 128, 185, 0.4); border-radius: 6px;")
        recom_layout = QVBoxLayout(recom_frame)
        recom_layout.setContentsMargins(14, 12, 14, 12)
        recom_layout.setSpacing(6)

        self.lbl_recom_content = QLabel()
        self.lbl_recom_content.setWordWrap(True)
        self.lbl_recom_content.setStyleSheet("color: #3498db; font-size: 12px; line-height: 140%;")
        recom_layout.addWidget(self.lbl_recom_content)

        layout.addWidget(recom_frame)

        layout.addStretch()

        # Botón de Acción Dinámico (Creado ANTES de chequear el estado)
        self.btn_install = QPushButton("Instalar Componentes Faltantes")
        self.btn_install.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        self.btn_install.clicked.connect(self.install_missing_components)
        layout.addWidget(self.btn_install)

        # Cargar el estado real al iniciar (con el botón ya creado)
        self.check_system_status()

    def check_system_status(self):
        """Verifica mediante pacman qué paquetes esenciales ya están instalados."""
        packages_to_check = [
            "gstreamer", "gst-plugins-good", "gst-plugins-bad",
            "gst-plugins-ugly", "gst-libav", "ttf-ms-fonts"
        ]

        installed = []
        missing = []

        for pkg in packages_to_check:
            try:
                result = subprocess.run(
                    ["pacman", "-Q", pkg],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode == 0:
                    installed.append(pkg)
                else:
                    missing.append(pkg)
            except Exception:
                missing.append(pkg)

        # Actualizar textos visuales de las tarjetas
        if installed:
            self.lbl_installed_content.setText(f"<b>Paquetes detectados:</b> {', '.join(installed)}")
        else:
            self.lbl_installed_content.setText("<b>Paquetes detectados:</b> Ninguno de los códecs recomendados está instalado.")

        if missing:
            self.lbl_recom_content.setText(
                f"<b>Faltan por instalar:</b> {', '.join(missing)}<br>"
                "<i>Se recomienda agregarlos para asegurar compatibilidad total con videos web, "
                "reproductores multimedia locales y documentos de Microsoft Office.</i>"
            )
            self.btn_install.setEnabled(True)
        else:
            self.lbl_recom_content.setText("<b>¡Todo al día!</b> Tu sistema ya cuenta con todos los códecs y fuentes recomendadas instaladas.")
            self.btn_install.setEnabled(False)
            self.btn_install.setText("Sistema Optimizado")

    def install_missing_components(self):
        """Instala los componentes faltantes utilizando pacman a través de pkexec."""
        packages = "gstreamer gst-plugins-good gst-plugins-bad gst-plugins-ugly gst-libav ttf-ms-fonts"
        cmd = f"pacman -S --needed --noconfirm {packages}"

        try:
            subprocess.run(["pkexec", "bash", "-c", cmd], check=True)
            QMessageBox.information(
                self,
                "¡Éxito!",
                "Los componentes se instalaron correctamente."
            )
            # Refrescar estados visuales
            self.check_system_status()
        except subprocess.CalledProcessError:
            QMessageBox.critical(
                self,
                "Cancelado o Error",
                "No se pudo completar la instalación. Es posible que se haya cancelado la autenticación."
            )

if __name__ == "__main__":
    # Asegurar nombre de escritorio para Wayland y X11
    QApplication.setDesktopFileName("sinergia-codec-fixer")

    app = QApplication(sys.argv)
    window = SinergiaCodecFixer()
    window.show()
    sys.exit(app.exec())
