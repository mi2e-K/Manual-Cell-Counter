"""
Data types for Fluorescence Microscope Image Analyzer.
Contains enums and dataclasses used throughout the application.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor


class ChannelMode(Enum):
    """Channel display modes."""
    COMPOSITE = auto()
    RED = auto()
    GREEN = auto()
    BLUE = auto()
    CYAN = auto()
    MAGENTA = auto()
    YELLOW = auto()


class MarkerType(Enum):
    """Cell marker display types."""
    DOT = "Dot"
    CIRCLE = "Circle"
    RECTANGLE = "Rectangle"


class ToolMode(Enum):
    """Tool modes for canvas interaction."""
    PAN = auto()
    CELL_COUNT = auto()
    ROI_DRAW = auto()


@dataclass
class CellType:
    """Represents a cell type for counting."""
    name: str
    color: QColor
    marker_type: MarkerType
    marker_size: int
    count: int = 0


@dataclass
class CellMarker:
    """Represents a single cell marker."""
    position: QPointF
    cell_type: str
    marker_number: int
    roi_name: Optional[str] = None


@dataclass
class ROI:
    """Represents a Region of Interest."""
    name: str
    points: list = field(default_factory=list)
    color: QColor = field(default_factory=lambda: QColor(255, 255, 0, 255))
    line_width: int = 2
    closed: bool = False


@dataclass
class ImageAdjustments:
    """Stores per-channel image adjustment settings."""
    # Brightness: -100 to 100
    brightness_r: int = 0
    brightness_g: int = 0
    brightness_b: int = 0
    
    # Contrast: 0.1 to 3.0
    contrast_r: float = 1.0
    contrast_g: float = 1.0
    contrast_b: float = 1.0
    
    # Noise reduction strength per channel: 0 to 10
    noise_r: int = 0
    noise_g: int = 0
    noise_b: int = 0
    
    def reset_brightness_r(self):
        """Reset red brightness."""
        self.brightness_r = 0
    
    def reset_brightness_g(self):
        """Reset green brightness."""
        self.brightness_g = 0
    
    def reset_brightness_b(self):
        """Reset blue brightness."""
        self.brightness_b = 0
    
    def reset_brightness(self):
        """Reset all brightness values."""
        self.brightness_r = 0
        self.brightness_g = 0
        self.brightness_b = 0
    
    def reset_contrast_r(self):
        """Reset red contrast."""
        self.contrast_r = 1.0
    
    def reset_contrast_g(self):
        """Reset green contrast."""
        self.contrast_g = 1.0
    
    def reset_contrast_b(self):
        """Reset blue contrast."""
        self.contrast_b = 1.0
    
    def reset_contrast(self):
        """Reset all contrast values."""
        self.contrast_r = 1.0
        self.contrast_g = 1.0
        self.contrast_b = 1.0
    
    def reset_noise_r(self):
        """Reset red noise reduction."""
        self.noise_r = 0
    
    def reset_noise_g(self):
        """Reset green noise reduction."""
        self.noise_g = 0
    
    def reset_noise_b(self):
        """Reset blue noise reduction."""
        self.noise_b = 0
    
    def reset_noise(self):
        """Reset all noise reduction."""
        self.noise_r = 0
        self.noise_g = 0
        self.noise_b = 0
    
    def reset_all(self):
        """Reset all adjustments."""
        self.reset_brightness()
        self.reset_contrast()
        self.reset_noise()
    
    def copy(self):
        """Create a copy of the adjustments."""
        return ImageAdjustments(
            brightness_r=self.brightness_r,
            brightness_g=self.brightness_g,
            brightness_b=self.brightness_b,
            contrast_r=self.contrast_r,
            contrast_g=self.contrast_g,
            contrast_b=self.contrast_b,
            noise_r=self.noise_r,
            noise_g=self.noise_g,
            noise_b=self.noise_b
        )
