#!/usr/bin/env python3
import sys
import os
import re
import json
import urllib.request
import urllib.parse
from pathlib import Path
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget,
    QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon

class SearchWorker(QThread):
    results_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, query):
        super().__init__()
        self.query = query.strip()

    def run(self):
        tracks = []
        try:
            # 1. Enlace directo de pista de Deezer
            track_match = re.search(r'deezer\.com/(?:\w+/)?track/(\d+)', self.query)
            if track_match:
                track_id = track_match.group(1)
                url = f"https://api.deezer.com/track/{track_id}"
                req = urllib.request.urlopen(url)
                data = json.loads(req.read().decode('utf-8'))
                if 'title' in data and 'artist' in data:
                    tracks.append({
                        'artist': data['artist']['name'],
                        'title': data['title'],
                        'album': data.get('album', {}).get('title', 'Singles'),
                        'track_position': data.get('track_position', 1)
                    })
                self.results_signal.emit(tracks)
                return

            # 2. Enlace directo de álbum de Deezer
            album_match = re.search(r'deezer\.com/(?:\w+/)?album/(\d+)', self.query)
            if album_match:
                album_id = album_match.group(1)
                url = f"https://api.deezer.com/album/{album_id}"
                req_album_info = urllib.request.urlopen(url)
                album_info = json.loads(req_album_info.read().decode('utf-8'))
                album_title = album_info.get('title', 'Álbum Desconocido')
                artist_name = album_info.get('artist', {}).get('name', 'Varios Artistas')

                tracks_url = f"https://api.deezer.com/album/{album_id}/tracks"
                req = urllib.request.urlopen(tracks_url)
                data = json.loads(req.read().decode('utf-8'))
                if 'data' in data:
                    for idx, item in enumerate(data['data'], start=1):
                        if 'title' in item:
                            tracks.append({
                                'artist': item.get('artist', {}).get('name', artist_name),
                                'title': item['title'],
                                'album': album_title,
                                'track_position': item.get('track_position', idx)
                            })
                # Ordenar estrictamente por número de pista original
                tracks = sorted(tracks, key=lambda x: x['track_position'])
                self.results_signal.emit(tracks)
                return

            # 3. Búsqueda inteligente de álbumes por texto
            encoded_query = urllib.parse.quote(self.query)
            album_search_url = f"https://api.deezer.com/search/album?q={encoded_query}&limit=1"

            try:
                req_album = urllib.request.urlopen(album_search_url)
                album_data = json.loads(req_album.read().decode('utf-8'))

                if 'data' in album_data and len(album_data['data']) > 0:
                    top_album = album_data['data'][0]
                    album_id = top_album['id']
                    album_title = top_album['title']
                    artist_name = top_album.get('artist', {}).get('name', 'Desconocido')

                    tracks_url = f"https://api.deezer.com/album/{album_id}/tracks"
                    req_tracks = urllib.request.urlopen(tracks_url)
                    tracks_data = json.loads(req_tracks.read().decode('utf-8'))

                    if 'data' in tracks_data and len(tracks_data['data']) > 0:
                        for idx, item in enumerate(tracks_data['data'], start=1):
                            tracks.append({
                                'artist': item.get('artist', {}).get('name', artist_name),
                                'title': item['title'],
                                'album': album_title,
                                'track_position': item.get('track_position', idx)
                            })
                        # Ordenar estrictamente por número de pista original
                        tracks = sorted(tracks, key=lambda x: x['track_position'])
                        self.results_signal.emit(tracks)
                        return
            except Exception:
                pass

            # 4. Fallback: Búsqueda general de pistas
            search_url = f"https://api.deezer.com/search?q={encoded_query}&limit=15"
            req = urllib.request.urlopen(search_url)
            data = json.loads(req.read().decode('utf-8'))

            if 'data' in data:
                for idx, item in enumerate(data['data'], start=1):
                    if 'title' in item and 'artist' in item:
                        tracks.append({
                            'artist': item['artist']['name'],
                            'title': item['title'],
                            'album': item.get('album', {}).get('title', 'Singles'),
                            'track_position': item.get('track_position', idx)
                        })

            self.results_signal.emit(tracks)

        except Exception as e:
            self.error_signal.emit(str(e))

