#!/usr/bin/env python3
import sys
import os
import subprocess
import time

os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class SinergiaServiceManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sinergia Service Manager - Gestor de Servicios")
        self.setFixedSize(720, 450)
        self.init_ui()
        self.cargar_servicios()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title = QLabel("⚙️ Gestor de Servicios de Sistema")
        title.setFont(QFont("Sans", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Administrá los servicios principales de Arch Linux fácilmente")
        subtitle.setFont(QFont("Sans", 10))
        subtitle.setStyleSheet("color: #888;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Tabla de servicios
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Servicio", "Descripción", "Estado / Inicio"])
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tabla)

        # Botonera de acciones
        btn_layout = QHBoxLayout()

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.clicked.connect(self.cargar_servicios)
        btn_layout.addWidget(btn_refresh)

        btn_start = QPushButton("▶️ Iniciar")
        btn_start.clicked.connect(lambda: self.ejecutar_accion("start"))
        btn_layout.addWidget(btn_start)

        btn_stop = QPushButton("⏹️ Detener")
        btn_stop.clicked.connect(lambda: self.ejecutar_accion("stop"))
        btn_layout.addWidget(btn_stop)

        btn_enable = QPushButton("🔒 Habilitar")
        btn_enable.clicked.connect(lambda: self.ejecutar_accion("enable"))
        btn_layout.addWidget(btn_enable)

        btn_disable = QPushButton("🔓 Deshabilitar")
        btn_disable.clicked.connect(lambda: self.ejecutar_accion("disable"))
        btn_layout.addWidget(btn_disable)

        layout.addLayout(btn_layout)

    def obtener_gestor_pantalla(self):
        """Detecta dinámicamente qué gestor de pantalla (DM) está activo o configurado."""
        try:
            # 1. Intentar consultar directamente el alias global de systemd para el display-manager
            res = subprocess.run(
                ["systemctl", "show", "display-manager.service", "--property=Id", "--value"],
                capture_output=True, text=True, check=True
            )
            dm = res.stdout.strip()
            if dm and dm != "display-manager.service":
                return dm
        except Exception:
            pass

        # 2. Si falla, buscar cuál de los gestores comunes está habilitado o instalado
        candidatos = ["gdm.service", "sddm.service", "lightdm.service", "lxdm.service", "xdm.service"]
        for cand in candidatos:
            try:
                res = subprocess.run(["systemctl", "is-enabled", cand], capture_output=True, text=True)
                if res.stdout.strip() in ["enabled", "linked"]:
                    return cand
            except Exception:
                continue

        # Por defecto si no encuentra ninguno
        return "sddm.service"

    def cargar_servicios(self):
        # Detectar dinámicamente el gestor de pantalla actual del entorno (GNOME, KDE, etc.)
        dm_service = self.obtener_gestor_pantalla()

        # Definir los nombres amigables según el DM detectado
        nombres_dm = {
            "gdm.service": "Gestor de Sesión (GDM - GNOME)",
            "sddm.service": "Gestor de Sesión (SDDM - KDE)",
            "lightdm.service": "Gestor de Sesión (LightDM)",
            "lxdm.service": "Gestor de Sesión (LXDM)"
        }
        dm_desc = nombres_dm.get(dm_service, f"Gestor de Sesión ({dm_service})")

        # Servicios base + el DM detectado dinámicamente
        servicios_comunes = [
            ("NetworkManager.service", "Gestor de Red"),
            ("bluetooth.service", "Servicio Bluetooth"),
            ("cups.service", "Sistema de Impresión (CUPS)"),
            ("sshd.service", "Servidor SSH"),
            (dm_service, dm_desc),
            ("firewalld.service", "Firewall del Sistema")
        ]

        self.tabla.setRowCount(len(servicios_comunes))
        for row, (service, desc) in enumerate(servicios_comunes):
            # Obtener estado activo
            res_active = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True)
            val_active = res_active.stdout.strip()
            activo = val_active == "active"

            # Obtener estado enabled
            res_enabled = subprocess.run(["systemctl", "is-enabled", service], capture_output=True, text=True)
            val_enabled = res_enabled.stdout.strip()
            habilitado = val_enabled == "enabled"

            estado_str = f"{'🟢 Activo' if activo else '🔴 Detenido'}  |  {'🔒 Habilitado' if habilitado else '🔓 Deshabilitado'}"

            item_serv = QTableWidgetItem(service)
            item_desc = QTableWidgetItem(desc)
            item_estado = QTableWidgetItem(estado_str)

            self.tabla.setItem(row, 0, item_serv)
            self.tabla.setItem(row, 1, item_desc)
            self.tabla.setItem(row, 2, item_estado)

    def ejecutar_accion(self, accion):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Selección requerida", "Por favor, seleccioná un servicio de la lista.")
            return

        service = self.tabla.item(fila, 0).text()

        if accion == "start":
            cmd = ["pkexec", "systemctl", "start", service]
        elif accion == "stop":
            cmd = ["pkexec", "systemctl", "stop", service]
        elif accion == "enable":
            cmd = ["pkexec", "systemctl", "enable", "--now", service]
        elif accion == "disable":
            cmd = ["pkexec", "systemctl", "disable", service]

        try:
            resultado = subprocess.run(cmd, capture_output=True, text=True, check=True)
            time.sleep(0.5)
            self.cargar_servicios()
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo ejecutar la acción '{accion}' en {service}.\n\nDetalle:\n{e.stderr.strip()}"
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SinergiaServiceManager()
    window.show()
    sys.exit(app.exec())
