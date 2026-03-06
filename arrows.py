import math
from PyQt5.QtWidgets import (QGraphicsPathItem, QGraphicsPolygonItem,
                              QGraphicsSimpleTextItem, QGraphicsEllipseItem)
from PyQt5.QtCore import Qt, QPointF, QLineF
from PyQt5.QtGui import (QPen, QBrush, QColor, QPolygonF, QFont,
                          QPainterPath, QPainterPathStroker)


# Valid cap styles for arrow endpoints
CAP_STYLES = ('none', 'arrow', 'ball')


class ArrowHead(QGraphicsPolygonItem):
    """Visual cap at an arrow endpoint: arrow triangle, ball, or nothing."""

    ARROW_SIZE = 12
    BALL_RADIUS = 4
    BALL_SEGMENTS = 16  # Polygon vertices to approximate a circle

    def __init__(self, style='arrow', parent=None):
        super().__init__(parent)
        self._style = style
        self.setBrush(QBrush(QColor("#333333")))
        self.setPen(QPen(Qt.NoPen))

    @property
    def style(self):
        return self._style

    @style.setter
    def style(self, value):
        self._style = value

    def update_position(self, line_end, angle):
        """Redraw the cap at line_end oriented by angle."""
        if self._style == 'arrow':
            self._draw_arrow(line_end, angle)
        elif self._style == 'ball':
            self._draw_ball(line_end)
        else:
            # 'none' — empty polygon hides the cap
            self.setPolygon(QPolygonF())

    def _draw_arrow(self, tip, angle):
        p1 = tip
        p2 = QPointF(
            tip.x() - self.ARROW_SIZE * math.cos(angle - math.pi / 6),
            tip.y() - self.ARROW_SIZE * math.sin(angle - math.pi / 6)
        )
        p3 = QPointF(
            tip.x() - self.ARROW_SIZE * math.cos(angle + math.pi / 6),
            tip.y() - self.ARROW_SIZE * math.sin(angle + math.pi / 6)
        )
        self.setPolygon(QPolygonF([p1, p2, p3]))

    def _draw_ball(self, center):
        r = self.BALL_RADIUS
        points = []
        for i in range(self.BALL_SEGMENTS):
            a = 2 * math.pi * i / self.BALL_SEGMENTS
            points.append(QPointF(center.x() + r * math.cos(a),
                                  center.y() + r * math.sin(a)))
        self.setPolygon(QPolygonF(points))

    def set_color(self, color):
        self.setBrush(QBrush(QColor(color)))


