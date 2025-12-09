#!/usr/bin/env python3
"""
Fluorescence Microscope Image Analyzer
Entry point for the application.

Usage:
    python -m fluoro_analyzer
    or
    python main.py
"""

import sys
from PyQt6.QtWidgets import QApplication
from .main_window import FluoroAnalyzer


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("FluoroCount")
    app.setApplicationVersion("1.0.0")
    
    window = FluoroAnalyzer()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
