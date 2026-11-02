import sys
import os
import subprocess
import re
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QComboBox, QProgressBar,
                             QLabel, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

class BurnWorker(QThread):
    progress_changed = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, iso_path, drive_path):
        super().__init__()
        self.iso_path = iso_path
        self.drive_path = drive_path

    def run(self):
        try:
            total_size = os.path.getsize(self.iso_path)

            # Usamos pkexec para pedir permisos de root de forma gráfica y nativa.
            # bs=4M y oflag=sync garantizan velocidad y escritura física real.
            cmd = ["pkexec", "dd", f"if={self.iso_path}", f"of={self.drive_path}", "bs=4M", "status=progress", "oflag=sync"]

            process = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True, bufsize=1)

            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break

                # Expresión regular para capturar bytes y velocidad intermitente de dd
                match = re.search(r'(\d+)\s+bytes', line)
                if match:
                    bytes_copied = int(match.group(1))
                    percentage = int((bytes_copied / total_size) * 100)
                    self.progress_changed.emit(min(percentage, 100))

                    # Intentar extraer velocidad si está disponible en la línea
                    vel_match = re.search(r',\s+([^,]+)$', line.strip())
                    if vel_match:
                        self.status_changed.emit(f"Escribiendo a {vel_match.group(1)}")

            if process.returncode == 0:
                self.finished.emit(True, "¡Imagen quemada con éxito! Ya podés retirar el pendrive.")
            elif process.returncode == 127:
                self.finished.emit(False, "Autenticación denegada o pkexec no disponible.")
            else:
                self.finished.emit(False, f"El proceso falló con código de salida: {process.returncode}")

        except Exception as e:
            self.finished.emit(False, str(e))


