#!/usr/bin/env python3
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
from PyQt6.QtCore import QEvent, QProcess, Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def cargar_icono_app() -> QIcon:
    candidatos = [
        Path("/usr/share/icons/hicolor/scalable/apps/sinergia-perifericos.svg"),
        Path(__file__).resolve().parent / "logo.svg",
    ]
    for ruta in candidatos:
        if ruta.is_file():
            icono = QIcon(str(ruta))
            if not icono.isNull():
                return icono
    return QIcon.fromTheme("preferences-system")


class SinergiaPerifericos(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setProperty("class", "sinergia-perifericos")
        self.setWindowTitle("Sinergia Periféricos")
        self.setWindowIcon(cargar_icono_app())
        self.resize(620, 560)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.leer_salida)
        self.process.readyReadStandardError.connect(self.leer_salida)
        self.process.finished.connect(self.proceso_finalizado)

        self.init_ui()
        self.actualizar_estilo_segun_tema()
        self.verificar_estado_actual()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        titulo = QLabel("Sinergia Periféricos — Bluetooth e Impresoras")
        titulo.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "Instalación de paquetes y activación de servicios para Bluetooth (Blueman) e Impresión (CUPS + Plasma)"
        )
        subtitulo.setFont(QFont("Sans Serif", 9))
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitulo)

        # --- 1. Bloque Bluetooth ---
        grp_bt = QGroupBox("1. Bluetooth (BlueZ + Blueman)")
        bt_layout = QVBoxLayout(grp_bt)

        self.lbl_estado_bt = QLabel("Estado: comprobando...")
        self.lbl_estado_bt.setFont(QFont("Sans Serif", 9, QFont.Weight.Bold))
        bt_layout.addWidget(self.lbl_estado_bt)

        self.chk_install_bt = QCheckBox(
            "Instalar soporte Bluetooth y gestor gráfico (bluez, bluez-utils, blueman)"
        )
        self.chk_install_bt.setChecked(True)
        bt_layout.addWidget(self.chk_install_bt)

        self.chk_enable_bt = QCheckBox(
            "Habilitar y levantar servicio bluetooth.service ahora"
        )
        self.chk_enable_bt.setChecked(True)
        bt_layout.addWidget(self.chk_enable_bt)

        layout.addWidget(grp_bt)

        # --- 2. Bloque Impresoras ---
        grp_print = QGroupBox("2. Impresión (CUPS + Preferencias de Plasma)")
        print_layout = QVBoxLayout(grp_print)

        self.lbl_estado_print = QLabel("Estado: comprobando...")
        self.lbl_estado_print.setFont(QFont("Sans Serif", 9, QFont.Weight.Bold))
        print_layout.addWidget(self.lbl_estado_print)

        self.chk_install_cups = QCheckBox(
            "Instalar impresión y módulo de Plasma (cups, cups-pdf, print-manager, system-config-printer)"
        )
        self.chk_install_cups.setChecked(True)
        print_layout.addWidget(self.chk_install_cups)

        self.chk_install_hplip = QCheckBox(
            "Incluir soporte para impresoras HP (hplip)"
        )
        self.chk_install_hplip.setChecked(False)
        print_layout.addWidget(self.chk_install_hplip)

        self.chk_enable_cups = QCheckBox(
            "Habilitar y levantar servicio cups.service ahora"
        )
        self.chk_enable_cups.setChecked(True)
        print_layout.addWidget(self.chk_enable_cups)

        layout.addWidget(grp_print)

        # --- Botones de acción ---
        acciones = QHBoxLayout()

        self.btn_run = QPushButton("Aplicar Selección")
        self.btn_run.setFixedHeight(36)
        self.btn_run.clicked.connect(self.ejecutar_acciones)
        acciones.addWidget(self.btn_run, 2)

        self.btn_refresh = QPushButton("Comprobar Estado")
        self.btn_refresh.setFixedHeight(36)
        self.btn_refresh.clicked.connect(self.verificar_estado_actual)
        acciones.addWidget(self.btn_refresh, 1)

        self.btn_clear = QPushButton("Limpiar Log")
        self.btn_clear.setFixedHeight(36)
        self.btn_clear.clicked.connect(self.limpiar_log)
        acciones.addWidget(self.btn_clear, 1)

        layout.addLayout(acciones)

        # --- Consola de salida ---
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Monospace", 9))
        layout.addWidget(self.log_output, 1)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ApplicationPaletteChange:
            self.actualizar_estilo_segun_tema()
        super().changeEvent(event)

    def actualizar_estilo_segun_tema(self):
        palette = QApplication.palette()
        is_light = palette.color(palette.ColorRole.Window).lightness() > 128

        if is_light:
            self.setStyleSheet("""
                QMainWindow { background-color: #f5f5f5; color: #222222; }
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #cccccc;
                    border-radius: 6px;
                    margin-top: 8px;
                    padding-top: 10px;
                }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
                QPushButton {
                    background-color: #ffffff;
                    color: #222222;
                    border: 1px solid #00acc1;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #eaeaea; border: 1px solid #00838f; }
                QPlainTextEdit {
                    background-color: #ffffff;
                    color: #1e1e1e;
                    border: 1px solid #cccccc;
                    border-radius: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #121212; color: #ffffff; }
                QGroupBox {
                    font-weight: bold;
                    color: #ffffff;
                    border: 1px solid #333333;
                    border-radius: 6px;
                    margin-top: 8px;
                    padding-top: 10px;
                }
                QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
                QLabel, QCheckBox { color: #eeeeee; }
                QPushButton {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #00acc1;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #2d2d2d; border: 1px solid #ffffff; }
                QPlainTextEdit {
                    background-color: #181818;
                    color: #e0e0e0;
                    border: 1px solid #333333;
                    border-radius: 6px;
                }
            """)

    @staticmethod
    def paquete_instalado(pkg: str) -> bool:
        res = subprocess.run(
            ["pacman", "-Q", pkg],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return res.returncode == 0

    @staticmethod
    def servicio_estado(unit: str) -> tuple[bool, bool]:
        activo = (
            subprocess.run(
                ["systemctl", "is-active", "--quiet", unit]
            ).returncode
            == 0
        )
        habilitado = (
            subprocess.run(
                ["systemctl", "is-enabled", "--quiet", unit]
            ).returncode
            == 0
        )
        return activo, habilitado

    def verificar_estado_actual(self):
        hora = datetime.now().strftime("%H:%M:%S")

        bluez_ok = self.paquete_instalado("bluez") and self.paquete_instalado(
            "bluez-utils"
        )
        blueman_ok = self.paquete_instalado("blueman")
        bt_act, bt_hab = self.servicio_estado("bluetooth.service")

        texto_bt = (
            f"bluez={'Instalado' if bluez_ok else 'Falta'} | "
            f"blueman={'Instalado' if blueman_ok else 'Falta'} | "
            f"bluetooth.service={'activo' if bt_act else 'inactivo'} / "
            f"{'habilitado' if bt_hab else 'deshabilitado'}"
        )
        self.lbl_estado_bt.setText(f"Estado: {texto_bt}")

        cups_ok = self.paquete_instalado("cups")
        pm_ok = self.paquete_instalado("print-manager")
        cups_act, cups_hab = self.servicio_estado("cups.service")

        texto_print = (
            f"cups={'Instalado' if cups_ok else 'Falta'} | "
            f"print-manager={'Instalado' if pm_ok else 'Falta'} | "
            f"cups.service={'activo' if cups_act else 'inactivo'} / "
            f"{'habilitado' if cups_hab else 'deshabilitado'}"
        )
        self.lbl_estado_print.setText(f"Estado: {texto_print}")

        self.log_output.appendPlainText(
            f"[{hora}] Comprobación de estado:\n"
            f"  • Bluetooth:  {texto_bt}\n"
            f"  • Impresión:  {texto_print}"
        )

    def construir_comando_shell(self) -> str:
        comandos = ["set -e"]
        paquetes = []

        if self.chk_install_bt.isChecked():
            paquetes.extend(["bluez", "bluez-utils", "blueman"])

        if self.chk_install_cups.isChecked():
            paquetes.extend([
                "cups",
                "cups-pdf",
                "print-manager",
                "system-config-printer",
            ])

        if self.chk_install_hplip.isChecked():
            paquetes.append("hplip")

        if paquetes:
            pkgs_str = " ".join(dict.fromkeys(paquetes))
            comandos.append(f"echo '==> Instalando paquetes: {pkgs_str}'")
            comandos.append(f"pacman -S --needed --noconfirm {pkgs_str}")

        if self.chk_enable_bt.isChecked():
            comandos.append("echo '==> Habilitando y levantando bluetooth.service...'")
            comandos.append("systemctl enable --now bluetooth.service")

        if self.chk_enable_cups.isChecked():
            comandos.append("echo '==> Habilitando y levantando cups.service...'")
            comandos.append("systemctl enable --now cups.service")

        if len(comandos) == 1:
            return ""

        return " && ".join(comandos)

    def ejecutar_acciones(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            return

        if not shutil.which("pkexec"):
            QMessageBox.critical(
                self,
                "Polkit no disponible",
                "No se encontró 'pkexec' en el sistema para elevar privilegios.",
            )
            return

        script = self.construir_comando_shell()
        if not script:
            self.log_output.appendPlainText("No seleccionaste ninguna acción.")
            return

        self.btn_run.setEnabled(False)
        self.btn_refresh.setEnabled(False)
        self.log_output.appendPlainText("Solicitando autorización con pkexec...\n")
        self.process.start("pkexec", ["bash", "-c", script])

    def leer_salida(self):
        data = bytes(self.process.readAllStandardOutput()) + bytes(
            self.process.readAllStandardError()
        )
        texto = data.decode("utf-8", errors="replace")
        if texto:
            self.log_output.appendPlainText(texto.rstrip("\n"))

    def proceso_finalizado(self, exit_code, _exit_status):
        self.btn_run.setEnabled(True)
        self.btn_refresh.setEnabled(True)
        self.verificar_estado_actual()

        if exit_code == 0:
            self.log_output.appendPlainText("\n✅ Operaciones completadas correctamente.")
        else:
            self.log_output.appendPlainText(
                f"\n❌ El proceso finalizó con código de salida {exit_code}."
            )

    def limpiar_log(self):
        self.log_output.clear()


if __name__ == "__main__":
    QApplication.setDesktopFileName("sinergia-perifericos")
    app = QApplication(sys.argv)
    app.setApplicationName("sinergia-perifericos")
    icono = cargar_icono_app()
    if not icono.isNull():
        app.setWindowIcon(icono)
    win = SinergiaPerifericos()
    win.show()
    sys.exit(app.exec())
