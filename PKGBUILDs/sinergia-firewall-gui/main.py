#!/usr/bin/env python3
import sys
import subprocess
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QPushButton, QMessageBox, QFrame, QHBoxLayout
)
from PyQt6.QtGui import QIcon

class SinergiaFirewallGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sinergia Firewall GUI")
        self.setFixedSize(600, 500)

        # Soporte correcto para Wayland y X11
        self.setWindowIcon(QIcon.fromTheme("sinergia-firewall-gui"))
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Título centrado
        title_label = QLabel("Gestor de Cortafuegos (UFW)")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #e74c3c;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # --- CUADRO 1: ESTADO ACTUAL DEL CORTAFUEGOS ---
        lbl_status_title = QLabel("1. Estado actual del sistema:")
        lbl_status_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #bdc3c7;")
        layout.addWidget(lbl_status_title)

        status_frame = QFrame()
        status_frame.setStyleSheet("background: transparent; border: 1px solid rgba(231, 76, 60, 0.4); border-radius: 6px;")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(14, 12, 14, 12)
        status_layout.setSpacing(6)

        self.lbl_status_content = QLabel()
        self.lbl_status_content.setWordWrap(True)
        self.lbl_status_content.setStyleSheet("color: #e74c3c; font-size: 12px; font-family: monospace;")
        status_layout.addWidget(self.lbl_status_content)

        layout.addWidget(status_frame)

        # --- CUADRO 2: REGLAS Y ACCESOS RÁPIDOS ---
        lbl_rules_title = QLabel("2. Información y políticas predeterminadas:")
        lbl_rules_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #bdc3c7;")
        layout.addWidget(lbl_rules_title)

        rules_frame = QFrame()
        rules_frame.setStyleSheet("background: transparent; border: 1px solid rgba(52, 152, 219, 0.4); border-radius: 6px;")
        rules_layout = QVBoxLayout(rules_frame)
        rules_layout.setContentsMargins(14, 12, 14, 12)
        rules_layout.setSpacing(6)

        self.lbl_rules_content = QLabel()
        self.lbl_rules_content.setWordWrap(True)
        self.lbl_rules_content.setStyleSheet("color: #3498db; font-size: 12px; line-height: 140%;")
        rules_layout.addWidget(self.lbl_rules_content)

        layout.addWidget(rules_frame)

        layout.addStretch()

        # Botón de Acción Dinámico (Activar / Desactivar Firewall)
        self.btn_toggle = QPushButton("Cargando estado...")
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        self.btn_toggle.clicked.connect(self.toggle_firewall)
        layout.addWidget(self.btn_toggle)

        # Cargar estado al iniciar
        self.check_firewall_status()

    def check_firewall_status(self):
        """Consulta el estado de ufw y systemd mediante subprocess."""
        try:
            result = subprocess.run(
                ["sudo", "ufw", "status"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            output = result.stdout.strip()

            # Verificamos también si el servicio en systemd está activo
            sys_result = subprocess.run(
                ["systemctl", "is-active", "ufw"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            is_sys_active = sys_result.stdout.strip() == "active"

            if "status: active" in output.lower() or is_sys_active:
                self.lbl_status_content.setText("<b>Estado: ACTIVO y protegido por systemd.</b>")
                self.lbl_rules_content.setText(f"<pre>{output}</pre>")
                self.btn_toggle.setText("Desactivar Cortafuegos")
                self.is_active = True
            else:
                self.lbl_status_content.setText("<b>Estado: INACTIVO (El sistema está expuesto).</b>")
                self.lbl_rules_content.setText("<i>Se recomienda activar el cortafuegos para bloquear conexiones entrantes no deseadas.</i>")
                self.btn_toggle.setText("Activar Cortafuegos (Recomendado)")
                self.is_active = False

        except Exception as e:
            self.lbl_status_content.setText("<b>Error:</b> No se pudo verificar UFW.")
            self.lbl_rules_content.setText(f"Detalle: {e}")
            self.btn_toggle.setEnabled(False)

    def toggle_firewall(self):
        """Activa o desactiva UFW y ajusta su persistencia en systemd mediante pkexec."""
        if self.is_active:
            cmd = "ufw disable && systemctl disable --now ufw"
        else:
            cmd = "ufw enable && systemctl enable --now ufw"

        try:
            subprocess.run(["pkexec", "bash", "-c", cmd], check=True)
            QMessageBox.information(
                self,
                "¡Éxito!",
                f"El cortafuegos se ha {'desactivado' + ' y deshabilitado en systemd' if self.is_active else 'activado y configurado para iniciar con el sistema'} correctamente."
            )
            self.check_firewall_status()
        except subprocess.CalledProcessError:
            QMessageBox.critical(
                self,
                "Cancelado o Error",
                "No se pudo modificar el estado del cortafuegos. Verifique la autenticación."
            )

if __name__ == "__main__":
    QApplication.setDesktopFileName("sinergia-firewall-gui")

    app = QApplication(sys.argv)
    window = SinergiaFirewallGUI()
    window.show()
    sys.exit(app.exec())
