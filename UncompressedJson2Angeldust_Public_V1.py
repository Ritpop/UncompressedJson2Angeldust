import os
import json
import numpy as np
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QLabel, QLineEdit, QPushButton, QCheckBox, QVBoxLayout, QHBoxLayout, QWidget
from minecraft_to_angeldust import minecraft_to_angeldust
from obi_functions import *

# Credits to obi
DEFAULT_OUTPUT_DIR = "output_chunks"
CONFIG_FILE = "settings.json"

def load_settings():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"use_default_path": True, "custom_output_path": DEFAULT_OUTPUT_DIR}

def save_settings(settings):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(settings, f)

def convert_json_to_voxels(json_file, output_dir):
    # Load the JSON data
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Find the minimum and maximum coordinates to calculate the size of the voxel grid
    min_x = min(block['x'] for block in data)
    max_x = max(block['x'] for block in data)
    min_y = min(block['y'] for block in data)
    max_y = max(block['y'] for block in data)
    min_z = min(block['z'] for block in data)
    max_z = max(block['z'] for block in data)

    # Calculate the size of the voxel grid
    size_x = max_x - min_x + 1
    size_y = max_y - min_y + 1
    size_z = max_z - min_z + 1
    print(size_x, size_y, size_z)

    # Create an empty array to store the block IDs with the same size as the json file
    voxels = np.zeros((size_x, size_y, size_z), dtype=np.int64)

    # Fill the voxels array with the correct angeldust block id
    for block in data:
        x, y, z = block['x'] - min_x, block['y'] - min_y, block['z'] - min_z

        block_name = block['block_name']
        block_id = minecraft_to_angeldust.get(block_name, [0])[0]  # Default to air block if not found
        voxels[x, y, z] = block_id

    # Mirror the voxel data along the x-axis
    voxels = np.flip(voxels, axis=0)
    
    chunk_size = 32
    chunks_x = (voxels.shape[0] + 31) // 32
    chunks_y = (voxels.shape[1] + 31) // 32

    # Loop for each chunk and export using the functions from obi
    for chunk_y in range(chunks_y):
        for chunk_x in range(chunks_x):
            chunk_start_x = chunk_x * chunk_size
            chunk_start_y = chunk_y * chunk_size
            chunk_end_x = min(chunk_start_x + chunk_size, voxels.shape[0])
            chunk_end_y = min(chunk_start_y + chunk_size, voxels.shape[1])

            chunk_voxels = voxels[chunk_start_x:chunk_end_x, chunk_start_y:chunk_end_y, :]

            # Pad the chunk with zeros to ensure it's at least 32x32x64 in size
            padded_chunk_voxels = np.zeros((chunk_size, chunk_size, 64), dtype=np.int64)
            padded_chunk_voxels[:chunk_voxels.shape[0], :chunk_voxels.shape[1], :chunk_voxels.shape[2]] = chunk_voxels

            reordered_x, reordered_y = chunks_x - 1 - chunk_x, chunks_y - 1 - chunk_y
            ba_x, ba_y = build_alone_offset((reordered_x, reordered_y))
            chunk_hex = f"{ba_x:05x}{ba_y:05x}"
            os.makedirs(output_dir, exist_ok=True)
            save_claim_from_voxels(padded_chunk_voxels, os.path.join(output_dir, chunk_hex))
    
    QMessageBox.information(None, "Success", f"Conversion completed successfully. Chunks saved in {output_dir}")

def build_alone_offset(offset):
    def bao(o):
        if o == 0:
            return 2
        else:
            return o // 2 if o > 8 else (o - 1) // 2 if o % 2 == 0 else (o + 1) // 2
    return int(32769 + bao(offset[1])), int(32769 + bao(offset[0]))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = load_settings()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('UncompressedJson2Angeldust')
        self.setGeometry(100, 100, 500, 300)

        layout = QVBoxLayout()

        # JSON file path
        self.file_path_label = QLabel('JSON Path:')
        layout.addWidget(self.file_path_label)

        self.file_path_entry = QLineEdit()
        layout.addWidget(self.file_path_entry)

        self.browse_button = QPushButton('Browse')
        self.browse_button.clicked.connect(self.open_file)
        layout.addWidget(self.browse_button)

        # Output path
        self.default_path_checkbox = QCheckBox('Use Default Output Path')
        self.default_path_checkbox.setChecked(self.settings.get("use_default_path", True))
        self.default_path_checkbox.toggled.connect(self.toggle_custom_folder)
        layout.addWidget(self.default_path_checkbox)

        self.custom_folder_label = QLabel('Custom Output Path:')
        layout.addWidget(self.custom_folder_label)

        self.custom_folder_entry = QLineEdit()
        if not self.settings.get("use_default_path", True):
            self.custom_folder_entry.setText(self.settings.get("custom_output_path", DEFAULT_OUTPUT_DIR))
        layout.addWidget(self.custom_folder_entry)

        self.custom_folder_button = QPushButton('Browse')
        self.custom_folder_button.clicked.connect(self.browse_custom_folder)
        layout.addWidget(self.custom_folder_button)

        # Convert button
        self.convert_button = QPushButton('Convert')
        self.convert_button.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_button)

        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'JSON files (*.json)')
        if file_path:
            self.file_path_entry.setText(file_path)

    def browse_custom_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Directory')
        if folder_path:
            self.custom_folder_entry.setText(folder_path)

    def toggle_custom_folder(self):
        use_default_path = self.default_path_checkbox.isChecked()
        self.custom_folder_entry.setEnabled(not use_default_path)
        self.custom_folder_button.setEnabled(not use_default_path)

    def start_conversion(self):
        input_file = self.file_path_entry.text()
        use_default_path = self.default_path_checkbox.isChecked()
        custom_output_path = self.custom_folder_entry.text() if not use_default_path else DEFAULT_OUTPUT_DIR

        if not input_file:
            QMessageBox.warning(self, "Error", "Please select a file")
            return

        if input_file.endswith(".json"):
            convert_json_to_voxels(input_file, custom_output_path)

        settings = {
            "use_default_path": use_default_path,
            "custom_output_path": custom_output_path
        }
        save_settings(settings)

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
