from PyQt5.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPen, QColor, QCursor


class ResizeHandle(QGraphicsRectItem):
    """Small draggable handle for resizing shapes."""
    
    HANDLE_SIZE = 8
    
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3
    
    def __init__(self, parent, position):
        super().__init__(-self.HANDLE_SIZE/2, -self.HANDLE_SIZE/2, 
                         self.HANDLE_SIZE, self.HANDLE_SIZE, parent)
        self.position = position
        self.parent_shape = parent
        
        self.setBrush(QBrush(QColor("#3498db")))
        self.setPen(QPen(QColor("#2980b9"), 1))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setCursor(self._get_cursor())
        self.setZValue(100)
        self.setVisible(False)
        
    def _get_cursor(self):
        if self.position in (self.TOP_LEFT, self.BOTTOM_RIGHT):
            return QCursor(Qt.SizeFDiagCursor)
        else:
            return QCursor(Qt.SizeBDiagCursor)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            self.parent_shape.handle_resize(self.position, value)
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        self.parent_shape.start_resize()
        event.accept()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.parent_shape.end_resize()
        event.accept()
        super().mouseReleaseEvent(event)