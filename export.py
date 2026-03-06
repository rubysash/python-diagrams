import json
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QRectF, QSize
from PyQt5.QtGui import QPainter, QImage, QColor
from PyQt5.QtSvg import QSvgGenerator

from shapes import DiagramRect, DiagramOval, DiagramDiamond, DiagramTriangle, DiagramText
from arrows import Arrow


class ExportManager:
    """Handles exporting diagram to various formats."""
    
    PADDING = 20
    PNG_SCALE = 2
    
    def __init__(self, scene):
        self.scene = scene
    
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
            if isinstance(item, (DiagramRect, DiagramOval, DiagramDiamond, DiagramTriangle)):
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
                        'label_font_size': item.label_font_size if hasattr(item, 'label_font_size') else 9
                    }
                    data['arrows'].append(arrow_data)
        
        return data
    
    def _deserialize_scene(self, data):
        """Deserialize shapes and arrows from a dictionary."""
        self.scene.clear_all()
        
        shape_map = {}  # Map IDs to created shape objects
        
        # Create shapes
        for shape_data in data.get('shapes', []):
            shape_type = shape_data.get('type')
            shape_id = shape_data.get('id')
            x = shape_data.get('x', 0)
            y = shape_data.get('y', 0)
            
            shape = None
            
            if shape_type == 'DiagramRect':
                shape = DiagramRect(
                    x, y,
                    width=shape_data.get('width', 100),
                    height=shape_data.get('height', 60),
                    color=shape_data.get('color', '#3498db')
                )
            elif shape_type == 'DiagramOval':
                shape = DiagramOval(
                    x, y,
                    width=shape_data.get('width', 100),
                    height=shape_data.get('height', 60),
                    color=shape_data.get('color', '#2ecc71')
                )
            elif shape_type == 'DiagramDiamond':
                shape = DiagramDiamond(
                    x, y,
                    width=shape_data.get('width', 100),
                    height=shape_data.get('height', 60),
                    color=shape_data.get('color', '#e74c3c')
                )
            elif shape_type == 'DiagramTriangle':
                shape = DiagramTriangle(
                    x, y,
                    width=shape_data.get('width', 100),
                    height=shape_data.get('height', 80),
                    color=shape_data.get('color', '#9b59b6')
                )
            elif shape_type == 'DiagramText':
                shape = DiagramText(
                    x, y,
                    text=shape_data.get('text', 'Text'),
                    font_family=shape_data.get('font_family', 'Arial'),
                    font_size=shape_data.get('font_size', 14),
                    color=shape_data.get('color', '#333333'),
                    bold=shape_data.get('bold', False),
                    underline=shape_data.get('underline', False)
                )
            
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
                    color=arrow_data.get('color', '#333333')
                )
                self.scene.addItem(arrow)
                
                # Set label color and font size before adding label
                if 'label_color' in arrow_data:
                    arrow.set_label_color(arrow_data['label_color'])
                if 'label_font_size' in arrow_data:
                    arrow.label_font_size = arrow_data['label_font_size']
                
                if arrow_data.get('label'):
                    arrow.add_label(arrow_data['label'])
        
        # Force scene to update its internal index and refresh
        self.scene.setSceneRect(self.scene.sceneRect())
        self.scene.update()
    
    def export_json(self, parent=None):
        """Export scene to JSON file."""
        items = [item for item in self.scene.items() 
                 if isinstance(item, (DiagramRect, DiagramOval, DiagramDiamond, 
                                      DiagramTriangle, DiagramText, Arrow))]
        if not items:
            QMessageBox.warning(parent, "Export", "Nothing to export!")
            return False
        
        filepath, _ = QFileDialog.getSaveFileName(
            parent, "Save Diagram", "", "Diagram Files (*.json)"
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
            parent, "Load Diagram", "", "Diagram Files (*.json)"
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
        
        image.save(filepath)
        
        QMessageBox.information(parent, "Export", f"Saved to {filepath}")
        return filepath