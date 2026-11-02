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
    self.setFixedSize(600, 450)

    # Widget central y layout principal
    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(15)

    # Título
    title_label = QLabel("🧹 Sinergia System Cleaner")
    title_label.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title_label)

    # Botones de acción
    btn_layout = QHBoxLayout()

    self.btn_cache = QPushButton("Limpiar Caché (Pacman)")
    self.btn_cache.setFixedHeight(40)
    self.btn_cache.clicked.connect(self.clean_cache)
    btn_layout.addWidget(self.btn_cache)

    self.btn_orphans = QPushButton("Eliminar Huérfanos (-Qdtq)")
    self.btn_orphans.setFixedHeight(40)
    self.btn_orphans.clicked.connect(self.clean_orphans)
    btn_layout.addWidget(self.btn_orphans)

    layout.addLayout(btn_layout)

    # Consola de salida en tiempo real
    self.console = QTextEdit()
    self.console.setReadOnly(True)
    self.console.setStyleSheet(
        "background-color: #1e1e1e; color: #00ff00; font-family: monospace;"
        " font-size: 11pt; border-radius: 5px; padding: 10px;"
    )
    layout.addWidget(self.console)

    # Botón de salir / cerrar
    self.btn_close = QPushButton("Cerrar")
    self.btn_close.setFixedHeight(35)
    self.btn_close.clicked.connect(self.close)
    layout.addWidget(self.btn_close)

  def run_shell_script(self, script_str):
    if self.process.state() == QProcess.ProcessState.Running:
      self.console.append(
          "\n⚠️ Ya hay un proceso ejecutándose. Por favor espera...\n"
      )
      return

    self.console.clear()
    self.console.append(f"$ {script_str}\n")
    self.process.start("pkexec", ["bash", "-c", script_str])

  def clean_cache(self):
    self.run_shell_script("pacman -Sc --noconfirm")

  def clean_orphans(self):
    script = (
        "if pacman -Qdtq > /dev/null 2>&1; then "
        "pacman -Rns --noconfirm $(pacman -Qdtq); "
        "else echo 'No hay paquetes huérfanos para eliminar.'; fi"
    )
    self.run_shell_script(script)

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
