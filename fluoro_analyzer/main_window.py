"""
Main window for Fluorescence Microscope Image Analyzer.
"""

import csv
import json
import numpy as np
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSpinBox,
    QGraphicsEllipseItem, QGraphicsTextItem,
    QFileDialog, QListWidget, QListWidgetItem, QGroupBox,
    QColorDialog, QMessageBox, QStatusBar, QToolBar, QSplitter,
    QScrollArea, QFrame, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QInputDialog, QMenu, QCheckBox,
    QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import (
    QImage, QPixmap, QColor, QPen, QBrush, QPolygonF,
    QFont, QAction, QKeySequence, QShortcut, QScreen
)

from PIL import Image

try:
    import tifffile
    HAS_TIFF = True
except ImportError:
    HAS_TIFF = False

from .datatypes import (
    ChannelMode, MarkerType, ToolMode, LabelPosition,
    CellType, CellMarker, ROI, ImageAdjustments
)
from .canvas import ImageCanvas
from .widgets import CellTypeWidget
from .adjustments_dialog import AdjustmentsDialog
from .image_processing import apply_all_adjustments


class FluoroAnalyzer(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluorescence Microscope Image Analyzer")
        self.setMinimumSize(1200, 800)
        
        # Data
        self.image_data: Optional[np.ndarray] = None  # Original image data
        self.current_file: Optional[str] = None
        self.channel_mode = ChannelMode.COMPOSITE
        self.cell_types: dict[str, CellType] = {}
        self.cell_markers: list[CellMarker] = []
        self.marker_items: list = []
        self.rois: list[ROI] = []
        self.current_roi: Optional[ROI] = None
        self.roi_items: list = []
        self.current_cell_type: Optional[str] = None
        
        # Undo/Redo stacks
        self.undo_stack: list = []
        
        # Selected marker for deletion
        self.selected_marker_index: int = -1
        
        # Output directory
        self.output_directory: Optional[str] = None
        
        # ROI name history
        self.roi_name_history: list = []
        
        # Channel checkbox states
        self.channel_r_enabled = True
        self.channel_g_enabled = True
        self.channel_b_enabled = True
        
        # Image adjustments
        self.image_adjustments = ImageAdjustments()
        self.preserve_adjustments_on_load = True
        self.adjustments_dialog: Optional[AdjustmentsDialog] = None
        
        # Setup UI
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_default_cell_types()
        self.apply_dark_theme()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Center window
        self.center_on_screen()
    
    def center_on_screen(self):
        """Center the window on the screen."""
        screen = QScreen.availableGeometry(self.screen())
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def setup_ui(self):
        """Setup the main UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create canvas first (needed by left panel)
        self.canvas = ImageCanvas(self)
        self.canvas.cell_clicked.connect(self.add_cell_marker)
        self.canvas.roi_point_added.connect(self.add_roi_point)
        self.canvas.roi_close_requested.connect(self.close_current_roi)
        self.canvas.roi_vertex_moved.connect(self.move_roi_vertex)
        self.canvas.roi_moved.connect(self.move_roi)
        self.canvas.marker_moved.connect(self.move_marker)
        self.canvas.marker_selected.connect(self.select_marker)
        
        # Left panel
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Center - Image canvas
        splitter.addWidget(self.canvas)
        
        # Right panel
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([280, 700, 250])
        
        # Toolbar
        self.create_toolbar()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Drop an image to begin")
    
    def create_left_panel(self) -> QWidget:
        """Create the left control panel."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(260)
        scroll.setMaximumWidth(320)
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # File controls
        file_group = QGroupBox("File")
        file_layout = QVBoxLayout(file_group)
        
        open_btn = QPushButton("📂 Open Image")
        open_btn.clicked.connect(self.open_file)
        file_layout.addWidget(open_btn)
        
        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)
        
        layout.addWidget(file_group)
        
        # Channel controls
        channel_group = QGroupBox("Channel Display")
        channel_layout = QVBoxLayout(channel_group)
        
        # RGB checkboxes
        checkbox_layout = QHBoxLayout()
        
        self.red_checkbox = QCheckBox("R")
        self.red_checkbox.setChecked(True)
        self.red_checkbox.setStyleSheet("""
            QCheckBox { color: #ff6666; font-weight: bold; }
            QCheckBox::indicator { width: 22px; height: 22px; }
            QCheckBox::indicator:checked { background-color: #ff6666; border: 2px solid #ff6666; border-radius: 3px; }
            QCheckBox::indicator:unchecked { background-color: #3c3c3c; border: 2px solid #ff6666; border-radius: 3px; }
        """)
        self.red_checkbox.stateChanged.connect(self.on_channel_checkbox_changed)
        checkbox_layout.addWidget(self.red_checkbox)
        
        self.green_checkbox = QCheckBox("G")
        self.green_checkbox.setChecked(True)
        self.green_checkbox.setStyleSheet("""
            QCheckBox { color: #66ff66; font-weight: bold; }
            QCheckBox::indicator { width: 22px; height: 22px; }
            QCheckBox::indicator:checked { background-color: #66ff66; border: 2px solid #66ff66; border-radius: 3px; }
            QCheckBox::indicator:unchecked { background-color: #3c3c3c; border: 2px solid #66ff66; border-radius: 3px; }
        """)
        self.green_checkbox.stateChanged.connect(self.on_channel_checkbox_changed)
        checkbox_layout.addWidget(self.green_checkbox)
        
        self.blue_checkbox = QCheckBox("B")
        self.blue_checkbox.setChecked(True)
        self.blue_checkbox.setStyleSheet("""
            QCheckBox { color: #6666ff; font-weight: bold; }
            QCheckBox::indicator { width: 22px; height: 22px; }
            QCheckBox::indicator:checked { background-color: #6666ff; border: 2px solid #6666ff; border-radius: 3px; }
            QCheckBox::indicator:unchecked { background-color: #3c3c3c; border: 2px solid #6666ff; border-radius: 3px; }
        """)
        self.blue_checkbox.stateChanged.connect(self.on_channel_checkbox_changed)
        checkbox_layout.addWidget(self.blue_checkbox)
        
        checkbox_layout.addStretch()
        channel_layout.addLayout(checkbox_layout)
        
        # Channel label
        self.channel_label = QLabel("Active: RGB")
        channel_layout.addWidget(self.channel_label)
        
        # Quick mode combo
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Preset:"))
        self.channel_combo = QComboBox()
        for mode in ChannelMode:
            self.channel_combo.addItem(mode.name.capitalize(), mode)
        self.channel_combo.currentIndexChanged.connect(self.channel_combo_changed)
        mode_layout.addWidget(self.channel_combo)
        channel_layout.addLayout(mode_layout)
        
        # Image adjustments button
        adjust_btn = QPushButton("🎨 Image Adjustments...")
        adjust_btn.clicked.connect(self.show_adjustments_dialog)
        channel_layout.addWidget(adjust_btn)
        
        # Preserve adjustments checkbox
        self.preserve_adj_checkbox = QCheckBox("Keep adjustments on new image")
        self.preserve_adj_checkbox.setChecked(True)
        self.preserve_adj_checkbox.stateChanged.connect(
            lambda state: setattr(self, 'preserve_adjustments_on_load', state == Qt.CheckState.Checked.value)
        )
        channel_layout.addWidget(self.preserve_adj_checkbox)
        
        layout.addWidget(channel_group)
        
        # Tool controls
        tool_group = QGroupBox("Tools")
        tool_layout = QVBoxLayout(tool_group)
        
        self.pan_btn = QPushButton("🖐 Pan Mode")
        self.pan_btn.setCheckable(True)
        self.pan_btn.setChecked(True)
        self.pan_btn.clicked.connect(lambda: self.set_tool_mode(ToolMode.PAN))
        tool_layout.addWidget(self.pan_btn)
        
        self.count_btn = QPushButton("🔢 Count Mode")
        self.count_btn.setCheckable(True)
        self.count_btn.clicked.connect(lambda: self.set_tool_mode(ToolMode.CELL_COUNT))
        tool_layout.addWidget(self.count_btn)
        
        self.roi_btn = QPushButton("✏️ ROI Mode")
        self.roi_btn.setCheckable(True)
        self.roi_btn.clicked.connect(lambda: self.set_tool_mode(ToolMode.ROI_DRAW))
        tool_layout.addWidget(self.roi_btn)
        
        reset_view_btn = QPushButton("🔄 Reset View")
        reset_view_btn.clicked.connect(self.canvas.reset_view)
        tool_layout.addWidget(reset_view_btn)
        
        layout.addWidget(tool_group)
        
        # Cell type controls
        cell_group = QGroupBox("Cell Types")
        cell_group.setMinimumHeight(250)
        cell_group.setMaximumHeight(350)
        cell_layout = QVBoxLayout(cell_group)
        
        # Active type selection
        active_layout = QHBoxLayout()
        active_layout.addWidget(QLabel("Active:"))
        self.active_cell_combo = QComboBox()
        self.active_cell_combo.currentTextChanged.connect(self.set_active_cell_type)
        active_layout.addWidget(self.active_cell_combo)
        cell_layout.addLayout(active_layout)
        
        # Cell type list
        self.cell_type_scroll = QScrollArea()
        self.cell_type_scroll.setWidgetResizable(True)
        self.cell_type_widget = QWidget()
        self.cell_type_layout = QVBoxLayout(self.cell_type_widget)
        self.cell_type_layout.setContentsMargins(0, 0, 0, 0)
        self.cell_type_layout.setSpacing(2)
        self.cell_type_scroll.setWidget(self.cell_type_widget)
        cell_layout.addWidget(self.cell_type_scroll)
        
        # Add/Clear buttons
        btn_layout = QHBoxLayout()
        add_type_btn = QPushButton("+ Add Type")
        add_type_btn.clicked.connect(self.add_cell_type)
        btn_layout.addWidget(add_type_btn)
        
        clear_btn = QPushButton("🗑 Clear All")
        clear_btn.clicked.connect(self.clear_all_markers)
        btn_layout.addWidget(clear_btn)
        cell_layout.addLayout(btn_layout)
        
        layout.addWidget(cell_group)
        
        # Image info
        info_group = QGroupBox("Image Info")
        info_layout = QVBoxLayout(info_group)
        self.info_label = QLabel("No image loaded")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        scroll.setWidget(panel)
        return scroll
    
    def create_right_panel(self) -> QWidget:
        """Create the right panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # ROI controls
        roi_group = QGroupBox("ROI Management")
        roi_layout = QVBoxLayout(roi_group)
        
        new_roi_btn = QPushButton("+ New ROI")
        new_roi_btn.clicked.connect(self.start_new_roi)
        roi_layout.addWidget(new_roi_btn)
        
        close_roi_btn = QPushButton("✓ Close Current ROI")
        close_roi_btn.clicked.connect(self.close_current_roi)
        roi_layout.addWidget(close_roi_btn)
        
        # ROI style controls
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Color:"))
        self.roi_color_btn = QPushButton()
        self.roi_color_btn.setFixedSize(30, 24)
        self.roi_color_btn.setStyleSheet("background-color: #ffff00; border: 1px solid #555; border-radius: 3px;")
        self.roi_color_btn.clicked.connect(self.change_roi_color)
        style_layout.addWidget(self.roi_color_btn)
        
        style_layout.addWidget(QLabel("Width:"))
        self.roi_width_spin = QSpinBox()
        self.roi_width_spin.setRange(1, 10)
        self.roi_width_spin.setValue(2)
        self.roi_width_spin.valueChanged.connect(self.change_roi_width)
        style_layout.addWidget(self.roi_width_spin)
        style_layout.addStretch()
        roi_layout.addLayout(style_layout)
        
        self.roi_list = QListWidget()
        self.roi_list.setMaximumHeight(120)
        self.roi_list.itemDoubleClicked.connect(self.rename_roi)
        self.roi_list.itemClicked.connect(self.on_roi_selected)
        self.roi_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.roi_list.customContextMenuRequested.connect(self.roi_context_menu)
        roi_layout.addWidget(self.roi_list)
        
        delete_roi_btn = QPushButton("🗑 Delete Selected ROI")
        delete_roi_btn.clicked.connect(self.delete_selected_roi)
        roi_layout.addWidget(delete_roi_btn)
        
        layout.addWidget(roi_group)
        
        # Results table
        results_group = QGroupBox("Results Summary")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Cell Type", "ROI", "Count"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_group)
        
        # Export options
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout(export_group)
        
        # Output directory
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Output:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Same as source file")
        dir_layout.addWidget(self.output_dir_edit)
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(browse_btn)
        export_layout.addLayout(dir_layout)
        
        self.export_image_checkbox = QCheckBox("Export overlay image (PNG)")
        self.export_image_checkbox.setChecked(True)
        export_layout.addWidget(self.export_image_checkbox)
        
        self.export_json_checkbox = QCheckBox("Export coordinates (JSON)")
        self.export_json_checkbox.setChecked(True)
        export_layout.addWidget(self.export_json_checkbox)
        
        self.export_csv_checkbox = QCheckBox("Export results (CSV)")
        self.export_csv_checkbox.setChecked(True)
        export_layout.addWidget(self.export_csv_checkbox)
        
        layout.addWidget(export_group)
        
        export_btn = QPushButton("💾 Export")
        export_btn.clicked.connect(self.export_all)
        layout.addWidget(export_btn)
        
        layout.addStretch()
        
        return panel
    
    def create_toolbar(self):
        """Create the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        open_action = QAction("📂 Open", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        pan_action = QAction("🖐 Pan", self)
        pan_action.triggered.connect(lambda: self.set_tool_mode(ToolMode.PAN))
        toolbar.addAction(pan_action)
        
        count_action = QAction("🔢 Count", self)
        count_action.triggered.connect(lambda: self.set_tool_mode(ToolMode.CELL_COUNT))
        toolbar.addAction(count_action)
        
        roi_action = QAction("✏️ ROI", self)
        roi_action.triggered.connect(lambda: self.set_tool_mode(ToolMode.ROI_DRAW))
        toolbar.addAction(roi_action)
        
        toolbar.addSeparator()
        
        adjust_action = QAction("🎨 Adjust", self)
        adjust_action.triggered.connect(self.show_adjustments_dialog)
        toolbar.addAction(adjust_action)
        
        toolbar.addSeparator()
        
        export_action = QAction("💾 Export", self)
        export_action.triggered.connect(self.export_all)
        toolbar.addAction(export_action)
        
        import_action = QAction("📥 Import", self)
        import_action.triggered.connect(self.import_coordinates_dialog)
        toolbar.addAction(import_action)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        shortcuts = {
            'R': self.toggle_red_channel,
            'G': self.toggle_green_channel,
            'B': self.toggle_blue_channel,
            'M': lambda: self.set_channel_mode(ChannelMode.MAGENTA),
            'C': lambda: self.set_channel_mode(ChannelMode.CYAN),
            'Y': lambda: self.set_channel_mode(ChannelMode.YELLOW),
            'A': lambda: self.set_channel_mode(ChannelMode.COMPOSITE),
            'Ctrl+O': self.open_file,
            'Ctrl+Z': self.undo_last_marker,
            'Ctrl+Shift+Z': self.redo_marker,
            'Ctrl+S': self.export_all,
            'Escape': self.cancel_roi,
            'Space': self.cycle_active_cell_type,
            'F': lambda: self.set_tool_mode(ToolMode.CELL_COUNT),
            'D': lambda: self.set_tool_mode(ToolMode.ROI_DRAW),
            'E': lambda: self.set_tool_mode(ToolMode.PAN),
            'V': self.canvas.reset_view,
            'Shift+D': self.start_new_roi,
        }
        
        for key, callback in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)
    
    def toggle_red_channel(self):
        self.red_checkbox.setChecked(not self.red_checkbox.isChecked())
    
    def toggle_green_channel(self):
        self.green_checkbox.setChecked(not self.green_checkbox.isChecked())
    
    def toggle_blue_channel(self):
        self.blue_checkbox.setChecked(not self.blue_checkbox.isChecked())
    
    def setup_default_cell_types(self):
        """Setup default cell types."""
        defaults = [
            CellType("Type 1", QColor(255, 100, 100), MarkerType.CIRCLE, 20),
            CellType("Type 2", QColor(100, 255, 100), MarkerType.CIRCLE, 20),
        ]
        
        for ct in defaults:
            self.cell_types[ct.name] = ct
            self.add_cell_type_widget(ct)
            self.active_cell_combo.addItem(ct.name)
        
        if defaults:
            self.current_cell_type = defaults[0].name
            self.active_cell_combo.setCurrentText(defaults[0].name)
    
    def add_cell_type_widget(self, cell_type: CellType):
        """Add a widget for a cell type."""
        widget = CellTypeWidget(cell_type)
        widget.type_changed.connect(self.refresh_markers)
        widget.name_change_requested.connect(self.handle_cell_type_rename)
        widget.delete_requested.connect(self.delete_cell_type)
        self.cell_type_layout.addWidget(widget)
    
    def delete_cell_type(self, name: str):
        """Delete a cell type."""
        if len(self.cell_types) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "At least one cell type must remain.")
            return
        
        # Remove markers of this type
        self.cell_markers = [m for m in self.cell_markers if m.cell_type != name]
        
        # Remove from cell_types dict
        if name in self.cell_types:
            del self.cell_types[name]
        
        # Remove widget
        for i in range(self.cell_type_layout.count()):
            widget = self.cell_type_layout.itemAt(i).widget()
            if isinstance(widget, CellTypeWidget) and widget.cell_type.name == name:
                self.cell_type_layout.removeWidget(widget)
                widget.deleteLater()
                break
        
        # Remove from combo
        index = self.active_cell_combo.findText(name)
        if index >= 0:
            self.active_cell_combo.removeItem(index)
        
        # Update current cell type if needed
        if self.current_cell_type == name:
            if self.cell_types:
                self.current_cell_type = list(self.cell_types.keys())[0]
                self.active_cell_combo.setCurrentText(self.current_cell_type)
            else:
                self.current_cell_type = None
        
        self.refresh_markers()
        self.update_results_table()
        self.status_bar.showMessage(f"Deleted cell type: {name}")
    
    def handle_cell_type_rename(self, old_name: str, new_name: str):
        """Handle cell type rename request."""
        if new_name in self.cell_types:
            QMessageBox.warning(self, "Name Exists", f"A cell type named '{new_name}' already exists.")
            for i in range(self.cell_type_layout.count()):
                widget = self.cell_type_layout.itemAt(i).widget()
                if isinstance(widget, CellTypeWidget) and widget.cell_type.name == old_name:
                    widget.update_name_display(old_name)
            return
        
        # Update cell type
        cell_type = self.cell_types.pop(old_name)
        cell_type.name = new_name
        self.cell_types[new_name] = cell_type
        
        # Update markers
        for marker in self.cell_markers:
            if marker.cell_type == old_name:
                marker.cell_type = new_name
        
        # Update combo
        index = self.active_cell_combo.findText(old_name)
        if index >= 0:
            self.active_cell_combo.setItemText(index, new_name)
        
        if self.current_cell_type == old_name:
            self.current_cell_type = new_name
        
        self.refresh_markers()
        self.update_results_table()
    
    def apply_dark_theme(self):
        """Apply dark theme to the application."""
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #2b2b2b; color: #ffffff; }
            QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 10px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton { background-color: #3c3c3c; border: 1px solid #555; border-radius: 4px; padding: 5px 10px; }
            QPushButton:hover { background-color: #4a4a4a; }
            QPushButton:pressed { background-color: #555555; }
            QPushButton:checked { background-color: #0078d4; }
            QComboBox, QLineEdit { background-color: #3c3c3c; border: 1px solid #555; border-radius: 3px; padding: 3px; }
            QSpinBox, QDoubleSpinBox { 
                background-color: #3c3c3c; 
                border: 1px solid #555; 
                border-radius: 3px; 
                padding: 3px;
                padding-right: 20px;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                height: 12px;
                border-left: 1px solid #555;
                border-bottom: 1px solid #555;
                border-top-right-radius: 3px;
                background-color: #4a4a4a;
            }
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
                background-color: #5a5a5a;
            }
            QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {
                background-color: #666666;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                height: 12px;
                border-left: 1px solid #555;
                border-bottom-right-radius: 3px;
                background-color: #4a4a4a;
            }
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #5a5a5a;
            }
            QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
                background-color: #666666;
            }
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
                width: 10px;
                height: 10px;
            }
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                width: 10px;
                height: 10px;
            }
            QListWidget, QTableWidget { background-color: #3c3c3c; border: 1px solid #555; }
            QScrollArea { border: none; }
            QToolBar { background-color: #2b2b2b; border: none; spacing: 5px; padding: 5px; }
            QStatusBar { background-color: #2b2b2b; }
            QSlider::groove:horizontal { height: 6px; background: #3c3c3c; border-radius: 3px; }
            QSlider::handle:horizontal { width: 14px; margin: -4px 0; background: #0078d4; border-radius: 7px; }
        """)
    
    def show_adjustments_dialog(self):
        """Show the image adjustments dialog."""
        if self.adjustments_dialog is None or not self.adjustments_dialog.isVisible():
            self.adjustments_dialog = AdjustmentsDialog(self.image_adjustments, self)
            self.adjustments_dialog.adjustments_changed.connect(self.on_adjustments_changed)
            self.adjustments_dialog.show()
        else:
            self.adjustments_dialog.raise_()
            self.adjustments_dialog.activateWindow()
    
    def on_adjustments_changed(self):
        """Handle adjustments change."""
        self.update_display()
    
    def on_channel_checkbox_changed(self):
        """Handle channel checkbox state changes."""
        self.channel_r_enabled = self.red_checkbox.isChecked()
        self.channel_g_enabled = self.green_checkbox.isChecked()
        self.channel_b_enabled = self.blue_checkbox.isChecked()
        self.update_channel_label()
        self.update_display()
    
    def channel_combo_changed(self, index):
        """Handle channel combo change."""
        mode = self.channel_combo.currentData()
        if mode:
            self.set_channel_mode(mode)
    
    def set_channel_mode(self, mode: ChannelMode):
        """Set the channel display mode."""
        self.channel_mode = mode
        self.channel_combo.blockSignals(True)
        self.channel_combo.setCurrentText(mode.name.capitalize())
        self.channel_combo.blockSignals(False)
        
        self.red_checkbox.blockSignals(True)
        self.green_checkbox.blockSignals(True)
        self.blue_checkbox.blockSignals(True)
        
        if mode == ChannelMode.COMPOSITE:
            self.red_checkbox.setChecked(True)
            self.green_checkbox.setChecked(True)
            self.blue_checkbox.setChecked(True)
        elif mode == ChannelMode.RED:
            self.red_checkbox.setChecked(True)
            self.green_checkbox.setChecked(False)
            self.blue_checkbox.setChecked(False)
        elif mode == ChannelMode.GREEN:
            self.red_checkbox.setChecked(False)
            self.green_checkbox.setChecked(True)
            self.blue_checkbox.setChecked(False)
        elif mode == ChannelMode.BLUE:
            self.red_checkbox.setChecked(False)
            self.green_checkbox.setChecked(False)
            self.blue_checkbox.setChecked(True)
        elif mode == ChannelMode.CYAN:
            self.red_checkbox.setChecked(False)
            self.green_checkbox.setChecked(True)
            self.blue_checkbox.setChecked(True)
        elif mode == ChannelMode.MAGENTA:
            self.red_checkbox.setChecked(True)
            self.green_checkbox.setChecked(False)
            self.blue_checkbox.setChecked(True)
        elif mode == ChannelMode.YELLOW:
            self.red_checkbox.setChecked(True)
            self.green_checkbox.setChecked(True)
            self.blue_checkbox.setChecked(False)
        
        self.red_checkbox.blockSignals(False)
        self.green_checkbox.blockSignals(False)
        self.blue_checkbox.blockSignals(False)
        
        self.channel_r_enabled = self.red_checkbox.isChecked()
        self.channel_g_enabled = self.green_checkbox.isChecked()
        self.channel_b_enabled = self.blue_checkbox.isChecked()
        
        self.update_channel_label()
        self.update_display()
    
    def update_channel_label(self):
        """Update the channel label."""
        channels = []
        if self.channel_r_enabled:
            channels.append("R")
        if self.channel_g_enabled:
            channels.append("G")
        if self.channel_b_enabled:
            channels.append("B")
        
        if channels:
            self.channel_label.setText(f"Active: {''.join(channels)}")
        else:
            self.channel_label.setText("Active: None")
    
    def set_tool_mode(self, mode: ToolMode):
        """Set the current tool mode."""
        self.canvas.set_tool_mode(mode)
        
        self.pan_btn.setChecked(mode == ToolMode.PAN)
        self.count_btn.setChecked(mode == ToolMode.CELL_COUNT)
        self.roi_btn.setChecked(mode == ToolMode.ROI_DRAW)
        
        mode_names = {ToolMode.PAN: "Pan", ToolMode.CELL_COUNT: "Count", ToolMode.ROI_DRAW: "ROI"}
        self.status_bar.showMessage(f"Mode: {mode_names[mode]}")
    
    def cycle_active_cell_type(self):
        """Cycle through available cell types."""
        if not self.cell_types:
            return
        
        type_names = list(self.cell_types.keys())
        if not type_names:
            return
        
        if self.current_cell_type in type_names:
            current_index = type_names.index(self.current_cell_type)
            next_index = (current_index + 1) % len(type_names)
        else:
            next_index = 0
        
        next_type = type_names[next_index]
        self.current_cell_type = next_type
        self.active_cell_combo.setCurrentText(next_type)
        self.status_bar.showMessage(f"Active cell type: {next_type}")
    
    def set_active_cell_type(self, name: str):
        """Set the active cell type."""
        self.current_cell_type = name
    
    def add_cell_type(self):
        """Add a new cell type."""
        name, ok = QInputDialog.getText(self, "New Cell Type", "Enter name:")
        if ok and name:
            if name in self.cell_types:
                QMessageBox.warning(self, "Exists", "Cell type already exists.")
                return
            
            color = QColorDialog.getColor(QColor(255, 255, 255), self)
            if color.isValid():
                ct = CellType(name, color, MarkerType.CIRCLE, 20)
                self.cell_types[name] = ct
                self.add_cell_type_widget(ct)
                self.active_cell_combo.addItem(name)
                self.current_cell_type = name
                self.active_cell_combo.setCurrentText(name)
    
    def open_file(self):
        """Open a file dialog to select an image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image",
            "", "Image Files (*.tif *.tiff *.png *.jpg *.jpeg);;All Files (*)"
        )
        if file_path:
            self.load_image(file_path)
    
    def browse_output_dir(self):
        """Browse for output directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory",
            self.output_dir_edit.text() or (str(Path(self.current_file).parent) if self.current_file else "")
        )
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def load_image(self, file_path: str):
        """Load an image file."""
        try:
            path = Path(file_path)
            
            # Save ROI names
            for roi in self.rois:
                if roi.name and roi.name not in self.roi_name_history:
                    self.roi_name_history.append(roi.name)
            
            # Reset markers and ROIs
            self.cell_markers.clear()
            self.undo_stack.clear()
            self.rois.clear()
            self.current_roi = None
            self.roi_list.clear()
            self.marker_items.clear()
            self.roi_items.clear()
            self.selected_marker_index = -1
            
            # Reset channels to all enabled
            self.red_checkbox.blockSignals(True)
            self.green_checkbox.blockSignals(True)
            self.blue_checkbox.blockSignals(True)
            self.red_checkbox.setChecked(True)
            self.green_checkbox.setChecked(True)
            self.blue_checkbox.setChecked(True)
            self.red_checkbox.blockSignals(False)
            self.green_checkbox.blockSignals(False)
            self.blue_checkbox.blockSignals(False)
            self.channel_r_enabled = True
            self.channel_g_enabled = True
            self.channel_b_enabled = True
            self.update_channel_label()
            
            # Reset adjustments if not preserving
            if not self.preserve_adjustments_on_load:
                self.image_adjustments.reset_all()
                if self.adjustments_dialog and self.adjustments_dialog.isVisible():
                    self.adjustments_dialog.load_values()
            
            if path.suffix.lower() in ('.tif', '.tiff') and HAS_TIFF:
                self.image_data = tifffile.imread(file_path)
                
                if self.image_data.ndim == 2:
                    self.image_data = np.stack([self.image_data] * 3, axis=-1)
                elif self.image_data.ndim == 3:
                    if self.image_data.shape[0] in (3, 4):
                        self.image_data = np.transpose(self.image_data, (1, 2, 0))
                    elif self.image_data.shape[2] not in (3, 4):
                        if self.image_data.shape[2] >= 3:
                            self.image_data = self.image_data[:, :, :3]
                        else:
                            padded = np.zeros((*self.image_data.shape[:2], 3), dtype=self.image_data.dtype)
                            padded[:, :, :self.image_data.shape[2]] = self.image_data
                            self.image_data = padded
            else:
                img = Image.open(file_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                self.image_data = np.array(img)
            
            if self.image_data.dtype != np.uint8:
                if self.image_data.max() > 255:
                    self.image_data = ((self.image_data - self.image_data.min()) / 
                                      (self.image_data.max() - self.image_data.min()) * 255).astype(np.uint8)
                else:
                    self.image_data = self.image_data.astype(np.uint8)
            
            self.current_file = file_path
            self.update_display(reset_view=True)
            self.update_image_info()
            self.update_results_table()
            self.status_bar.showMessage(f"Loaded: {path.name}")
            
            # Restore focus to main window for shortcuts to work
            self.activateWindow()
            self.setFocus()
            
            # Check for existing coordinate file
            coord_file = path.parent / f"{path.stem}_coordinates.json"
            if coord_file.exists():
                reply = QMessageBox.question(
                    self, "Load Coordinates",
                    f"Found coordinate data for this image:\n{coord_file.name}\n\nLoad markers and ROIs?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.import_coordinates(str(coord_file))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image:\n{str(e)}")
    
    def update_display(self, reset_view: bool = False):
        """Update the image display."""
        if self.image_data is None:
            return
        
        # Apply image adjustments
        adjusted_data = apply_all_adjustments(self.image_data, self.image_adjustments)
        
        # Apply channel mode
        display_data = self.apply_channel_mode(adjusted_data)
        
        # Convert to QImage
        height, width = display_data.shape[:2]
        if display_data.ndim == 3 and display_data.shape[2] == 3:
            bytes_per_line = 3 * width
            qimage = QImage(display_data.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        else:
            bytes_per_line = width
            qimage = QImage(display_data.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
        
        pixmap = QPixmap.fromImage(qimage)
        
        self.marker_items.clear()
        self.roi_items.clear()
        
        if reset_view:
            self.canvas.set_image(pixmap)
        else:
            self.canvas.update_pixmap(pixmap)
        
        self.refresh_markers()
        self.refresh_rois()
    
    def apply_channel_mode(self, data: np.ndarray) -> np.ndarray:
        """Apply channel mode to image data."""
        if data.ndim != 3 or data.shape[2] < 3:
            return data
        
        r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
        result = np.zeros_like(data)
        
        if self.channel_r_enabled:
            result[:, :, 0] = r
        if self.channel_g_enabled:
            result[:, :, 1] = g
        if self.channel_b_enabled:
            result[:, :, 2] = b
        
        return result
    
    def update_image_info(self):
        """Update image info label."""
        if self.image_data is not None:
            h, w = self.image_data.shape[:2]
            channels = self.image_data.shape[2] if self.image_data.ndim == 3 else 1
            dtype = self.image_data.dtype
            self.info_label.setText(f"Size: {w} x {h}\nChannels: {channels}\nType: {dtype}")
            self.file_label.setText(Path(self.current_file).name if self.current_file else "Unknown")
        else:
            self.info_label.setText("No image loaded")
            self.file_label.setText("No file loaded")
    
    def add_cell_marker(self, pos: QPointF):
        """Add a cell marker."""
        if not self.current_cell_type or self.current_cell_type not in self.cell_types:
            self.status_bar.showMessage("Please select a cell type first")
            return
        
        self.undo_stack.clear()
        
        roi_name = None
        for roi in self.rois:
            if roi.closed:
                polygon = QPolygonF([QPointF(*p) for p in roi.points])
                if polygon.containsPoint(pos, Qt.FillRule.OddEvenFill):
                    roi_name = roi.name
                    break
        
        type_markers = [m for m in self.cell_markers if m.cell_type == self.current_cell_type]
        marker_number = len(type_markers) + 1
        
        marker = CellMarker(pos, self.current_cell_type, marker_number, roi_name)
        self.cell_markers.append(marker)
        
        self.refresh_markers()
        self.update_results_table()
        self.status_bar.showMessage(f"Added {self.current_cell_type} marker #{marker_number}")
    
    def refresh_markers(self):
        """Refresh all marker displays."""
        for item in self.marker_items:
            try:
                if item.scene() is not None:
                    self.canvas.scene.removeItem(item)
            except RuntimeError:
                pass
        self.marker_items.clear()
        
        type_counts = {name: 0 for name in self.cell_types}
        
        for idx, marker in enumerate(self.cell_markers):
            if marker.cell_type not in self.cell_types:
                continue
            
            cell_type = self.cell_types[marker.cell_type]
            type_counts[marker.cell_type] += 1
            
            pos = marker.position
            size = cell_type.marker_size
            color = cell_type.color
            
            # Highlight selected marker
            is_selected = (idx == self.selected_marker_index)
            
            pen = QPen(color)
            pen.setWidth(3 if is_selected else 2)
            if is_selected:
                pen.setStyle(Qt.PenStyle.DashLine)
            brush = QBrush(QColor(color.red(), color.green(), color.blue(), 80 if is_selected else 50))
            
            if cell_type.marker_type == MarkerType.DOT:
                item = QGraphicsEllipseItem(pos.x() - 3, pos.y() - 3, 6, 6)
                item.setPen(pen)
                item.setBrush(QBrush(color))
            elif cell_type.marker_type == MarkerType.CIRCLE:
                item = QGraphicsEllipseItem(
                    pos.x() - size/2, pos.y() - size/2, size, size
                )
                item.setPen(pen)
                item.setBrush(brush)
            else:
                from PyQt6.QtWidgets import QGraphicsRectItem
                item = QGraphicsRectItem(
                    pos.x() - size/2, pos.y() - size/2, size, size
                )
                item.setPen(pen)
                item.setBrush(brush)
            
            self.canvas.scene.addItem(item)
            self.marker_items.append(item)
            
            # Calculate label position based on cell type setting
            font = QFont("Arial", 12, QFont.Weight.Bold)
            text_item = QGraphicsTextItem(str(marker.marker_number))
            text_item.setDefaultTextColor(color)
            text_item.setFont(font)
            
            # Get text bounds for positioning
            text_bounds = text_item.boundingRect()
            tw, th = text_bounds.width(), text_bounds.height()
            
            label_pos = cell_type.label_position
            if label_pos == LabelPosition.RIGHT:
                text_x = pos.x() + size/2 + 2
                text_y = pos.y() - th/2
            elif label_pos == LabelPosition.LEFT:
                text_x = pos.x() - size/2 - tw - 2
                text_y = pos.y() - th/2
            elif label_pos == LabelPosition.TOP:
                text_x = pos.x() - tw/2
                text_y = pos.y() - size/2 - th - 2
            elif label_pos == LabelPosition.BOTTOM:
                text_x = pos.x() - tw/2
                text_y = pos.y() + size/2 + 2
            elif label_pos == LabelPosition.TOP_RIGHT:
                text_x = pos.x() + size/2 + 2
                text_y = pos.y() - size/2 - th
            elif label_pos == LabelPosition.TOP_LEFT:
                text_x = pos.x() - size/2 - tw - 2
                text_y = pos.y() - size/2 - th
            elif label_pos == LabelPosition.BOTTOM_RIGHT:
                text_x = pos.x() + size/2 + 2
                text_y = pos.y() + size/2
            elif label_pos == LabelPosition.BOTTOM_LEFT:
                text_x = pos.x() - size/2 - tw - 2
                text_y = pos.y() + size/2
            else:
                text_x = pos.x() + size/2 + 2
                text_y = pos.y() - th/2
            
            text_item.setPos(text_x, text_y)
            self.canvas.scene.addItem(text_item)
            self.marker_items.append(text_item)
        
        for i in range(self.cell_type_layout.count()):
            widget = self.cell_type_layout.itemAt(i).widget()
            if isinstance(widget, CellTypeWidget):
                count = type_counts.get(widget.cell_type.name, 0)
                widget.update_count(count)
    
    def undo_last_marker(self):
        """Remove the last added marker."""
        if self.cell_markers:
            marker = self.cell_markers.pop()
            self.undo_stack.append(marker)
            self.refresh_markers()
            self.update_results_table()
            self.status_bar.showMessage(f"Removed {marker.cell_type} marker #{marker.marker_number}")
    
    def redo_marker(self):
        """Redo the last undone marker."""
        if self.undo_stack:
            marker = self.undo_stack.pop()
            self.cell_markers.append(marker)
            self.refresh_markers()
            self.update_results_table()
            self.status_bar.showMessage(f"Restored {marker.cell_type} marker #{marker.marker_number}")
    
    def find_marker_at(self, pos: QPointF) -> int:
        """Find marker at position."""
        threshold = 15
        for idx, marker in enumerate(self.cell_markers):
            dist = ((pos.x() - marker.position.x()) ** 2 + 
                    (pos.y() - marker.position.y()) ** 2) ** 0.5
            if dist < threshold:
                return idx
        return -1
    
    def move_marker(self, marker_idx: int, new_pos: QPointF):
        """Move a marker."""
        if 0 <= marker_idx < len(self.cell_markers):
            marker = self.cell_markers[marker_idx]
            marker.position = new_pos
            
            marker.roi_name = None
            for roi in self.rois:
                if roi.closed:
                    polygon = QPolygonF([QPointF(*p) for p in roi.points])
                    if polygon.containsPoint(new_pos, Qt.FillRule.OddEvenFill):
                        marker.roi_name = roi.name
                        break
            
            self.refresh_markers()
            self.update_results_table()
    
    def select_marker(self, marker_idx: int):
        """Select a marker for potential deletion."""
        self.selected_marker_index = marker_idx
        if marker_idx >= 0:
            marker = self.cell_markers[marker_idx]
            self.status_bar.showMessage(
                f"Selected {marker.cell_type} marker #{marker.marker_number} - Press Delete or Backspace to remove"
            )
        self.refresh_markers()
    
    def delete_selected_marker(self):
        """Delete the currently selected marker."""
        if 0 <= self.selected_marker_index < len(self.cell_markers):
            marker = self.cell_markers.pop(self.selected_marker_index)
            self.undo_stack.append(marker)
            self.status_bar.showMessage(f"Deleted {marker.cell_type} marker #{marker.marker_number}")
            self.selected_marker_index = -1
            
            # Renumber remaining markers of the same type
            type_num = 1
            for m in self.cell_markers:
                if m.cell_type == marker.cell_type:
                    m.marker_number = type_num
                    type_num += 1
            
            self.refresh_markers()
            self.update_results_table()
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            if self.selected_marker_index >= 0:
                self.delete_selected_marker()
                return
        super().keyPressEvent(event)
    
    def clear_all_markers(self):
        """Clear all markers."""
        reply = QMessageBox.question(
            self, "Confirm Clear",
            "Are you sure you want to clear all markers?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.cell_markers.clear()
            self.undo_stack.clear()
            self.refresh_markers()
            self.update_results_table()
            self.status_bar.showMessage("Cleared all markers")
    
    def start_new_roi(self):
        """Start drawing a new ROI."""
        if self.roi_name_history:
            dialog = QDialog(self)
            dialog.setWindowTitle("New ROI")
            dialog.setMinimumWidth(300)
            layout = QVBoxLayout(dialog)
            layout.setSpacing(10)
            
            label = QLabel("Enter ROI name or select from history:")
            layout.addWidget(label)
            
            combo = QComboBox()
            combo.setEditable(True)
            combo.setMinimumHeight(28)
            combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            combo.setStyleSheet("""
                QComboBox { padding: 4px 8px; border: 1px solid #555; border-radius: 4px; background: #3c3c3c; }
                QComboBox::drop-down { width: 24px; border-left: 1px solid #555; background: #4a4a4a; }
                QComboBox QAbstractItemView { background: #3c3c3c; border: 1px solid #555; selection-background-color: #0078d4; }
            """)
            
            for name in reversed(self.roi_name_history):
                combo.addItem(name)
            
            if self.roi_name_history:
                combo.setCurrentText(self.roi_name_history[-1])
                combo.lineEdit().selectAll()
            
            layout.addWidget(combo)
            
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            combo.setFocus()
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                name = combo.currentText().strip()
                if name:
                    self._create_roi(name)
        else:
            name, ok = QInputDialog.getText(self, "New ROI", "Enter ROI name:")
            if ok and name:
                self._create_roi(name)
    
    def _create_roi(self, name: str):
        """Create a new ROI."""
        style = self.roi_color_btn.styleSheet()
        color_str = style.split("background-color:")[1].split(";")[0].strip()
        color = QColor(color_str)
        line_width = self.roi_width_spin.value()
        
        self.current_roi = ROI(name, color=color, line_width=line_width)
        self.rois.append(self.current_roi)
        self.set_tool_mode(ToolMode.ROI_DRAW)
        self.canvas.last_roi_point = None
        self.status_bar.showMessage(f"Drawing ROI: {name} - Left-click to add points, Right-click to close")
    
    def add_roi_point(self, pos: QPointF):
        """Add a point to the current ROI."""
        if self.current_roi:
            self.current_roi.points.append((pos.x(), pos.y()))
            self.canvas.set_last_roi_point(pos)
            self.refresh_rois()
            self.status_bar.showMessage(f"ROI: {self.current_roi.name} - {len(self.current_roi.points)} points")
    
    def close_current_roi(self):
        """Close the current ROI."""
        if self.current_roi and len(self.current_roi.points) >= 3:
            self.current_roi.closed = True
            self.roi_list.addItem(self.current_roi.name)
            self.current_roi = None
            self.canvas.clear_temp_line()
            self.canvas.last_roi_point = None
            self.set_tool_mode(ToolMode.ROI_DRAW)
            self.refresh_rois()
            self.update_results_table()
            self.status_bar.showMessage("ROI closed")
        elif self.current_roi:
            self.status_bar.showMessage(f"ROI needs at least 3 points")
    
    def cancel_roi(self):
        """Cancel the current ROI."""
        if self.current_roi:
            self.rois.remove(self.current_roi)
            self.current_roi = None
            self.canvas.clear_temp_line()
            self.canvas.last_roi_point = None
            self.set_tool_mode(ToolMode.PAN)
            self.refresh_rois()
            self.status_bar.showMessage("ROI cancelled")
    
    def refresh_rois(self):
        """Refresh ROI display."""
        for item in self.roi_items:
            try:
                if item.scene() is not None:
                    self.canvas.scene.removeItem(item)
            except RuntimeError:
                pass
        self.roi_items.clear()
        
        for roi in self.rois:
            if not roi.points:
                continue
            
            pen = QPen(roi.color)
            pen.setWidth(roi.line_width)
            
            num_points = len(roi.points)
            if num_points >= 2:
                for i in range(num_points - 1):
                    p1 = roi.points[i]
                    p2 = roi.points[i + 1]
                    line = self.canvas.scene.addLine(p1[0], p1[1], p2[0], p2[1], pen)
                    self.roi_items.append(line)
                
                if roi.closed and num_points >= 3:
                    p1 = roi.points[-1]
                    p2 = roi.points[0]
                    line = self.canvas.scene.addLine(p1[0], p1[1], p2[0], p2[1], pen)
                    self.roi_items.append(line)
            
            vertex_size = 10
            for px, py in roi.points:
                vertex = QGraphicsEllipseItem(
                    px - vertex_size/2, py - vertex_size/2, vertex_size, vertex_size
                )
                vertex.setPen(pen)
                vertex.setBrush(QBrush(roi.color))
                self.canvas.scene.addItem(vertex)
                self.roi_items.append(vertex)
            
            if roi.points:
                first_point = roi.points[0]
                text = QGraphicsTextItem(roi.name)
                text.setDefaultTextColor(roi.color)
                text.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                text.setPos(first_point[0], first_point[1] - 20)
                self.canvas.scene.addItem(text)
                self.roi_items.append(text)
    
    def find_roi_vertex_at(self, pos: QPointF) -> tuple:
        """Find ROI vertex at position."""
        threshold = 15
        for roi_idx, roi in enumerate(self.rois):
            if roi.closed:
                for vertex_idx, (px, py) in enumerate(roi.points):
                    dist = ((pos.x() - px) ** 2 + (pos.y() - py) ** 2) ** 0.5
                    if dist < threshold:
                        return (roi_idx, vertex_idx)
        return (-1, -1)
    
    def find_roi_at(self, pos: QPointF) -> int:
        """Find ROI containing position."""
        for idx, roi in enumerate(self.rois):
            if roi.closed:
                polygon = QPolygonF([QPointF(*p) for p in roi.points])
                if polygon.containsPoint(pos, Qt.FillRule.OddEvenFill):
                    return idx
        return -1
    
    def move_roi_vertex(self, roi_idx: int, vertex_idx: int, new_pos: QPointF):
        """Move an ROI vertex."""
        if 0 <= roi_idx < len(self.rois):
            roi = self.rois[roi_idx]
            if 0 <= vertex_idx < len(roi.points):
                roi.points[vertex_idx] = (new_pos.x(), new_pos.y())
                self.refresh_rois()
    
    def move_roi(self, roi_idx: int, delta: QPointF):
        """Move an entire ROI."""
        if 0 <= roi_idx < len(self.rois):
            roi = self.rois[roi_idx]
            roi.points = [(px + delta.x(), py + delta.y()) for px, py in roi.points]
            self.refresh_rois()
    
    def rename_roi(self, item: QListWidgetItem):
        """Rename an ROI."""
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "Rename ROI", "Enter new name:", text=old_name)
        if ok and new_name and new_name != old_name:
            for roi in self.rois:
                if roi.name == old_name:
                    roi.name = new_name
                    item.setText(new_name)
                    for marker in self.cell_markers:
                        if marker.roi_name == old_name:
                            marker.roi_name = new_name
                    self.refresh_rois()
                    self.update_results_table()
                    break
    
    def on_roi_selected(self, item: QListWidgetItem):
        """Handle ROI selection."""
        for roi in self.rois:
            if roi.name == item.text():
                self.roi_color_btn.setStyleSheet(
                    f"background-color: {roi.color.name()}; border: 1px solid #555; border-radius: 3px;"
                )
                self.roi_width_spin.blockSignals(True)
                self.roi_width_spin.setValue(roi.line_width)
                self.roi_width_spin.blockSignals(False)
                break
    
    def change_roi_color(self):
        """Change ROI color."""
        current_color = QColor(255, 255, 0)
        current_item = self.roi_list.currentItem()
        if current_item:
            for roi in self.rois:
                if roi.name == current_item.text():
                    current_color = roi.color
                    break
        
        color = QColorDialog.getColor(current_color, self, "Select ROI Color")
        if color.isValid():
            self.roi_color_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #555; border-radius: 3px;"
            )
            if current_item:
                for roi in self.rois:
                    if roi.name == current_item.text():
                        roi.color = color
                        self.refresh_rois()
                        break
    
    def change_roi_width(self, width: int):
        """Change ROI width."""
        current_item = self.roi_list.currentItem()
        if current_item:
            for roi in self.rois:
                if roi.name == current_item.text():
                    roi.line_width = width
                    self.refresh_rois()
                    break
    
    def roi_context_menu(self, pos):
        """Show ROI context menu."""
        item = self.roi_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            rename_action = menu.addAction("Rename")
            delete_action = menu.addAction("Delete")
            
            action = menu.exec(self.roi_list.mapToGlobal(pos))
            if action == rename_action:
                self.rename_roi(item)
            elif action == delete_action:
                self.delete_roi(item.text())
    
    def delete_selected_roi(self):
        """Delete selected ROI."""
        current = self.roi_list.currentItem()
        if current:
            self.delete_roi(current.text())
    
    def delete_roi(self, name: str):
        """Delete an ROI by name."""
        for roi in self.rois[:]:
            if roi.name == name:
                self.rois.remove(roi)
                for i in range(self.roi_list.count()):
                    if self.roi_list.item(i).text() == name:
                        self.roi_list.takeItem(i)
                        break
                for marker in self.cell_markers:
                    if marker.roi_name == name:
                        marker.roi_name = None
                self.refresh_rois()
                self.update_results_table()
                break
    
    def update_results_table(self):
        """Update results table."""
        markers_in_roi = [m for m in self.cell_markers if m.roi_name]
        
        results = {}
        for marker in markers_in_roi:
            key = (marker.cell_type, marker.roi_name)
            results[key] = results.get(key, 0) + 1
        
        self.results_table.setRowCount(len(results))
        for i, ((cell_type, roi_name), count) in enumerate(sorted(results.items())):
            self.results_table.setItem(i, 0, QTableWidgetItem(cell_type))
            self.results_table.setItem(i, 1, QTableWidgetItem(roi_name))
            self.results_table.setItem(i, 2, QTableWidgetItem(str(count)))
    
    def export_csv(self):
        """Export results to CSV."""
        markers_in_roi = [m for m in self.cell_markers if m.roi_name]
        closed_rois = [roi for roi in self.rois if roi.closed]
        
        if not closed_rois:
            QMessageBox.warning(self, "No Data", "No closed ROIs to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    image_name = Path(self.current_file).name if self.current_file else "Unknown"
                    
                    # Write marker details section
                    writer.writerow(["=== Marker Details ==="])
                    writer.writerow(["Image", "Cell Type", "Marker #", "X", "Y", "ROI"])
                    for marker in markers_in_roi:
                        writer.writerow([
                            image_name, marker.cell_type, marker.marker_number,
                            f"{marker.position.x():.2f}", f"{marker.position.y():.2f}",
                            marker.roi_name
                        ])
                    
                    # Write summary section with all combinations (including zeros)
                    writer.writerow([])  # Empty row separator
                    writer.writerow(["=== Summary (per ROI) ==="])
                    writer.writerow(["Image", "ROI", "Cell Type", "Count"])
                    
                    for roi in closed_rois:
                        for cell_type_name in self.cell_types.keys():
                            count = sum(1 for m in markers_in_roi 
                                       if m.roi_name == roi.name and m.cell_type == cell_type_name)
                            writer.writerow([image_name, roi.name, cell_type_name, count])
                
                self.status_bar.showMessage(f"Exported to {file_path}")
                return file_path
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")
        return None
    
    def export_image(self, base_path: str) -> Optional[str]:
        """Export overlay image."""
        if self.image_data is None:
            return None
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            adjusted_data = apply_all_adjustments(self.image_data, self.image_adjustments)
            img_data = adjusted_data.copy()
            
            if img_data.ndim == 2:
                img_data = np.stack([img_data] * 3, axis=-1)
            elif img_data.shape[2] == 4:
                img_data = img_data[:, :, :3]
            
            img = Image.fromarray(img_data, 'RGB')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
            except:
                font = ImageFont.load_default()
                small_font = font
            
            for roi in self.rois:
                if roi.closed and len(roi.points) >= 3:
                    color = (roi.color.red(), roi.color.green(), roi.color.blue())
                    points = [(int(p[0]), int(p[1])) for p in roi.points]
                    
                    for i in range(len(points)):
                        p1 = points[i]
                        p2 = points[(i + 1) % len(points)]
                        draw.line([p1, p2], fill=color, width=roi.line_width)
                    
                    draw.text((points[0][0], points[0][1] - 15), roi.name, fill=color, font=small_font)
            
            for marker in self.cell_markers:
                if marker.cell_type in self.cell_types:
                    cell_type = self.cell_types[marker.cell_type]
                    color = (cell_type.color.red(), cell_type.color.green(), cell_type.color.blue())
                    pos = (int(marker.position.x()), int(marker.position.y()))
                    size = cell_type.marker_size // 2
                    
                    if cell_type.marker_type == MarkerType.DOT:
                        draw.ellipse([pos[0]-3, pos[1]-3, pos[0]+3, pos[1]+3], fill=color)
                    elif cell_type.marker_type == MarkerType.CIRCLE:
                        draw.ellipse([pos[0]-size, pos[1]-size, pos[0]+size, pos[1]+size], outline=color, width=2)
                    else:
                        draw.rectangle([pos[0]-size, pos[1]-size, pos[0]+size, pos[1]+size], outline=color, width=2)
                    
                    draw.text((pos[0] + size + 2, pos[1] - size), str(marker.marker_number), fill=color, font=font)
            
            output_path = f"{base_path}_overlay.png"
            img.save(output_path, 'PNG', optimize=True)
            return output_path
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export image: {e}")
            return None
    
    def export_json(self, base_path: str) -> Optional[str]:
        """Export coordinates to JSON."""
        try:
            data = {
                "image": Path(self.current_file).name if self.current_file else "Unknown",
                "image_size": {
                    "width": self.image_data.shape[1] if self.image_data is not None else 0,
                    "height": self.image_data.shape[0] if self.image_data is not None else 0
                },
                "adjustments": {
                    "brightness": {"r": self.image_adjustments.brightness_r, 
                                   "g": self.image_adjustments.brightness_g, 
                                   "b": self.image_adjustments.brightness_b},
                    "contrast": {"r": self.image_adjustments.contrast_r, 
                                 "g": self.image_adjustments.contrast_g, 
                                 "b": self.image_adjustments.contrast_b},
                    "noise_reduction": {"r": self.image_adjustments.noise_r,
                                        "g": self.image_adjustments.noise_g,
                                        "b": self.image_adjustments.noise_b}
                },
                "rois": [],
                "markers": [],
                "summary": {}
            }
            
            for roi in self.rois:
                if roi.closed:
                    roi_data = {
                        "name": roi.name,
                        "color": roi.color.name(),
                        "line_width": roi.line_width,
                        "points": [{"x": p[0], "y": p[1]} for p in roi.points]
                    }
                    data["rois"].append(roi_data)
            
            markers_in_roi = [m for m in self.cell_markers if m.roi_name]
            for marker in markers_in_roi:
                marker_data = {
                    "cell_type": marker.cell_type,
                    "marker_number": marker.marker_number,
                    "x": marker.position.x(),
                    "y": marker.position.y(),
                    "roi": marker.roi_name
                }
                data["markers"].append(marker_data)
            
            for cell_type in self.cell_types:
                data["summary"][cell_type] = {}
                for roi in self.rois:
                    if roi.closed:
                        count = sum(1 for m in markers_in_roi 
                                   if m.cell_type == cell_type and m.roi_name == roi.name)
                        data["summary"][cell_type][roi.name] = count
            
            output_path = f"{base_path}_coordinates.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return output_path
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export JSON: {e}")
            return None
    
    def export_all(self):
        """Export all selected formats."""
        markers_in_roi = [m for m in self.cell_markers if m.roi_name]
        closed_rois = [roi for roi in self.rois if roi.closed]
        
        if not closed_rois:
            QMessageBox.warning(self, "No Data", "No closed ROIs to export.")
            return
        
        if not self.current_file:
            QMessageBox.warning(self, "No Image", "Please load an image first.")
            return
        
        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            output_dir = str(Path(self.current_file).parent)
        
        base_name = Path(self.current_file).stem
        base_path = str(Path(output_dir) / base_name)
        
        exported_files = []
        
        if self.export_csv_checkbox.isChecked():
            csv_path = f"{base_path}_results.csv"
            try:
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    image_name = Path(self.current_file).name
                    
                    # Write marker details section
                    writer.writerow(["=== Marker Details ==="])
                    writer.writerow(["Image", "Cell Type", "Marker #", "X", "Y", "ROI"])
                    for marker in markers_in_roi:
                        writer.writerow([
                            image_name, marker.cell_type, marker.marker_number,
                            f"{marker.position.x():.2f}", f"{marker.position.y():.2f}",
                            marker.roi_name
                        ])
                    
                    # Write summary section with all combinations (including zeros)
                    writer.writerow([])  # Empty row separator
                    writer.writerow(["=== Summary (per ROI) ==="])
                    writer.writerow(["Image", "ROI", "Cell Type", "Count"])
                    
                    for roi in closed_rois:
                        for cell_type_name in self.cell_types.keys():
                            count = sum(1 for m in markers_in_roi 
                                       if m.roi_name == roi.name and m.cell_type == cell_type_name)
                            writer.writerow([image_name, roi.name, cell_type_name, count])
                    
                exported_files.append(csv_path)
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Failed to export CSV: {e}")
        
        if self.export_json_checkbox.isChecked():
            json_path = self.export_json(base_path)
            if json_path:
                exported_files.append(json_path)
        
        if self.export_image_checkbox.isChecked() and self.image_data is not None:
            img_path = self.export_image(base_path)
            if img_path:
                exported_files.append(img_path)
        
        if exported_files:
            self.status_bar.showMessage(f"Exported {len(exported_files)} file(s)")
            self.show_auto_dismiss_message(
                "Export Complete", 
                f"Exported {len(exported_files)} file(s):\n" + "\n".join([Path(f).name for f in exported_files])
            )
    
    def import_coordinates_dialog(self):
        """Open file dialog to import coordinates."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Coordinates",
            str(Path(self.current_file).parent) if self.current_file else "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.import_coordinates(file_path)
    
    def import_coordinates(self, file_path: str):
        """Import coordinates from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Clear existing markers and ROIs
            self.cell_markers.clear()
            self.undo_stack.clear()
            self.rois.clear()
            self.current_roi = None
            self.roi_list.clear()
            self.marker_items.clear()
            self.roi_items.clear()
            self.selected_marker_index = -1
            
            # Import ROIs
            if 'rois' in data:
                for roi_data in data['rois']:
                    color = QColor(roi_data.get('color', '#ffff00'))
                    roi = ROI(
                        name=roi_data.get('name', 'ROI'),
                        color=color,
                        line_width=roi_data.get('line_width', 2),
                        closed=True
                    )
                    for point in roi_data.get('points', []):
                        roi.points.append((point['x'], point['y']))
                    if roi.points:
                        self.rois.append(roi)
                        self.roi_list.addItem(roi.name)
            
            # Import markers
            if 'markers' in data:
                # Group markers by cell type to assign numbers
                type_counts = {}
                for marker_data in data['markers']:
                    cell_type_name = marker_data.get('cell_type', 'Type 1')
                    
                    # Create cell type if it doesn't exist
                    if cell_type_name not in self.cell_types:
                        # Try to find a color from an existing type, or use default
                        color = QColor(255, 255, 255)
                        ct = CellType(cell_type_name, color, MarkerType.CIRCLE, 20)
                        self.cell_types[cell_type_name] = ct
                        self.add_cell_type_widget(ct)
                        self.active_cell_combo.addItem(cell_type_name)
                    
                    # Track counts per type
                    if cell_type_name not in type_counts:
                        type_counts[cell_type_name] = 0
                    type_counts[cell_type_name] += 1
                    
                    marker = CellMarker(
                        position=QPointF(marker_data['x'], marker_data['y']),
                        cell_type=cell_type_name,
                        marker_number=type_counts[cell_type_name],
                        roi_name=marker_data.get('roi')
                    )
                    self.cell_markers.append(marker)
            
            # Import adjustments if available
            if 'adjustments' in data:
                adj = data['adjustments']
                if 'brightness' in adj:
                    self.image_adjustments.brightness_r = adj['brightness'].get('r', 0)
                    self.image_adjustments.brightness_g = adj['brightness'].get('g', 0)
                    self.image_adjustments.brightness_b = adj['brightness'].get('b', 0)
                if 'contrast' in adj:
                    self.image_adjustments.contrast_r = adj['contrast'].get('r', 1.0)
                    self.image_adjustments.contrast_g = adj['contrast'].get('g', 1.0)
                    self.image_adjustments.contrast_b = adj['contrast'].get('b', 1.0)
                if 'noise_reduction' in adj:
                    self.image_adjustments.noise_r = adj['noise_reduction'].get('r', 0)
                    self.image_adjustments.noise_g = adj['noise_reduction'].get('g', 0)
                    self.image_adjustments.noise_b = adj['noise_reduction'].get('b', 0)
                
                # Update dialog if open
                if self.adjustments_dialog and self.adjustments_dialog.isVisible():
                    self.adjustments_dialog.load_values()
            
            self.refresh_markers()
            self.refresh_rois()
            self.update_results_table()
            self.update_display()
            
            self.status_bar.showMessage(f"Imported coordinates from {Path(file_path).name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import coordinates:\n{str(e)}")
    
    def show_auto_dismiss_message(self, title: str, message: str, timeout_ms: int = 1500):
        """Show auto-dismissing message."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        QTimer.singleShot(timeout_ms, msg_box.accept)
        msg_box.exec()
    
    def dragEnterEvent(self, event):
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.tif', '.tiff', '.png', '.jpg', '.jpeg')):
                self.load_image(file_path)
