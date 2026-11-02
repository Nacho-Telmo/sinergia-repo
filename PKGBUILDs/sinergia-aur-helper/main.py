import sys
import subprocess
import shutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QTextEdit, QSplitter, QMessageBox, QTabWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import urllib.request
import urllib.parse
import json

class AURSearchWorker(QThread):
    """Hilo secundario para buscar paquetes en la API de AUR y verificar estado en pacman"""
    results_ready = pyqtSignal(list)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        if not self.query.strip():
            self.results_ready.emit([])
            return

        try:
            url = f"https://aur.archlinux.org/rpc/?v=5&type=search&arg={urllib.parse.quote(self.query)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'SinergiaAURHelper/1.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if data.get('type') == 'search':
                    results = data.get('results', [])
                    installed_packages = self.get_installed_packages()

                    for pkg in results:
                        pkg_name = pkg.get('Name', '')
                        pkg['is_installed'] = pkg_name in installed_packages

                    self.results_ready.emit(results)
                else:
                    self.results_ready.emit([])
        except Exception as e:
            print(f"Error en la búsqueda: {e}")
            self.results_ready.emit([])

    def get_installed_packages(self):
        try:
            output = subprocess.check_output(["pacman", "-Qq"], text=True)
            return set(output.splitlines())
        except Exception:
            return set()

class AURPKGBUILDWorker(QThread):
    """Hilo secundario para descargar el PKGBUILD de un paquete de AUR"""
    pkgbuild_ready = pyqtSignal(str)

    def __init__(self, pkg_name):
        super().__init__()
        self.pkg_name = pkg_name

    def run(self):
        if not self.pkg_name:
            self.pkgbuild_ready.emit("No hay paquete seleccionado.")
            return

        try:
            url = f"https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h={urllib.parse.quote(self.pkg_name)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'SinergiaAURHelper/1.0'})
            with urllib.request.urlopen(req) as response:
                content = response.read().decode('utf-8', errors='ignore')
                self.pkgbuild_ready.emit(content)
        except Exception as e:
            self.pkgbuild_ready.emit(f"No se pudo cargar el PKGBUILD para {self.pkg_name}.\nError: {e}")

class SinergiaAURWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sinergia AUR Helper")
        self.setMinimumSize(1050, 750)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Barra de búsqueda y botón de recarga superior
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar paquete en AUR (ej: google-chrome, spotify)...")
        self.search_input.returnPressed.connect(self.perform_search)

        self.search_btn = QPushButton("Buscar")
        self.search_btn.clicked.connect(self.perform_search)

        self.reload_btn = QPushButton("🔄 Actualizar Estados")
        self.reload_btn.setToolTip("Vuelve a consultar el estado de instalación de los paquetes mostrados")
        self.reload_btn.clicked.connect(self.refresh_current_view)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.reload_btn)
        main_layout.addLayout(search_layout)

        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Tabla de resultados
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Estado", "Repo", "Paquete", "Versión", "Votos", "Popularidad", "Descripción"])
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.on_package_selected)
        splitter.addWidget(self.table)

        # Panel inferior contenedor
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Pestañas inferiores (Detalles y PKGBUILD)
        self.tabs = QTabWidget()

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlaceholderText("Selecciona un paquete de la lista para ver sus detalles...")
        self.tabs.addTab(self.details_text, "Detalles del Paquete")

        self.pkgbuild_text = QTextEdit()
        self.pkgbuild_text.setReadOnly(True)
        self.pkgbuild_text.setFont(QFont("Monospace", 10))
        self.pkgbuild_text.setPlaceholderText("El PKGBUILD se cargará aquí para su inspección...")
        self.tabs.addTab(self.pkgbuild_text, "Inspeccionar PKGBUILD")

        bottom_layout.addWidget(self.tabs)

        # Contenedor de botones de acción
        actions_layout = QHBoxLayout()

        self.install_btn = QPushButton("Instalar Paquete")
        self.install_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 10px; font-size: 11pt;")
        self.install_btn.setEnabled(False)
        self.install_btn.clicked.connect(self.install_selected_package)
        actions_layout.addWidget(self.install_btn)

        self.uninstall_btn = QPushButton("Desinstalar Paquete")
        self.uninstall_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 10px; font-size: 11pt;")
        self.uninstall_btn.setEnabled(False)
        self.uninstall_btn.clicked.connect(self.uninstall_selected_package)
        actions_layout.addWidget(self.uninstall_btn)

        bottom_layout.addLayout(actions_layout)

        splitter.addWidget(bottom_widget)
        splitter.setSizes([400, 300])
        main_layout.addWidget(splitter)

        self.current_results = []
        self.selected_package_name = None
        self.is_package_installed = False
        self.search_worker = None
        self.pkgbuild_worker = None

    def perform_search(self):
        query = self.search_input.text()
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Buscando...")

        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.quit()
            self.search_worker.wait()

        self.search_worker = AURSearchWorker(query)
        self.search_worker.results_ready.connect(self.handle_results)
        self.search_worker.start()

    def refresh_current_view(self):
        if self.search_input.text().strip():
            self.perform_search()

    def handle_results(self, results):
        self.current_results = results
        self.table.setRowCount(len(results))

        for row, pkg in enumerate(results):
            is_installed = pkg.get('is_installed', False)
            status_text = "Instalado" if is_installed else "No instalado"

            status_item = QTableWidgetItem(status_text)
            if is_installed:
                status_item.setForeground(QColor("#22c55e"))

            self.table.setItem(row, 0, status_item)
            self.table.setItem(row, 1, QTableWidgetItem("aur"))
            self.table.setItem(row, 2, QTableWidgetItem(pkg.get('Name', '')))
            self.table.setItem(row, 3, QTableWidgetItem(pkg.get('Version', '')))
            self.table.setItem(row, 4, QTableWidgetItem(str(pkg.get('NumVotes', 0))))
            self.table.setItem(row, 5, QTableWidgetItem(f"{pkg.get('Popularity', 0.0):.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(pkg.get('Description', '')))

        self.search_btn.setEnabled(True)
        self.search_btn.setText("Buscar")
        self.install_btn.setEnabled(False)
        self.uninstall_btn.setEnabled(False)
        self.selected_package_name = None
        self.details_text.clear()
        self.pkgbuild_text.clear()

    def on_package_selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.current_results):
            return

        pkg = self.current_results[row]
        self.selected_package_name = pkg.get('Name')
        self.is_package_installed = pkg.get('is_installed', False)

        status_html = "<span style='color: #22c55e; font-weight: bold;'>Instalado</span>" if self.is_package_installed else "<span style='color: #94a3b8;'>No instalado</span>"

        info = f"<b>Estado en el sistema:</b> {status_html}<br>" \
               f"<b>Repositorio:</b> AUR<br>" \
               f"<b>Paquete:</b> {self.selected_package_name}<br>" \
               f"<b>Versión:</b> {pkg.get('Version')}<br>" \
               f"<b>Mantenedor:</b> {pkg.get('Maintainer', 'Ninguno / Huérfano')}<br>" \
               f"<b>Votos:</b> {pkg.get('NumVotes')} | <b>Popularidad:</b> {pkg.get('Popularity', 0.0):.2f}<br>" \
               f"<b>URL:</b> <a href='{pkg.get('URL')}'>{pkg.get('URL')}</a><br>" \
               f"<b>Descripción:</b> {pkg.get('Description')}"
        self.details_text.setHtml(info)

        self.install_btn.setEnabled(True)
        self.uninstall_btn.setEnabled(self.is_package_installed)

        if self.pkgbuild_worker and self.pkgbuild_worker.isRunning():
            self.pkgbuild_worker.quit()
            self.pkgbuild_worker.wait()

        self.pkgbuild_text.setText("Descargando PKGBUILD...")
        self.pkgbuild_worker = AURPKGBUILDWorker(self.selected_package_name)
        self.pkgbuild_worker.pkgbuild_ready.connect(self.handle_pkgbuild)
        self.pkgbuild_worker.start()

    def handle_pkgbuild(self, content):
        self.pkgbuild_text.setText(content)

    def run_in_terminal(self, command_args):
        terminals = ["konsole", "xfce4-terminal", "alacritty", "kitty", "gnome-terminal", "xterm"]
        selected_term = None
        for term in terminals:
            if shutil.which(term):
                selected_term = term
                break

        try:
            if selected_term == "konsole":
                subprocess.Popen(["konsole", "-e"] + command_args)
            elif selected_term == "xfce4-terminal":
                subprocess.Popen(["xfce4-terminal", "-e"] + command_args)
            elif selected_term == "alacritty":
                subprocess.Popen(["alacritty", "-e"] + command_args)
            elif selected_term == "kitty":
                subprocess.Popen(["kitty"] + command_args)
            elif selected_term == "gnome-terminal":
                subprocess.Popen(["gnome-terminal", "--"] + command_args)
            elif selected_term == "xterm":
                subprocess.Popen(["xterm", "-e"] + command_args)
            else:
                subprocess.Popen(command_args)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la terminal: {e}")

    def install_selected_package(self):
        if not self.selected_package_name:
            return

        helper = None
        if shutil.which("yay"):
            helper = "yay"
        elif shutil.which("paru"):
            helper = "paru"

        if not helper:
            QMessageBox.warning(
                self,
                "Falta asistente de AUR",
                "No se encontró 'yay' ni 'paru' en el sistema. Necesitas tener uno instalado para compilar e instalar paquetes."
            )
            return

        cmd = [helper, "-S", "--noconfirm", self.selected_package_name]
        self.run_in_terminal(cmd)

    def uninstall_selected_package(self):
        if not self.selected_package_name:
            return

        cmd = ["sudo", "pacman", "-Rns", "--noconfirm", self.selected_package_name]
        self.run_in_terminal(cmd)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SinergiaAURWindow()
    window.show()
    sys.exit(app.exec())
