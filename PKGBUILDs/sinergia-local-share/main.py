#!/usr/bin/env python3
import sys
import os
import socket
import http.server
import socketserver
import urllib.parse
from pathlib import Path
from io import BytesIO
import qrcode

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QPixmap, QImage, QIcon, QGuiApplication

class ServerWorker(QThread):
    def __init__(self, file_path, port=8080):
        super().__init__()
        self.file_path = file_path
        self.port = port
        self.httpd = None

    def run(self):
        os.chdir(self.file_path.parent)
        Handler = http.server.SimpleHTTPRequestHandler
        try:
            with socketserver.TCPServer(("", self.port), Handler) as self.httpd:
                self.httpd.serve_forever()
        except Exception:
            pass

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        self.quit()
        self.wait()


class DropArea(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.main_window = parent
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.initUI()

    def initUI(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #3daee9;
                border-radius: 8px;
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)
        layout = QVBoxLayout()
        self.label = QLabel('📁 Arrastrá tu archivo acá\no hacé clic para seleccionarlo', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("border: none; background: transparent; color: #dfdfdf;")
        layout.addWidget(self.label)
        self.setLayout(layout)

    def mousePressEvent(self, event):
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


class LocalShareApp(QWidget):
    def __init__(self):
        super().__init__()
        self.input_path = None
        self.server_thread = None
        self.port = 8080
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Sinergia Local Share')
        self.setFixedSize(400, 480)

        self.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:disabled {
                background-color: #454545;
                color: #888888;
            }
        """)

        layout = QVBoxLayout()

        self.drop_area = DropArea(self)
        layout.addWidget(self.drop_area)

        self.file_label = QLabel('Ningún archivo seleccionado', self)
        self.file_label.setStyleSheet("color: #f67400; font-weight: bold; font-size: 11px;")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.file_label)

        # Etiqueta para mostrar el QR
        self.qr_label = QLabel(self)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setStyleSheet("background-color: #1e1e1e; border-radius: 6px; padding: 5px;")
        self.qr_label.setFixedSize(380, 200)
        self.show_default_qr_message("Esperando archivo...")
        layout.addWidget(self.qr_label)

        self.btn_stop = QPushButton('⏹️ Detener Servidor y Limpiar', self)
        self.btn_stop.clicked.connect(self.reset_state)
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)

        self.setLayout(layout)

    def show_default_qr_message(self, text):
        self.qr_label.clear()
        self.qr_label.setText(f"<span style='color: #888888; font-size: 12px;'>{text}</span>")

    def select_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo para compartir", "", "Todos los archivos (*)")
        if file_path:
            self.set_input_file(file_path)

    def set_input_file(self, file_path):
        if self.server_thread:
            self.server_thread.stop()

        self.input_path = Path(file_path)
        self.file_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 11px;")
        self.file_label.setText(f"✓ {self.input_path.name}")

        # Obtener IP local y codificar correctamente el nombre para la URL
        local_ip = self.get_local_ip()
        encoded_filename = urllib.parse.quote(self.input_path.name)
        file_url = f"http://{local_ip}:{self.port}/{encoded_filename}"

        # Generar QR
        self.generate_qr(file_url)

        # Iniciar servidor HTTP en segundo plano
        self.server_thread = ServerWorker(self.input_path, self.port)
        self.server_thread.start()

        self.btn_stop.setEnabled(True)
        self.drop_area.setEnabled(False)

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def generate_qr(self, url):
        qr = qrcode.QRCode(box_size=3, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qimage = QImage.fromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimage)

        self.qr_label.setPixmap(pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def reset_state(self):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread = None

        self.input_path = None
        self.file_label.setStyleSheet("color: #f67400; font-weight: bold; font-size: 11px;")
        self.file_label.setText("Ningún archivo seleccionado")
        self.show_default_qr_message("Servidor detenido. Seleccioná otro archivo.")
        self.btn_stop.setEnabled(False)
        self.drop_area.setEnabled(True)

    def closeEvent(self, event):
        if self.server_thread:
            self.server_thread.stop()
        event.accept()

if __name__ == '__main__':
    QGuiApplication.setDesktopFileName("sinergia-local-share")
    app = QApplication(sys.argv)

    icon_path = Path(__file__).parent / "logo.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        app.setWindowIcon(QIcon.fromTheme("sinergia-local-share"))

    ex = LocalShareApp()
    ex.show()
    sys.exit(app.exec())
