#!/usr/bin/env python3
import re
import sys
from PyQt6.QtCore import QDir, QProcess, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class SinergiaYTDLPWindow(QWidget):

  def __init__(self):
    super().__init__()
    self.initUI()
    self.process = None

  def initUI(self):
    self.setWindowTitle("Sinergia YT-DLP Manager")
    self.resize(750, 630)

    # Layout principal
    main_layout = QVBoxLayout()

    # 1. URL de entrada
    url_layout = QHBoxLayout()
    url_label = QLabel("URL del video/playlist:")
    self.url_input = QLineEdit()
    self.url_input.setPlaceholderText(
        "https://www.youtube.com/watch?v=..."
    )
    url_layout.addWidget(url_label)
    url_layout.addWidget(self.url_input)
    main_layout.addLayout(url_layout)

    # 2. Selector de formato y Directorio de salida
    options_layout = QHBoxLayout()

    format_label = QLabel("Formato:")
    self.format_combo = QComboBox()
    self.format_combo.addItems([
        "Video MP4 (Mejor calidad)",
        "Solo Audio MP3",
        "Solo Audio FLAC (Alta calidad)",
    ])

    dir_label = QLabel("Guardar en:")
    self.dir_input = QLineEdit()
    self.dir_input.setText(QDir.homePath() + "/Descargas")

    self.browse_btn = QPushButton("Explorar...")
    self.browse_btn.clicked.connect(self.select_output_dir)

    self.open_dir_btn = QPushButton("📂 Abrir")
    self.open_dir_btn.setToolTip("Abrir carpeta de descargas")
    self.open_dir_btn.clicked.connect(self.open_output_dir)

    options_layout.addWidget(format_label)
    options_layout.addWidget(self.format_combo)
    options_layout.addWidget(dir_label)
    options_layout.addWidget(self.dir_input)
    options_layout.addWidget(self.browse_btn)
    options_layout.addWidget(self.open_dir_btn)
    main_layout.addLayout(options_layout)

    # 3. Opciones adicionales (Miniaturas y Organización)
    options_extra_layout = QVBoxLayout()

    thumb_layout = QHBoxLayout()
    self.chk_thumb = QCheckBox("Descargar miniatura")
    self.chk_embed_thumb = QCheckBox(
        "Incrustar miniatura en el archivo (Carátula)"
    )
    self.chk_embed_thumb.setChecked(True)
    thumb_layout.addWidget(self.chk_thumb)
    thumb_layout.addWidget(self.chk_embed_thumb)
    thumb_layout.addStretch()

    org_layout = QHBoxLayout()
    self.chk_organize = QCheckBox("Organizar en carpetas (Artista / Álbum)")
    self.chk_organize.setChecked(True)
    org_layout.addWidget(self.chk_organize)
    org_layout.addStretch()

    options_extra_layout.addLayout(thumb_layout)
    options_extra_layout.addLayout(org_layout)
    main_layout.addLayout(options_extra_layout)

    # 4. Barra de progreso visual
    self.progress_bar = QProgressBar()
    self.progress_bar.setValue(0)
    self.progress_bar.setStyleSheet(
        "QProgressBar { border: 2px solid #444; border-radius: 5px; text-align:"
        " center; background: #222; color: white; }"
        "QProgressBar::chunk { background-color: #2e7d32; }"
    )
    main_layout.addWidget(self.progress_bar)

    # 5. Botón de descarga
    self.download_btn = QPushButton("Iniciar Descarga")
    self.download_btn.setStyleSheet(
        "background-color: #2e7d32; color: white; font-weight: bold; padding:"
        " 10px;"
    )
    self.download_btn.clicked.connect(self.start_download)
    main_layout.addWidget(self.download_btn)

    # 6. Consola de registro en tiempo real
    self.console = QTextEdit()
    self.console.setReadOnly(True)
    self.console.setStyleSheet(
        "background-color: #1e1e1e; color: #00ff00; font-family: monospace;"
    )
    main_layout.addWidget(self.console)

    self.setLayout(main_layout)

  def select_output_dir(self):
    dir_path = QFileDialog.getExistingDirectory(
        self, "Seleccionar carpeta de destino"
    )
    if dir_path:
      self.dir_input.setText(dir_path)

  def open_output_dir(self):
    dir_path = self.dir_input.text().strip()
    if dir_path:
      url = QUrl.fromLocalFile(dir_path)
      QDesktopServices.openUrl(url)
    else:
      self.console.append(
          "⚠️ La ruta de la carpeta de destino está vacía.\n"
      )

  def start_download(self):
    url = self.url_input.text().strip()
    output_dir = self.dir_input.text().strip()

    if not url:
      self.console.append("❌ Error: Ingresá una URL válida.\n")
      return

    if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
      self.console.append("⚠️ Ya hay una descarga en curso.\n")
      return

    self.progress_bar.setValue(0)

    # Construir comando yt-dlp base
    cmd_args = []
    selected_format = self.format_combo.currentIndex()

    if selected_format == 0:  # Video MP4
      cmd_args = [
          "-f",
          "bv*+ba/b",
          "--merge-output-format",
          "mp4",
          "-P",
          output_dir,
          url,
      ]
    elif selected_format == 1:  # Audio MP3
      cmd_args = [
          "-x",
          "--audio-format",
          "mp3",
          "--audio-quality",
          "0",
          "-P",
          output_dir,
          url,
      ]
    elif selected_format == 2:  # Audio FLAC
      cmd_args = [
          "-x",
          "--audio-format",
          "flac",
          "-P",
          output_dir,
          url,
      ]

    # Añadir opciones de organización por carpetas (Artista / Álbum)
    if self.chk_organize.isChecked():
      cmd_args.extend([
          "-o",
          "%(artist|uploader)s/%(album|playlist_title)s/%(title)s.%(ext)s",
      ])

    # Añadir opciones de miniaturas si están marcadas
    if self.chk_thumb.isChecked():
      cmd_args.append("--write-thumbnail")
    if self.chk_embed_thumb.isChecked():
      cmd_args.append("--embed-thumbnail")

    self.console.append(
        f"🚀 Ejecutando: yt-dlp {' '.join(cmd_args)}\n"
    )

    # Configurar QProcess
    self.process = QProcess(self)
    self.process.setProcessChannelMode(
        QProcess.ProcessChannelMode.MergedChannels
    )
    self.process.readyReadStandardOutput.connect(self.handle_stdout)
    self.process.finished.connect(self.download_finished)

    self.process.start("yt-dlp", cmd_args)
    self.download_btn.setEnabled(False)

  def handle_stdout(self):
    data = self.process.readAllStandardOutput()
    output = bytes(data).decode("utf-8", errors="ignore")
    self.console.insertPlainText(output)
    self.console.verticalScrollBar().setValue(
        self.console.verticalScrollBar().maximum()
    )

    # Buscar el porcentaje en el texto para mover la QProgressBar
    match = re.search(r"\[download\]\s+([\d\.]+)%", output)
    if match:
      try:
        percentage = float(match.group(1))
        self.progress_bar.setValue(int(percentage))
      except ValueError:
        pass

  def download_finished(self):
    self.progress_bar.setValue(100)
    self.console.append("\n✅ ¡Proceso de descarga finalizado!\n")
    self.download_btn.setEnabled(True)


if __name__ == "__main__":
  app = QApplication(sys.argv)
  window = SinergiaYTDLPWindow()
  window.show()
  sys.exit(app.exec())
