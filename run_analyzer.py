#!/usr/bin/env python3
"""
Fluorescence Microscope Image Analyzer - Standalone Launcher

Run this script directly to start the application:
    python run_analyzer.py
"""

import sys
import os

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from fluoro_analyzer import FluoroAnalyzer


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Fluorescence Microscope Image Analyzer")
    app.setApplicationVersion("1.0.0")
    
    window = FluoroAnalyzer()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
