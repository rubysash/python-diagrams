from PyQt5.QtWidgets import QGraphicsScene, QInputDialog, QMenu
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QColor, QPen

from shapes import (
    DiagramRect, DiagramSquare, DiagramOval, DiagramCircle,
    DiagramDiamond, DiagramHexagon, DiagramOctagon,
    DiagramTriangle, DiagramTriangleInverted,
    DiagramTriangleLeft, DiagramTriangleRight,
    DiagramText,
)
from arrows import Arrow, BendHandle
from handles import ResizeHandle

PASTE_OFFSET = 20

# All shape types for isinstance checks (excludes Arrow/ResizeHandle)
SHAPE_CLASSES = (
    DiagramRect, DiagramSquare, DiagramOval, DiagramCircle,
    DiagramDiamond, DiagramHexagon, DiagramOctagon,
    DiagramTriangle, DiagramTriangleInverted,
    DiagramTriangleLeft, DiagramTriangleRight,
    DiagramText,
)

# Map class names to factory functions for clipboard paste / JSON load
SHAPE_CONSTRUCTORS = {
    'DiagramRect': lambda d: DiagramRect(
        d['x'], d['y'], d.get('width', 100), d.get('height', 60), d.get('color', '#3498db')),
    'DiagramSquare': lambda d: DiagramSquare(
        d['x'], d['y'], d.get('width', 80), d.get('height', 80), d.get('color', '#2980b9')),
    'DiagramOval': lambda d: DiagramOval(
        d['x'], d['y'], d.get('width', 100), d.get('height', 60), d.get('color', '#2ecc71')),
    'DiagramCircle': lambda d: DiagramCircle(
        d['x'], d['y'], d.get('width', 80), d.get('height', 80), d.get('color', '#27ae60')),
    'DiagramDiamond': lambda d: DiagramDiamond(
        d['x'], d['y'], d.get('width', 100), d.get('height', 60), d.get('color', '#e74c3c')),
    'DiagramHexagon': lambda d: DiagramHexagon(
        d['x'], d['y'], d.get('width', 100), d.get('height', 86), d.get('color', '#8e44ad')),
    'DiagramOctagon': lambda d: DiagramOctagon(
        d['x'], d['y'], d.get('width', 100), d.get('height', 100), d.get('color', '#c0392b')),
    'DiagramTriangle': lambda d: DiagramTriangle(
        d['x'], d['y'], d.get('width', 100), d.get('height', 80), d.get('color', '#9b59b6')),
    'DiagramTriangleInverted': lambda d: DiagramTriangleInverted(
        d['x'], d['y'], d.get('width', 100), d.get('height', 80), d.get('color', '#e67e22')),
    'DiagramTriangleLeft': lambda d: DiagramTriangleLeft(
        d['x'], d['y'], d.get('width', 80), d.get('height', 100), d.get('color', '#1abc9c')),
    'DiagramTriangleRight': lambda d: DiagramTriangleRight(
        d['x'], d['y'], d.get('width', 80), d.get('height', 100), d.get('color', '#3498db')),
    'DiagramText': lambda d: DiagramText(
        d['x'], d['y'],
        text=d.get('text', 'Text'),
        font_family=d.get('font_family', 'Arial'),
        font_size=d.get('font_size', 14),
        color=d.get('color', '#333333'),
        bold=d.get('bold', False),
        underline=d.get('underline', False)),
}


