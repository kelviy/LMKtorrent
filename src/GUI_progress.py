#!/usr/bin/env python3
# gui_gui.py
# CSC3002F Group Assignment 2025 - GUI Version
# This script creates a PyQt GUI to download files sequentially.
# Each file’s download widget shows a main cumulative progress bar along with
# sub progress bars for each seeder connection (including seeder IP/port info).
#
# Owners: Kelvin Wei, Liam de Saldanha, Mark Du Preez

from operator import add
import sys, os, traceback
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QPushButton, QProgressBar, QLabel, QFileDialog, QScrollArea, QFrame, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from CLI_GUI import Peer  # Using the modified Peer class from CLI_GUI.py

def main():
    app = QApplication(sys.argv)

    # Defaults
    tracker_addr = ("127.0.0.1", 12500)
    seeder_reference = []

    usr_ans = input("Enter Tracker ip and port number seperated by spaces (eg 127.0.0.1 12500):")
    if usr_ans != "":
        usr_ans = usr_ans.split(" ")
        tracker_addr = (usr_ans[0], int(usr_ans))
    
    window = MainWindow(tracker_addr, seeder_reference)
    window.show()
    app.exec()

    seeder_reference[0].start_main_loop()

# Custom Widget to display download progress for a single file download instance.
class FileDownloadWidget(QWidget):
    def __init__(self, file_name, download_id):
        super().__init__()
        self.file_name = file_name
        self.download_id = download_id
        # Stores per-connection progress: connection_index -> (current, total, seeder_info).
        self.sub_progress = {}
        # Stores sub-widget components: connection_index -> (QLabel, QProgressBar).
        self.sub_widgets = {}
        
        main_layout = QVBoxLayout()
        # Label showing download index, file name and cumulative progress.
        self.file_label = QLabel(f"Download #{download_id}: {file_name} - 0% complete")
        main_layout.addWidget(self.file_label)
        # Cumulative progress bar.
        self.cumulative_bar = QProgressBar()
        self.cumulative_bar.setMinimum(0)
        self.cumulative_bar.setMaximum(100)
        main_layout.addWidget(self.cumulative_bar)
        
        # Container for sub progress bars (each representing a seeder connection).
        self.sub_container = QVBoxLayout()
        frame = QFrame()
        # Use PyQt6 enums: QFrame.Shape.Box and QFrame.Shadow.Raised.
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        frame.setLayout(self.sub_container)
        main_layout.addWidget(frame)
        
        self.setLayout(main_layout)
    
    def update_progress(self, connection_index, current, total, seeder_info):
        # Save progress for this connection.
        self.sub_progress[connection_index] = (current, total, seeder_info)
        # Create sub-widget if it doesn't already exist.
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
        # Update the sub progress bar for this connection.
        label, progress_bar = self.sub_widgets[connection_index]
        sub_percent = int((current / total) * 100) if total > 0 else 0
        progress_bar.setValue(sub_percent)
        # Compute cumulative progress over all seeder connections.
        total_current = sum(val[0] for val in self.sub_progress.values())
        total_total = sum(val[1] for val in self.sub_progress.values())
        cumulative = int((total_current / total_total) * 100) if total_total > 0 else 0
        self.cumulative_bar.setValue(cumulative)
        self.file_label.setText(f"Download #{self.download_id}: {self.file_name} - {cumulative}% complete")
    
    def mark_complete(self):
        self.file_label.setText(f"Download #{self.download_id}: {self.file_name} - Download Complete")

# Worker thread to download a single file
class DownloadWorker(QThread):
    # Signal: file_name, connection_index, current, total, seeder_info, download_id
    progressChanged = pyqtSignal(str, int, int, int, tuple, int)
    # Signal when a file is finished: file_name, download_id.
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

