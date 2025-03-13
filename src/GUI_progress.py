#!/usr/bin/env python3
# gui_gui.py
# CSC3002F Group Assignment 2025 - GUI Version
# This script creates a PyQt GUI to download files sequentially.
# Each file’s download widget shows a main cumulative progress bar along with
# sub progress bars for each seeder connection (including seeder IP/port info).
#
# Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

import sys, os, traceback
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QProgressBar, QLabel, QFileDialog, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from CLI_GUI import Peer  # Using the modified Peer class from CLI_GUI.py

# --- Custom Widget to display download progress for a single file download instance ---
class FileDownloadWidget(QWidget):
    def __init__(self, file_name, download_id):
        super().__init__()
        self.file_name = file_name
        self.download_id = download_id
        # Stores per-connection progress: connection_index -> (current, total, seeder_info)
        self.sub_progress = {}
        # Stores sub-widget components: connection_index -> (QLabel, QProgressBar)
        self.sub_widgets = {}
        
        main_layout = QVBoxLayout()
        # Label showing download index, file name and cumulative progress
        self.file_label = QLabel(f"Download #{download_id}: {file_name} - 0% complete")
        main_layout.addWidget(self.file_label)
        # Cumulative progress bar
        self.cumulative_bar = QProgressBar()
        self.cumulative_bar.setMinimum(0)
        self.cumulative_bar.setMaximum(100)
        main_layout.addWidget(self.cumulative_bar)
        
        # Container for sub progress bars (each representing a seeder connection)
        self.sub_container = QVBoxLayout()
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        frame.setLayout(self.sub_container)
        main_layout.addWidget(frame)
        
        self.setLayout(main_layout)
    
    def update_progress(self, connection_index, current, total, seeder_info):
        # Save progress for this connection
        self.sub_progress[connection_index] = (current, total, seeder_info)
        # Create sub-widget if it doesn't already exist
        if connection_index not in self.sub_widgets:
            sub_widget = QWidget()
            sub_layout = QHBoxLayout()
            sub_widget.setLayout(sub_layout)
            label = QLabel(f"Seeder: {seeder_info[0]}:{seeder_info[1]}")
            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            progress_bar.setValue(0)
            sub_layout.addWidget(label)
            sub_layout.addWidget(progress_bar)
            self.sub_container.addWidget(sub_widget)
            self.sub_widgets[connection_index] = (label, progress_bar)
        # Update the sub progress bar for this connection
        label, progress_bar = self.sub_widgets[connection_index]
        sub_percent = int((current / total) * 100) if total > 0 else 0
        progress_bar.setValue(sub_percent)
        # Compute cumulative progress over all seeder connections
        total_current = sum(val[0] for val in self.sub_progress.values())
        total_total = sum(val[1] for val in self.sub_progress.values())
        cumulative = int((total_current / total_total) * 100) if total_total > 0 else 0
        self.cumulative_bar.setValue(cumulative)
        self.file_label.setText(f"Download #{self.download_id}: {self.file_name} - {cumulative}% complete")
    
    def mark_complete(self):
        self.file_label.setText(f"Download #{self.download_id}: {self.file_name} - Download Complete")


# --- Worker thread to download a single file ---
class DownloadWorker(QThread):
    # Signal: file_name, connection_index, current, total, seeder_info, download_id
    progressChanged = pyqtSignal(str, int, int, int, tuple, int)
    # Signal when a file is finished: file_name, download_id
    downloadFinished = pyqtSignal(str, int)
    
    def __init__(self, peer, file_name, download_id, parent=None):
        super().__init__(parent)
        self.peer = peer
        self.file_name = file_name
        self.download_id = download_id
        
    def run(self):
        try:
            # Define a progress callback to be used by the backend.
            def progress_callback(file_name, connection_index, current, total, seeder_info):
                # Ensure seeder_info is a tuple.
                self.progressChanged.emit(file_name, connection_index, current, total, tuple(seeder_info), self.download_id)
            self.peer.leecher.request_file(self.file_name, progress_callback=progress_callback)
            self.downloadFinished.emit(self.file_name, self.download_id)
        except Exception as e:
            print("Error in DownloadWorker:", e)
            traceback.print_exc()


# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Downloader GUI")
        self.resize(900, 700)
        self.peer = None  # Initialized in init_peer
        # For sequential downloads (Download All Files)
        self.sequential_queue = []  # List of file names (in order)
        self.current_worker = None  # For sequential mode
        # Mapping from unique download_id to its FileDownloadWidget
        self.download_widgets = {}
        # Mapping from unique download_id to its DownloadWorker
        self.download_workers = {}
        self.download_counter = 0  # Unique download ID counter

        # Set up main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout()
        central_widget.setLayout(self.main_layout)
        
        # Top controls
        top_layout = QHBoxLayout()
        self.tracker_label = QLabel("Tracker: 127.0.0.1:12500")
        top_layout.addWidget(self.tracker_label)
        self.folder_button = QPushButton("Select Download Folder")
        self.folder_button.clicked.connect(self.select_folder)
        top_layout.addWidget(self.folder_button)
        self.download_all_button = QPushButton("Download All Files (Sequential)")
        self.download_all_button.clicked.connect(self.download_all_files)
        top_layout.addWidget(self.download_all_button)
        self.main_layout.addLayout(top_layout)
        
        # File list widget
        self.file_list_widget = QListWidget()
        self.main_layout.addWidget(self.file_list_widget)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh File List")
        self.refresh_button.clicked.connect(self.load_file_list)
        self.main_layout.addWidget(self.refresh_button)
        
        # Download selected files button (for individual downloads)
        self.download_button = QPushButton("Download Selected Files")
        self.download_button.clicked.connect(self.download_selected_files)
        self.main_layout.addWidget(self.download_button)
        
        # Scroll area for file download widgets (progress list that sticks to the bottom)
        self.progress_area = QScrollArea()
        self.progress_area_widget = QWidget()
        self.progress_area_layout = QVBoxLayout()
        self.progress_area_widget.setLayout(self.progress_area_layout)
        self.progress_area.setWidgetResizable(True)
        self.progress_area.setWidget(self.progress_area_widget)
        self.main_layout.addWidget(self.progress_area)
        
        self.init_peer("./tmp/")
        self.load_file_list()
    
    def init_peer(self, download_folder):
        tracker_addr = ("127.0.0.1", 12500)
        # Initialize Peer with the given download folder
        self.peer = Peer(tracker_addr, download_folder)
    
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.init_peer(folder)
            self.load_file_list()
    
    def load_file_list(self):
        self.file_list_widget.clear()
        if self.peer:
            for file_name, size in self.peer.leecher.file_list.items():
                self.file_list_widget.addItem(f"{file_name} ({size} bytes)")
    
    def download_selected_files(self):
        selected_items = self.file_list_widget.selectedItems()
        if not selected_items:
            return
        # Start downloads concurrently for each selected file
        for item in selected_items:
            file_name = item.text().split(" (")[0]
            self.start_file_download(file_name, sequential=False)
    
    def download_all_files(self):
        # Build sequential queue (top-to-bottom based on file list order)
        self.sequential_queue = []
        for index in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(index)
            file_name = item.text().split(" (")[0]
            self.sequential_queue.append(file_name)
        self.download_all_button.setEnabled(False)
        self.start_next_in_queue()
    
    def start_next_in_queue(self):
        if self.sequential_queue:
            file_name = self.sequential_queue.pop(0)
            self.start_file_download(file_name, sequential=True)
        else:
            self.download_all_button.setEnabled(True)
    
    def start_file_download(self, file_name, sequential=False):
        # Increment counter to get a unique download ID
        self.download_counter += 1
        download_id = self.download_counter
        
        # Create a new FileDownloadWidget and add it to the progress area.
        widget = FileDownloadWidget(file_name, download_id)
        self.progress_area_layout.addWidget(widget)
        self.download_widgets[download_id] = widget
        
        # Create and start a DownloadWorker for this file download.
        worker = DownloadWorker(self.peer, file_name, download_id)
        worker.progressChanged.connect(self.handle_progress)
        worker.downloadFinished.connect(lambda fn, did=download_id, seq=sequential: self.handle_finished(fn, did, seq))
        self.download_workers[download_id] = worker
        if sequential:
            self.current_worker = worker
        worker.start()
        worker.finished.connect(worker.deleteLater)
    
    def handle_progress(self, file_name, connection_index, current, total, seeder_info, download_id):
        if download_id in self.download_widgets:
            widget = self.download_widgets[download_id]
            widget.update_progress(connection_index, current, total, seeder_info)
            # Auto-scroll to ensure the current download widget is visible.
            self.progress_area.verticalScrollBar().setValue(self.progress_area.verticalScrollBar().maximum())
    
    def handle_finished(self, file_name, download_id, sequential):
        if download_id in self.download_widgets:
            widget = self.download_widgets[download_id]
            widget.mark_complete()
        if download_id in self.download_workers:
            worker = self.download_workers.pop(download_id)
            worker.quit()
            worker.wait()
        if sequential and self.current_worker:
            self.current_worker = None
            self.start_next_in_queue()
    
    def closeEvent(self, event):
        for worker in self.download_workers.values():
            worker.quit()
            worker.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())