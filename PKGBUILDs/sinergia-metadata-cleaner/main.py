#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon, QGuiApplication
from PIL import Image

class DropArea(QFrame):
    """Un contenedor con estilo visual que detecta cuando se arrastran archivos encima."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.main_window = parent
        self.initUI()

    def initUI(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #6c757d;
                border-radius: 8px;
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout()
        self.label = QLabel('Arrastrá tu foto acá\no usá el botón de abajo', self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.label)
        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # Resaltar el rectángulo cuando la foto entra a la zona
            self.setStyleSheet("""
                QFrame {
                    border: 2px dashed #3daee9;
                    border-radius: 8px;
                    background-color: #31363b;
                    color: #ffffff;
                }
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        # Volver al estilo original cuando el cursor sale del rectángulo
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #6c757d;
                border-radius: 8px;
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)

    def dropEvent(self, event):
        # Restaurar estilo al soltar
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #6c757d;
                border-radius: 8px;
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            self.main_window.process_image(file_path)


class MetadataCleanerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.last_output_path = None

    def initUI(self):
        self.setWindowTitle('Sinergia Metadata Cleaner')
        self.setFixedSize(420, 310)

        layout = QVBoxLayout()

        # Área interactiva de arrastre y soltar con rectángulo visual
        self.drop_area = DropArea(self)
        layout.addWidget(self.drop_area)

        self.btn_select = QPushButton('Seleccionar Imagen', self)
        self.btn_select.clicked.connect(self.select_file_dialog)
        layout.addWidget(self.btn_select)

        # Botón con el texto solicitado (inicialmente deshabilitado)
        self.btn_open_folder = QPushButton('📂 Abrir carpeta de destino', self)
        self.btn_open_folder.clicked.connect(self.open_and_select_file)
        self.btn_open_folder.setEnabled(False)
        layout.addWidget(self.btn_open_folder)

        self.setLayout(layout)

    def select_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "", "Imágenes (*.jpg *.jpeg *.png *.webp *.bmp)"
        )

        if file_path:
            self.process_image(file_path)

    def process_image(self, file_path):
        valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        path = Path(file_path)

        if path.suffix.lower() not in valid_extensions:
            QMessageBox.warning(self, "Formato no válido", "Por favor, seleccioná una imagen compatible.")
            return

        try:
            self.last_output_path = path.parent / f"{path.stem}-sin-data.png"

            # Limpiar metadatos mediante transferencia directa de bytes
            with Image.open(path) as img:
                clean_img = Image.frombytes(img.mode, img.size, img.tobytes())
                clean_img.save(self.last_output_path, 'PNG')

                self.btn_open_folder.setEnabled(True)

                QMessageBox.information(
                    self, "¡Éxito!",
                    f"Imagen limpia guardada en:\n{self.last_output_path.name}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Ocurrió un error al procesar la imagen:\n{str(e)}")

    def open_and_select_file(self):
        if self.last_output_path and self.last_output_path.exists():
            file_uri = QUrl.fromLocalFile(str(self.last_output_path)).toString()
            try:
                subprocess.run([
                    'dbus-send', '--session', '--dest=org.freedesktop.FileManager1',
                    '--type=method_call', '/org/freedesktop/FileManager1',
                    'org.freedesktop.FileManager1.ShowItems',
                    f'array:string:{file_uri}', 'string:""'
                ], check=True)
            except Exception:
                folder_url = QUrl.fromLocalFile(str(self.last_output_path.parent))
                QDesktopServices.openUrl(folder_url)

if __name__ == '__main__':
    # Clave para Wayland: asocia el app_id de la ventana con el archivo .desktop del sistema
    QGuiApplication.setDesktopFileName("sinergia-metadata-cleaner")

    app = QApplication(sys.argv)

    # Configurar icono compatible con Wayland y X11 (busca el SVG local o recurre al tema del sistema)
    icon_path = Path(__file__).parent / "logo.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        app.setWindowIcon(QIcon.fromTheme("sinergia-metadata-cleaner"))

    ex = MetadataCleanerApp()
    ex.show()
    sys.exit(app.exec())