# Main Window
class MainWindow(QMainWindow):
    def __init__(self, addr, seeder_reference):
        super().__init__()
        self.setWindowTitle("File Downloader GUI")
        self.resize(900, 700)
        # Will be initialized in init_peer.
        self.peer = None
        # Default tracker address.
        self.tracker_addr = addr
        # For sequential downloads (download all files).

        # List of file names (in order).
        self.sequential_queue = []
        # For sequential mode.
        self.current_worker = None

        # Mapping from unique download_id to its FileDownloadWidget.
        self.download_widgets = {}
        # Mapping from unique download_id to its DownloadWorker.
        self.download_workers = {}
        # Unique download ID counter
        self.download_counter = 0

        # Set up main layout.
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout()
        central_widget.setLayout(self.main_layout)
        
        # Top controls
        top_layout = QHBoxLayout()
        self.tracker_label = QLabel(f"Tracker: {self.tracker_addr[0]}:{self.tracker_addr[1]}")
        top_layout.addWidget(self.tracker_label)
        self.folder_button = QPushButton("Select Download Folder")
        self.folder_button.clicked.connect(self.select_folder)
        top_layout.addWidget(self.folder_button)

        # Change Tracker button
        self.change_tracker_button = QPushButton("Change Tracker")
        self.change_tracker_button.clicked.connect(self.change_tracker)
        top_layout.addWidget(self.change_tracker_button)
        self.download_all_button = QPushButton("Download All Files")
        self.download_all_button.clicked.connect(self.download_all_files)
        top_layout.addWidget(self.download_all_button)
        self.main_layout.addLayout(top_layout)
        
        # File list widget
        self.file_list_widget = QListWidget()
        self.main_layout.addWidget(self.file_list_widget)
        
        # Refresh button
        self.seed_button = QPushButton("Seed All Files")
        self.seed_button.clicked.connect(self.seed_all_files)
        self.main_layout.addWidget(self.seed_button)
        
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

        # For reference seederlist back to main function.
        self.seeder_reference = seeder_reference

    def seed_all_files(self):
        if self.peer.check_all_files():
            addr, ok = QInputDialog.getText(self, "Seeding", 
                                            "Enter Seeding IP and Port (ex: 127.0.0.1 12500):")
            addr = addr.split()
            if ok:
                print("seeding")
                self.peer.change_to_seeder((addr[0],int(addr[1])))
                self.seeder_reference.append(self.peer.seeder)
                # Will not stop. Need to exit whole program to stop

                msg_box = QMessageBox()
                msg_box.setWindowTitle("Seeding")
                msg_box.setText("Seeder started. Switching to terminal")
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()
                self.close()

        else:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Error")
            msg_box.setText("You need to download all files")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
            
    def init_peer(self, download_folder):
        # Initialize Peer with the current tracker address.
        self.peer = Peer(self.tracker_addr, download_folder)
    
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.init_peer(folder)
            self.load_file_list()
    
    def change_tracker(self):
        # Show an input dialog to change tracker.
        tracker_str, ok = QInputDialog.getText(self, "Change Tracker", 
                                               "Enter Tracker IP and Port (ex: 127.0.0.1 12500):")
        if ok and tracker_str:
            parts = tracker_str.split()
            if len(parts) == 2:
                ip = parts[0].strip()
                try:
                    port = int(parts[1].strip())
                except ValueError:
                    # Optionally show an error message here
                    return
                self.tracker_addr = (ip, port)
                self.tracker_label.setText(f"Tracker: {ip}:{port}")

                # Reinitialize peer with the new tracker using the current download folder.
                folder = self.peer.leecher.download_path if self.peer else "./tmp/"
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
        # Start downloads concurrently for each selected file.
        for item in selected_items:
            file_name = item.text().split(" (")[0]
            self.start_file_download(file_name, sequential=False)
    
    def download_all_files(self):
        # Build sequential queue (top-to-bottom based on file list order).
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
        # Increment counter to get a unique download ID.
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
            # Auto-scroll so that the current download widget is visible.
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
    main()