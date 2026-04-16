import json
from pathlib import Path
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QRectF, QSize
from PyQt5.QtGui import QPainter, QImage, QColor
from PyQt5.QtSvg import QSvgGenerator

from shapes import (
    DiagramRect, DiagramSquare, DiagramOval, DiagramCircle,
    DiagramDiamond, DiagramHexagon, DiagramOctagon,
    DiagramTriangle, DiagramTriangleInverted,
    DiagramTriangleLeft, DiagramTriangleRight,
    DiagramText, DiagramImage,
)
from arrows import Arrow, AnchorPoint

# All geometric shape classes (excludes DiagramText which serializes differently)
_GEO_SHAPES = (
    DiagramRect, DiagramSquare, DiagramOval, DiagramCircle,
    DiagramDiamond, DiagramHexagon, DiagramOctagon,
    DiagramTriangle, DiagramTriangleInverted,
    DiagramTriangleLeft, DiagramTriangleRight,
)

# All shape classes including text, images, and anchors
_ALL_SHAPES = _GEO_SHAPES + (DiagramText, DiagramImage, AnchorPoint)


def _build_shape_constructors():
    """Return a dict mapping type names to factory functions for deserialization."""
    # Geometric shapes all share the same (x, y, width, height, color) signature
    geo_map = {
        'DiagramRect': (DiagramRect, 100, 60, '#3498db'),
        'DiagramSquare': (DiagramSquare, 80, 80, '#2980b9'),
        'DiagramOval': (DiagramOval, 100, 60, '#2ecc71'),
        'DiagramCircle': (DiagramCircle, 80, 80, '#27ae60'),
        'DiagramDiamond': (DiagramDiamond, 100, 60, '#e74c3c'),
        'DiagramHexagon': (DiagramHexagon, 100, 86, '#8e44ad'),
        'DiagramOctagon': (DiagramOctagon, 100, 100, '#c0392b'),
        'DiagramTriangle': (DiagramTriangle, 100, 80, '#9b59b6'),
        'DiagramTriangleInverted': (DiagramTriangleInverted, 100, 80, '#e67e22'),
        'DiagramTriangleLeft': (DiagramTriangleLeft, 80, 100, '#1abc9c'),
        'DiagramTriangleRight': (DiagramTriangleRight, 80, 100, '#3498db'),
    }

    constructors = {}
    for name, (cls, dw, dh, dc) in geo_map.items():
        constructors[name] = (
            lambda d, _cls=cls, _dw=dw, _dh=dh, _dc=dc: _cls(
                d.get('x', 0), d.get('y', 0),
                width=d.get('width', _dw),
                height=d.get('height', _dh),
                color=d.get('color', _dc),
            )
        )

    # DiagramText has a different constructor signature
    constructors['DiagramText'] = lambda d: DiagramText(
        d.get('x', 0), d.get('y', 0),
        text=d.get('text', 'Text'),
        font_family=d.get('font_family', 'Arial'),
        font_size=d.get('font_size', 14),
        color=d.get('color', '#333333'),
        bold=d.get('bold', False),
        underline=d.get('underline', False),
    )

    # AnchorPoint for free-floating arrow endpoints
    constructors['AnchorPoint'] = lambda d: AnchorPoint(
        d.get('x', 0), d.get('y', 0),
    )

    # DiagramImage for imported pictures
    constructors['DiagramImage'] = lambda d: DiagramImage(
        d.get('x', 0), d.get('y', 0),
        image_path=d.get('image_path'),
        width=d.get('width', 100),
        height=d.get('height', 100),
    )

    return constructors


