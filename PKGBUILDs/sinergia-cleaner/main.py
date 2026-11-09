#!/usr/bin/env python3
import sys
from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class SinergiaCleanerApp(QMainWindow):

  def __init__(self):
    super().__init__()
    self.init_ui()
    self.process = QProcess(self)
    self.process.readyReadStandardOutput.connect(self.handle_stdout)
    self.process.readyReadStandardError.connect(self.handle_stderr)
    self.process.finished.connect(self.process_finished)

  def init_ui(self):
    self.setWindowTitle("Sinergia Cleaner")
    self.setFixedSize(620, 520)
    self.setStyleSheet("""
        QMainWindow {
            background-color: #121212;
            color: #ffffff;
        }
        QLabel {
            color: #ffffff;
        }
    """)

    # Widget central y layout principal
    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(14)

    # Título
    title_label = QLabel("🧹 Sinergia System Cleaner")
    title_label.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title_label)

    # Fila 1 de Botones de acción (Sistema / Root)
    btn_layout_1 = QHBoxLayout()

    self.btn_cache = QPushButton("Limpiar Caché (Pacman)")
    self.btn_cache.setFixedHeight(38)
    self.btn_cache.setStyleSheet(self.get_button_style("#00acc1", "#00838f"))
    self.btn_cache.clicked.connect(self.clean_cache)
    btn_layout_1.addWidget(self.btn_cache)

    self.btn_orphans = QPushButton("Eliminar Huérfanos (-Qdtq)")
    self.btn_orphans.setFixedHeight(38)
    self.btn_orphans.setStyleSheet(self.get_button_style("#00acc1", "#00838f"))
    self.btn_orphans.clicked.connect(self.clean_orphans)
    btn_layout_1.addWidget(self.btn_orphans)

    layout.addLayout(btn_layout_1)

    # Fila 2 de Botones de acción (Usuario / Local)
    btn_layout_2 = QHBoxLayout()

    self.btn_user_cache = QPushButton("Limpiar Caché Usuario")
    self.btn_user_cache.setFixedHeight(38)
    self.btn_user_cache.setStyleSheet(self.get_button_style("#7e57c2", "#5e35b1"))
    self.btn_user_cache.clicked.connect(self.clean_user_cache)
    btn_layout_2.addWidget(self.btn_user_cache)

    self.btn_thumbnails = QPushButton("Limpiar Miniaturas")
    self.btn_thumbnails.setFixedHeight(38)
    self.btn_thumbnails.setStyleSheet(self.get_button_style("#7e57c2", "#5e35b1"))
    self.btn_thumbnails.clicked.connect(self.clean_thumbnails)
    btn_layout_2.addWidget(self.btn_thumbnails)

    layout.addLayout(btn_layout_2)

    # Consola de salida en tiempo real
    self.console = QTextEdit()
    self.console.setReadOnly(True)
    self.console.setStyleSheet(
        "background-color: #1e1e1e; color: #00ff00; font-family: monospace;"
        " font-size: 10pt; border-radius: 6px; padding: 10px; border: 1px solid #282828;"
    )
    layout.addWidget(self.console)

    # Botón de salir / cerrar
    self.btn_close = QPushButton("Cerrar")
    self.btn_close.setFixedHeight(35)
    self.btn_close.setStyleSheet("""
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
    self.btn_close.clicked.connect(self.close)
    layout.addWidget(self.btn_close)

  def get_button_style(self, bg_color, hover_color):
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

  def run_shell_script(self, script_str, as_root=True):
    if self.process.state() == QProcess.ProcessState.Running:
      self.console.append(
          "\n⚠️ Ya hay un proceso ejecutándose. Por favor espera...\n"
      )
      return

    self.console.clear()
    self.console.append(f"$ {script_str}\n")

    if as_root:
      self.process.start("pkexec", ["bash", "-c", script_str])
    else:
      self.process.start("bash", ["-c", script_str])

  def clean_cache(self):
    self.run_shell_script("pacman -Sc --noconfirm", as_root=True)

  def clean_orphans(self):
    script = (
        "if pacman -Qdtq > /dev/null 2>&1; then "
        "pacman -Rns --noconfirm $(pacman -Qdtq); "
        "else echo 'No hay paquetes huérfanos para eliminar.'; fi"
    )
    self.run_shell_script(script, as_root=True)

  def clean_user_cache(self):
    # Limpia archivos temporales en ~/.cache sin borrar directorios estructurales críticos
    script = (
        "find ~/.cache/ -mindepth 1 -maxdepth 1 ! -name 'thumbnails' -exec rm -rf {} + 2>/dev/null; "
        "echo '¡Caché de usuario limpiada correctamente!'"
    )
    self.run_shell_script(script, as_root=False)

  def clean_thumbnails(self):
    # Limpia las miniaturas almacenadas de forma segura
    script = (
        "rm -rf ~/.cache/thumbnails/* 2>/dev/null; "
        "echo '¡Carpeta de miniaturas vaciada con éxito!'"
    )
    self.run_shell_script(script, as_root=False)

  def handle_stdout(self):
    data = self.process.readAllStandardOutput().data().decode("utf-8")
    self.console.insertPlainText(data)
    self.console.ensureCursorVisible()

  def handle_stderr(self):
    data = self.process.readAllStandardError().data().decode("utf-8")
    self.console.insertPlainText(data)
    self.console.ensureCursorVisible()

  def process_finished(self, exit_code, exit_status):
    self.console.append(
        f"\n--- Proceso finalizado con código {exit_code} ---\n"
    )


if __name__ == "__main__":
  app = QApplication(sys.argv)
  window = SinergiaCleanerApp()
  window.show()
  sys.exit(app.exec())
