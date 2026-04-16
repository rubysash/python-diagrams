import json
import shutil
from pathlib import Path

from PyQt5.QtWidgets import (QMainWindow, QGraphicsView, QToolBar, QAction,
                             QActionGroup, QColorDialog, QPushButton, QLabel,
                             QFontComboBox, QSpinBox, QComboBox, QWidget,
                             QHBoxLayout, QShortcut, QDialog, QVBoxLayout,
                             QTextBrowser)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import (QPainter, QColor, QIcon, QPixmap, QPainterPath,
                          QPolygonF, QPen, QBrush, QFont, QKeySequence)

from scene import DiagramScene
from export import ExportManager
from config import APP_NAME, VERSION


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


def draw_square(painter, size):
    """Draw square icon."""
    painter.drawRect(5, 5, 14, 14)


def draw_oval(painter, size):
    """Draw oval icon."""
    painter.drawEllipse(4, 6, 16, 12)


def draw_circle(painter, size):
    """Draw circle icon."""
    painter.drawEllipse(5, 5, 14, 14)


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


def draw_hexagon(painter, size):
    """Draw hexagon icon."""
    from PyQt5.QtCore import QPointF
    points = QPolygonF([
        QPointF(8, 4),
        QPointF(16, 4),
        QPointF(20, 12),
        QPointF(16, 20),
        QPointF(8, 20),
        QPointF(4, 12),
    ])
    painter.drawPolygon(points)


def draw_octagon(painter, size):
    """Draw octagon icon."""
    from PyQt5.QtCore import QPointF
    points = QPolygonF([
        QPointF(8, 4),
        QPointF(16, 4),
        QPointF(20, 8),
        QPointF(20, 16),
        QPointF(16, 20),
        QPointF(8, 20),
        QPointF(4, 16),
        QPointF(4, 8),
    ])
    painter.drawPolygon(points)


def draw_triangle(painter, size):
    """Draw triangle icon (pointing up)."""
    from PyQt5.QtCore import QPointF
    points = QPolygonF([
        QPointF(12, 4),
        QPointF(20, 20),
        QPointF(4, 20)
    ])
    painter.drawPolygon(points)


def draw_triangle_inverted(painter, size):
    """Draw inverted triangle icon (pointing down)."""
    from PyQt5.QtCore import QPointF
    points = QPolygonF([
        QPointF(4, 4),
        QPointF(20, 4),
        QPointF(12, 20)
    ])
    painter.drawPolygon(points)


def draw_triangle_left(painter, size):
    """Draw left-facing triangle icon."""
    from PyQt5.QtCore import QPointF
    points = QPolygonF([
        QPointF(20, 4),
        QPointF(20, 20),
        QPointF(4, 12)
    ])
    painter.drawPolygon(points)