class ExportManager:
    """Handles exporting diagram to various formats."""
    
    PADDING = 20
    PNG_SCALE = 2

    def __init__(self, scene):
        self.scene = scene

    def _hide_anchors(self):
        """Hide anchor points before export for clean output."""
        self._hidden_anchors = []
        for item in self.scene.items():
            if isinstance(item, AnchorPoint) and item.isVisible():
                item.setVisible(False)
                self._hidden_anchors.append(item)

    def _show_anchors(self):
        """Restore anchor point visibility after export."""
        for item in self._hidden_anchors:
            item.setVisible(True)
        self._hidden_anchors = []

    def _get_export_rect(self):
        """Get bounding rectangle of all items with padding."""
        items_rect = self.scene.itemsBoundingRect()
        if items_rect.isEmpty():
            return None
        items_rect.adjust(-self.PADDING, -self.PADDING, 
                          self.PADDING, self.PADDING)
        return items_rect
    
    def _serialize_scene(self):
        """Serialize all shapes and arrows to a dictionary."""
        data = {
            'version': 1,
            'shapes': [],
            'arrows': []
        }
        
        shape_ids = {}  # Map shape objects to IDs for arrow references
        shape_id = 0
        
        # Serialize shapes
        for item in self.scene.items():
            if isinstance(item, AnchorPoint):
                shape_data = {
                    'id': shape_id,
                    'type': 'AnchorPoint',
                    'x': item.pos().x(),
                    'y': item.pos().y(),
                    'z': item.zValue()
                }
                data['shapes'].append(shape_data)
                shape_ids[item] = shape_id
                shape_id += 1

            elif isinstance(item, _GEO_SHAPES):
                shape_data = {
                    'id': shape_id,
                    'type': item.__class__.__name__,
                    'x': item.pos().x(),
                    'y': item.pos().y(),
                    'width': item.shape_width,
                    'height': item.shape_height,
                    'color': item.shape_color.name(),
                    'label': item.label.text() if item.label else None,
                    'label_color': item.label_color.name() if hasattr(item, 'label_color') else '#ffffff',
                    'label_font_size': item.label_font_size if hasattr(item, 'label_font_size') else 14,
                    'z': item.zValue()
                }
                data['shapes'].append(shape_data)
                shape_ids[item] = shape_id
                shape_id += 1

            elif isinstance(item, DiagramImage):
                shape_data = {
                    'id': shape_id,
                    'type': 'DiagramImage',
                    'x': item.pos().x(),
                    'y': item.pos().y(),
                    'width': item.shape_width,
                    'height': item.shape_height,
                    'image_path': Path(item.image_path).as_posix(),
                    'z': item.zValue()
                }
                data['shapes'].append(shape_data)
                shape_ids[item] = shape_id
                shape_id += 1

            elif isinstance(item, DiagramText):
                shape_data = {
                    'id': shape_id,
                    'type': 'DiagramText',
                    'x': item.pos().x(),
                    'y': item.pos().y(),
                    'text': item.toPlainText(),
                    'color': item.text_color.name(),
                    'font_family': item.font_family,
                    'font_size': item.font_size,
                    'bold': item.is_bold,
                    'underline': item.is_underline,
                    'z': item.zValue()
                }
                data['shapes'].append(shape_data)
                shape_ids[item] = shape_id
                shape_id += 1
        
        # Serialize arrows
        for item in self.scene.items():
            if isinstance(item, Arrow):
                if item.start_shape in shape_ids and item.end_shape in shape_ids:
                    arrow_data = {
                        'start_id': shape_ids[item.start_shape],
                        'end_id': shape_ids[item.end_shape],
                        'bidirectional': item.bidirectional,
                        'color': item.arrow_color.name(),
                        'label': item.label.text() if item.label else None,
                        'label_color': item.label_color.name() if hasattr(item, 'label_color') else '#333333',
                        'label_font_size': item.label_font_size if hasattr(item, 'label_font_size') else 9,
                        'line_style': item.line_style,
                        'line_width': item.line_width,
                        'bend_points': [{'x': bp.x(), 'y': bp.y()} for bp in item.bend_points],
                        'start_cap': item.start_cap,
                        'end_cap': item.end_cap,
                    }
                    data['arrows'].append(arrow_data)
        
        return data
    
    def _deserialize_scene(self, data):
        """Deserialize shapes and arrows from a dictionary."""
        self.scene.clear_all()
        
        shape_map = {}  # Map IDs to created shape objects
        
        # Create shapes using constructor map to avoid large if/elif chains
        constructors = _build_shape_constructors()
        for shape_data in data.get('shapes', []):
            shape_type = shape_data.get('type')
            shape_id = shape_data.get('id')

            constructor = constructors.get(shape_type)
            shape = constructor(shape_data) if constructor else None
            
            if shape:
                self.scene.addItem(shape)
                shape_map[shape_id] = shape
                
                # Set z-order if specified
                if 'z' in shape_data:
                    shape.setZValue(shape_data['z'])
                
                # Set label color and font size for non-text shapes
                if shape_type != 'DiagramText':
                    if hasattr(shape, 'set_label_color'):
                        label_color = shape_data.get('label_color', '#ffffff')
                        shape.set_label_color(label_color)
                    if hasattr(shape, 'label_font_size'):
                        shape.label_font_size = shape_data.get('label_font_size', 14)
                
                # Add label for non-text shapes
                if shape_type != 'DiagramText' and shape_data.get('label'):
                    shape.add_label(shape_data['label'])
        
        # Create arrows
        for arrow_data in data.get('arrows', []):
            start_id = arrow_data.get('start_id')
            end_id = arrow_data.get('end_id')
            
            if start_id in shape_map and end_id in shape_map:
                arrow = Arrow(
                    shape_map[start_id],
                    shape_map[end_id],
                    bidirectional=arrow_data.get('bidirectional', False),
                    color=arrow_data.get('color', '#333333'),
                    line_style=arrow_data.get('line_style', 'Solid'),
                    line_width=arrow_data.get('line_width', 2),
                    bend_points=arrow_data.get('bend_points', []),
                    start_cap=arrow_data.get('start_cap'),
                    end_cap=arrow_data.get('end_cap'),
                )
                self.scene.addItem(arrow)
                
                # Set label color and font size before adding label
                if 'label_color' in arrow_data:
                    arrow.set_label_color(arrow_data['label_color'])
                if 'label_font_size' in arrow_data:
                    arrow.label_font_size = arrow_data['label_font_size']
                
                if arrow_data.get('label'):
                    arrow.add_label(arrow_data['label'])
        
        # Auto-snap anchors to nearby shapes after load
        if hasattr(self.scene, '_snap_all_anchors'):
            self.scene._snap_all_anchors()

        # Force scene to update its internal index and refresh
        self.scene.setSceneRect(self.scene.sceneRect())
        self.scene.update()
    
    def export_json(self, parent=None):
        """Export scene to JSON file."""
        items = [item for item in self.scene.items()
                 if isinstance(item, (_ALL_SHAPES + (Arrow,)))]
        if not items:
            QMessageBox.warning(parent, "Export", "Nothing to export!")
            return False
        
        filepath, _ = QFileDialog.getSaveFileName(
            parent, "Save Diagram", "diagrams", "Diagram Files (*.json)"
        )
        
        if not filepath:
            return False
        
        if not filepath.endswith('.json'):
            filepath += '.json'
        
        data = self._serialize_scene()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        QMessageBox.information(parent, "Save", f"Saved to {filepath}")
        return filepath
    
    def load_json(self, parent=None):
        """Load scene from JSON file."""
        filepath, _ = QFileDialog.getOpenFileName(
            parent, "Load Diagram", "diagrams", "Diagram Files (*.json)"
        )
        
        if not filepath:
            return False
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self._deserialize_scene(data)
            QMessageBox.information(parent, "Load", f"Loaded {filepath}")
            return True
            
        except json.JSONDecodeError as e:
            QMessageBox.critical(parent, "Error", f"Invalid JSON file: {e}")
            return False
        except Exception as e:
            QMessageBox.critical(parent, "Error", f"Failed to load: {e}")
            return False
    
    def import_json(self, parent=None):
        """Import shapes from a JSON file into the current canvas (merge, no clear)."""
        filepath, _ = QFileDialog.getOpenFileName(
            parent, "Import Diagram", "diagrams", "Diagram Files (*.json)"
        )

        if not filepath:
            return False

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Use the scene's paste_data with zero offset to add items in place
            self.scene.save_undo()
            count = self.scene._paste_data(data, offset_x=0, offset_y=0)
            QMessageBox.information(parent, "Import",
                                    f"Imported {count} item(s) from {filepath}")
            return True

        except json.JSONDecodeError as e:
            QMessageBox.critical(parent, "Error", f"Invalid JSON file: {e}")
            return False
        except Exception as e:
            QMessageBox.critical(parent, "Error", f"Failed to import: {e}")
            return False

    def export_svg(self, parent=None):
        """Export scene to SVG file."""
        export_rect = self._get_export_rect()
        if not export_rect:
            QMessageBox.warning(parent, "Export", "Nothing to export!")
            return False
        
        filepath, _ = QFileDialog.getSaveFileName(
            parent, "Export SVG", "", "SVG Files (*.svg)"
        )
        
        if not filepath:
            return False
        
        if not filepath.endswith('.svg'):
            filepath += '.svg'
        
        self.scene.clearSelection()
        self._hide_anchors()

        # Use same scaling approach as PNG for consistent rendering
        scale = self.PNG_SCALE
        width = int(export_rect.width() * scale)
        height = int(export_rect.height() * scale)
        
        generator = QSvgGenerator()
        generator.setFileName(filepath)
        generator.setSize(QSize(width, height))
        # ViewBox in original coordinates - SVG viewers will scale properly
        generator.setViewBox(QRectF(0, 0, export_rect.width(), export_rect.height()))
        # Use 90 DPI - the SVG standard that matches Qt's internal calculations
        generator.setResolution(90)
        generator.setTitle("Diagram Export")
        generator.setDescription("Created with Diagram Builder")
        
        painter = QPainter()
        painter.begin(generator)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        painter.fillRect(QRectF(0, 0, export_rect.width(), export_rect.height()), QColor("#f9f9f9"))
        
        # Render using original coordinates (matching viewBox)
        target_rect = QRectF(0, 0, export_rect.width(), export_rect.height())
        self.scene.render(painter, target_rect, export_rect)
        
        painter.end()
        self._show_anchors()

        QMessageBox.information(parent, "Export", f"Saved to {filepath}")
        return filepath

    def export_png(self, parent=None):
        """Export scene to PNG file."""
        export_rect = self._get_export_rect()
        if not export_rect:
            QMessageBox.warning(parent, "Export", "Nothing to export!")
            return False
        
        filepath, _ = QFileDialog.getSaveFileName(
            parent, "Export PNG", "", "PNG Files (*.png)"
        )
        
        if not filepath:
            return False
        
        if not filepath.endswith('.png'):
            filepath += '.png'
        
        self.scene.clearSelection()
        self._hide_anchors()

        width = int(export_rect.width() * self.PNG_SCALE)
        height = int(export_rect.height() * self.PNG_SCALE)
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(QColor("#f9f9f9"))

        painter = QPainter()
        painter.begin(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        target_rect = QRectF(0, 0, width, height)
        self.scene.render(painter, target_rect, export_rect)

        painter.end()
        self._show_anchors()
        
        image.save(filepath)
        
        QMessageBox.information(parent, "Export", f"Saved to {filepath}")
        return filepath