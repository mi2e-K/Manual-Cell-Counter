# FluoroCount

A desktop application for manual cell counting in fluorescence microscopy images.

## Features

- **Multi-channel support**: View RGB channels individually or combined (TIFF, PNG, JPEG)
- **Manual cell counting**: Click to place markers with customizable types, colors, and shapes
- **ROI analysis**: Draw polygonal regions of interest; counts are calculated per-ROI
- **Image adjustments**: Per-channel brightness, contrast, and noise reduction with real-time preview
- **Export**: CSV results, JSON coordinates, and overlay images

## Installation

```bash
pip install -r requirements.txt
python run_analyzer.py
```

### Requirements
- Python 3.9+
- PyQt6, NumPy, Pillow, tifffile, scipy

## Quick Start

1. **Load image**: Drag & drop or click "Open Image"
2. **Draw ROI**: Click "+ New ROI", left-click to add points, right-click to close
3. **Count cells**: Select cell type, switch to Count Mode, click on cells
4. **Export**: Click "Export Results" to save CSV/JSON/PNG

## Shortcuts

| Key | Action |
|-----|--------|
| R/G/B | Toggle channels |
| F | Count Mode |
| D | ROI Mode |
| Shift+D | Add new ROI |
| Space | Toggle active cell type |
| Ctrl+Z | Undo marker |
| Ctrl+Shift+Z | Redo marker |
| Ctrl+S | Export results |

## License

MIT License
