import math
from PyQt5.QtWidgets import (QGraphicsPathItem, QGraphicsPolygonItem,
                              QGraphicsSimpleTextItem, QGraphicsEllipseItem)
from PyQt5.QtCore import Qt, QPointF, QLineF
from PyQt5.QtGui import (QPen, QBrush, QColor, QPolygonF, QFont,
                          QPainterPath, QPainterPathStroker)


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
            line_end.x() - self.ARROW_SIZE * math.cos(angle - math.pi / 6),
            line_end.y() - self.ARROW_SIZE * math.sin(angle - math.pi / 6)
        )
        p3 = QPointF(
            line_end.x() - self.ARROW_SIZE * math.cos(angle + math.pi / 6),
            line_end.y() - self.ARROW_SIZE * math.sin(angle + math.pi / 6)
        )
        self.setPolygon(QPolygonF([p1, p2, p3]))

    def set_color(self, color):
        self.setBrush(QBrush(QColor(color)))


class BendHandle(QGraphicsEllipseItem):
    """Draggable handle at an arrow bend point."""

    HANDLE_SIZE = 8

    def __init__(self, arrow, index, pos):
        half = self.HANDLE_SIZE / 2
        super().__init__(-half, -half, self.HANDLE_SIZE, self.HANDLE_SIZE)
        self.arrow = arrow
        self.index = index
        self.setPos(pos)
        self.setBrush(QBrush(QColor("#4a90d9")))
        self.setPen(QPen(QColor("#2c3e50"), 1))
        self.setFlags(self.ItemIsMovable | self.ItemSendsGeometryChanges)
        self.setZValue(10)  # Above arrows and shapes
        self.setCursor(Qt.SizeAllCursor)

    def itemChange(self, change, value):
        """Update the parent arrow's bend point when this handle is dragged."""
        if change == self.ItemPositionHasChanged and self.arrow:
            if 0 <= self.index < len(self.arrow.bend_points):
                self.arrow.bend_points[self.index] = QPointF(value)
                self.arrow.update_position()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        """Save undo before dragging a bend point."""
        if event.button() == Qt.LeftButton:
            scene = self.scene()
            if scene and hasattr(scene, 'save_undo'):
                scene.save_undo()
        super().mousePressEvent(event)


# Map user-facing style names to Qt pen styles
LINE_STYLES = {
    'Solid': Qt.SolidLine,
    'Dashed': Qt.DashLine,
    'Dotted': Qt.DotLine,
    'Dash-Dot': Qt.DashDotLine,
}


