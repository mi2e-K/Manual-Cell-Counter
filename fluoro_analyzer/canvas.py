"""
Image canvas widget for Fluorescence Microscope Image Analyzer.
"""

from typing import Optional

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsTextItem
from PyQt6.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPixmap, QPainter, QColor, QPen, QBrush, QFont,
    QWheelEvent, QMouseEvent, QDragEnterEvent, QDropEvent
)

from .datatypes import ToolMode


class ImageCanvas(QGraphicsView):
    """Custom graphics view for displaying and interacting with images."""
    
    cell_clicked = pyqtSignal(QPointF)
    roi_point_added = pyqtSignal(QPointF)
    roi_close_requested = pyqtSignal()
    roi_vertex_moved = pyqtSignal(int, int, QPointF)  # roi_index, vertex_index, new_pos
    roi_moved = pyqtSignal(int, QPointF)  # roi_index, delta
    marker_moved = pyqtSignal(int, QPointF)  # marker_index, new_pos
    marker_selected = pyqtSignal(int)  # marker_index (-1 to deselect)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Setup
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        
        # State
        self.pixmap_item: Optional[QGraphicsPixmapItem] = None
        self.tool_mode = ToolMode.PAN
        self.zoom_factor = 1.0
        self.placeholder_text: Optional[QGraphicsTextItem] = None
        
        # ROI drawing state
        self.temp_line = None
        self.last_roi_point: Optional[QPointF] = None
        
        # ROI editing state
        self.dragging_vertex = False
        self.dragging_roi = False
        self.selected_roi_index = -1
        self.selected_vertex_index = -1
        self.drag_start_pos: Optional[QPointF] = None
        
        # Marker dragging state
        self.dragging_marker = False
        self.selected_marker_index = -1
        
        # Right-click panning state
        self.right_click_panning = False
        self.pan_start_pos: Optional[QPointF] = None
        
        # Enable mouse tracking for real-time line
        self.setMouseTracking(True)
        
        # Accept drops
        self.setAcceptDrops(True)
        
        # Show placeholder
        self.show_placeholder()
    
    def show_placeholder(self):
        """Show placeholder text when no image is loaded."""
        if self.placeholder_text is None:
            self.placeholder_text = QGraphicsTextItem("Drop image file here\n\nSupported formats:\nTIFF, PNG, JPEG")
            self.placeholder_text.setDefaultTextColor(QColor(100, 100, 100))
            font = QFont("Arial", 18)
            self.placeholder_text.setFont(font)
            self.scene.addItem(self.placeholder_text)
            bounds = self.placeholder_text.boundingRect()
            self.placeholder_text.setPos(-bounds.width() / 2, -bounds.height() / 2)
            self.setSceneRect(-200, -100, 400, 200)
    
    def hide_placeholder(self):
        """Hide placeholder text."""
        if self.placeholder_text is not None:
            self.scene.removeItem(self.placeholder_text)
            self.placeholder_text = None
    
    def set_tool_mode(self, mode: ToolMode):
        """Set the current tool mode."""
        self.tool_mode = mode
        self.clear_temp_line()
        self.last_roi_point = None
        
        if mode == ToolMode.PAN:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
    
    def set_last_roi_point(self, point: QPointF):
        """Set the last ROI point for real-time line drawing."""
        self.last_roi_point = point
    
    def clear_temp_line(self):
        """Clear the temporary ROI line."""
        if self.temp_line:
            self.scene.removeItem(self.temp_line)
            self.temp_line = None
    
    def set_image(self, pixmap: QPixmap):
        """Set the displayed image (resets view to fit)."""
        self.hide_placeholder()
        self.scene.clear()
        self.placeholder_text = None
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.setSceneRect(QRectF(pixmap.rect()))
        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_factor = 1.0
        self.temp_line = None
        self.last_roi_point = None
    
    def update_pixmap(self, pixmap: QPixmap):
        """Update the displayed image without resetting view/zoom."""
        if self.pixmap_item is None:
            self.set_image(pixmap)
            return
        
        # Save current transform and scroll position
        current_transform = self.transform()
        h_scroll = self.horizontalScrollBar().value()
        v_scroll = self.verticalScrollBar().value()
        
        # Clear and recreate scene
        self.hide_placeholder()
        self.scene.clear()
        self.placeholder_text = None
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.setSceneRect(QRectF(pixmap.rect()))
        
        # Restore transform and scroll position
        self.setTransform(current_transform)
        self.horizontalScrollBar().setValue(h_scroll)
        self.verticalScrollBar().setValue(v_scroll)
        
        self.temp_line = None
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming."""
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
            self.zoom_factor *= factor
        else:
            self.scale(1 / factor, 1 / factor)
            self.zoom_factor /= factor
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        scene_pos = self.mapToScene(event.pos())
        
        if event.button() == Qt.MouseButton.LeftButton:
            if self.tool_mode == ToolMode.CELL_COUNT:
                self.cell_clicked.emit(scene_pos)
            elif self.tool_mode == ToolMode.ROI_DRAW:
                # Check if clicking on a vertex to edit
                main_window = self.window()
                if hasattr(main_window, 'find_roi_vertex_at'):
                    roi_idx, vertex_idx = main_window.find_roi_vertex_at(scene_pos)
                    if roi_idx >= 0 and vertex_idx >= 0:
                        self.dragging_vertex = True
                        self.selected_roi_index = roi_idx
                        self.selected_vertex_index = vertex_idx
                        self.drag_start_pos = scene_pos
                        return
                    
                    roi_idx = main_window.find_roi_at(scene_pos)
                    if roi_idx >= 0:
                        self.dragging_roi = True
                        self.selected_roi_index = roi_idx
                        self.drag_start_pos = scene_pos
                        return
                
                self.roi_point_added.emit(scene_pos)
            else:
                super().mousePressEvent(event)
                
        elif event.button() == Qt.MouseButton.RightButton:
            if self.tool_mode == ToolMode.ROI_DRAW:
                main_window = self.window()
                if hasattr(main_window, 'current_roi') and main_window.current_roi:
                    self.roi_close_requested.emit()
                else:
                    self.right_click_panning = True
                    self.pan_start_pos = event.pos()
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
            elif self.tool_mode == ToolMode.CELL_COUNT:
                main_window = self.window()
                if hasattr(main_window, 'find_marker_at'):
                    marker_idx = main_window.find_marker_at(scene_pos)
                    if marker_idx >= 0:
                        # Select the marker first
                        self.marker_selected.emit(marker_idx)
                        # Prepare for potential drag
                        self.dragging_marker = True
                        self.selected_marker_index = marker_idx
                        self.drag_start_pos = scene_pos
                        self.setCursor(Qt.CursorShape.SizeAllCursor)
                        return
                    else:
                        # Deselect if clicking on empty area
                        self.marker_selected.emit(-1)
                
                self.right_click_panning = True
                self.pan_start_pos = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events."""
        scene_pos = self.mapToScene(event.pos())
        
        if self.dragging_vertex and self.selected_roi_index >= 0:
            self.roi_vertex_moved.emit(self.selected_roi_index, self.selected_vertex_index, scene_pos)
            return
        
        if self.dragging_roi and self.selected_roi_index >= 0 and self.drag_start_pos:
            delta = scene_pos - self.drag_start_pos
            self.roi_moved.emit(self.selected_roi_index, delta)
            self.drag_start_pos = scene_pos
            return
        
        if self.dragging_marker and self.selected_marker_index >= 0:
            self.marker_moved.emit(self.selected_marker_index, scene_pos)
            return
        
        if self.right_click_panning and self.pan_start_pos:
            delta = event.pos() - self.pan_start_pos
            self.pan_start_pos = event.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            return
        
        if self.tool_mode == ToolMode.ROI_DRAW and self.last_roi_point:
            self.clear_temp_line()
            pen = QPen(QColor(255, 255, 0, 180))
            pen.setWidth(2)
            pen.setStyle(Qt.PenStyle.DashLine)
            self.temp_line = self.scene.addLine(
                self.last_roi_point.x(), self.last_roi_point.y(),
                scene_pos.x(), scene_pos.y(),
                pen
            )
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_vertex = False
            self.dragging_roi = False
            self.selected_roi_index = -1
            self.selected_vertex_index = -1
            self.drag_start_pos = None
        elif event.button() == Qt.MouseButton.RightButton:
            self.dragging_marker = False
            self.selected_marker_index = -1
            self.right_click_panning = False
            self.pan_start_pos = None
            if self.tool_mode == ToolMode.PAN:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
        super().mouseReleaseEvent(event)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Handle drag move events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.tif', '.tiff', '.png', '.jpg', '.jpeg')):
                main_window = self.window()
                if hasattr(main_window, 'load_image'):
                    main_window.load_image(file_path)
                event.acceptProposedAction()
    
    def reset_view(self):
        """Reset view to fit the image."""
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)
            self.zoom_factor = 1.0