class DownloadWorker(QThread):
    progress_signal = pyqtSignal(str)
    percent_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, tracks_to_download, base_output_dir):
        super().__init__()
        self.tracks_to_download = tracks_to_download
        self.base_output_dir = base_output_dir

    def sanitize_name(self, name):
        return re.sub(r'[\\/*?:"<>|]', "", name).strip()

    def run(self):
        try:
            total_tracks = len(self.tracks_to_download)
            for index, track in enumerate(self.tracks_to_download, start=1):
                artist = self.sanitize_name(track['artist'])
                album = self.sanitize_name(track['album'])

                target_dir = self.base_output_dir / (artist if artist else "Desconocido") / (album if album else "Singles")
                target_dir.mkdir(parents=True, exist_ok=True)

                query = f"{track['artist']} - {track['title']}"
                self.progress_signal.emit(f"[{index}/{total_tracks}] Descargando: {query}")

                # Incluir número de pista con dos dígitos para ordenamiento cronológico en disco
                track_num_str = f"{index:02d}"
                filename_template = f"{track_num_str} - %(title)s.%(ext)s"

                cmd = [
                    "yt-dlp",
                    f"ytsearch1:{query}",
                    "-x", "--audio-format", "mp3",
                    "--embed-thumbnail", "--add-metadata",
                    "--output", str(target_dir / filename_template)
                ]

                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8"
                )

                for line in process.stdout:
                    line_str = line.strip()
                    match_pct = re.search(r'(\d{1,3}(?:\.\d+)?)%', line_str)
                    if match_pct:
                        try:
                            track_pct = float(match_pct.group(1))
                            base_progress = ((index - 1) / total_tracks) * 100
                            track_contribution = (track_pct / total_tracks)
                            total_progress = int(base_progress + track_contribution)
                            self.percent_signal.emit(min(total_progress, 100))
                        except ValueError:
                            pass

                process.wait()

                completed_progress = int((index / total_tracks) * 100)
                self.percent_signal.emit(completed_progress)

            self.percent_signal.emit(100)
            self.finished_signal.emit(True, "¡Descargas organizadas y finalizadas con éxito!")

        except Exception as e:
            self.finished_signal.emit(False, f"Excepción: {str(e)}")

class SinergiaLongPlayApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setProperty("class", "sinergia-longplay")

        icon_path_sys = Path("/usr/share/icons/hicolor/scalable/apps/sinergia-longplay.svg")
        if not icon_path_sys.exists():
            icon_path_sys = Path("/usr/share/icons/hicolor/128x128/apps/sinergia-longplay.png")
        if icon_path_sys.exists():
            self.setWindowIcon(QIcon(str(icon_path_sys)))

        self.setWindowTitle("Sinergia LongPlay")
        self.resize(750, 640)

        self.music_dir = Path.home() / "Music" / "SinergiaLongPlay"
        self.music_dir.mkdir(parents=True, exist_ok=True)

        self.current_results = []
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("🎵 Sinergia LongPlay (Deezer + yt-dlp)")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #c0caf5;")
        layout.addWidget(title)

        # Barra de búsqueda
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar álbum completo o artista...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #1f2335;
                color: #c0caf5;
                border: 1px solid #3b4261;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
        """)
        self.search_input.returnPressed.connect(self.start_search)
        search_layout.addWidget(self.search_input)

        self.btn_search = QPushButton("🔍 Buscar")
        self.btn_search.setStyleSheet("""
            QPushButton {
                background-color: #3d59a1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #4c6fc1; }
        """)
        self.btn_search.clicked.connect(self.start_search)
        search_layout.addWidget(self.btn_search)
        layout.addLayout(search_layout)

        # Cabecera de resultados y botón Seleccionar Todo
        results_header_layout = QHBoxLayout()
        results_label = QLabel("Resultados (Ordenados por pista original):")
        results_label.setStyleSheet("color: #7aa2f7; font-size: 12px; font-weight: bold;")
        results_header_layout.addWidget(results_label)

        results_header_layout.addStretch()

        self.btn_select_all = QPushButton("☑ Seleccionar todo")
        self.btn_select_all.setStyleSheet("""
            QPushButton {
                background-color: #292e42;
                color: #c0caf5;
                border: 1px solid #3b4261;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3b4261; }
        """)
        self.btn_select_all.clicked.connect(self.select_all_tracks)
        results_header_layout.addWidget(self.btn_select_all)

        layout.addLayout(results_header_layout)

        # Lista interactiva
        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #1f2335;
                border: 1px solid #292e42;
                border-radius: 8px;
                color: #c0caf5;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #16161e;
            }
            QListWidget::item:selected {
                background-color: #3d59a1;
                color: white;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.results_list)

        # Barra de Progreso Global
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1f2335;
                border: 1px solid #292e42;
                border-radius: 8px;
                text-align: center;
                color: #c0caf5;
                font-weight: bold;
                font-size: 12px;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #9ece6a;
                border-radius: 7px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Botón de descarga
        self.btn_download = QPushButton("📥 Descargar tu música")
        self.btn_download.setStyleSheet("""
            QPushButton {
                background-color: #9ece6a;
                color: #16161e;
                border: none;
                border-radius: 8px;
                padding: 11px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #b9f27c; }
            QPushButton:disabled { background-color: #292e42; color: #565f89; }
        """)
        self.btn_download.clicked.connect(self.start_download)
        layout.addWidget(self.btn_download)

        # Layout inferior: Ruta de destino + Botón Abrir Carpeta
        folder_layout = QHBoxLayout()
        self.status_label = QLabel(f"Destino: {self.music_dir}")
        self.status_label.setStyleSheet("color: #7aa2f7; font-size: 12px;")
        folder_layout.addWidget(self.status_label)

        folder_layout.addStretch()

        self.btn_open_folder = QPushButton("📂 Abrir Carpeta")
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background-color: #3b4261;
                color: #c0caf5;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4c6fc1; color: white; }
        """)
        self.btn_open_folder.clicked.connect(self.open_music_folder)
        folder_layout.addWidget(self.btn_open_folder)
        layout.addLayout(folder_layout)

        # Consola de registro
        self.log_list = QListWidget()
        self.log_list.setMaximumHeight(90)
        self.log_list.setStyleSheet("""
            QListWidget {
                background-color: #16161e;
                border: 1px solid #292e42;
                border-radius: 8px;
                color: #565f89;
                padding: 4px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.log_list)

        self.setStyleSheet("QMainWindow { background-color: #16161e; }")

    def select_all_tracks(self):
        self.results_list.selectAll()

    def open_music_folder(self):
        try:
            subprocess.Popen(["xdg-open", str(self.music_dir)])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir la carpeta: {e}")

    def start_search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Atención", "Ingresa un término de búsqueda o enlace.")
            return

        self.btn_search.setEnabled(False)
        self.search_input.setEnabled(False)
        self.results_list.clear()
        self.log_list.addItem("Consultando álbumes y pistas en la API de Deezer...")

        self.search_worker = SearchWorker(query)
        self.search_worker.results_signal.connect(self.handle_search_results)
        self.search_worker.error_signal.connect(self.handle_search_error)
        self.search_worker.start()

    def handle_search_results(self, tracks):
        self.btn_search.setEnabled(True)
        self.search_input.setEnabled(True)
        self.current_results = tracks
        self.log_list.clear()

        if not tracks:
            self.results_list.addItem("No se encontraron resultados.")
            return

        for idx, track in enumerate(tracks, start=1):
            item_text = f"{idx:02d}. {track['artist']}  —  {track['title']}  ({track['album']})"
            self.results_list.addItem(item_text)

        self.log_list.addItem(f"¡Cargados {len(tracks)} temas ordenados! Hacé clic en 'Seleccionar todo' y dale a descargar.")

    def handle_search_error(self, err):
        self.btn_search.setEnabled(True)
        self.search_input.setEnabled(True)
        self.log_list.addItem(f"Error en la búsqueda: {err}")

    def start_download(self):
        selected_indexes = self.results_list.selectedIndexes()
        if not selected_indexes:
            QMessageBox.warning(self, "Atención", "Selecciona al menos una canción de la lista.")
            return

        tracks_to_download = [self.current_results[index.row()] for index in selected_indexes]

        self.btn_download.setEnabled(False)
        self.search_input.setEnabled(False)
        self.btn_search.setEnabled(False)
        self.progress_bar.setValue(0)

        self.download_worker = DownloadWorker(tracks_to_download, self.music_dir)
        self.download_worker.progress_signal.connect(self.append_log)
        self.download_worker.percent_signal.connect(self.progress_bar.setValue)
        self.download_worker.finished_signal.connect(self.download_finished)
        self.download_worker.start()

    def append_log(self, message):
        self.log_list.addItem(message)
        self.log_list.scrollToItem(self.log_list.item(self.log_list.count() - 1))

    def download_finished(self, success, message):
        self.btn_download.setEnabled(True)
        self.search_input.setEnabled(True)
        self.btn_search.setEnabled(True)
        self.append_log(message)
        if success:
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Completado", f"Las descargas se guardaron ordenadas en:\n{self.music_dir}")

if __name__ == "__main__":
    QApplication.setDesktopFileName("sinergia-longplay")
    app = QApplication(sys.argv)
    window = SinergiaLongPlayApp()
    window.show()
    sys.exit(app.exec())
