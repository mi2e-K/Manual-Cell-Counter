"""
Custom widgets for Fluorescence Microscope Image Analyzer.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSpinBox, QColorDialog, QLineEdit
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor

from .datatypes import CellType, MarkerType


class CellTypeWidget(QWidget):
    """Widget for configuring a cell type."""
    
    type_changed = pyqtSignal()
    name_change_requested = pyqtSignal(str, str)  # old_name, new_name
    delete_requested = pyqtSignal(str)  # cell_type_name
    
    def __init__(self, cell_type: CellType, parent=None):
        super().__init__(parent)
        self.cell_type = cell_type
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(3)
        
        # Editable name
        self.name_edit = QLineEdit(self.cell_type.name)
        self.name_edit.setMaximumWidth(70)
        self.name_edit.editingFinished.connect(self.on_name_edited)
        layout.addWidget(self.name_edit)
        
        # Color button
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(22, 22)
        self.color_btn.setStyleSheet(
            f"background-color: {self.cell_type.color.name()}; border: 1px solid #555; border-radius: 3px;"
        )
        self.color_btn.clicked.connect(self.change_color)
        layout.addWidget(self.color_btn)
        
        # Marker type
        self.marker_combo = QComboBox()
        self.marker_combo.setMaximumWidth(70)
        for mt in MarkerType:
            self.marker_combo.addItem(mt.value, mt)
        self.marker_combo.setCurrentText(self.cell_type.marker_type.value)
        self.marker_combo.currentIndexChanged.connect(self.marker_type_changed)
        layout.addWidget(self.marker_combo)
        
        # Size
        self.size_spin = QSpinBox()
        self.size_spin.setRange(5, 100)
        self.size_spin.setValue(self.cell_type.marker_size)
        self.size_spin.setFixedWidth(70)
        self.size_spin.valueChanged.connect(self.size_changed)
        layout.addWidget(self.size_spin)
        
        # Count label
        self.count_label = QLabel("(0)")
        self.count_label.setMinimumWidth(28)
        layout.addWidget(self.count_label)
        
        # Delete button
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(20, 20)
        self.delete_btn.setToolTip("Delete this cell type")
        self.delete_btn.setStyleSheet("""
            QPushButton { 
                background-color: #5c3c3c; 
                border: 1px solid #755; 
                border-radius: 3px; 
                font-weight: bold;
                color: #faa;
            }
            QPushButton:hover { background-color: #7c4c4c; }
        """)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        layout.addWidget(self.delete_btn)
    
    def on_name_edited(self):
        """Handle name edit completion."""
        new_name = self.name_edit.text().strip()
        if new_name and new_name != self.cell_type.name:
            self.name_change_requested.emit(self.cell_type.name, new_name)
    
    def update_name_display(self, new_name: str):
        """Update the displayed name after external change."""
        self.name_edit.setText(new_name)
    
    def change_color(self):
        color = QColorDialog.getColor(self.cell_type.color, self)
        if color.isValid():
            self.cell_type.color = color
            self.color_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #555; border-radius: 3px;"
            )
            self.type_changed.emit()
    
    def marker_type_changed(self, index):
        self.cell_type.marker_type = self.marker_combo.currentData()
        self.type_changed.emit()
    
    def size_changed(self, value):
        self.cell_type.marker_size = value
        self.type_changed.emit()
    
    def update_count(self, count: int):
        self.cell_type.count = count
        self.count_label.setText(f"({count})")
    
    def on_delete_clicked(self):
        """Handle delete button click."""
        self.delete_requested.emit(self.cell_type.name)
