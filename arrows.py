import math
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPolygonItem, QGraphicsSimpleTextItem
from PyQt5.QtCore import Qt, QPointF, QLineF
from PyQt5.QtGui import QPen, QBrush, QColor, QPolygonF, QFont


class ArrowHead(QGraphicsPolygonItem):
    """Arrowhead triangle."""
    
    ARROW_SIZE = 12
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBrush(QBrush(QColor("#333333")))
        self.setPen(QPen(Qt.NoPen))
    
    def update_position(self, line_end, angle):
        p1 = line_end
        p2 = QPointF(
            line_end.x() - self.ARROW_SIZE * math.cos(angle - math.pi/6),
            line_end.y() - self.ARROW_SIZE * math.sin(angle - math.pi/6)
        )
        p3 = QPointF(
            line_end.x() - self.ARROW_SIZE * math.cos(angle + math.pi/6),
            line_end.y() - self.ARROW_SIZE * math.sin(angle + math.pi/6)
        )
        self.setPolygon(QPolygonF([p1, p2, p3]))
    
    def set_color(self, color):
        self.setBrush(QBrush(QColor(color)))


class Arrow(QGraphicsLineItem):
    """Arrow connecting two shapes."""
    
    def __init__(self, start_shape, end_shape, bidirectional=False, color="#333333"):
        super().__init__()
        
        self.start_shape = start_shape
        self.end_shape = end_shape
        self.bidirectional = bidirectional
        self.arrow_color = QColor(color)
        self.label = None
        self.label_color = QColor("#333333")  # Default label color
        self.label_font_size = 9  # Default label font size
        
        self.setPen(QPen(self.arrow_color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.setFlags(self.ItemIsSelectable)
        self.setZValue(-1)
        
        self.end_head = ArrowHead(self)
        self.start_head = ArrowHead(self) if bidirectional else None
        
        start_shape.add_arrow(self)
        end_shape.add_arrow(self)
        
        self.update_position()
    
    def set_label_color(self, color):
        """Set the label color."""
        self.label_color = QColor(color)
        if self.label:
            self.label.setBrush(QBrush(self.label_color))
    
    def get_label_color(self):
        """Get the current label color."""
        return self.label_color
    
    def set_label_font_size(self, size):
        """Set the font size for the label."""
        self.label_font_size = size
        if self.label:
            font = QFont("Arial")
            font.setPointSize(size)
            self.label.setFont(font)
            self.center_label()
    
    def get_label_font_size(self):
        """Get the current label font size."""
        return self.label_font_size
    
    def add_label(self, text):
        if self.label:
            self.label.setText(text)
        else:
            self.label = QGraphicsSimpleTextItem(text, self)
            self.label.setBrush(QBrush(self.label_color))
        # Apply font with explicit family for consistent SVG rendering
        font = QFont("Arial")
        font.setPointSize(self.label_font_size)
        self.label.setFont(font)
        self.center_label()
    
    def center_label(self):
        if self.label:
            line = self.line()
            mid_point = QPointF(
                (line.p1().x() + line.p2().x()) / 2,
                (line.p1().y() + line.p2().y()) / 2
            )
            label_rect = self.label.boundingRect()
            self.label.setPos(
                mid_point.x() - label_rect.width() / 2,
                mid_point.y() - label_rect.height() - 2
            )
    
    def update_position(self):
        if not self.start_shape or not self.end_shape:
            return
        
        start_center = self.start_shape.get_center()
        end_center = self.end_shape.get_center()
        
        start_point = self.start_shape.get_connection_point(end_center)
        end_point = self.end_shape.get_connection_point(start_center)
        
        self.setLine(QLineF(start_point, end_point))
        
        line = self.line()
        angle = math.atan2(line.dy(), line.dx())
        
        self.end_head.update_position(end_point, angle)
        self.end_head.set_color(self.arrow_color)
        
        if self.start_head:
            reverse_angle = angle + math.pi
            self.start_head.update_position(start_point, reverse_angle)
            self.start_head.set_color(self.arrow_color)
        
        self.center_label()
    
    def set_color(self, color):
        self.arrow_color = QColor(color)
        self.setPen(QPen(self.arrow_color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        self.end_head.set_color(color)
        if self.start_head:
            self.start_head.set_color(color)
    
    def detach(self):
        if self.start_shape:
            self.start_shape.remove_arrow(self)
        if self.end_shape:
            self.end_shape.remove_arrow(self)
    
    def paint(self, painter, option, widget=None):
        if self.isSelected():
            pen = QPen(QColor("#ff6b6b"), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        else:
            pen = QPen(self.arrow_color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setPen(pen)
        super().paint(painter, option, widget)