from PyQt5.QtWidgets import (QMainWindow, QGraphicsView, QToolBar, QAction, 
                             QActionGroup, QColorDialog, QPushButton, QLabel,
                             QFontComboBox, QSpinBox, QWidget, QHBoxLayout)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPainter, QColor, QIcon, QPixmap, QPainterPath, QPolygonF, QPen, QBrush, QFont

from scene import DiagramScene
from export import ExportManager


def create_icon(draw_func, size=24, color="#555555"):
    """Create an icon by drawing on a pixmap."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(color), 2))
    painter.setBrush(QBrush(QColor(color)))
    draw_func(painter, size)
    painter.end()
    return QIcon(pixmap)


def draw_select(painter, size):
    """Draw cursor/pointer icon."""
    painter.setBrush(Qt.NoBrush)
    # Arrow pointer
    path = QPainterPath()
    path.moveTo(6, 4)
    path.lineTo(6, 18)
    path.lineTo(10, 14)
    path.lineTo(14, 20)
    path.lineTo(16, 18)
    path.lineTo(12, 12)
    path.lineTo(18, 12)
    path.closeSubpath()
    painter.fillPath(path, QColor("#555555"))


def draw_rectangle(painter, size):
    """Draw rectangle icon."""
    painter.drawRect(4, 6, 16, 12)


def draw_oval(painter, size):
    """Draw oval icon."""
    painter.drawEllipse(4, 6, 16, 12)


def draw_diamond(painter, size):
    """Draw diamond icon."""
    from PyQt5.QtCore import QPointF
    points = QPolygonF([
        QPointF(12, 4),
        QPointF(20, 12),
        QPointF(12, 20),
        QPointF(4, 12)
    ])
    painter.drawPolygon(points)


def draw_triangle(painter, size):
    """Draw triangle icon."""
    from PyQt5.QtCore import QPointF
    points = QPolygonF([
        QPointF(12, 4),
        QPointF(20, 20),
        QPointF(4, 20)
    ])
    painter.drawPolygon(points)


def draw_arrow(painter, size):
    """Draw single arrow icon."""
    painter.drawLine(4, 12, 16, 12)
    # Arrowhead
    from PyQt5.QtCore import QPointF
    points = QPolygonF([
        QPointF(20, 12),
        QPointF(14, 8),
        QPointF(14, 16)
    ])
    painter.drawPolygon(points)


def draw_arrow_bidir(painter, size):
    """Draw bidirectional arrow icon."""
    painter.drawLine(8, 12, 16, 12)
    from PyQt5.QtCore import QPointF
    # Right arrowhead
    points1 = QPolygonF([
        QPointF(20, 12),
        QPointF(14, 8),
        QPointF(14, 16)
    ])
    painter.drawPolygon(points1)
    # Left arrowhead
    points2 = QPolygonF([
        QPointF(4, 12),
        QPointF(10, 8),
        QPointF(10, 16)
    ])
    painter.drawPolygon(points2)


def draw_text(painter, size):
    """Draw text icon (letter T)."""
    painter.setBrush(Qt.NoBrush)
    pen = painter.pen()
    pen.setWidth(3)
    painter.setPen(pen)
    # Draw T shape
    painter.drawLine(6, 6, 18, 6)   # Top horizontal
    painter.drawLine(12, 6, 12, 20)  # Vertical stem


class ColorButton(QPushButton):
    """Button showing current color."""
    
    def __init__(self, color="#3498db", parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self.setToolTip("Choose color")
        self._color = QColor(color)
        self.update_icon()
    
    def update_icon(self):
        pixmap = QPixmap(24, 24)
        pixmap.fill(self._color)
        self.setIcon(QIcon(pixmap))
        self.setIconSize(pixmap.size())
    
    def set_color(self, color):
        self._color = QColor(color)
        self.update_icon()
    
    def get_color(self):
        return self._color


class DiagramView(QGraphicsView):
    """Custom graphics view with proper focus handling for keyboard events."""
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        # Enable focus to receive keyboard events
        self.setFocusPolicy(Qt.StrongFocus)
    
    def mousePressEvent(self, event):
        # Ensure view has focus when clicked for keyboard events
        self.setFocus()
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagram Builder")
        self.setGeometry(100, 100, 1200, 800)
        
        self.scene = DiagramScene(self)
        self.scene.setSceneRect(0, 0, 2000, 2000)
        
        # Use custom view with proper focus handling
        self.view = DiagramView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.setCentralWidget(self.view)
        
        self.export_manager = ExportManager(self.scene)
        
        self.scene.status_message.connect(self.statusBar().showMessage)
        self.scene.shape_selected.connect(self._on_shape_selected)
        self.scene.text_selected.connect(self._on_text_selected)
        
        self._init_toolbar()
        self.statusBar().showMessage("Double-click to add shapes | Click to select | Right-click to label | Delete to remove")
    
    def _init_toolbar(self):
        toolbar = QToolBar("Tools")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        
        # Shape tools with icons
        tools = [
            (DiagramScene.MODE_SELECT, "Select (V)", draw_select),
            (DiagramScene.MODE_RECTANGLE, "Rectangle", draw_rectangle),
            (DiagramScene.MODE_OVAL, "Oval", draw_oval),
            (DiagramScene.MODE_DIAMOND, "Diamond", draw_diamond),
            (DiagramScene.MODE_TRIANGLE, "Triangle", draw_triangle),
            (DiagramScene.MODE_TEXT, "Text Label", draw_text),
        ]
        
        for mode, tooltip, draw_func in tools:
            icon = create_icon(draw_func)
            action = QAction(icon, "", self)
            action.setCheckable(True)
            action.setToolTip(tooltip)
            action.triggered.connect(lambda checked, m=mode: self.scene.set_mode(m))
            self.tool_group.addAction(action)
            toolbar.addAction(action)
            
            if mode == DiagramScene.MODE_RECTANGLE:
                action.setChecked(True)
        
        toolbar.addSeparator()
        
        # Arrow tools
        arrow_icon = create_icon(draw_arrow)
        arrow_action = QAction(arrow_icon, "", self)
        arrow_action.setCheckable(True)
        arrow_action.setToolTip("Arrow (click source, then target)")
        arrow_action.triggered.connect(lambda: self.scene.set_mode(DiagramScene.MODE_ARROW))
        self.tool_group.addAction(arrow_action)
        toolbar.addAction(arrow_action)
        
        bidir_icon = create_icon(draw_arrow_bidir)
        bidir_action = QAction(bidir_icon, "", self)
        bidir_action.setCheckable(True)
        bidir_action.setToolTip("Two-way arrow")
        bidir_action.triggered.connect(lambda: self.scene.set_mode(DiagramScene.MODE_ARROW_BIDIR))
        self.tool_group.addAction(bidir_action)
        toolbar.addAction(bidir_action)
        
        toolbar.addSeparator()
        
        # Color picker for shapes
        toolbar.addWidget(QLabel(" Fill:"))
        self.color_button = ColorButton()
        self.color_button.setToolTip("Shape fill color")
        self.color_button.clicked.connect(self._pick_color)
        toolbar.addWidget(self.color_button)
        
        # Color picker for labels
        toolbar.addWidget(QLabel(" Label:"))
        self.label_color_button = ColorButton(color="#333333")
        self.label_color_button.setToolTip("Label text color (right-click to add label)")
        self.label_color_button.clicked.connect(self._pick_label_color)
        toolbar.addWidget(self.label_color_button)
        
        toolbar.addSeparator()
        
        # Text formatting controls
        toolbar.addWidget(QLabel(" Font:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Arial"))
        self.font_combo.setMaximumWidth(150)
        self.font_combo.setToolTip("Font family")
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        toolbar.addWidget(self.font_combo)
        
        toolbar.addWidget(QLabel(" Size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 72)
        self.size_spin.setValue(14)
        self.size_spin.setToolTip("Font size")
        self.size_spin.valueChanged.connect(self._on_size_changed)
        toolbar.addWidget(self.size_spin)
        
        # Bold button
        self.bold_action = QAction("B", self)
        self.bold_action.setCheckable(True)
        self.bold_action.setToolTip("Bold")
        font = self.bold_action.font()
        font.setBold(True)
        self.bold_action.setFont(font)
        self.bold_action.triggered.connect(self._on_bold_changed)
        toolbar.addAction(self.bold_action)
        
        # Underline button
        self.underline_action = QAction("U", self)
        self.underline_action.setCheckable(True)
        self.underline_action.setToolTip("Underline")
        font = self.underline_action.font()
        font.setUnderline(True)
        self.underline_action.setFont(font)
        self.underline_action.triggered.connect(self._on_underline_changed)
        toolbar.addAction(self.underline_action)
        
        toolbar.addSeparator()
        
        # Save/Load buttons
        save_action = QAction("Save", self)
        save_action.setToolTip("Save diagram to JSON")
        save_action.triggered.connect(lambda: self.export_manager.export_json(self))
        toolbar.addAction(save_action)
        
        load_action = QAction("Load", self)
        load_action.setToolTip("Load diagram from JSON")
        load_action.triggered.connect(lambda: self.export_manager.load_json(self))
        toolbar.addAction(load_action)
        
        toolbar.addSeparator()
        
        # Export buttons
        export_svg = QAction("SVG", self)
        export_svg.setToolTip("Export to SVG")
        export_svg.triggered.connect(lambda: self.export_manager.export_svg(self))
        toolbar.addAction(export_svg)
        
        export_png = QAction("PNG", self)
        export_png.setToolTip("Export to PNG")
        export_png.triggered.connect(lambda: self.export_manager.export_png(self))
        toolbar.addAction(export_png)
        
        toolbar.addSeparator()
        
        clear_action = QAction("Clear", self)
        clear_action.setToolTip("Clear all")
        clear_action.triggered.connect(self.scene.clear_all)
        toolbar.addAction(clear_action)
    
    def _pick_color(self):
        current = self.color_button.get_color()
        color = QColorDialog.getColor(current, self, "Choose Fill Color")
        if color.isValid():
            self.color_button.set_color(color)
            self.scene.set_color(color)
    
    def _pick_label_color(self):
        current = self.label_color_button.get_color()
        color = QColorDialog.getColor(current, self, "Choose Label Color")
        if color.isValid():
            self.label_color_button.set_color(color)
            self.scene.set_label_color(color)
    
    def _on_shape_selected(self, shape):
        # Update fill color button
        if hasattr(shape, 'get_color'):
            self.color_button.set_color(shape.get_color())
        
        # Update label color button if shape has a label
        if hasattr(shape, 'label') and shape.label and hasattr(shape, 'get_label_color'):
            self.label_color_button.set_color(shape.get_label_color())
    
    def _on_text_selected(self, text_shape):
        """Update formatting controls when a text shape is selected."""
        # Block signals to avoid triggering changes while updating
        self.font_combo.blockSignals(True)
        self.size_spin.blockSignals(True)
        self.bold_action.blockSignals(True)
        self.underline_action.blockSignals(True)
        
        self.font_combo.setCurrentFont(QFont(text_shape.font_family))
        self.size_spin.setValue(text_shape.font_size)
        self.bold_action.setChecked(text_shape.is_bold)
        self.underline_action.setChecked(text_shape.is_underline)
        
        self.font_combo.blockSignals(False)
        self.size_spin.blockSignals(False)
        self.bold_action.blockSignals(False)
        self.underline_action.blockSignals(False)
    
    def _on_font_changed(self, font):
        """Handle font family change."""
        self.scene.set_text_settings(font_family=font.family())
    
    def _on_size_changed(self, size):
        """Handle font size change."""
        self.scene.set_text_settings(font_size=size)
    
    def _on_bold_changed(self, checked):
        """Handle bold toggle."""
        self.scene.set_text_settings(bold=checked)
    
    def _on_underline_changed(self, checked):
        """Handle underline toggle."""
        self.scene.set_text_settings(underline=checked)