class DDBurnerPro(QWidget):
    def __init__(self):
        super().__init__()
        self.iso_path = ""
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        self.setWindowTitle("Sinergia DD Burner")
        self.setFixedSize(450, 280)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # SECCIÓN ISO
        lbl_iso_title = QLabel("Archivo de Imagen (ISO/IMG):")
        lbl_iso_title.setObjectName("SectionTitle")
        layout.addWidget(lbl_iso_title)

        iso_row = QHBoxLayout()
        self.btn_iso = QPushButton("Seleccionar ISO")
        self.btn_iso.clicked.connect(self.select_iso)
        self.lbl_iso_name = QLabel("Ninguna imagen seleccionada")
        self.lbl_iso_name.setWordWrap(True)
        iso_row.addWidget(self.btn_iso)
        iso_row.addWidget(self.lbl_iso_name, 1)
        layout.addLayout(iso_row)

        # SECCIÓN PENDRIVE
        lbl_drive_title = QLabel("Dispositivo de Destino:")
        lbl_drive_title.setObjectName("SectionTitle")
        layout.addWidget(lbl_drive_title)

        drive_row = QHBoxLayout()
        self.combo_drives = QComboBox()
        self.btn_refresh = QPushButton("⟳")
        self.btn_refresh.setToolTip("Refrescar lista de unidades")
        self.btn_refresh.setFixedWidth(40)
        self.btn_refresh.clicked.connect(self.refresh_drives)

        drive_row.addWidget(self.combo_drives, 1)
        drive_row.addWidget(self.btn_refresh)
        layout.addLayout(drive_row)

        # PROGRESO
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Estado: Esperando inicio...")
        self.lbl_status.setObjectName("StatusLabel")
        layout.addWidget(self.lbl_status)

        # ACCIÓN
        self.btn_burn = QPushButton("Quemar Imagen")
        self.btn_burn.setObjectName("BurnButton")
        self.btn_burn.clicked.connect(self.start_burning)
        layout.addWidget(self.btn_burn)

        self.setLayout(layout)
        self.refresh_drives()

    def apply_styles(self):
        # Hoja de estilos QSS oscura moderna
        qss = """
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QLabel#SectionTitle {
                font-weight: bold;
                color: #b4befe;
            }
            QLabel#StatusLabel {
                color: #a6adc8;
                font-size: 11px;
            }
            QPushButton {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 12px;
                color: #cdd6f4;
            }
            QPushButton:hover {
                background-color: #45475a;
                border: 1px solid #585b70;
            }
            QPushButton:pressed {
                background-color: #585b70;
            }
QPushButton#BurnButton {
    background-color: #a6e3a1;
    color: #11111b !important;
    font-weight: bold;
    font-size: 14px;
    height: 40px;
    border-radius: 6px;
    border: 1px solid #1e1e2e;
}
            QPushButton#BurnButton:hover {
                background-color: #b4befe;
            }
            QPushButton#BurnButton:disabled {
                background-color: #181825;
                color: #585b70;
            }
            QComboBox {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 5px;
                color: #cdd6f4;
            }
            QComboBox::drop-down {
                border: 0px;
            }
            QProgressBar {
                border: 1px solid #45475a;
                border-radius: 6px;
                background-color: #11111b;
                text-align: center;
                font-weight: bold;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #a6e3a1;
                border-radius: 5px;
            }
        """
        self.setStyleSheet(qss)

    def select_iso(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar ISO o IMG", "", "Imágenes de disco (*.iso *.img)")
        if file_path:
            self.iso_path = file_path
            self.lbl_iso_name.setText(os.path.basename(file_path))

    def refresh_drives(self):
        self.combo_drives.clear()
        try:
            # Listamos usando lsblk obteniendo nombre, tamaño, modelo y punto de montaje
            output = subprocess.check_output(["lsblk", "-dno", "NAME,SIZE,MODEL,MOUNTPOINTS"], text=True)
            devices_found = False

            for line in output.strip().split('\n'):
                if line:
                    parts = line.split(maxsplit=3)
                    if len(parts) < 2:
                        continue

                    name = f"/dev/{parts[0]}"
                    size = parts[1]
                    # Manejar si no tiene modelo o puntos de montaje mapeados
                    model = "Unidad Genérica"
                    mounts = ""

                    if len(parts) == 3:
                        if parts[2].startswith('/') or parts[2] == '[]':
                            mounts = parts[2]
                        else:
                            model = parts[2]
                    elif len(parts) == 4:
                        model = parts[2]
                        mounts = parts[3]

                    # FILTRO DE SEGURIDAD: Si está montado en la raíz o boot, lo salteamos de la lista
                    if "/" == mounts.strip() or "/boot" in mounts:
                        continue

                    self.combo_drives.addItem(f"⚡ {name} ({size}) - {model}", name)
                    devices_found = True

            if not devices_found:
                self.combo_drives.addItem("No se detectaron pendrives seguros", "")

        except Exception as e:
            self.combo_drives.addItem("Error al listar unidades", "")
            self.lbl_status.setText(f"Error lsblk: {str(e)}")

    def start_burning(self):
        drive = self.combo_drives.currentData()
        if not self.iso_path or not drive:
            QMessageBox.warning(self, "Datos faltantes", "Por favor, selecciona una imagen ISO y un destino válido.")
            return

        # Cartel de advertencia definitivo
        confirm = QMessageBox.question(
            self, "¡ADVERTENCIA DE DESTRUCCIÓN!",
            f"¿Estás absolutamente seguro de que querés escribir en {drive}?\n\n"
            "Todos los datos actuales de ese dispositivo se borrarán por completo de forma irreversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.btn_burn.setEnabled(False)
            self.btn_iso.setEnabled(False)
            self.btn_refresh.setEnabled(False)
            self.combo_drives.setEnabled(False)

            self.progress_bar.setValue(0)
            self.lbl_status.setText("Estado: Autenticando...")

            # Lanzamos el Worker de DD
            self.worker = BurnWorker(self.iso_path, drive)
            self.worker.progress_changed.connect(self.progress_bar.setValue)
            self.worker.status_changed.connect(self.lbl_status.setText)
            self.worker.finished.connect(self.burn_finished)
            self.worker.start()

    def burn_finished(self, success, message):
        self.btn_burn.setEnabled(True)
        self.btn_iso.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        self.combo_drives.setEnabled(True)

        if success:
            self.progress_bar.setValue(100)
            self.lbl_status.setText("Estado: Finalizado con éxito.")
            QMessageBox.information(self, "Proceso Completado", message)
        else:
            self.progress_bar.setValue(0)
            self.lbl_status.setText("Estado: Hubo un error.")
            QMessageBox.critical(self, "Error de Escritura", message)
        self.refresh_drives()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = DDBurnerPro()
    gui.show()
    sys.exit(app.exec())
