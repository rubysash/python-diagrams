#!/usr/bin/env python3
"""
Diagram Builder - A simple diagram maker with shapes and arrows.

Usage:
    python main.py
"""

import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Diagram Builder")
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
