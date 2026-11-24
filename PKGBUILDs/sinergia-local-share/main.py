#!/usr/bin/env python3
import sys
import os
import socket
import http.server
import socketserver
import urllib.parse
import subprocess
import re
from pathlib import Path
from io import BytesIO
import qrcode

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QFrame, QCheckBox, QLineEdit, QHBoxLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QIcon, QGuiApplication

class SafeHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if any(x in self.path for x in ["favicon.ico", "logo.svg"]):
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def translate_path(self, path):
        url_path = urllib.parse.urlparse(path)[2]
        url_path = urllib.parse.unquote(url_path, encoding='utf-8', errors='replace')
        parts = [p for p in url_path.split('/') if p and p != '..']
        translated = os.getcwd()
        for part in parts:
            translated = os.path.join(translated, part)
        return translated

    def copyfile(self, source, outputfile):
        # Capturar y silenciar si el cliente corta o reinicia la conexión abruptamente (cierre de pestaña / cancelación)
        try:
            super().copyfile(source, outputfile)
        except (ConnectionResetError, BrokenPipeError):
            pass

    def log_message(self, format, *args):
        try:
            msg = format % args if args else format
            if any(x in str(msg) for x in ["favicon.ico", "logo.svg"]):
                return
        except Exception:
            pass
        super().log_message(format, *args)


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


class ServerWorker(QThread):
    error_occurred = pyqtSignal(str)
    port_ready = pyqtSignal(int)

    def __init__(self, file_path, port=8080):
        super().__init__()
        self.file_path = file_path
        self.port = port
        self.httpd = None

    def run(self):
        os.chdir(self.file_path.parent)
        Handler = SafeHandler
        bound_port = None
        for candidate in range(self.port, self.port + 15):
            try:
                self.httpd = ReusableThreadingTCPServer(("0.0.0.0", candidate), Handler)
                bound_port = candidate
                break
            except OSError:
                continue

        if not self.httpd or bound_port is None:
            self.error_occurred.emit(f"No se pudo abrir ningún puerto entre {self.port} y {self.port + 14}.")
            return

        self.port = bound_port
        self.port_ready.emit(bound_port)
        try:
            with self.httpd:
                self.httpd.serve_forever()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        self.quit()
        self.wait()


