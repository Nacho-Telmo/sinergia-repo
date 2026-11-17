#!/usr/bin/env python3
import sys
import subprocess
import shutil
import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QFrame, QComboBox, QProgressBar
)
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QIcon, QGuiApplication

class VideoWorker(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, input_path, output_path, profile):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.profile = profile

    def run(self):
        duration = self.get_video_duration(self.input_path)

        cmd = ['ffmpeg', '-y', '-i', str(self.input_path)]

        if self.profile == "Web / Telegram (Rápido y liviano)":
            cmd.extend(['-c:v', 'libx264', '-crf', '28', '-preset', 'fast', '-c:a', 'aac', '-b:a', '128k'])
        elif self.profile == "YouTube / Alta Calidad":
            cmd.extend(['-c:v', 'libx264', '-crf', '22', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k'])
        else:  # Móvil / Compacto (Vertical 9:16 con recorte automático central)
            cmd.extend([
                '-c:v', 'libx264', '-crf', '32', '-preset', 'veryfast',
                '-vf', 'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280',
                '-c:a', 'aac', '-b:a', '96k'
            ])

        cmd.append(str(self.output_path))

        try:
            process = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8', errors='ignore'
            )

            time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})")

            for line in process.stderr:
                match = time_pattern.search(line)
                if match and duration > 0:
                    h, m, s, ms = map(int, match.groups())
                    current_seconds = h * 3600 + m * 60 + s + ms / 100.0
                    progress = int((current_seconds / duration) * 100)
                    self.progress_signal.emit(min(progress, 100))

            process.wait()
            if process.returncode == 0:
                self.progress_signal.emit(100)  # Forzar el 100% al terminar
                self.finished_signal.emit(True, "¡Video comprimido con éxito!")
            else:
                self.finished_signal.emit(False, "El proceso de compresión falló.")
        except Exception as e:
            self.finished_signal.emit(False, str(e))

    def get_video_duration(self, file_path):
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', str(file_path)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0


class DropArea(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.main_window = parent
        self.initUI()

    def initUI(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #3daee9;
                border-radius: 8px;
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)
        layout = QVBoxLayout()
        self.label = QLabel('📁 Arrastrá tu video acá\no hacé clic para seleccionarlo', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("border: none; background: transparent; color: #dfdfdf;")
        layout.addWidget(self.label)
        self.setLayout(layout)

    def mousePressEvent(self, event):
        # Al hacer clic en el área, abrir el diálogo de selección de archivos
        if event.button() == Qt.MouseButton.LeftButton:
            self.main_window.select_file_dialog()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    border: 2px dashed #f67400;
                    border-radius: 8px;
                    background-color: #31363b;
                    color: #ffffff;
                }
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #3daee9;
                border-radius: 8px;
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)

    def dropEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #3daee9;
                border-radius: 8px;
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            self.main_window.set_input_file(file_path)


class VideoCompressorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.input_path = None
        self.output_path = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Sinergia Video Compressor')
        self.setFixedSize(440, 340)

        self.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 5px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:disabled {
                background-color: #454545;
                color: #888888;
            }
            QComboBox {
                background-color: #31363b;
                color: white;
                border: 1px solid #3daee9;
                border-radius: 4px;
                padding: 4px;
            }
            QProgressBar {
                border: 1px solid #454545;
                border-radius: 4px;
                text-align: center;
                color: white;
                background-color: #2b2b2b;
            }
            QProgressBar::chunk {
                background-color: #2ecc71;
                border-radius: 3px;
            }
        """)

        layout = QVBoxLayout()

        self.drop_area = DropArea(self)
        layout.addWidget(self.drop_area)

        self.file_label = QLabel('Ningún archivo seleccionado', self)
        self.file_label.setStyleSheet("color: #f67400; font-weight: bold; font-size: 12px;")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.file_label)

        profile_layout = QHBoxLayout()
        profile_label = QLabel('Perfil:', self)
        profile_label.setStyleSheet("color: white; font-weight: bold;")
        self.combo_profile = QComboBox(self)
        self.combo_profile.addItems([
            "Web / Telegram (Rápido y liviano)",
            "YouTube / Alta Calidad",
            "Móvil / Compacto (Vertical 9:16)"
        ])
        profile_layout.addWidget(profile_label)
        profile_layout.addWidget(self.combo_profile)
        layout.addLayout(profile_layout)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.btn_compress = QPushButton('⚙️ Comprimir Video', self)
        self.btn_compress.clicked.connect(self.start_compression)
        self.btn_compress.setEnabled(False)
        layout.addWidget(self.btn_compress)

        self.btn_open_folder = QPushButton('📂 Abrir carpeta de destino', self)
        self.btn_open_folder.clicked.connect(self.open_and_select_file)
        self.btn_open_folder.setEnabled(False)
        layout.addWidget(self.btn_open_folder)

        self.setLayout(layout)

    def select_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar video", "", "Videos (*.mp4 *.mkv *.mov *.avi *.webm)"
        )
        if file_path:
            self.set_input_file(file_path)

    def set_input_file(self, file_path):
        self.input_path = Path(file_path)
        self.file_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 12px;")
        self.file_label.setText(f"✓ {self.input_path.name}")
        self.btn_compress.setEnabled(True)

    def start_compression(self):
        if not self.input_path or not self.input_path.exists():
            return

        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
            QMessageBox.critical(self, "Error", "No se encontró ffmpeg o ffprobe en el sistema.\nInstalalo con: sudo pacman -S ffmpeg")
            return

        self.output_path = self.input_path.parent / f"{self.input_path.stem}-comprimido.mp4"
        profile = self.combo_profile.currentText()

        self.drop_area.setEnabled(False)
        self.btn_compress.setEnabled(False)
        self.combo_profile.setEnabled(False)
        self.progress_bar.setValue(0)

        self.worker = VideoWorker(self.input_path, self.output_path, profile)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.compression_finished)
        self.worker.start()

    def compression_finished(self, success, message):
        self.drop_area.setEnabled(True)
        self.combo_profile.setEnabled(True)

        if success:
            self.btn_compress.setEnabled(True)
            self.btn_open_folder.setEnabled(True)
            QMessageBox.information(self, "¡Éxito!", f"{message}\nGuardado en:\n{self.output_path.name}")
        else:
            self.btn_compress.setEnabled(True)
            QMessageBox.critical(self, "Error", message)

    def open_and_select_file(self):
        if self.output_path and self.output_path.exists():
            file_uri = QUrl.fromLocalFile(str(self.output_path)).toString()
            try:
                subprocess.run([
                    'dbus-send', '--session', '--dest=org.freedesktop.FileManager1',
                    '--type=method_call', '/org/freedesktop/FileManager1',
                    'org.freedesktop.FileManager1.ShowItems',
                    f'array:string:{file_uri}', 'string:""'
                ], check=True)
            except Exception:
                folder_url = QUrl.fromLocalFile(str(self.output_path.parent))
                QDesktopServices.openUrl(folder_url)

if __name__ == 'main' or __name__ == '__main__':
    QGuiApplication.setDesktopFileName("sinergia-video-compressor")
    app = QApplication(sys.argv)

    icon_path = Path(__file__).parent / "logo.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        app.setWindowIcon(QIcon.fromTheme("sinergia-video-compressor"))

    ex = VideoCompressorApp()
    ex.show()
    sys.exit(app.exec())
