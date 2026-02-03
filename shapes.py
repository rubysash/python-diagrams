from PyQt5.QtWidgets import (QGraphicsRectItem, QGraphicsEllipseItem, 
                             QGraphicsPolygonItem, QGraphicsTextItem, QGraphicsItem)
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPolygonF, QColor, QPen, QBrush, QFont

from handles import ResizeHandle


class BaseShape:
    """Mixin providing common functionality for all diagram shapes."""
    
    MIN_WIDTH = 40
    MIN_HEIGHT = 30
    
    def _get_contrasting_color(self, color):
        """Return a contrasting color (white or dark) based on luminance."""
        r, g, b = color.red(), color.green(), color.blue()
        # Calculate perceived luminance
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        # Return white for dark colors, dark gray for light colors
        return QColor("#ffffff") if luminance < 0.5 else QColor("#333333")
    
    def init_shape(self, x, y, width, height, color):
        self.shape_width = width
        self.shape_height = height
        self.shape_color = QColor(color)
        self.label = None
        self.label_color = self._get_contrasting_color(self.shape_color)
        self.label_font_size = 14  # Default label font size
        self.arrows = []
        self._resizing = False
        self._initial_rect = None
        
        self.setPos(x, y)
        self.update_appearance()
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable | 
            QGraphicsItem.ItemSendsGeometryChanges
        )
        
        self.handles = []
        for pos in [ResizeHandle.TOP_LEFT, ResizeHandle.TOP_RIGHT,
                    ResizeHandle.BOTTOM_LEFT, ResizeHandle.BOTTOM_RIGHT]:
            handle = ResizeHandle(self, pos)
            self.handles.append(handle)
        self.update_handles()
    
    def update_appearance(self):
        self.setBrush(QBrush(self.shape_color))
        self.setPen(QPen(self.shape_color.darker(120), 2))
    
    def set_color(self, color):
        self.shape_color = QColor(color)
        self.update_appearance()
    
    def get_color(self):
        return self.shape_color
    
    def set_label_color(self, color):
        self.label_color = QColor(color)
        if self.label:
            self.label.setDefaultTextColor(self.label_color)
    
    def get_label_color(self):
        return self.label_color
    
    def set_label_font_size(self, size):
        """Set the font size for the label."""
        self.label_font_size = size
        if self.label:
            font = self.label.font()
            font.setPointSize(size)
            self.label.setFont(font)
            self.center_label()
    
    def get_label_font_size(self):
        """Get the current label font size."""
        return self.label_font_size
    
    def add_label(self, text):
        if self.label:
            self.label.setPlainText(text)
        else:
            self.label = QGraphicsTextItem(text, self)
            self.label.setDefaultTextColor(self.label_color)
        # Apply font size
        font = QFont()
        font.setPointSize(self.label_font_size)
        self.label.setFont(font)
        self.center_label()
    
    def center_label(self):
        if self.label:
            rect = self.boundingRect()
            label_rect = self.label.boundingRect()
            self.label.setPos(
                rect.center().x() - label_rect.width() / 2,
                rect.center().y() - label_rect.height() / 2
            )
    
    def get_center(self):
        rect = self.boundingRect()
        return self.mapToScene(rect.center())
    
    def get_connection_point(self, target_pos):
        center = self.get_center()
        rect = self.sceneBoundingRect()
        
        dx = target_pos.x() - center.x()
        dy = target_pos.y() - center.y()
        
        if abs(dx) > abs(dy):
            if dx > 0:
                return QPointF(rect.right(), center.y())
            else:
                return QPointF(rect.left(), center.y())
        else:
            if dy > 0:
                return QPointF(center.x(), rect.bottom())
            else:
                return QPointF(center.x(), rect.top())
    
    def add_arrow(self, arrow):
        if arrow not in self.arrows:
            self.arrows.append(arrow)
    
    def remove_arrow(self, arrow):
        if arrow in self.arrows:
            self.arrows.remove(arrow)
    
    def update_arrows(self):
        for arrow in self.arrows:
            arrow.update_position()
    
    def update_handles(self):
        rect = self.boundingRect()
        positions = {
            ResizeHandle.TOP_LEFT: rect.topLeft(),
            ResizeHandle.TOP_RIGHT: rect.topRight(),
            ResizeHandle.BOTTOM_LEFT: rect.bottomLeft(),
            ResizeHandle.BOTTOM_RIGHT: rect.bottomRight()
        }
        for handle in self.handles:
            handle.setPos(positions[handle.position])
    
    def show_handles(self, visible):
        for handle in self.handles:
            handle.setVisible(visible)
    
    def start_resize(self):
        self._resizing = True
        self._initial_rect = self.boundingRect()
        # Temporarily disable moving while resizing
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
    
    def end_resize(self):
        self._resizing = False
        self._initial_rect = None
        # Restore movability
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.update_handles()
    
    def _on_item_change(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.show_handles(value)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            self.update_arrows()


class DiagramRect(QGraphicsRectItem, BaseShape):
    """Rectangle shape."""
    
    def __init__(self, x, y, width=100, height=60, color="#3498db"):
        super().__init__(0, 0, width, height)
        self.init_shape(x, y, width, height, color)
    
    def itemChange(self, change, value):
        self._on_item_change(change, value)
        return super().itemChange(change, value)
    
    def handle_resize(self, handle_pos, new_pos):
        if not self._resizing:
            return
        rect = self.rect()
        
        if handle_pos == ResizeHandle.TOP_LEFT:
            new_rect = QRectF(new_pos, rect.bottomRight())
        elif handle_pos == ResizeHandle.TOP_RIGHT:
            new_rect = QRectF(QPointF(rect.left(), new_pos.y()), 
                             QPointF(new_pos.x(), rect.bottom()))
        elif handle_pos == ResizeHandle.BOTTOM_LEFT:
            new_rect = QRectF(QPointF(new_pos.x(), rect.top()),
                             QPointF(rect.right(), new_pos.y()))
        elif handle_pos == ResizeHandle.BOTTOM_RIGHT:
            new_rect = QRectF(rect.topLeft(), new_pos)
        
        if new_rect.width() >= self.MIN_WIDTH and new_rect.height() >= self.MIN_HEIGHT:
            self.setRect(new_rect.normalized())
            self.shape_width = new_rect.width()
            self.shape_height = new_rect.height()
            self.center_label()
            self.update_arrows()


class DiagramOval(QGraphicsEllipseItem, BaseShape):
    """Oval/ellipse shape."""
    
    def __init__(self, x, y, width=100, height=60, color="#2ecc71"):
        super().__init__(0, 0, width, height)
        self.init_shape(x, y, width, height, color)
    
    def itemChange(self, change, value):
        self._on_item_change(change, value)
        return super().itemChange(change, value)
    
    def handle_resize(self, handle_pos, new_pos):
        if not self._resizing:
            return
        rect = self.rect()
        
        if handle_pos == ResizeHandle.TOP_LEFT:
            new_rect = QRectF(new_pos, rect.bottomRight())
        elif handle_pos == ResizeHandle.TOP_RIGHT:
            new_rect = QRectF(QPointF(rect.left(), new_pos.y()), 
                             QPointF(new_pos.x(), rect.bottom()))
        elif handle_pos == ResizeHandle.BOTTOM_LEFT:
            new_rect = QRectF(QPointF(new_pos.x(), rect.top()),
                             QPointF(rect.right(), new_pos.y()))
        elif handle_pos == ResizeHandle.BOTTOM_RIGHT:
            new_rect = QRectF(rect.topLeft(), new_pos)
        
        if new_rect.width() >= self.MIN_WIDTH and new_rect.height() >= self.MIN_HEIGHT:
            self.setRect(new_rect.normalized())
            self.shape_width = new_rect.width()
            self.shape_height = new_rect.height()
            self.center_label()
            self.update_arrows()


class DiagramDiamond(QGraphicsPolygonItem, BaseShape):
    """Diamond shape (decision node)."""
    
    def __init__(self, x, y, width=100, height=60, color="#e74c3c"):
        self._width = width
        self._height = height
        poly = self._create_polygon(width, height)
        super().__init__(poly)
        self.init_shape(x, y, width, height, color)
    
    def itemChange(self, change, value):
        self._on_item_change(change, value)
        return super().itemChange(change, value)
    
    def _create_polygon(self, width, height):
        return QPolygonF([
            QPointF(width / 2, 0),
            QPointF(width, height / 2),
            QPointF(width / 2, height),
            QPointF(0, height / 2)
        ])
    
    def handle_resize(self, handle_pos, new_pos):
        if not self._resizing:
            return
        rect = self.boundingRect()
        
        if handle_pos == ResizeHandle.TOP_LEFT:
            new_rect = QRectF(new_pos, rect.bottomRight())
        elif handle_pos == ResizeHandle.TOP_RIGHT:
            new_rect = QRectF(QPointF(rect.left(), new_pos.y()), 
                             QPointF(new_pos.x(), rect.bottom()))
        elif handle_pos == ResizeHandle.BOTTOM_LEFT:
            new_rect = QRectF(QPointF(new_pos.x(), rect.top()),
                             QPointF(rect.right(), new_pos.y()))
        elif handle_pos == ResizeHandle.BOTTOM_RIGHT:
            new_rect = QRectF(rect.topLeft(), new_pos)
        
        new_rect = new_rect.normalized()
        
        if new_rect.width() >= self.MIN_WIDTH and new_rect.height() >= self.MIN_HEIGHT:
            self._width = new_rect.width()
            self._height = new_rect.height()
            self.shape_width = self._width
            self.shape_height = self._height
            
            new_poly = self._create_polygon(self._width, self._height)
            offset = new_rect.topLeft()
            translated_poly = QPolygonF([p + offset for p in new_poly])
            self.setPolygon(translated_poly)
            
            self.center_label()
            self.update_arrows()


class DiagramTriangle(QGraphicsPolygonItem, BaseShape):
    """Triangle shape (pointing up)."""
    
    def __init__(self, x, y, width=100, height=80, color="#9b59b6"):
        self._width = width
        self._height = height
        poly = self._create_polygon(width, height)
        super().__init__(poly)
        self.init_shape(x, y, width, height, color)
    
    def itemChange(self, change, value):
        self._on_item_change(change, value)
        return super().itemChange(change, value)
    
    def _create_polygon(self, width, height):
        return QPolygonF([
            QPointF(width / 2, 0),
            QPointF(width, height),
            QPointF(0, height)
        ])
    
    def handle_resize(self, handle_pos, new_pos):
        if not self._resizing:
            return
        rect = self.boundingRect()
        
        if handle_pos == ResizeHandle.TOP_LEFT:
            new_rect = QRectF(new_pos, rect.bottomRight())
        elif handle_pos == ResizeHandle.TOP_RIGHT:
            new_rect = QRectF(QPointF(rect.left(), new_pos.y()), 
                             QPointF(new_pos.x(), rect.bottom()))
        elif handle_pos == ResizeHandle.BOTTOM_LEFT:
            new_rect = QRectF(QPointF(new_pos.x(), rect.top()),
                             QPointF(rect.right(), new_pos.y()))
        elif handle_pos == ResizeHandle.BOTTOM_RIGHT:
            new_rect = QRectF(rect.topLeft(), new_pos)
        
        new_rect = new_rect.normalized()
        
        if new_rect.width() >= self.MIN_WIDTH and new_rect.height() >= self.MIN_HEIGHT:
            self._width = new_rect.width()
            self._height = new_rect.height()
            self.shape_width = self._width
            self.shape_height = self._height
            
            new_poly = self._create_polygon(self._width, self._height)
            offset = new_rect.topLeft()
            translated_poly = QPolygonF([p + offset for p in new_poly])
            self.setPolygon(translated_poly)
            
            self.center_label()
            self.update_arrows()


class DiagramTriangleInverted(QGraphicsPolygonItem, BaseShape):
    """Inverted triangle shape (pointing down)."""
    
    def __init__(self, x, y, width=100, height=80, color="#e67e22"):
        self._width = width
        self._height = height
        poly = self._create_polygon(width, height)
        super().__init__(poly)
        self.init_shape(x, y, width, height, color)
    
    def itemChange(self, change, value):
        self._on_item_change(change, value)
        return super().itemChange(change, value)
    
    def _create_polygon(self, width, height):
        return QPolygonF([
            QPointF(0, 0),
            QPointF(width, 0),
            QPointF(width / 2, height)
        ])
    
    def handle_resize(self, handle_pos, new_pos):
        if not self._resizing:
            return
        rect = self.boundingRect()
        
        if handle_pos == ResizeHandle.TOP_LEFT:
            new_rect = QRectF(new_pos, rect.bottomRight())
        elif handle_pos == ResizeHandle.TOP_RIGHT:
            new_rect = QRectF(QPointF(rect.left(), new_pos.y()), 
                             QPointF(new_pos.x(), rect.bottom()))
        elif handle_pos == ResizeHandle.BOTTOM_LEFT:
            new_rect = QRectF(QPointF(new_pos.x(), rect.top()),
                             QPointF(rect.right(), new_pos.y()))
        elif handle_pos == ResizeHandle.BOTTOM_RIGHT:
            new_rect = QRectF(rect.topLeft(), new_pos)
        
        new_rect = new_rect.normalized()
        
        if new_rect.width() >= self.MIN_WIDTH and new_rect.height() >= self.MIN_HEIGHT:
            self._width = new_rect.width()
            self._height = new_rect.height()
            self.shape_width = self._width
            self.shape_height = self._height
            
            new_poly = self._create_polygon(self._width, self._height)
            offset = new_rect.topLeft()
            translated_poly = QPolygonF([p + offset for p in new_poly])
            self.setPolygon(translated_poly)
            
            self.center_label()
            self.update_arrows()


class DiagramTriangleLeft(QGraphicsPolygonItem, BaseShape):
    """Left-facing triangle shape (pointing left)."""
    
    def __init__(self, x, y, width=80, height=100, color="#1abc9c"):
        self._width = width
        self._height = height
        poly = self._create_polygon(width, height)
        super().__init__(poly)
        self.init_shape(x, y, width, height, color)
    
    def itemChange(self, change, value):
        self._on_item_change(change, value)
        return super().itemChange(change, value)
    
    def _create_polygon(self, width, height):
        return QPolygonF([
            QPointF(width, 0),
            QPointF(width, height),
            QPointF(0, height / 2)
        ])
    
    def handle_resize(self, handle_pos, new_pos):
        if not self._resizing:
            return
        rect = self.boundingRect()
        
        if handle_pos == ResizeHandle.TOP_LEFT:
            new_rect = QRectF(new_pos, rect.bottomRight())
        elif handle_pos == ResizeHandle.TOP_RIGHT:
            new_rect = QRectF(QPointF(rect.left(), new_pos.y()), 
                             QPointF(new_pos.x(), rect.bottom()))
        elif handle_pos == ResizeHandle.BOTTOM_LEFT:
            new_rect = QRectF(QPointF(new_pos.x(), rect.top()),
                             QPointF(rect.right(), new_pos.y()))
        elif handle_pos == ResizeHandle.BOTTOM_RIGHT:
            new_rect = QRectF(rect.topLeft(), new_pos)
        
        new_rect = new_rect.normalized()
        
        if new_rect.width() >= self.MIN_WIDTH and new_rect.height() >= self.MIN_HEIGHT:
            self._width = new_rect.width()
            self._height = new_rect.height()
            self.shape_width = self._width
            self.shape_height = self._height
            
            new_poly = self._create_polygon(self._width, self._height)
            offset = new_rect.topLeft()
            translated_poly = QPolygonF([p + offset for p in new_poly])
            self.setPolygon(translated_poly)
            
            self.center_label()
            self.update_arrows()


class DiagramTriangleRight(QGraphicsPolygonItem, BaseShape):
    """Right-facing triangle shape (pointing right)."""
    
    def __init__(self, x, y, width=80, height=100, color="#3498db"):
        self._width = width
        self._height = height
        poly = self._create_polygon(width, height)
        super().__init__(poly)
        self.init_shape(x, y, width, height, color)
    
    def itemChange(self, change, value):
        self._on_item_change(change, value)
        return super().itemChange(change, value)
    
    def _create_polygon(self, width, height):
        return QPolygonF([
            QPointF(0, 0),
            QPointF(width, height / 2),
            QPointF(0, height)
        ])
    
    def handle_resize(self, handle_pos, new_pos):
        if not self._resizing:
            return
        rect = self.boundingRect()
        
        if handle_pos == ResizeHandle.TOP_LEFT:
            new_rect = QRectF(new_pos, rect.bottomRight())
        elif handle_pos == ResizeHandle.TOP_RIGHT:
            new_rect = QRectF(QPointF(rect.left(), new_pos.y()), 
                             QPointF(new_pos.x(), rect.bottom()))
        elif handle_pos == ResizeHandle.BOTTOM_LEFT:
            new_rect = QRectF(QPointF(new_pos.x(), rect.top()),
                             QPointF(rect.right(), new_pos.y()))
        elif handle_pos == ResizeHandle.BOTTOM_RIGHT:
            new_rect = QRectF(rect.topLeft(), new_pos)
        
        new_rect = new_rect.normalized()
        
        if new_rect.width() >= self.MIN_WIDTH and new_rect.height() >= self.MIN_HEIGHT:
            self._width = new_rect.width()
            self._height = new_rect.height()
            self.shape_width = self._width
            self.shape_height = self._height
            
            new_poly = self._create_polygon(self._width, self._height)
            offset = new_rect.topLeft()
            translated_poly = QPolygonF([p + offset for p in new_poly])
            self.setPolygon(translated_poly)
            
            self.center_label()
            self.update_arrows()


class DiagramText(QGraphicsTextItem):
    """Editable text label shape."""
    
    MIN_WIDTH = 20
    MIN_HEIGHT = 20
    
    def __init__(self, x, y, text="Text", font_family="Arial", font_size=14, 
                 color="#333333", bold=False, underline=False):
        super().__init__(text)
        
        self.text_color = QColor(color)
        self.font_family = font_family
        self.font_size = font_size
        self.is_bold = bold
        self.is_underline = underline
        self.arrows = []
        self.handles = []
        self.label = None  # For compatibility with BaseShape interface
        
        self.setPos(x, y)
        self.setDefaultTextColor(self.text_color)
        self.update_font()
        
        self.setFlags(
            QGraphicsItem.ItemIsMovable | 
            QGraphicsItem.ItemIsSelectable | 
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setZValue(1)
    
    def update_font(self):
        font = QFont(self.font_family, self.font_size)
        font.setBold(self.is_bold)
        font.setUnderline(self.is_underline)
        self.setFont(font)
    
    def set_text(self, text):
        self.setPlainText(text)
    
    def get_text(self):
        return self.toPlainText()
    
    def set_color(self, color):
        self.text_color = QColor(color)
        self.setDefaultTextColor(self.text_color)
    
    def get_color(self):
        return self.text_color
    
    def set_font_family(self, family):
        self.font_family = family
        self.update_font()
    
    def set_font_size(self, size):
        self.font_size = size
        self.update_font()
    
    def set_bold(self, bold):
        self.is_bold = bold
        self.update_font()
    
    def set_underline(self, underline):
        self.is_underline = underline
        self.update_font()
    
    def get_center(self):
        rect = self.boundingRect()
        return self.mapToScene(rect.center())
    
    def get_connection_point(self, target_pos):
        center = self.get_center()
        rect = self.sceneBoundingRect()
        
        dx = target_pos.x() - center.x()
        dy = target_pos.y() - center.y()
        
        if abs(dx) > abs(dy):
            if dx > 0:
                return QPointF(rect.right(), center.y())
            else:
                return QPointF(rect.left(), center.y())
        else:
            if dy > 0:
                return QPointF(center.x(), rect.bottom())
            else:
                return QPointF(center.x(), rect.top())
    
    def add_arrow(self, arrow):
        if arrow not in self.arrows:
            self.arrows.append(arrow)
    
    def remove_arrow(self, arrow):
        if arrow in self.arrows:
            self.arrows.remove(arrow)
    
    def update_arrows(self):
        for arrow in self.arrows:
            arrow.update_position()
    
    def add_label(self, text):
        """For compatibility - just update the text content."""
        self.setPlainText(text)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            self.update_arrows()
        return super().itemChange(change, value)