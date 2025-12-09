"""
Custom widgets for Fluorescence Microscope Image Analyzer.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QComboBox,
    QSpinBox, QColorDialog, QLineEdit, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor

from .datatypes import CellType, MarkerType, LabelPosition


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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(2)
        
        # Row 1: Name, Color, Count, Delete
        row1 = QHBoxLayout()
        row1.setSpacing(4)
        
        # Editable name
        self.name_edit = QLineEdit(self.cell_type.name)
        self.name_edit.setMinimumWidth(80)
        self.name_edit.editingFinished.connect(self.on_name_edited)
        row1.addWidget(self.name_edit)
        
        # Color button
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(24, 24)
        self.color_btn.setStyleSheet(
            f"background-color: {self.cell_type.color.name()}; border: 1px solid #555; border-radius: 3px;"
        )
        self.color_btn.setToolTip("Change color")
        self.color_btn.clicked.connect(self.change_color)
        row1.addWidget(self.color_btn)
        
        # Count label
        self.count_label = QLabel("(0)")
        self.count_label.setMinimumWidth(35)
        self.count_label.setStyleSheet("font-weight: bold;")
        row1.addWidget(self.count_label)
        
        # Delete button
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setToolTip("Delete this cell type")
        self.delete_btn.setStyleSheet("""
            QPushButton { 
                background-color: #5c3c3c; 
                border: 1px solid #755; 
                border-radius: 3px; 
                font-weight: bold;
                font-size: 14px;
                color: #faa;
            }
            QPushButton:hover { background-color: #7c4c4c; }
        """)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        row1.addWidget(self.delete_btn)
        
        main_layout.addLayout(row1)
        
        # Row 2: Marker type, Size, Label position
        row2 = QHBoxLayout()
        row2.setSpacing(4)
        
        # Marker type
        row2.addWidget(QLabel("Shape:"))
        self.marker_combo = QComboBox()
        self.marker_combo.setMinimumWidth(70)
        for mt in MarkerType:
            self.marker_combo.addItem(mt.value, mt)
        self.marker_combo.setCurrentText(self.cell_type.marker_type.value)
        self.marker_combo.currentIndexChanged.connect(self.marker_type_changed)
        row2.addWidget(self.marker_combo)
        
        # Size
        self.size_spin = QSpinBox()
        self.size_spin.setRange(5, 100)
        self.size_spin.setValue(self.cell_type.marker_size)
        self.size_spin.setFixedWidth(70)
        self.size_spin.valueChanged.connect(self.size_changed)
        row2.addWidget(self.size_spin)
        
        # Label position
        row2.addWidget(QLabel("Label:"))
        self.label_pos_combo = QComboBox()
        self.label_pos_combo.setMinimumWidth(50)
        self.label_pos_combo.setToolTip("Label position")
        pos_abbrev = {
            LabelPosition.RIGHT: "R",
            LabelPosition.LEFT: "L",
            LabelPosition.TOP: "T",
            LabelPosition.BOTTOM: "B",
            LabelPosition.TOP_RIGHT: "TR",
            LabelPosition.TOP_LEFT: "TL",
            LabelPosition.BOTTOM_RIGHT: "BR",
            LabelPosition.BOTTOM_LEFT: "BL",
        }
        for lp in LabelPosition:
            self.label_pos_combo.addItem(pos_abbrev[lp], lp)
        self.label_pos_combo.setCurrentIndex(
            list(LabelPosition).index(self.cell_type.label_position)
        )
        self.label_pos_combo.currentIndexChanged.connect(self.label_pos_changed)
        row2.addWidget(self.label_pos_combo)
        
        row2.addStretch()
        main_layout.addLayout(row2)
        
        # Add a subtle border/background to separate cell types
        self.setStyleSheet("""
            CellTypeWidget {
                background-color: #383838;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
            }
        """)
    
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
    
    def label_pos_changed(self, index):
        self.cell_type.label_position = self.label_pos_combo.currentData()
        self.type_changed.emit()
    
    def update_count(self, count: int):
        self.cell_type.count = count
        self.count_label.setText(f"({count})")
    
    def on_delete_clicked(self):
        """Handle delete button click with confirmation."""
        reply = QMessageBox.question(
            self, "Delete Cell Type",
            f"Are you sure you want to delete '{self.cell_type.name}'?\n\n"
            "All markers of this type will also be removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self.cell_type.name)