class AnchorPoint(QGraphicsEllipseItem):
    """Draggable endpoint for arrows. Can dock to shape edges or float freely."""

    ANCHOR_SIZE = 8
    SNAP_DISTANCE = 30  # Max distance to snap to a shape edge

    def __init__(self, x, y):
        half = self.ANCHOR_SIZE / 2
        super().__init__(-half, -half, self.ANCHOR_SIZE, self.ANCHOR_SIZE)
        self.setPos(x, y)
        self.setFlags(
            self.ItemIsMovable |
            self.ItemIsSelectable |
            self.ItemSendsGeometryChanges
        )
        self.setZValue(5)
        self.setCursor(Qt.SizeAllCursor)
        self.arrows = []
        self.docked_shape = None  # Shape this anchor is snapped to
        self._dock_angle = 0.0    # Angle from shape center to dock point

    def shape(self):
        """Wider hit area for easier clicking."""
        path = QPainterPath()
        hit = 16
        half = hit / 2
        path.addEllipse(-half, -half, hit, hit)
        return path

    def get_center(self):
        if self.docked_shape:
            return self.docked_shape.get_center()
        return self.scenePos()

    def get_connection_point(self, target_pos):
        """When docked, compute edge point at the stored angle on the shape."""
        if self.docked_shape:
            pt = self._edge_point_at_angle(self.docked_shape, self._dock_angle)
            # Move anchor dot to the edge point (without triggering itemChange)
            self.setFlag(self.ItemSendsGeometryChanges, False)
            self.setPos(pt)
            self.setFlag(self.ItemSendsGeometryChanges, True)
            return pt
        return self.scenePos()

    @staticmethod
    def _edge_point_at_angle(shape, angle):
        """Get the point on the shape's bounding rect edge at a given angle."""
        rect = shape.sceneBoundingRect()
        cx, cy = rect.center().x(), rect.center().y()
        dx = math.cos(angle)
        dy = math.sin(angle)
        hw = rect.width() / 2
        hh = rect.height() / 2
        # Time to hit vertical and horizontal edges
        tx = (hw / abs(dx)) if abs(dx) > 1e-10 else float('inf')
        ty = (hh / abs(dy)) if abs(dy) > 1e-10 else float('inf')
        t = min(tx, ty)
        return QPointF(cx + dx * t, cy + dy * t)

    def add_arrow(self, arrow):
        if arrow not in self.arrows:
            self.arrows.append(arrow)

    def remove_arrow(self, arrow):
        if arrow in self.arrows:
            self.arrows.remove(arrow)

    def dock_to(self, shape):
        """Snap this anchor to a shape's edge. Arrow follows the shape."""
        if self.docked_shape is shape:
            return
        self.undock()
        self.docked_shape = shape
        # Store angle from shape center to anchor position (determines edge point)
        center = shape.get_center()
        self._dock_angle = math.atan2(
            self.scenePos().y() - center.y(),
            self.scenePos().x() - center.x()
        )
        # Register our arrows with the shape so it updates them when it moves
        for arrow in self.arrows:
            shape.add_arrow(arrow)
        # Trigger arrow recalculation to position anchor on edge
        for arrow in self.arrows:
            arrow.update_position()

    def undock(self):
        """Detach from the docked shape."""
        if not self.docked_shape:
            return
        # Unregister our arrows from the shape
        for arrow in self.arrows:
            try:
                self.docked_shape.remove_arrow(arrow)
            except (RuntimeError, AttributeError):
                pass
        self.docked_shape = None

    def try_snap(self):
        """Check nearby shapes and dock/undock as appropriate."""
        scene = self.scene()
        if not scene or not hasattr(scene, 'find_nearest_shape'):
            return
        shape = scene.find_nearest_shape(self.scenePos(), self.SNAP_DISTANCE, exclude=self)
        if shape:
            self.dock_to(shape)
        elif self.docked_shape:
            self.undock()

    def itemChange(self, change, value):
        if change == self.ItemPositionHasChanged:
            for arrow in self.arrows:
                arrow.update_position()
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        """Undock before dragging so anchor moves freely."""
        if event.button() == Qt.LeftButton:
            if self.docked_shape:
                self.undock()
            scene = self.scene()
            if scene and hasattr(scene, 'save_undo'):
                scene.save_undo()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Try to snap to a nearby shape after drag ends."""
        super().mouseReleaseEvent(event)
        self.try_snap()

    def paint(self, painter, option, widget=None):
        """Draw with different colors: gray=free, green=docked, blue=selected."""
        if self.isSelected():
            self.setBrush(QBrush(QColor(74, 144, 217, 120)))
            self.setPen(QPen(QColor("#4a90d9"), 1.5))
        elif self.docked_shape:
            self.setBrush(QBrush(QColor(46, 204, 113, 160)))
            self.setPen(QPen(QColor("#27ae60"), 1.5))
        else:
            self.setBrush(QBrush(QColor("#aaaaaa")))
            self.setPen(QPen(QColor("#666666"), 1))
        super().paint(painter, option, widget)


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
        self.setZValue(10)
        self.setCursor(Qt.SizeAllCursor)

    def itemChange(self, change, value):
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
    """Arrow connecting two shapes or anchor points, with bend points and cap styles."""

    def __init__(self, start_shape, end_shape, bidirectional=False,
                 color="#333333", line_style='Solid', line_width=2,
                 bend_points=None, start_cap=None, end_cap=None):
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

        # Cap styles: 'none', 'arrow', 'ball'
        # If not specified, derive from bidirectional flag for backward compat
        self.start_cap = start_cap if start_cap is not None else ('arrow' if bidirectional else 'none')
        self.end_cap = end_cap if end_cap is not None else 'arrow'

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

        # Always create both heads; style controls visibility
        self.end_head = ArrowHead(style=self.end_cap, parent=self)
        self.start_head = ArrowHead(style=self.start_cap, parent=self)

        start_shape.add_arrow(self)
        end_shape.add_arrow(self)

        self.update_position()

    # ------------------------------------------------------------------
    # Cap style management
    # ------------------------------------------------------------------

    def set_start_cap(self, style):
        """Change the start endpoint cap style."""
        self.start_cap = style
        self.start_head.style = style
        self.update_position()

    def set_end_cap(self, style):
        """Change the end endpoint cap style."""
        self.end_cap = style
        self.end_head.style = style
        self.update_position()

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _get_all_points(self):
        """Return full point list: start connection -> bends -> end connection."""
        start_center = self.start_shape.get_center()
        end_center = self.end_shape.get_center()

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
        if segment_index is None:
            segment_index = self._find_segment_index(scene_pos)
        self.bend_points.insert(segment_index, QPointF(scene_pos))
        self._rebuild_bend_handles()
        self.update_position()

    def remove_bend_point(self, index):
        if 0 <= index < len(self.bend_points):
            self.bend_points.pop(index)
            self._rebuild_bend_handles()
            self.update_position()

    def _rebuild_bend_handles(self):
        self._remove_bend_handles()
        scene = self.scene()
        if not scene:
            return
        for i, bp in enumerate(self.bend_points):
            handle = BendHandle(self, i, bp)
            scene.addItem(handle)
            self._bend_handles.append(handle)

    def _remove_bend_handles(self):
        for handle in self._bend_handles:
            handle.arrow = None
            try:
                scene = handle.scene()
                if scene:
                    scene.removeItem(handle)
            except RuntimeError:
                pass
        self._bend_handles.clear()

    def _show_bend_handles(self):
        if not self.bend_points:
            return
        if not self._bend_handles:
            self._rebuild_bend_handles()
        for handle in self._bend_handles:
            handle.setVisible(True)

    def _hide_bend_handles(self):
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
        if not self.start_shape or not self.end_shape:
            return

        points = self._get_all_points()

        # Build QPainterPath through all points
        path = QPainterPath()
        path.moveTo(points[0])
        for p in points[1:]:
            path.lineTo(p)
        self.setPath(path)

        # End cap
        last_seg = QLineF(points[-2], points[-1])
        end_angle = math.atan2(last_seg.dy(), last_seg.dx())
        self.end_head.update_position(points[-1], end_angle)
        self.end_head.set_color(self.arrow_color)

        # Start cap
        first_seg = QLineF(points[1], points[0])
        start_angle = math.atan2(first_seg.dy(), first_seg.dx())
        self.start_head.update_position(points[0], start_angle)
        self.start_head.set_color(self.arrow_color)

        # Sync bend handle positions
        for i, handle in enumerate(self._bend_handles):
            if i < len(self.bend_points):
                try:
                    if handle.scene():
                        handle.setFlag(handle.ItemSendsGeometryChanges, False)
                        handle.setPos(self.bend_points[i])
                        handle.setFlag(handle.ItemSendsGeometryChanges, True)
                except RuntimeError:
                    pass

        self.center_label()

    def _update_pen(self):
        qt_style = LINE_STYLES.get(self.line_style, Qt.SolidLine)
        self.setPen(QPen(self.arrow_color, self.line_width, qt_style,
                         Qt.RoundCap, Qt.RoundJoin))

    def set_color(self, color):
        self.arrow_color = QColor(color)
        self._update_pen()
        self.end_head.set_color(color)
        self.start_head.set_color(color)

    def set_line_style(self, style_name):
        self.line_style = style_name
        self._update_pen()

    def set_line_width(self, width):
        self.line_width = width
        self._update_pen()

    def detach(self):
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