class Arrow(QGraphicsPathItem):
    """Arrow connecting two shapes with optional bend points for routing."""

    def __init__(self, start_shape, end_shape, bidirectional=False,
                 color="#333333", line_style='Solid', line_width=2,
                 bend_points=None):
        super().__init__()

        self.start_shape = start_shape
        self.end_shape = end_shape
        self.bidirectional = bidirectional
        self.arrow_color = QColor(color)
        self.line_style = line_style
        self.line_width = line_width
        self.label = None
        self.label_color = QColor("#333333")
        self.label_font_size = 9

        # Bend points in scene coordinates for segmented routing
        self.bend_points = []
        for p in (bend_points or []):
            if isinstance(p, dict):
                self.bend_points.append(QPointF(p['x'], p['y']))
            elif isinstance(p, QPointF):
                self.bend_points.append(QPointF(p))
            else:
                self.bend_points.append(QPointF(p[0], p[1]))

        self._bend_handles = []

        self._update_pen()
        self.setFlags(self.ItemIsSelectable)
        self.setZValue(-1)

        self.end_head = ArrowHead(self)
        self.start_head = ArrowHead(self) if bidirectional else None

        start_shape.add_arrow(self)
        end_shape.add_arrow(self)

        self.update_position()

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _get_all_points(self):
        """Return full point list: start connection -> bends -> end connection."""
        start_center = self.start_shape.get_center()
        end_center = self.end_shape.get_center()

        # Aim connection point at first/last bend (not opposite shape center)
        start_target = self.bend_points[0] if self.bend_points else end_center
        end_target = self.bend_points[-1] if self.bend_points else start_center

        start_point = self.start_shape.get_connection_point(start_target)
        end_point = self.end_shape.get_connection_point(end_target)

        return [start_point] + list(self.bend_points) + [end_point]

    def shape(self):
        """Wider hit area for easier clicking on arrow segments."""
        stroker = QPainterPathStroker()
        stroker.setWidth(max(self.line_width + 8, 12))
        return stroker.createStroke(self.path())

    @staticmethod
    def _point_to_segment_dist(p, a, b):
        """Perpendicular distance from point p to line segment a-b."""
        dx, dy = b.x() - a.x(), b.y() - a.y()
        len_sq = dx * dx + dy * dy
        if len_sq == 0:
            return math.hypot(p.x() - a.x(), p.y() - a.y())
        t = max(0, min(1, ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / len_sq))
        proj_x = a.x() + t * dx
        proj_y = a.y() + t * dy
        return math.hypot(p.x() - proj_x, p.y() - proj_y)

    def _find_segment_index(self, scene_pos):
        """Find closest segment to scene_pos. Returns insertion index for bend_points."""
        points = self._get_all_points()
        min_dist = float('inf')
        best_idx = 0
        for i in range(len(points) - 1):
            dist = self._point_to_segment_dist(scene_pos, points[i], points[i + 1])
            if dist < min_dist:
                min_dist = dist
                best_idx = i
        return best_idx

    # ------------------------------------------------------------------
    # Bend point management
    # ------------------------------------------------------------------

    def add_bend_point(self, scene_pos, segment_index=None):
        """Insert a bend point at the clicked position on the closest segment."""
        if segment_index is None:
            segment_index = self._find_segment_index(scene_pos)
        self.bend_points.insert(segment_index, QPointF(scene_pos))
        self._rebuild_bend_handles()
        self.update_position()

    def remove_bend_point(self, index):
        """Remove a bend point by index."""
        if 0 <= index < len(self.bend_points):
            self.bend_points.pop(index)
            self._rebuild_bend_handles()
            self.update_position()

    def _rebuild_bend_handles(self):
        """Remove old handles and create new ones for current bend points."""
        self._remove_bend_handles()
        scene = self.scene()
        if not scene:
            return
        for i, bp in enumerate(self.bend_points):
            handle = BendHandle(self, i, bp)
            scene.addItem(handle)
            self._bend_handles.append(handle)

    def _remove_bend_handles(self):
        """Remove all bend handles from the scene."""
        for handle in self._bend_handles:
            handle.arrow = None  # Prevent callbacks during removal
            try:
                scene = handle.scene()
                if scene:
                    scene.removeItem(handle)
            except RuntimeError:
                pass  # Handle already deleted (e.g. by scene.clear())
        self._bend_handles.clear()

    def _show_bend_handles(self):
        """Show or create bend handles when arrow is selected."""
        if not self.bend_points:
            return
        if not self._bend_handles:
            self._rebuild_bend_handles()
        for handle in self._bend_handles:
            handle.setVisible(True)

    def _hide_bend_handles(self):
        """Hide bend handles when arrow is deselected."""
        for handle in self._bend_handles:
            try:
                handle.setVisible(False)
            except RuntimeError:
                pass

    # ------------------------------------------------------------------
    # Label
    # ------------------------------------------------------------------

    def set_label_color(self, color):
        self.label_color = QColor(color)
        if self.label:
            self.label.setBrush(QBrush(self.label_color))

    def get_label_color(self):
        return self.label_color

    def set_label_font_size(self, size):
        self.label_font_size = size
        if self.label:
            font = QFont("Arial")
            font.setPointSize(size)
            self.label.setFont(font)
            self.center_label()

    def get_label_font_size(self):
        return self.label_font_size

    def add_label(self, text):
        if self.label:
            self.label.setText(text)
        else:
            self.label = QGraphicsSimpleTextItem(text, self)
            self.label.setBrush(QBrush(self.label_color))
        font = QFont("Arial")
        font.setPointSize(self.label_font_size)
        self.label.setFont(font)
        self.center_label()

    def center_label(self):
        """Place label at the midpoint of the middle segment."""
        if not self.label:
            return
        points = self._get_all_points()
        n = len(points)
        mid_idx = n // 2
        p1 = points[mid_idx - 1]
        p2 = points[mid_idx]
        mid = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
        label_rect = self.label.boundingRect()
        self.label.setPos(
            mid.x() - label_rect.width() / 2,
            mid.y() - label_rect.height() - 2
        )

    # ------------------------------------------------------------------
    # Position and rendering
    # ------------------------------------------------------------------

    def update_position(self):
        """Rebuild the path and arrowheads from current positions and bends."""
        if not self.start_shape or not self.end_shape:
            return

        points = self._get_all_points()

        # Build QPainterPath through all points
        path = QPainterPath()
        path.moveTo(points[0])
        for p in points[1:]:
            path.lineTo(p)
        self.setPath(path)

        # End arrowhead uses last segment angle
        last_seg = QLineF(points[-2], points[-1])
        end_angle = math.atan2(last_seg.dy(), last_seg.dx())
        self.end_head.update_position(points[-1], end_angle)
        self.end_head.set_color(self.arrow_color)

        # Start arrowhead for bidirectional arrows uses first segment angle
        if self.start_head:
            first_seg = QLineF(points[1], points[0])
            start_angle = math.atan2(first_seg.dy(), first_seg.dx())
            self.start_head.update_position(points[0], start_angle)
            self.start_head.set_color(self.arrow_color)

        # Sync bend handle positions (handles track the arrow, not vice versa here)
        for i, handle in enumerate(self._bend_handles):
            if i < len(self.bend_points):
                try:
                    if handle.scene():
                        # Block signals to avoid feedback loop
                        handle.setFlag(handle.ItemSendsGeometryChanges, False)
                        handle.setPos(self.bend_points[i])
                        handle.setFlag(handle.ItemSendsGeometryChanges, True)
                except RuntimeError:
                    pass

        self.center_label()

    def _update_pen(self):
        """Rebuild the pen from current color, width, and style."""
        qt_style = LINE_STYLES.get(self.line_style, Qt.SolidLine)
        self.setPen(QPen(self.arrow_color, self.line_width, qt_style,
                         Qt.RoundCap, Qt.RoundJoin))

    def set_color(self, color):
        self.arrow_color = QColor(color)
        self._update_pen()
        self.end_head.set_color(color)
        if self.start_head:
            self.start_head.set_color(color)

    def set_line_style(self, style_name):
        self.line_style = style_name
        self._update_pen()

    def set_line_width(self, width):
        self.line_width = width
        self._update_pen()

    def detach(self):
        """Disconnect from shapes and clean up bend handles."""
        self._remove_bend_handles()
        if self.start_shape:
            self.start_shape.remove_arrow(self)
        if self.end_shape:
            self.end_shape.remove_arrow(self)

    def paint(self, painter, option, widget=None):
        qt_style = LINE_STYLES.get(self.line_style, Qt.SolidLine)
        if self.isSelected():
            pen = QPen(QColor("#ff6b6b"), self.line_width + 1, qt_style,
                       Qt.RoundCap, Qt.RoundJoin)
            self._show_bend_handles()
        else:
            pen = QPen(self.arrow_color, self.line_width, qt_style,
                       Qt.RoundCap, Qt.RoundJoin)
            self._hide_bend_handles()
        self.setPen(pen)
        super().paint(painter, option, widget)
