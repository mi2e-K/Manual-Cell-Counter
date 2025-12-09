"""
Image Adjustments Dialog for Fluorescence Microscope Image Analyzer.
Provides controls for brightness, contrast, and noise reduction per channel.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSlider, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

from .datatypes import ImageAdjustments


class AdjustmentsDialog(QDialog):
    """Dialog for image adjustments with real-time preview."""
    
    adjustments_changed = pyqtSignal()
    
    def __init__(self, adjustments: ImageAdjustments, parent=None):
        super().__init__(parent)
        self.adjustments = adjustments
        self.setWindowTitle("Image Adjustments")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        self._updating = False  # Prevent recursive updates
        
        self.setup_ui()
        self.load_values()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Apply spinbox styling for better button accessibility
        spinbox_style = """
            QSpinBox, QDoubleSpinBox { 
                background-color: #3c3c3c; 
                border: 1px solid #555; 
                border-radius: 3px; 
                padding: 2px;
                padding-right: 18px;
                color: white;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 18px;
                height: 11px;
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
                width: 18px;
                height: 11px;
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
                width: 8px;
                height: 8px;
            }
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                width: 8px;
                height: 8px;
            }
        """
        self.setStyleSheet(spinbox_style)
        
        # Brightness section
        brightness_group = QGroupBox("Brightness (per channel)")
        brightness_layout = QGridLayout(brightness_group)
        brightness_layout.setColumnStretch(1, 1)  # Make slider column stretch
        
        # Red brightness
        brightness_layout.addWidget(QLabel("Red:"), 0, 0)
        self.brightness_r_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_r_slider.setRange(-100, 100)
        self.brightness_r_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.brightness_r_slider.valueChanged.connect(self.on_brightness_r_changed)
        brightness_layout.addWidget(self.brightness_r_slider, 0, 1)
        self.brightness_r_spin = QSpinBox()
        self.brightness_r_spin.setRange(-100, 100)
        self.brightness_r_spin.setFixedWidth(60)
        self.brightness_r_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.brightness_r_spin.valueChanged.connect(self.on_brightness_r_spin_changed)
        brightness_layout.addWidget(self.brightness_r_spin, 0, 2)
        self.reset_brightness_r_btn = QPushButton("↺")
        self.reset_brightness_r_btn.setFixedWidth(36)
        self.reset_brightness_r_btn.setToolTip("Reset Red Brightness")
        self.reset_brightness_r_btn.clicked.connect(self.reset_brightness_r)
        brightness_layout.addWidget(self.reset_brightness_r_btn, 0, 3)
        
        # Green brightness
        brightness_layout.addWidget(QLabel("Green:"), 1, 0)
        self.brightness_g_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_g_slider.setRange(-100, 100)
        self.brightness_g_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.brightness_g_slider.valueChanged.connect(self.on_brightness_g_changed)
        brightness_layout.addWidget(self.brightness_g_slider, 1, 1)
        self.brightness_g_spin = QSpinBox()
        self.brightness_g_spin.setRange(-100, 100)
        self.brightness_g_spin.setFixedWidth(60)
        self.brightness_g_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.brightness_g_spin.valueChanged.connect(self.on_brightness_g_spin_changed)
        brightness_layout.addWidget(self.brightness_g_spin, 1, 2)
        self.reset_brightness_g_btn = QPushButton("↺")
        self.reset_brightness_g_btn.setFixedWidth(36)
        self.reset_brightness_g_btn.setToolTip("Reset Green Brightness")
        self.reset_brightness_g_btn.clicked.connect(self.reset_brightness_g)
        brightness_layout.addWidget(self.reset_brightness_g_btn, 1, 3)
        
        # Blue brightness
        brightness_layout.addWidget(QLabel("Blue:"), 2, 0)
        self.brightness_b_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_b_slider.setRange(-100, 100)
        self.brightness_b_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.brightness_b_slider.valueChanged.connect(self.on_brightness_b_changed)
        brightness_layout.addWidget(self.brightness_b_slider, 2, 1)
        self.brightness_b_spin = QSpinBox()
        self.brightness_b_spin.setRange(-100, 100)
        self.brightness_b_spin.setFixedWidth(60)
        self.brightness_b_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.brightness_b_spin.valueChanged.connect(self.on_brightness_b_spin_changed)
        brightness_layout.addWidget(self.brightness_b_spin, 2, 2)
        self.reset_brightness_b_btn = QPushButton("↺")
        self.reset_brightness_b_btn.setFixedWidth(36)
        self.reset_brightness_b_btn.setToolTip("Reset Blue Brightness")
        self.reset_brightness_b_btn.clicked.connect(self.reset_brightness_b)
        brightness_layout.addWidget(self.reset_brightness_b_btn, 2, 3)
        
        # Reset All Brightness button
        reset_brightness_all_btn = QPushButton("Reset All Brightness")
        reset_brightness_all_btn.clicked.connect(self.reset_brightness_all)
        brightness_layout.addWidget(reset_brightness_all_btn, 3, 0, 1, 4)
        
        layout.addWidget(brightness_group)
        
        # Contrast section
        contrast_group = QGroupBox("Contrast (per channel)")
        contrast_layout = QGridLayout(contrast_group)
        contrast_layout.setColumnStretch(1, 1)
        
        # Red contrast
        contrast_layout.addWidget(QLabel("Red:"), 0, 0)
        self.contrast_r_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_r_slider.setRange(10, 300)  # 0.1 to 3.0
        self.contrast_r_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.contrast_r_slider.valueChanged.connect(self.on_contrast_r_changed)
        contrast_layout.addWidget(self.contrast_r_slider, 0, 1)
        self.contrast_r_spin = QDoubleSpinBox()
        self.contrast_r_spin.setRange(0.1, 3.0)
        self.contrast_r_spin.setSingleStep(0.1)
        self.contrast_r_spin.setDecimals(2)
        self.contrast_r_spin.setFixedWidth(60)
        self.contrast_r_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.contrast_r_spin.valueChanged.connect(self.on_contrast_r_spin_changed)
        contrast_layout.addWidget(self.contrast_r_spin, 0, 2)
        self.reset_contrast_r_btn = QPushButton("↺")
        self.reset_contrast_r_btn.setFixedWidth(36)
        self.reset_contrast_r_btn.setToolTip("Reset Red Contrast")
        self.reset_contrast_r_btn.clicked.connect(self.reset_contrast_r)
        contrast_layout.addWidget(self.reset_contrast_r_btn, 0, 3)
        
        # Green contrast
        contrast_layout.addWidget(QLabel("Green:"), 1, 0)
        self.contrast_g_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_g_slider.setRange(10, 300)
        self.contrast_g_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.contrast_g_slider.valueChanged.connect(self.on_contrast_g_changed)
        contrast_layout.addWidget(self.contrast_g_slider, 1, 1)
        self.contrast_g_spin = QDoubleSpinBox()
        self.contrast_g_spin.setRange(0.1, 3.0)
        self.contrast_g_spin.setSingleStep(0.1)
        self.contrast_g_spin.setDecimals(2)
        self.contrast_g_spin.setFixedWidth(60)
        self.contrast_g_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.contrast_g_spin.valueChanged.connect(self.on_contrast_g_spin_changed)
        contrast_layout.addWidget(self.contrast_g_spin, 1, 2)
        self.reset_contrast_g_btn = QPushButton("↺")
        self.reset_contrast_g_btn.setFixedWidth(36)
        self.reset_contrast_g_btn.setToolTip("Reset Green Contrast")
        self.reset_contrast_g_btn.clicked.connect(self.reset_contrast_g)
        contrast_layout.addWidget(self.reset_contrast_g_btn, 1, 3)
        
        # Blue contrast
        contrast_layout.addWidget(QLabel("Blue:"), 2, 0)
        self.contrast_b_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_b_slider.setRange(10, 300)
        self.contrast_b_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.contrast_b_slider.valueChanged.connect(self.on_contrast_b_changed)
        contrast_layout.addWidget(self.contrast_b_slider, 2, 1)
        self.contrast_b_spin = QDoubleSpinBox()
        self.contrast_b_spin.setRange(0.1, 3.0)
        self.contrast_b_spin.setSingleStep(0.1)
        self.contrast_b_spin.setDecimals(2)
        self.contrast_b_spin.setFixedWidth(60)
        self.contrast_b_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.contrast_b_spin.valueChanged.connect(self.on_contrast_b_spin_changed)
        contrast_layout.addWidget(self.contrast_b_spin, 2, 2)
        self.reset_contrast_b_btn = QPushButton("↺")
        self.reset_contrast_b_btn.setFixedWidth(36)
        self.reset_contrast_b_btn.setToolTip("Reset Blue Contrast")
        self.reset_contrast_b_btn.clicked.connect(self.reset_contrast_b)
        contrast_layout.addWidget(self.reset_contrast_b_btn, 2, 3)
        
        # Reset All Contrast button
        reset_contrast_all_btn = QPushButton("Reset All Contrast")
        reset_contrast_all_btn.clicked.connect(self.reset_contrast_all)
        contrast_layout.addWidget(reset_contrast_all_btn, 3, 0, 1, 4)
        
        layout.addWidget(contrast_group)
        
        # Noise reduction section (per channel)
        noise_group = QGroupBox("Noise Reduction (per channel)")
        noise_layout = QGridLayout(noise_group)
        noise_layout.setColumnStretch(1, 1)
        
        # Red noise
        noise_layout.addWidget(QLabel("Red:"), 0, 0)
        self.noise_r_slider = QSlider(Qt.Orientation.Horizontal)
        self.noise_r_slider.setRange(0, 10)
        self.noise_r_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.noise_r_slider.valueChanged.connect(self.on_noise_r_changed)
        noise_layout.addWidget(self.noise_r_slider, 0, 1)
        self.noise_r_spin = QSpinBox()
        self.noise_r_spin.setRange(0, 10)
        self.noise_r_spin.setFixedWidth(60)
        self.noise_r_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.noise_r_spin.valueChanged.connect(self.on_noise_r_spin_changed)
        noise_layout.addWidget(self.noise_r_spin, 0, 2)
        self.reset_noise_r_btn = QPushButton("↺")
        self.reset_noise_r_btn.setFixedWidth(36)
        self.reset_noise_r_btn.setToolTip("Reset Red Noise Reduction")
        self.reset_noise_r_btn.clicked.connect(self.reset_noise_r)
        noise_layout.addWidget(self.reset_noise_r_btn, 0, 3)
        
        # Green noise
        noise_layout.addWidget(QLabel("Green:"), 1, 0)
        self.noise_g_slider = QSlider(Qt.Orientation.Horizontal)
        self.noise_g_slider.setRange(0, 10)
        self.noise_g_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.noise_g_slider.valueChanged.connect(self.on_noise_g_changed)
        noise_layout.addWidget(self.noise_g_slider, 1, 1)
        self.noise_g_spin = QSpinBox()
        self.noise_g_spin.setRange(0, 10)
        self.noise_g_spin.setFixedWidth(60)
        self.noise_g_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.noise_g_spin.valueChanged.connect(self.on_noise_g_spin_changed)
        noise_layout.addWidget(self.noise_g_spin, 1, 2)
        self.reset_noise_g_btn = QPushButton("↺")
        self.reset_noise_g_btn.setFixedWidth(36)
        self.reset_noise_g_btn.setToolTip("Reset Green Noise Reduction")
        self.reset_noise_g_btn.clicked.connect(self.reset_noise_g)
        noise_layout.addWidget(self.reset_noise_g_btn, 1, 3)
        
        # Blue noise
        noise_layout.addWidget(QLabel("Blue:"), 2, 0)
        self.noise_b_slider = QSlider(Qt.Orientation.Horizontal)
        self.noise_b_slider.setRange(0, 10)
        self.noise_b_slider.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.noise_b_slider.valueChanged.connect(self.on_noise_b_changed)
        noise_layout.addWidget(self.noise_b_slider, 2, 1)
        self.noise_b_spin = QSpinBox()
        self.noise_b_spin.setRange(0, 10)
        self.noise_b_spin.setFixedWidth(60)
        self.noise_b_spin.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.noise_b_spin.valueChanged.connect(self.on_noise_b_spin_changed)
        noise_layout.addWidget(self.noise_b_spin, 2, 2)
        self.reset_noise_b_btn = QPushButton("↺")
        self.reset_noise_b_btn.setFixedWidth(36)
        self.reset_noise_b_btn.setToolTip("Reset Blue Noise Reduction")
        self.reset_noise_b_btn.clicked.connect(self.reset_noise_b)
        noise_layout.addWidget(self.reset_noise_b_btn, 2, 3)
        
        # Reset All Noise button
        reset_noise_all_btn = QPushButton("Reset All Noise Reduction")
        reset_noise_all_btn.clicked.connect(self.reset_noise_all)
        noise_layout.addWidget(reset_noise_all_btn, 3, 0, 1, 4)
        
        layout.addWidget(noise_group)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        reset_all_btn = QPushButton("Reset All Adjustments")
        reset_all_btn.clicked.connect(self.reset_all)
        button_layout.addWidget(reset_all_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_values(self):
        """Load current adjustment values into controls."""
        self._updating = True
        
        # Brightness
        self.brightness_r_slider.setValue(self.adjustments.brightness_r)
        self.brightness_r_spin.setValue(self.adjustments.brightness_r)
        self.brightness_g_slider.setValue(self.adjustments.brightness_g)
        self.brightness_g_spin.setValue(self.adjustments.brightness_g)
        self.brightness_b_slider.setValue(self.adjustments.brightness_b)
        self.brightness_b_spin.setValue(self.adjustments.brightness_b)
        
        # Contrast
        self.contrast_r_slider.setValue(int(self.adjustments.contrast_r * 100))
        self.contrast_r_spin.setValue(self.adjustments.contrast_r)
        self.contrast_g_slider.setValue(int(self.adjustments.contrast_g * 100))
        self.contrast_g_spin.setValue(self.adjustments.contrast_g)
        self.contrast_b_slider.setValue(int(self.adjustments.contrast_b * 100))
        self.contrast_b_spin.setValue(self.adjustments.contrast_b)
        
        # Noise
        self.noise_r_slider.setValue(self.adjustments.noise_r)
        self.noise_r_spin.setValue(self.adjustments.noise_r)
        self.noise_g_slider.setValue(self.adjustments.noise_g)
        self.noise_g_spin.setValue(self.adjustments.noise_g)
        self.noise_b_slider.setValue(self.adjustments.noise_b)
        self.noise_b_spin.setValue(self.adjustments.noise_b)
        
        self._updating = False
    
    def emit_change(self):
        """Emit change signal if not in update mode."""
        if not self._updating:
            self.adjustments_changed.emit()
    
    # Brightness handlers
    def on_brightness_r_changed(self, value):
        self.adjustments.brightness_r = value
        self._updating = True
        self.brightness_r_spin.setValue(value)
        self._updating = False
        self.emit_change()
    
    def on_brightness_r_spin_changed(self, value):
        if not self._updating:
            self._updating = True
            self.brightness_r_slider.setValue(value)
            self._updating = False
            self.adjustments.brightness_r = value
            self.emit_change()
    
    def on_brightness_g_changed(self, value):
        self.adjustments.brightness_g = value
        self._updating = True
        self.brightness_g_spin.setValue(value)
        self._updating = False
        self.emit_change()
    
    def on_brightness_g_spin_changed(self, value):
        if not self._updating:
            self._updating = True
            self.brightness_g_slider.setValue(value)
            self._updating = False
            self.adjustments.brightness_g = value
            self.emit_change()
    
    def on_brightness_b_changed(self, value):
        self.adjustments.brightness_b = value
        self._updating = True
        self.brightness_b_spin.setValue(value)
        self._updating = False
        self.emit_change()
    
    def on_brightness_b_spin_changed(self, value):
        if not self._updating:
            self._updating = True
            self.brightness_b_slider.setValue(value)
            self._updating = False
            self.adjustments.brightness_b = value
            self.emit_change()
    
    # Contrast handlers
    def on_contrast_r_changed(self, value):
        contrast = value / 100.0
        self.adjustments.contrast_r = contrast
        self._updating = True
        self.contrast_r_spin.setValue(contrast)
        self._updating = False
        self.emit_change()
    
    def on_contrast_r_spin_changed(self, value):
        if not self._updating:
            self._updating = True
            self.contrast_r_slider.setValue(int(value * 100))
            self._updating = False
            self.adjustments.contrast_r = value
            self.emit_change()
    
    def on_contrast_g_changed(self, value):
        contrast = value / 100.0
        self.adjustments.contrast_g = contrast
        self._updating = True
        self.contrast_g_spin.setValue(contrast)
        self._updating = False
        self.emit_change()
    
    def on_contrast_g_spin_changed(self, value):
        if not self._updating:
            self._updating = True
            self.contrast_g_slider.setValue(int(value * 100))
            self._updating = False
            self.adjustments.contrast_g = value
            self.emit_change()
    
    def on_contrast_b_changed(self, value):
        contrast = value / 100.0
        self.adjustments.contrast_b = contrast
        self._updating = True
        self.contrast_b_spin.setValue(contrast)
        self._updating = False
        self.emit_change()
    
    def on_contrast_b_spin_changed(self, value):
        if not self._updating:
            self._updating = True
            self.contrast_b_slider.setValue(int(value * 100))
            self._updating = False
            self.adjustments.contrast_b = value
            self.emit_change()
    
    # Noise handlers
    def on_noise_r_changed(self, value):
        self.adjustments.noise_r = value
        self._updating = True
        self.noise_r_spin.setValue(value)
        self._updating = False
        self.emit_change()
    
    def on_noise_r_spin_changed(self, value):
        if not self._updating:
            self._updating = True
            self.noise_r_slider.setValue(value)
            self._updating = False
            self.adjustments.noise_r = value
            self.emit_change()
    
    def on_noise_g_changed(self, value):
        self.adjustments.noise_g = value
        self._updating = True
        self.noise_g_spin.setValue(value)
        self._updating = False
        self.emit_change()
    
    def on_noise_g_spin_changed(self, value):
        if not self._updating:
            self._updating = True
            self.noise_g_slider.setValue(value)
            self._updating = False
            self.adjustments.noise_g = value
            self.emit_change()
    
    def on_noise_b_changed(self, value):
        self.adjustments.noise_b = value
        self._updating = True
        self.noise_b_spin.setValue(value)
        self._updating = False
        self.emit_change()
    
    def on_noise_b_spin_changed(self, value):
        if not self._updating:
            self._updating = True
            self.noise_b_slider.setValue(value)
            self._updating = False
            self.adjustments.noise_b = value
            self.emit_change()
    
    # Reset handlers - individual channel
    def reset_brightness_r(self):
        self.adjustments.reset_brightness_r()
        self.load_values()
        self.emit_change()
    
    def reset_brightness_g(self):
        self.adjustments.reset_brightness_g()
        self.load_values()
        self.emit_change()
    
    def reset_brightness_b(self):
        self.adjustments.reset_brightness_b()
        self.load_values()
        self.emit_change()
    
    def reset_contrast_r(self):
        self.adjustments.reset_contrast_r()
        self.load_values()
        self.emit_change()
    
    def reset_contrast_g(self):
        self.adjustments.reset_contrast_g()
        self.load_values()
        self.emit_change()
    
    def reset_contrast_b(self):
        self.adjustments.reset_contrast_b()
        self.load_values()
        self.emit_change()
    
    def reset_noise_r(self):
        self.adjustments.reset_noise_r()
        self.load_values()
        self.emit_change()
    
    def reset_noise_g(self):
        self.adjustments.reset_noise_g()
        self.load_values()
        self.emit_change()
    
    def reset_noise_b(self):
        self.adjustments.reset_noise_b()
        self.load_values()
        self.emit_change()
    
    # Reset handlers - all channels
    def reset_brightness_all(self):
        self.adjustments.reset_brightness()
        self.load_values()
        self.emit_change()
    
    def reset_contrast_all(self):
        self.adjustments.reset_contrast()
        self.load_values()
        self.emit_change()
    
    def reset_noise_all(self):
        self.adjustments.reset_noise()
        self.load_values()
        self.emit_change()
    
    def reset_all(self):
        self.adjustments.reset_all()
        self.load_values()
        self.emit_change()