class DiagramScene(QGraphicsScene):
    """Scene managing diagram shapes and interactions."""

    shape_selected = pyqtSignal(object)
    text_selected = pyqtSignal(object)  # Signal for text selection with formatting info
    status_message = pyqtSignal(str)

    MODE_SELECT = "Select"
    MODE_RECTANGLE = "Rectangle"
    MODE_SQUARE = "Square"
    MODE_OVAL = "Oval"
    MODE_CIRCLE = "Circle"
    MODE_DIAMOND = "Diamond"
    MODE_HEXAGON = "Hexagon"
    MODE_OCTAGON = "Octagon"
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
        self._clipboard = None
        # Track positions before a drag to detect actual moves
        self._drag_start_positions = None
        # Grid settings
        self.grid_size = 20
        self.grid_visible = False
        self.snap_to_grid = False
        # Undo/redo stacks store full scene snapshots
        self._undo_stack = []
        self._redo_stack = []
        self._max_undo = 10
        # Text settings
        self.text_settings = {
            'font_family': 'Arial',
            'font_size': 14,
            'bold': False,
            'underline': False
        }
    
    def drawBackground(self, painter, rect):
        """Draw grid overlay when enabled."""
        super().drawBackground(painter, rect)
        if not self.grid_visible:
            return

        grid = self.grid_size
        pen = QPen(QColor("#d0d0d0"), 0.5)
        painter.setPen(pen)

        # Calculate grid lines within the visible rect
        left = int(rect.left()) - (int(rect.left()) % grid)
        top = int(rect.top()) - (int(rect.top()) % grid)

        # Vertical lines
        x = left
        while x <= rect.right():
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += grid

        # Horizontal lines
        y = top
        while y <= rect.bottom():
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += grid

    def snap_position(self, pos):
        """Snap a QPointF to the nearest grid point."""
        if not self.snap_to_grid:
            return pos
        grid = self.grid_size
        x = round(pos.x() / grid) * grid
        y = round(pos.y() / grid) * grid
        return type(pos)(x, y)

    def toggle_grid(self, visible):
        """Show or hide the grid overlay."""
        self.grid_visible = visible
        self.update()

    def toggle_snap(self, enabled):
        """Enable or disable snap-to-grid."""
        self.snap_to_grid = enabled

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
            # Direct check for any diagram shape
            if isinstance(item, SHAPE_CLASSES):
                return item
            # Check if clicking on a child item (like a label) — return the parent shape
            parent = item.parentItem()
            if parent and isinstance(parent, SHAPE_CLASSES):
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

    def get_bend_handle_at(self, pos):
        """Check if there's a bend handle at the given position."""
        items = self.items(pos)
        for item in items:
            if isinstance(item, BendHandle):
                return item
        return None
    
    def mouseDoubleClickEvent(self, event):
        pos = event.scenePos()

        # In select mode, double-click a shape/arrow to edit or add bend
        if self.current_mode == self.MODE_SELECT:
            # Double-click a bend handle to remove it
            bend_handle = self.get_bend_handle_at(pos)
            if bend_handle and bend_handle.arrow:
                self.save_undo()
                bend_handle.arrow.remove_bend_point(bend_handle.index)
                self.status_message.emit("Bend point removed")
                return

            shape = self.get_shape_at(pos)
            arrow = self.get_arrow_at(pos)
            if shape:
                self._add_label_to_shape(shape)
            elif arrow:
                # Double-click arrow to add a bend point
                self.save_undo()
                arrow.add_bend_point(pos)
                arrow.setSelected(True)
                self.status_message.emit("Bend point added (double-click to remove)")
            else:
                super().mouseDoubleClickEvent(event)
            return

        # Arrow modes don't create shapes on double-click
        if self.current_mode in (self.MODE_ARROW, self.MODE_ARROW_BIDIR):
            super().mouseDoubleClickEvent(event)
            return

        # Shape modes: double-click empty space to create a new shape
        if self.get_shape_at(pos) is None:
            shape = self._create_shape(pos.x() - 50, pos.y() - 30)
            if shape:
                self.save_undo()
                self.addItem(shape)
                self.status_message.emit(f"Created {self.current_mode}")

        super().mouseDoubleClickEvent(event)
    
    def _create_shape(self, x, y):
        color = self.current_color.name()
        # Map mode names to shape classes for simple constructors
        simple_shapes = {
            self.MODE_RECTANGLE: DiagramRect,
            self.MODE_SQUARE: DiagramSquare,
            self.MODE_OVAL: DiagramOval,
            self.MODE_CIRCLE: DiagramCircle,
            self.MODE_DIAMOND: DiagramDiamond,
            self.MODE_HEXAGON: DiagramHexagon,
            self.MODE_OCTAGON: DiagramOctagon,
            self.MODE_TRIANGLE: DiagramTriangle,
            self.MODE_TRIANGLE_INVERTED: DiagramTriangleInverted,
            self.MODE_TRIANGLE_LEFT: DiagramTriangleLeft,
            self.MODE_TRIANGLE_RIGHT: DiagramTriangleRight,
        }
        shape_cls = simple_shapes.get(self.current_mode)
        if shape_cls:
            return shape_cls(x, y, color=color)
        if self.current_mode == self.MODE_TEXT:
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

        # Check bend handles first - let them drag, keep parent arrow selected
        bend_handle = self.get_bend_handle_at(pos)
        if bend_handle and bend_handle.arrow:
            if event.button() == Qt.RightButton:
                self._show_bend_handle_context_menu(event, bend_handle)
                return
            # Let Qt handle the drag; re-select the arrow so handles stay visible
            super().mousePressEvent(event)
            if bend_handle.arrow:
                bend_handle.arrow.setSelected(True)
            return

        # Check if clicking on a resize handle first - let it handle its own events
        handle = self.get_handle_at(pos)
        if handle and handle.isVisible():
            super().mousePressEvent(event)
            return

        shape = self.get_shape_at(pos)
        arrow = self.get_arrow_at(pos)
        
        if event.button() == Qt.RightButton:
            if shape:
                self._show_context_menu(event, shape)
                return
            elif arrow:
                self._show_arrow_context_menu(event, arrow)
                return
        
        if event.button() == Qt.LeftButton and self.current_mode in (self.MODE_ARROW, self.MODE_ARROW_BIDIR):
            if shape:
                if self._arrow_start_shape is None:
                    self._arrow_start_shape = shape
                    shape.setSelected(True)
                    self.status_message.emit("Click destination shape")
                elif shape != self._arrow_start_shape:
                    bidirectional = (self.current_mode == self.MODE_ARROW_BIDIR)
                    self.save_undo()
                    new_arrow = Arrow(self._arrow_start_shape, shape, bidirectional,color=self.current_color.name())
                    self.addItem(new_arrow)
                    self._arrow_start_shape.setSelected(False)
                    self._arrow_start_shape = None
                    self.status_message.emit("Arrow created — double-click arrow to add bend points")
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
            modifiers = event.modifiers()
            multi_select = modifiers & (Qt.ControlModifier | Qt.ShiftModifier)

            if shape:
                if multi_select:
                    shape.setSelected(not shape.isSelected())
                else:
                    if not shape.isSelected():
                        self.clearSelection()
                        shape.setSelected(True)
                # Snapshot positions before a potential drag
                self._drag_start_positions = {
                    item: item.pos()
                    for item in self.selectedItems()
                    if isinstance(item, SHAPE_CLASSES)
                }
                self.shape_selected.emit(shape)
                if isinstance(shape, DiagramText):
                    self.text_selected.emit(shape)
            elif arrow:
                if multi_select:
                    arrow.setSelected(not arrow.isSelected())
                else:
                    self.clearSelection()
                    arrow.setSelected(True)
            else:
                if not multi_select:
                    self.clearSelection()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Save undo if items moved, then snap to grid."""
        super().mouseReleaseEvent(event)

        # Check if any shapes actually moved during this drag
        if self._drag_start_positions:
            moved = any(
                item.pos() != old_pos
                for item, old_pos in self._drag_start_positions.items()
                if item.scene() is not None  # item still in scene
            )
            if moved:
                # Save the pre-drag state as an undo snapshot
                # We need to reconstruct it from stored positions
                self._save_move_undo(self._drag_start_positions)
            self._drag_start_positions = None

        # Snap to grid after move
        if self.snap_to_grid:
            for item in self.selectedItems():
                if isinstance(item, SHAPE_CLASSES):
                    snapped = self.snap_position(item.pos())
                    if snapped != item.pos():
                        item.setPos(snapped)
            # Snap visible bend handles too
            for item in self.items():
                if isinstance(item, BendHandle) and item.isVisible():
                    snapped = self.snap_position(item.pos())
                    if snapped != item.pos():
                        item.setPos(snapped)

    def _save_move_undo(self, start_positions):
        """Save undo by temporarily restoring pre-drag positions for snapshot."""
        # Record current (post-drag) positions
        current_positions = {item: item.pos() for item in start_positions}
        # Move items back to pre-drag positions
        for item, old_pos in start_positions.items():
            if item.scene() is not None:
                item.setPos(old_pos)
        # Take snapshot of pre-drag state
        self.save_undo()
        # Restore post-drag positions
        for item, new_pos in current_positions.items():
            if item.scene() is not None:
                item.setPos(new_pos)

    def _show_context_menu(self, event, shape):
        """Show right-click context menu for a shape."""
        menu = QMenu()
        label_action = menu.addAction("Edit Label...")
        menu.addSeparator()
        front_action = menu.addAction("Send to Front")
        forward_action = menu.addAction("Send Forward")
        backward_action = menu.addAction("Send Backward")
        back_action = menu.addAction("Send to Back")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        # Get screen position from the scene event
        view = self.views()[0] if self.views() else None
        screen_pos = view.mapToGlobal(view.mapFromScene(event.scenePos())) if view else None
        if screen_pos is None:
            return

        chosen = menu.exec_(screen_pos)
        if chosen == label_action:
            self._add_label_to_shape(shape)
        elif chosen == front_action:
            self._send_to_front(shape)
        elif chosen == forward_action:
            self._change_z_for_item(shape, 1)
        elif chosen == backward_action:
            self._change_z_for_item(shape, -1)
        elif chosen == back_action:
            self._send_to_back(shape)
        elif chosen == delete_action:
            shape.setSelected(True)
            self._delete_selected()

    def _show_arrow_context_menu(self, event, arrow):
        """Show right-click context menu for an arrow."""
        menu = QMenu()
        label_action = menu.addAction("Edit Label...")
        bend_action = menu.addAction("Add Bend Point")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        view = self.views()[0] if self.views() else None
        screen_pos = view.mapToGlobal(view.mapFromScene(event.scenePos())) if view else None
        if screen_pos is None:
            return

        chosen = menu.exec_(screen_pos)
        if chosen == label_action:
            self._add_label_to_arrow(arrow)
        elif chosen == bend_action:
            self.save_undo()
            arrow.add_bend_point(event.scenePos())
            arrow.setSelected(True)
            self.status_message.emit("Bend point added")
        elif chosen == delete_action:
            arrow.setSelected(True)
            self._delete_selected()

    def _show_bend_handle_context_menu(self, event, handle):
        """Show right-click context menu for a bend handle."""
        menu = QMenu()
        remove_action = menu.addAction("Remove Bend Point")

        view = self.views()[0] if self.views() else None
        screen_pos = view.mapToGlobal(view.mapFromScene(event.scenePos())) if view else None
        if screen_pos is None:
            return

        chosen = menu.exec_(screen_pos)
        if chosen == remove_action:
            self.save_undo()
            handle.arrow.remove_bend_point(handle.index)
            self.status_message.emit("Bend point removed")

    def _send_to_front(self, item):
        """Move item above all others."""
        self.save_undo()
        max_z = max((i.zValue() for i in self.items()), default=0)
        item.setZValue(max_z + 1)
        self.status_message.emit("Sent to front")

    def _send_to_back(self, item):
        """Move item below all others."""
        self.save_undo()
        min_z = min((i.zValue() for i in self.items()), default=0)
        item.setZValue(min_z - 1)
        self.status_message.emit("Sent to back")

    def _change_z_for_item(self, item, delta):
        """Nudge a single item's z-order."""
        self.save_undo()
        item.setZValue(item.zValue() + delta)
        direction = "forward" if delta > 0 else "backward"
        self.status_message.emit(f"Sent {direction}")

    def _rename_selected(self):
        """Open the label dialog for the first selected shape or arrow (F2)."""
        selected = self.selectedItems()
        if not selected:
            self.status_message.emit("Nothing selected to rename")
            return
        item = selected[0]
        if isinstance(item, SHAPE_CLASSES):
            self._add_label_to_shape(item)
        elif isinstance(item, Arrow):
            self._add_label_to_arrow(item)

    def _add_label_to_shape(self, shape):
        current_text = ""
        if isinstance(shape, DiagramText):
            current_text = shape.get_text()
        elif hasattr(shape, 'label') and shape.label:
            current_text = shape.label.text()
        text, ok = QInputDialog.getText(None, "Label", "Enter text:", text=current_text)
        if ok and text:
            self.save_undo()
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
            current_text = arrow.label.text()
        text, ok = QInputDialog.getText(None, "Arrow Label", "Enter label:", text=current_text)
        if ok and text:
            self.save_undo()
            # Set label color before adding label
            if hasattr(arrow, 'set_label_color'):
                arrow.set_label_color(self.current_label_color)
            # Set label font size from current text settings
            if hasattr(arrow, 'label_font_size'):
                arrow.label_font_size = self.text_settings['font_size']
            arrow.add_label(text)
            self.status_message.emit("Arrow label added")
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F2:
            self._rename_selected()
        elif event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self._delete_selected()
        elif event.key() == Qt.Key_Escape:
            self._arrow_start_shape = None
            self.clearSelection()
            self.status_message.emit("Selection cleared")
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self._change_z_order(1)
        elif event.key() == Qt.Key_Minus:
            self._change_z_order(-1)
        elif event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                self._copy_selected()
            elif event.key() == Qt.Key_X:
                self._cut_selected()
            elif event.key() == Qt.Key_V:
                self._paste_clipboard()
            elif event.key() == Qt.Key_Z:
                self.undo()
            elif event.key() == Qt.Key_Y:
                self.redo()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    
    # ------------------------------------------------------------------
    # Clipboard helpers
    # ------------------------------------------------------------------

    def _serialize_selected(self):
        """Serialize selected shapes and their interconnecting arrows."""
        items = self.selectedItems()
        shapes = [i for i in items if isinstance(i, SHAPE_CLASSES)]
        if not shapes:
            return None

        shape_id_map = {}
        shape_list = []
        for idx, item in enumerate(shapes):
            shape_id_map[item] = idx
            shape_list.append(self._serialize_shape(item, idx))

        arrow_list = []
        for item in self.items():
            if not isinstance(item, Arrow):
                continue
            if item.start_shape in shape_id_map and item.end_shape in shape_id_map:
                arrow_list.append({
                    'start_id': shape_id_map[item.start_shape],
                    'end_id': shape_id_map[item.end_shape],
                    'bidirectional': item.bidirectional,
                    'color': item.arrow_color.name(),
                    'label': item.label.text() if item.label else None,
                    'label_color': item.label_color.name(),
                    'label_font_size': item.label_font_size,
                    'line_style': item.line_style,
                    'line_width': item.line_width,
                    'bend_points': [{'x': bp.x(), 'y': bp.y()} for bp in item.bend_points],
                })

        return {'shapes': shape_list, 'arrows': arrow_list}

    @staticmethod
    def _serialize_shape(item, shape_id):
        """Return a dict representing a single shape."""
        if isinstance(item, DiagramText):
            return {
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
                'z': item.zValue(),
            }
        return {
            'id': shape_id,
            'type': item.__class__.__name__,
            'x': item.pos().x(),
            'y': item.pos().y(),
            'width': item.shape_width,
            'height': item.shape_height,
            'color': item.shape_color.name(),
            'label': item.label.text() if item.label else None,
            'label_color': item.label_color.name(),
            'label_font_size': item.label_font_size,
            'z': item.zValue(),
        }

    def _paste_data(self, data, offset_x=PASTE_OFFSET, offset_y=PASTE_OFFSET):
        """Instantiate shapes and arrows from clipboard data, offset from original."""
        self.clearSelection()
        shape_map = {}

        for shape_data in data['shapes']:
            shifted = dict(shape_data, x=shape_data['x'] + offset_x,
                           y=shape_data['y'] + offset_y)
            constructor = SHAPE_CONSTRUCTORS.get(shifted['type'])
            if constructor is None:
                continue
            shape = constructor(shifted)
            self.addItem(shape)
            shape_map[shifted['id']] = shape

            if shifted['type'] != 'DiagramText':
                if hasattr(shape, 'set_label_color'):
                    shape.set_label_color(shifted.get('label_color', '#ffffff'))
                shape.label_font_size = shifted.get('label_font_size', 14)
                if shifted.get('label'):
                    shape.add_label(shifted['label'])

            if 'z' in shifted:
                shape.setZValue(shifted['z'])
            shape.setSelected(True)

        for arrow_data in data.get('arrows', []):
            start = shape_map.get(arrow_data['start_id'])
            end = shape_map.get(arrow_data['end_id'])
            if start is None or end is None:
                continue
            # Offset bend points along with shapes
            raw_bends = arrow_data.get('bend_points', [])
            offset_bends = [{'x': bp['x'] + offset_x, 'y': bp['y'] + offset_y}
                            for bp in raw_bends]
            arrow = Arrow(start, end,
                          bidirectional=arrow_data.get('bidirectional', False),
                          color=arrow_data.get('color', '#333333'),
                          line_style=arrow_data.get('line_style', 'Solid'),
                          line_width=arrow_data.get('line_width', 2),
                          bend_points=offset_bends)
            self.addItem(arrow)
            if 'label_color' in arrow_data:
                arrow.set_label_color(arrow_data['label_color'])
            if 'label_font_size' in arrow_data:
                arrow.label_font_size = arrow_data['label_font_size']
            if arrow_data.get('label'):
                arrow.add_label(arrow_data['label'])

        count = len(shape_map)
        return count

    def _copy_selected(self):
        """Copy selected shapes to the internal clipboard."""
        data = self._serialize_selected()
        if data is None:
            self.status_message.emit("Nothing selected to copy")
            return
        self._clipboard = data
        count = len(data['shapes'])
        self.status_message.emit(f"Copied {count} item(s)")

    def _cut_selected(self):
        """Cut selected shapes to the internal clipboard."""
        data = self._serialize_selected()
        if data is None:
            self.status_message.emit("Nothing selected to cut")
            return
        self._clipboard = data
        count = len(data['shapes'])
        self.save_undo()
        self._delete_selected(save_undo=False)
        self.status_message.emit(f"Cut {count} item(s)")

    def _paste_clipboard(self):
        """Paste shapes from the internal clipboard."""
        if not self._clipboard:
            self.status_message.emit("Clipboard is empty")
            return
        self.save_undo()
        count = self._paste_data(self._clipboard)
        self.status_message.emit(f"Pasted {count} item(s)")

    # ------------------------------------------------------------------
    # Undo / Redo (snapshot-based, max 10 levels)
    # ------------------------------------------------------------------

    def _snapshot(self):
        """Serialize the entire scene to a dict for undo/redo storage."""
        shapes = [i for i in self.items() if isinstance(i, SHAPE_CLASSES)]
        shape_id_map = {}
        shape_list = []
        for idx, item in enumerate(shapes):
            shape_id_map[item] = idx
            shape_list.append(self._serialize_shape(item, idx))

        arrow_list = []
        for item in self.items():
            if not isinstance(item, Arrow):
                continue
            if item.start_shape in shape_id_map and item.end_shape in shape_id_map:
                arrow_list.append({
                    'start_id': shape_id_map[item.start_shape],
                    'end_id': shape_id_map[item.end_shape],
                    'bidirectional': item.bidirectional,
                    'color': item.arrow_color.name(),
                    'label': item.label.text() if item.label else None,
                    'label_color': item.label_color.name(),
                    'label_font_size': item.label_font_size,
                    'line_style': item.line_style,
                    'line_width': item.line_width,
                    'bend_points': [{'x': bp.x(), 'y': bp.y()} for bp in item.bend_points],
                })
        return {'shapes': shape_list, 'arrows': arrow_list}

    def _restore_snapshot(self, data):
        """Clear the scene and rebuild from a snapshot dict."""
        self.clear()
        self.setBackgroundBrush(QColor("#f9f9f9"))
        self._arrow_start_shape = None
        # Reuse paste logic with zero offset to recreate items in place
        self._paste_data(data, offset_x=0, offset_y=0)
        self.clearSelection()

    def save_undo(self):
        """Push current state onto the undo stack. Call before mutating actions."""
        snapshot = self._snapshot()
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
        # Any new action invalidates the redo history
        self._redo_stack.clear()

    def undo(self):
        """Restore the previous scene state."""
        if not self._undo_stack:
            self.status_message.emit("Nothing to undo")
            return
        # Save current state to redo before restoring
        self._redo_stack.append(self._snapshot())
        snapshot = self._undo_stack.pop()
        self._restore_snapshot(snapshot)
        self.status_message.emit("Undo")

    def redo(self):
        """Re-apply the last undone action."""
        if not self._redo_stack:
            self.status_message.emit("Nothing to redo")
            return
        # Save current state to undo before restoring
        self._undo_stack.append(self._snapshot())
        snapshot = self._redo_stack.pop()
        self._restore_snapshot(snapshot)
        self.status_message.emit("Redo")

    def _change_z_order(self, delta):
        """Change z-order of selected items."""
        items = self.selectedItems()
        if not items:
            self.status_message.emit("Nothing selected")
            return

        self.save_undo()
        for item in items:
            current_z = item.zValue()
            item.setZValue(current_z + delta)
        
        direction = "up" if delta > 0 else "down"
        self.status_message.emit(f"Moved {len(items)} item(s) {direction} (z={items[0].zValue():.0f})")
    
    def _delete_selected(self, save_undo=True):
        items = self.selectedItems()
        if not items:
            self.status_message.emit("Nothing selected")
            return

        if save_undo:
            self.save_undo()
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
        self.save_undo()
        self.clear()
        self.setBackgroundBrush(QColor("#f9f9f9"))
        self._arrow_start_shape = None
        self.status_message.emit("Canvas cleared")