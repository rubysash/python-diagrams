from PyQt5.QtWidgets import QGraphicsScene, QInputDialog
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from shapes import (DiagramRect, DiagramOval, DiagramDiamond, DiagramTriangle, 
                    DiagramTriangleInverted, DiagramTriangleLeft, DiagramTriangleRight,
                    DiagramText)
from arrows import Arrow
from handles import ResizeHandle


class DiagramScene(QGraphicsScene):
    """Scene managing diagram shapes and interactions."""
    
    shape_selected = pyqtSignal(object)
    text_selected = pyqtSignal(object)  # Signal for text selection with formatting info
    status_message = pyqtSignal(str)
    
    MODE_SELECT = "Select"
    MODE_RECTANGLE = "Rectangle"
    MODE_OVAL = "Oval"
    MODE_DIAMOND = "Diamond"
    MODE_TRIANGLE = "Triangle"
    MODE_TRIANGLE_INVERTED = "Triangle Inverted"
    MODE_TRIANGLE_LEFT = "Triangle Left"
    MODE_TRIANGLE_RIGHT = "Triangle Right"
    MODE_TEXT = "Text"
    MODE_ARROW = "Arrow"
    MODE_ARROW_BIDIR = "Two-Way"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_mode = self.MODE_RECTANGLE
        self.current_color = QColor("#3498db")
        self.current_label_color = QColor("#333333")  # Separate label color
        self.setBackgroundBrush(QColor("#f9f9f9"))
        self._arrow_start_shape = None
        # Text settings
        self.text_settings = {
            'font_family': 'Arial',
            'font_size': 14,
            'bold': False,
            'underline': False
        }
    
    def set_mode(self, mode):
        self.current_mode = mode
        self._arrow_start_shape = None
        self.status_message.emit(f"Tool: {mode}")
    
    def set_color(self, color):
        self.current_color = QColor(color)
        selected = self.selectedItems()
        if not selected:
            self.status_message.emit("Select an item first to change its color")
            return
        
        for item in selected:
            if isinstance(item, DiagramText):
                # DiagramText: change text color
                item.set_color(color)
                self.status_message.emit("Text color changed")
            elif hasattr(item, 'set_color'):
                # Shape: change fill color
                item.set_color(color)
                self.status_message.emit("Shape color changed")
    
    def set_label_color(self, color):
        """Set the current label color for new labels."""
        self.current_label_color = QColor(color)
        # Apply to selected items' labels
        selected = self.selectedItems()
        for item in selected:
            if hasattr(item, 'label') and item.label is not None:
                if hasattr(item, 'set_label_color'):
                    item.set_label_color(color)
                    self.status_message.emit("Label color changed")
    
    def set_text_settings(self, font_family=None, font_size=None, bold=None, underline=None):
        """Update text settings and apply to selected text items and shape labels."""
        if font_family is not None:
            self.text_settings['font_family'] = font_family
        if font_size is not None:
            self.text_settings['font_size'] = font_size
        if bold is not None:
            self.text_settings['bold'] = bold
        if underline is not None:
            self.text_settings['underline'] = underline
        
        # Apply to selected items
        for item in self.selectedItems():
            if isinstance(item, DiagramText):
                # Apply all text settings to DiagramText
                if font_family is not None:
                    item.set_font_family(font_family)
                if font_size is not None:
                    item.set_font_size(font_size)
                if bold is not None:
                    item.set_bold(bold)
                if underline is not None:
                    item.set_underline(underline)
            elif isinstance(item, Arrow):
                # Apply font size to arrow labels
                if font_size is not None and hasattr(item, 'set_label_font_size'):
                    item.set_label_font_size(font_size)
                    self.status_message.emit("Arrow label size changed")
            elif hasattr(item, 'label') and item.label is not None:
                # Apply font size to shape labels
                if font_size is not None and hasattr(item, 'set_label_font_size'):
                    item.set_label_font_size(font_size)
                    self.status_message.emit("Label size changed")
    
    def get_shape_at(self, pos):
        items = self.items(pos)
        for item in items:
            # Direct check for diagram shapes (including new triangle types)
            if isinstance(item, (DiagramRect, DiagramOval, DiagramDiamond, 
                                 DiagramTriangle, DiagramTriangleInverted,
                                 DiagramTriangleLeft, DiagramTriangleRight,
                                 DiagramText)):
                return item
            # Check if clicking on a child item (like a label) - return the parent shape
            parent = item.parentItem()
            if parent and isinstance(parent, (DiagramRect, DiagramOval, DiagramDiamond, 
                                              DiagramTriangle, DiagramTriangleInverted,
                                              DiagramTriangleLeft, DiagramTriangleRight)):
                return parent
        return None
    
    def get_arrow_at(self, pos):
        items = self.items(pos)
        for item in items:
            if isinstance(item, Arrow):
                return item
        return None
    
    def get_handle_at(self, pos):
        """Check if there's a resize handle at the given position."""
        items = self.items(pos)
        for item in items:
            if isinstance(item, ResizeHandle):
                return item
        return None
    
    def mouseDoubleClickEvent(self, event):
        if self.current_mode in (self.MODE_SELECT, self.MODE_ARROW, self.MODE_ARROW_BIDIR):
            super().mouseDoubleClickEvent(event)
            return
        
        pos = event.scenePos()
        if self.get_shape_at(pos) is None:
            shape = self._create_shape(pos.x() - 50, pos.y() - 30)
            if shape:
                self.addItem(shape)
                self.status_message.emit(f"Created {self.current_mode}")
        
        super().mouseDoubleClickEvent(event)
    
    def _create_shape(self, x, y):
        color = self.current_color.name()
        if self.current_mode == self.MODE_RECTANGLE:
            return DiagramRect(x, y, color=color)
        elif self.current_mode == self.MODE_OVAL:
            return DiagramOval(x, y, color=color)
        elif self.current_mode == self.MODE_DIAMOND:
            return DiagramDiamond(x, y, color=color)
        elif self.current_mode == self.MODE_TRIANGLE:
            return DiagramTriangle(x, y, color=color)
        elif self.current_mode == self.MODE_TRIANGLE_INVERTED:
            return DiagramTriangleInverted(x, y, color=color)
        elif self.current_mode == self.MODE_TRIANGLE_LEFT:
            return DiagramTriangleLeft(x, y, color=color)
        elif self.current_mode == self.MODE_TRIANGLE_RIGHT:
            return DiagramTriangleRight(x, y, color=color)
        elif self.current_mode == self.MODE_TEXT:
            return DiagramText(
                x, y, 
                text="Text",
                font_family=self.text_settings['font_family'],
                font_size=self.text_settings['font_size'],
                color=color,
                bold=self.text_settings['bold'],
                underline=self.text_settings['underline']
            )
        return None
    
    def mousePressEvent(self, event):
        pos = event.scenePos()
        
        # Check if clicking on a resize handle first - let it handle its own events
        handle = self.get_handle_at(pos)
        if handle and handle.isVisible():
            super().mousePressEvent(event)
            return
        
        shape = self.get_shape_at(pos)
        arrow = self.get_arrow_at(pos)
        
        if event.button() == Qt.RightButton:
            if shape:
                self._add_label_to_shape(shape)
                return
            elif arrow:
                self._add_label_to_arrow(arrow)
                return
        
        if event.button() == Qt.LeftButton and self.current_mode in (self.MODE_ARROW, self.MODE_ARROW_BIDIR):
            if shape:
                if self._arrow_start_shape is None:
                    self._arrow_start_shape = shape
                    shape.setSelected(True)
                    self.status_message.emit("Click destination shape")
                elif shape != self._arrow_start_shape:
                    bidirectional = (self.current_mode == self.MODE_ARROW_BIDIR)
                    new_arrow = Arrow(self._arrow_start_shape, shape, bidirectional,color=self.current_color.name())
                    self.addItem(new_arrow)
                    self._arrow_start_shape.setSelected(False)
                    self._arrow_start_shape = None
                    self.status_message.emit("Arrow created")
                else:
                    self._arrow_start_shape.setSelected(False)
                    self._arrow_start_shape = None
                    self.status_message.emit("Cancelled")
            else:
                if self._arrow_start_shape:
                    self._arrow_start_shape.setSelected(False)
                self._arrow_start_shape = None
                self.status_message.emit("Click a shape to start arrow")
            return
        
        if event.button() == Qt.LeftButton:
            if shape:
                # Only clear selection if clicking on a different shape
                if not shape.isSelected():
                    self.clearSelection()
                    shape.setSelected(True)
                self.shape_selected.emit(shape)
                # Also emit text_selected for text shapes
                if isinstance(shape, DiagramText):
                    self.text_selected.emit(shape)
            elif arrow:
                self.clearSelection()
                arrow.setSelected(True)
            else:
                # Clicked on empty space - clear selection
                self.clearSelection()
        
        super().mousePressEvent(event)
    
    def _add_label_to_shape(self, shape):
        current_text = ""
        if isinstance(shape, DiagramText):
            current_text = shape.get_text()
        elif hasattr(shape, 'label') and shape.label:
            current_text = shape.label.toPlainText()
        text, ok = QInputDialog.getText(None, "Label", "Enter text:", text=current_text)
        if ok and text:
            # Set label color before adding label
            if hasattr(shape, 'set_label_color'):
                shape.set_label_color(self.current_label_color)
            # Set label font size from current text settings
            if hasattr(shape, 'label_font_size'):
                shape.label_font_size = self.text_settings['font_size']
            shape.add_label(text)
            self.status_message.emit("Label added")
            # Select the shape so color picker changes will apply
            self.clearSelection()
            shape.setSelected(True)
            # Emit signal to update UI
            self.shape_selected.emit(shape)
    
    def _add_label_to_arrow(self, arrow):
        current_text = ""
        if hasattr(arrow, 'label') and arrow.label:
            current_text = arrow.label.toPlainText()
        text, ok = QInputDialog.getText(None, "Arrow Label", "Enter label:", text=current_text)
        if ok and text:
            # Set label color before adding label
            if hasattr(arrow, 'set_label_color'):
                arrow.set_label_color(self.current_label_color)
            # Set label font size from current text settings
            if hasattr(arrow, 'label_font_size'):
                arrow.label_font_size = self.text_settings['font_size']
            arrow.add_label(text)
            self.status_message.emit("Arrow label added")
    
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self._delete_selected()
        elif event.key() == Qt.Key_Escape:
            self._arrow_start_shape = None
            self.clearSelection()
            self.status_message.emit("Selection cleared")
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self._change_z_order(1)
        elif event.key() == Qt.Key_Minus:
            self._change_z_order(-1)
        else:
            super().keyPressEvent(event)
    
    def _change_z_order(self, delta):
        """Change z-order of selected items."""
        items = self.selectedItems()
        if not items:
            self.status_message.emit("Nothing selected")
            return
        
        for item in items:
            current_z = item.zValue()
            item.setZValue(current_z + delta)
        
        direction = "up" if delta > 0 else "down"
        self.status_message.emit(f"Moved {len(items)} item(s) {direction} (z={items[0].zValue():.0f})")
    
    def _delete_selected(self):
        items = self.selectedItems()
        if not items:
            self.status_message.emit("Nothing selected")
            return
        
        for item in items:
            if hasattr(item, 'arrows'):
                for arrow in item.arrows[:]:
                    arrow.detach()
                    self.removeItem(arrow)
            if hasattr(item, 'detach'):
                item.detach()
            self.removeItem(item)
        
        self.status_message.emit(f"Deleted {len(items)} item(s)")
    
    def clear_all(self):
        self.clear()
        self.setBackgroundBrush(QColor("#f9f9f9"))
        self._arrow_start_shape = None
        self.status_message.emit("Canvas cleared")