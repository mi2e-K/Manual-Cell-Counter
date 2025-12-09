"""
Fluorescence Microscope Image Analyzer
A PyQt6-based tool for viewing and analyzing fluorescence microscope images.
"""

from .main_window import FluoroAnalyzer
from .datatypes import (
    ChannelMode, MarkerType, ToolMode, LabelPosition,
    CellType, CellMarker, ROI, ImageAdjustments
)
from .canvas import ImageCanvas
from .widgets import CellTypeWidget
from .adjustments_dialog import AdjustmentsDialog
from .image_processing import (
    apply_brightness, apply_contrast, apply_noise_reduction_channel,
    apply_all_adjustments
)

__version__ = "1.0.0"
__all__ = [
    'FluoroAnalyzer',
    'ChannelMode', 'MarkerType', 'ToolMode', 'LabelPosition',
    'CellType', 'CellMarker', 'ROI', 'ImageAdjustments',
    'ImageCanvas', 'CellTypeWidget', 'AdjustmentsDialog',
    'apply_brightness', 'apply_contrast', 'apply_noise_reduction_channel',
    'apply_all_adjustments'
]