class CloudflareWorker(QThread):
    url_ready = pyqtSignal(str)

    def __init__(self, port=8080):
        super().__init__()
        self.port = port
        self.process = None

    def run(self):
        cmd = ['cloudflared', 'tunnel', '--url', f'http://localhost:{self.port}']
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            for line in self.process.stderr:
                if "trycloudflare.com" in line:
                    match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
                    if match:
                        public_url = match.group(0)
                        self.url_ready.emit(public_url)
                        break
        except Exception:
            pass

    def stop(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
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
        self.cloudflare_thread = None
        self.current_url = ""
        self.port = 8080
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Sinergia Local Share')
        self.setFixedSize(400, 600)

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
            QCheckBox {
                color: #f67400;
                font-size: 13px;
                font-weight: bold;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)

        layout = QVBoxLayout()

        self.drop_area = DropArea(self)
        layout.addWidget(self.drop_area)

        self.file_label = QLabel('Ningún archivo seleccionado', self)
        self.file_label.setStyleSheet("color: #f67400; font-weight: bold; font-size: 11px;")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.file_label)

        self.chk_remote = QCheckBox("🌐 Modo Remoto global (vía Cloudflare)", self)
        layout.addWidget(self.chk_remote)

        self.qr_label = QLabel(self)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setStyleSheet("background-color: #1e1e1e; border-radius: 6px; padding: 5px;")
        self.qr_label.setFixedSize(380, 160)
        self.show_default_qr_message("Esperando archivo...")
        layout.addWidget(self.qr_label)

        # Fila para el enlace y botón de copia rápida
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit(self)
        self.url_input.setReadOnly(True)
        self.url_input.setPlaceholderText("Enlace listo para copiar...")
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #3daee9;
                border: 1px solid #3daee9;
                border-radius: 4px;
                padding: 6px;
                font-family: monospace;
                font-size: 11px;
            }
        """)

        self.btn_copy = QPushButton("📋 Copiar", self)
        self.btn_copy.setFixedWidth(85)
        self.btn_copy.clicked.connect(self.copy_url_to_clipboard)
        self.btn_copy.setEnabled(False)

        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.btn_copy)
        layout.addLayout(url_layout)

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
        if self.cloudflare_thread:
            self.cloudflare_thread.stop()

        self.input_path = Path(file_path)
        self.file_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 11px;")
        self.file_label.setText(f"✓ {self.input_path.name}")

        encoded_filename = urllib.parse.quote(self.input_path.name)

        # Iniciar servidor HTTP en segundo plano con SafeHandler
        self.server_thread = ServerWorker(self.input_path, self.port)
        self.server_thread.error_occurred.connect(self.on_server_error)

        if self.chk_remote.isChecked():
            self.server_thread.port_ready.connect(self.start_cloudflare_tunnel)
            self.server_thread.start()
        else:
            self.server_thread.port_ready.connect(
                lambda actual_port, fname=encoded_filename: self.on_local_server_ready(actual_port, fname)
            )
            self.server_thread.start()

        self.btn_stop.setEnabled(True)
        self.drop_area.setEnabled(False)
        self.chk_remote.setEnabled(False)


    def on_local_server_ready(self, actual_port, encoded_filename):
        self.port = actual_port
        local_ip = self.get_local_ip()
        file_url = f"http://{local_ip}:{self.port}/{encoded_filename}"
        self.generate_qr(file_url)

    def start_cloudflare_tunnel(self, actual_port):
        self.port = actual_port
        encoded_filename = urllib.parse.quote(self.input_path.name) if self.input_path else ""
        self.show_default_qr_message("Conectando con Cloudflare...")
        self.cloudflare_thread = CloudflareWorker(self.port)
        self.cloudflare_thread.url_ready.connect(lambda base_url: self.on_cloudflare_ready(base_url, encoded_filename))
        self.cloudflare_thread.start()

    def on_server_error(self, message):
        self.show_default_qr_message(f"Error de red: {message}")
        self.btn_stop.setEnabled(True)
        self.drop_area.setEnabled(True)
        self.chk_remote.setEnabled(True)

    def on_cloudflare_ready(self, base_url, encoded_filename):
        public_url = f"{base_url}/{encoded_filename}"
        self.generate_qr(public_url)

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
        self.current_url = url
        self.url_input.setText(url)
        self.btn_copy.setEnabled(True)
        self.btn_copy.setText("📋 Copiar")

        qr = qrcode.QRCode(box_size=3, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qimage = QImage.fromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimage)

        self.qr_label.setPixmap(pixmap.scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def copy_url_to_clipboard(self):
        if self.current_url:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.current_url)
            self.btn_copy.setText("¡Copiado!")

    def reset_state(self):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread = None
        if self.cloudflare_thread:
            self.cloudflare_thread.stop()
            self.cloudflare_thread = None

        self.input_path = None
        self.current_url = ""
        self.url_input.clear()
        self.btn_copy.setEnabled(False)
        self.btn_copy.setText("📋 Copiar")

        self.file_label.setStyleSheet("color: #f67400; font-weight: bold; font-size: 11px;")
        self.file_label.setText("Ningún archivo seleccionado")
        self.show_default_qr_message("Servidor detenido. Seleccioná otro archivo.")
        self.btn_stop.setEnabled(False)
        self.drop_area.setEnabled(True)
        self.chk_remote.setEnabled(True)

    def closeEvent(self, event):
        if self.server_thread:
            self.server_thread.stop()
        if self.cloudflare_thread:
            self.cloudflare_thread.stop()
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