def draw_triangle_right(painter, size):
    """Draw right-facing triangle icon."""
    from PyQt5.QtCore import QPointF
    points = QPolygonF([
        QPointF(4, 4),
        QPointF(20, 12),
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


def draw_image(painter, size):
    """Draw image/picture icon."""
    painter.setBrush(Qt.NoBrush)
    # Frame
    painter.drawRect(4, 5, 16, 14)
    # Mountain shapes
    path = QPainterPath()
    path.moveTo(4, 19)
    path.lineTo(10, 11)
    path.lineTo(15, 16)
    path.lineTo(17, 13)
    path.lineTo(20, 19)
    painter.drawPath(path)
    # Sun
    painter.drawEllipse(14, 7, 3, 3)


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
    """Custom graphics view with zoom, focus handling, and additive rubber band."""

    ZOOM_FACTOR = 1.15
    ZOOM_MIN = 0.1
    ZOOM_MAX = 10.0

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self._pre_rubber_selection = set()
        self._current_zoom = 1.0

    def wheelEvent(self, event):
        """Zoom in/out with mouse wheel."""
        if event.angleDelta().y() > 0:
            factor = self.ZOOM_FACTOR
        else:
            factor = 1.0 / self.ZOOM_FACTOR

        # Clamp zoom level to min/max bounds
        new_zoom = self._current_zoom * factor
        if new_zoom < self.ZOOM_MIN or new_zoom > self.ZOOM_MAX:
            return

        self._current_zoom = new_zoom
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        self.setFocus()
        # Remember current selection when Shift/Ctrl is held for additive rubber band
        if event.modifiers() & (Qt.ShiftModifier | Qt.ControlModifier):
            self._pre_rubber_selection = set(self.scene().selectedItems())
        else:
            self._pre_rubber_selection = set()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # After rubber band finishes, restore previous selection alongside new
        if self._pre_rubber_selection:
            for item in self._pre_rubber_selection:
                item.setSelected(True)
            self._pre_rubber_selection = set()


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
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
        self.scene.arrow_selected.connect(self._on_arrow_selected)
        
        self._init_toolbar()
        self.statusBar().showMessage("Double-click to add shapes | Click to select | Right-click to label | Delete to remove")
    
    def _init_toolbar(self):
        icon_size = QSize(24, 24)
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        self._tool_actions = {}  # mode -> QAction for shortcut lookup

        # --- Shapes toolbar ---
        shapes_tb = QToolBar("Shapes")
        shapes_tb.setIconSize(icon_size)
        self.addToolBar(shapes_tb)

        shape_tools = [
            (DiagramScene.MODE_SELECT, "Select", draw_select, "V"),
            (DiagramScene.MODE_RECTANGLE, "Rectangle", draw_rectangle, "R"),
            (DiagramScene.MODE_SQUARE, "Square", draw_square, "S"),
            (DiagramScene.MODE_OVAL, "Oval", draw_oval, "O"),
            (DiagramScene.MODE_CIRCLE, "Circle", draw_circle, "I"),
            (DiagramScene.MODE_DIAMOND, "Diamond", draw_diamond, "D"),
            (DiagramScene.MODE_HEXAGON, "Hexagon", draw_hexagon, "H"),
            (DiagramScene.MODE_OCTAGON, "Octagon", draw_octagon, "G"),
            (DiagramScene.MODE_TEXT, "Text Label", draw_text, "X"),
        ]
        self._add_tool_actions(shapes_tb, shape_tools,
                               default_mode=DiagramScene.MODE_RECTANGLE)

        # --- Triangles toolbar ---
        tri_tb = QToolBar("Triangles")
        tri_tb.setIconSize(icon_size)
        self.addToolBar(tri_tb)

        tri_tools = [
            (DiagramScene.MODE_TRIANGLE, "Triangle (Up)", draw_triangle, "T"),
            (DiagramScene.MODE_TRIANGLE_INVERTED, "Triangle (Down)", draw_triangle_inverted, None),
            (DiagramScene.MODE_TRIANGLE_LEFT, "Triangle (Left)", draw_triangle_left, None),
            (DiagramScene.MODE_TRIANGLE_RIGHT, "Triangle (Right)", draw_triangle_right, None),
        ]
        self._add_tool_actions(tri_tb, tri_tools)

        # --- Arrows toolbar ---
        arrow_tb = QToolBar("Arrows")
        arrow_tb.setIconSize(icon_size)
        self.addToolBar(arrow_tb)

        arrow_tools = [
            (DiagramScene.MODE_ARROW, "Line", draw_arrow, "A"),
        ]
        self._add_tool_actions(arrow_tb, arrow_tools)

        # Line style dropdown for arrows
        arrow_tb.addSeparator()
        arrow_tb.addWidget(QLabel(" Style:"))
        self.line_style_combo = QComboBox()
        self.line_style_combo.addItems(["Solid", "Dashed", "Dotted", "Dash-Dot"])
        self.line_style_combo.setToolTip("Arrow line style")
        self.line_style_combo.setMaximumWidth(90)
        self.line_style_combo.currentTextChanged.connect(self._on_line_style_changed)
        arrow_tb.addWidget(self.line_style_combo)

        # Line width dropdown for arrows
        arrow_tb.addWidget(QLabel(" Width:"))
        self.line_width_combo = QComboBox()
        self.line_width_combo.addItems(["1", "2", "3", "4", "5"])
        self.line_width_combo.setCurrentText("2")
        self.line_width_combo.setToolTip("Arrow line width")
        self.line_width_combo.setMaximumWidth(50)
        self.line_width_combo.currentTextChanged.connect(self._on_line_width_changed)
        arrow_tb.addWidget(self.line_width_combo)

        # Endpoint cap style dropdowns
        arrow_tb.addSeparator()
        arrow_tb.addWidget(QLabel(" Start:"))
        self.start_cap_combo = QComboBox()
        self.start_cap_combo.addItems(["None", "Arrow", "Ball"])
        self.start_cap_combo.setToolTip("Start endpoint style")
        self.start_cap_combo.setMaximumWidth(70)
        self.start_cap_combo.currentTextChanged.connect(self._on_start_cap_changed)
        arrow_tb.addWidget(self.start_cap_combo)

        arrow_tb.addWidget(QLabel(" End:"))
        self.end_cap_combo = QComboBox()
        self.end_cap_combo.addItems(["None", "Arrow", "Ball"])
        self.end_cap_combo.setCurrentText("Arrow")
        self.end_cap_combo.setToolTip("End endpoint style")
        self.end_cap_combo.setMaximumWidth(70)
        self.end_cap_combo.currentTextChanged.connect(self._on_end_cap_changed)
        arrow_tb.addWidget(self.end_cap_combo)

        # --- Format toolbar ---
        fmt_tb = QToolBar("Format")
        fmt_tb.setIconSize(icon_size)
        self.addToolBar(fmt_tb)

        fmt_tb.addWidget(QLabel(" Fill:"))
        self.color_button = ColorButton()
        self.color_button.setToolTip("Shape fill color")
        self.color_button.clicked.connect(self._pick_color)
        fmt_tb.addWidget(self.color_button)

        fmt_tb.addWidget(QLabel(" Label:"))
        self.label_color_button = ColorButton(color="#333333")
        self.label_color_button.setToolTip("Label text color (right-click to add label)")
        self.label_color_button.clicked.connect(self._pick_label_color)
        fmt_tb.addWidget(self.label_color_button)

        fmt_tb.addSeparator()

        fmt_tb.addWidget(QLabel(" Font:"))
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Arial"))
        self.font_combo.setMaximumWidth(150)
        self.font_combo.setToolTip("Font family")
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        fmt_tb.addWidget(self.font_combo)

        fmt_tb.addWidget(QLabel(" Size:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 72)
        self.size_spin.setValue(14)
        self.size_spin.setToolTip("Font size")
        self.size_spin.valueChanged.connect(self._on_size_changed)
        fmt_tb.addWidget(self.size_spin)

        self.bold_action = QAction("B", self)
        self.bold_action.setCheckable(True)
        self.bold_action.setToolTip("Bold")
        font = self.bold_action.font()
        font.setBold(True)
        self.bold_action.setFont(font)
        self.bold_action.triggered.connect(self._on_bold_changed)
        fmt_tb.addAction(self.bold_action)

        self.underline_action = QAction("U", self)
        self.underline_action.setCheckable(True)
        self.underline_action.setToolTip("Underline")
        font = self.underline_action.font()
        font.setUnderline(True)
        self.underline_action.setFont(font)
        self.underline_action.triggered.connect(self._on_underline_changed)
        fmt_tb.addAction(self.underline_action)

        # --- File toolbar ---
        file_tb = QToolBar("File")
        file_tb.setIconSize(icon_size)
        self.addToolBar(file_tb)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.setToolTip("Save diagram to JSON (Ctrl+S)")
        save_action.triggered.connect(lambda: self.export_manager.export_json(self))
        file_tb.addAction(save_action)

        load_action = QAction("Load", self)
        load_action.setShortcut(QKeySequence("Ctrl+O"))
        load_action.setToolTip("Load diagram from JSON (Ctrl+O)")
        load_action.triggered.connect(lambda: self.export_manager.load_json(self))
        file_tb.addAction(load_action)

        import_action = QAction("Import", self)
        import_action.setToolTip("Import shapes from JSON (merges into current canvas)")
        import_action.triggered.connect(lambda: self.export_manager.import_json(self))
        file_tb.addAction(import_action)

        image_action = QAction(create_icon(draw_image), "Picture", self)
        image_action.setToolTip("Import a picture as an object")
        image_action.triggered.connect(self._import_image)
        file_tb.addAction(image_action)

        file_tb.addSeparator()

        export_svg = QAction("SVG", self)
        export_svg.setToolTip("Export to SVG")
        export_svg.triggered.connect(lambda: self.export_manager.export_svg(self))
        file_tb.addAction(export_svg)

        export_png = QAction("PNG", self)
        export_png.setToolTip("Export to PNG")
        export_png.triggered.connect(lambda: self.export_manager.export_png(self))
        file_tb.addAction(export_png)

        file_tb.addSeparator()

        clear_action = QAction("Clear", self)
        clear_action.setToolTip("Clear all")
        clear_action.triggered.connect(self.scene.clear_all)
        file_tb.addAction(clear_action)

        file_tb.addSeparator()

        # Grid and snap toggles
        grid_action = QAction("Grid", self)
        grid_action.setCheckable(True)
        grid_action.setToolTip("Toggle grid overlay")
        grid_action.triggered.connect(self.scene.toggle_grid)
        file_tb.addAction(grid_action)

        snap_action = QAction("Snap", self)
        snap_action.setCheckable(True)
        snap_action.setToolTip("Toggle snap-to-grid")
        snap_action.triggered.connect(self.scene.toggle_snap)
        file_tb.addAction(snap_action)

        file_tb.addSeparator()

        help_action = QAction("?", self)
        help_action.setToolTip("Keyboard shortcuts & help")
        help_action.triggered.connect(self._show_help)
        file_tb.addAction(help_action)

    def _add_tool_actions(self, toolbar, tools, default_mode=None):
        """Add checkable tool actions to a toolbar with optional shortcuts."""
        for mode, tooltip, draw_func, shortcut in tools:
            icon = create_icon(draw_func)
            action = QAction(icon, "", self)
            action.setCheckable(True)
            tip = f"{tooltip} ({shortcut})" if shortcut else tooltip
            action.setToolTip(tip)
            action.triggered.connect(lambda checked, m=mode: self.scene.set_mode(m))
            self.tool_group.addAction(action)
            toolbar.addAction(action)
            self._tool_actions[mode] = action

            if mode == default_mode:
                action.setChecked(True)

            if shortcut:
                sc = QShortcut(QKeySequence(shortcut), self)
                sc.activated.connect(lambda m=mode: self._activate_tool(m))
    
    def _activate_tool(self, mode):
        """Switch to a tool mode via keyboard shortcut."""
        action = self._tool_actions.get(mode)
        if action:
            action.setChecked(True)
            self.scene.set_mode(mode)

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

    def _on_arrow_selected(self, arrow):
        """Update arrow toolbar controls to reflect selected arrow's properties."""
        self.line_style_combo.blockSignals(True)
        self.line_style_combo.setCurrentText(arrow.line_style)
        self.line_style_combo.blockSignals(False)

        self.line_width_combo.blockSignals(True)
        self.line_width_combo.setCurrentText(str(arrow.line_width))
        self.line_width_combo.blockSignals(False)

        self.start_cap_combo.blockSignals(True)
        self.start_cap_combo.setCurrentText(arrow.start_cap.capitalize())
        self.start_cap_combo.blockSignals(False)

        self.end_cap_combo.blockSignals(True)
        self.end_cap_combo.setCurrentText(arrow.end_cap.capitalize())
        self.end_cap_combo.blockSignals(False)

    def _on_line_style_changed(self, style_name):
        """Apply line style to selected arrows."""
        from arrows import Arrow
        for item in self.scene.selectedItems():
            if isinstance(item, Arrow):
                item.set_line_style(style_name)

    def _on_line_width_changed(self, width_text):
        """Apply line width to selected arrows."""
        from arrows import Arrow
        width = int(width_text)
        for item in self.scene.selectedItems():
            if isinstance(item, Arrow):
                item.set_line_width(width)

    def _on_start_cap_changed(self, cap_name):
        """Apply start cap style to selected arrows and set default for new ones."""
        from arrows import Arrow
        style = cap_name.lower()
        self.scene.current_start_cap = style
        for item in self.scene.selectedItems():
            if isinstance(item, Arrow):
                item.set_start_cap(style)

    def _on_end_cap_changed(self, cap_name):
        """Apply end cap style to selected arrows and set default for new ones."""
        from arrows import Arrow
        style = cap_name.lower()
        self.scene.current_end_cap = style
        for item in self.scene.selectedItems():
            if isinstance(item, Arrow):
                item.set_end_cap(style)

    def _import_image(self):
        """Import an image, copy it to the diagrams folder, and add it to the scene."""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        from shapes import DiagramImage
        
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Picture", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.svg)"
        )
        
        if not filepath:
            return
            
        src_path = Path(filepath)
        dest_dir = Path("diagrams")
        dest_dir.mkdir(exist_ok=True)
        dest_path = dest_dir / src_path.name
        
        try:
            # Copy file to diagrams folder if it's not already there
            if src_path.resolve() != dest_path.resolve():
                shutil.copy2(src_path, dest_path)
            
            # Add to scene at center of view
            view_rect = self.view.viewport().rect()
            scene_center = self.view.mapToScene(view_rect.center())
            
            self.scene.save_undo()
            image_item = DiagramImage(
                scene_center.x() - 50, scene_center.y() - 50,
                str(dest_path)
            )
            self.scene.addItem(image_item)
            self.scene.clearSelection()
            image_item.setSelected(True)
            self.statusBar().showMessage(f"Imported image: {src_path.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import image: {e}")

    def _show_help(self):
        """Show keyboard shortcuts and controls in a formatted popup."""
        html = """
        <style>
            table { border-collapse: collapse; width: 100%; margin-bottom: 12px; }
            th { background: #2c3e50; color: white; padding: 6px 10px; text-align: left; }
            td { padding: 4px 10px; border-bottom: 1px solid #ddd; }
            tr:nth-child(even) { background: #f2f2f2; }
            h3 { margin: 10px 0 4px 0; color: #2c3e50; }
        </style>

        <h3>Tool Shortcuts</h3>
        <table>
            <tr><th>Key</th><th>Tool</th></tr>
            <tr><td>V</td><td>Select</td></tr>
            <tr><td>R</td><td>Rectangle</td></tr>
            <tr><td>S</td><td>Square</td></tr>
            <tr><td>O</td><td>Oval</td></tr>
            <tr><td>I</td><td>Circle</td></tr>
            <tr><td>D</td><td>Diamond</td></tr>
            <tr><td>H</td><td>Hexagon</td></tr>
            <tr><td>G</td><td>Octagon</td></tr>
            <tr><td>T</td><td>Triangle (Up)</td></tr>
            <tr><td>X</td><td>Text Label</td></tr>
            <tr><td>A</td><td>Line</td></tr>
        </table>

        <h3>Editing</h3>
        <table>
            <tr><th>Shortcut</th><th>Action</th></tr>
            <tr><td>Ctrl+C</td><td>Copy</td></tr>
            <tr><td>Ctrl+X</td><td>Cut</td></tr>
            <tr><td>Ctrl+V</td><td>Paste</td></tr>
            <tr><td>Ctrl+Z</td><td>Undo</td></tr>
            <tr><td>Ctrl+Y</td><td>Redo</td></tr>
            <tr><td>Delete</td><td>Delete selected</td></tr>
            <tr><td>F2</td><td>Rename / edit label</td></tr>
            <tr><td>Escape</td><td>Clear selection</td></tr>
            <tr><td>+ / =</td><td>Layer up (send forward)</td></tr>
            <tr><td>-</td><td>Layer down (send backward)</td></tr>
        </table>

        <h3>Arrows &amp; Lines</h3>
        <table>
            <tr><th>Action</th><th>How</th></tr>
            <tr><td>Free-standing line</td><td>Line tool → click empty space for start &amp; end</td></tr>
            <tr><td>Connect to shape</td><td>Line tool → click shape for start/end</td></tr>
            <tr><td>Endpoint style</td><td>Select arrow → Start/End dropdowns (None, Arrow, Ball)</td></tr>
            <tr><td>Add bend point</td><td>Double-click an arrow segment</td></tr>
            <tr><td>Move bend point</td><td>Drag the blue handle</td></tr>
            <tr><td>Remove bend point</td><td>Double-click handle, or right-click → Remove</td></tr>
        </table>

        <h3>File</h3>
        <table>
            <tr><th>Shortcut</th><th>Action</th></tr>
            <tr><td>Ctrl+S</td><td>Save diagram</td></tr>
            <tr><td>Ctrl+O</td><td>Open diagram</td></tr>
        </table>

        <h3>Navigation</h3>
        <table>
            <tr><th>Action</th><th>How</th></tr>
            <tr><td>Zoom in/out</td><td>Mouse wheel</td></tr>
            <tr><td>Multi-select</td><td>Ctrl+Click or Shift+Click</td></tr>
            <tr><td>Box select</td><td>Drag on empty canvas</td></tr>
            <tr><td>Additive box select</td><td>Shift+Drag</td></tr>
            <tr><td>Double-click canvas</td><td>Add shape</td></tr>
            <tr><td>Double-click shape</td><td>Edit label</td></tr>
            <tr><td>Right-click</td><td>Context menu</td></tr>
        </table>
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts & Help")
        dialog.setMinimumSize(420, 520)
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setHtml(html)
        browser.setOpenExternalLinks(False)
        layout.addWidget(browser)
        dialog.exec_()