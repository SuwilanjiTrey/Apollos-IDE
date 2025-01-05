from PyQt5.QtWidgets import ( QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, 
                            QLabel,  QDoubleSpinBox, 
                            QSplitter, 
                            QFileDialog, QFormLayout, QGroupBox, QGraphicsScene, QGraphicsView,
                            QListWidget, QListWidgetItem)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QBrush
from PyQt5.QtCore import Qt
import os


class SpriteCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setBackgroundBrush(QBrush(QColor("#2B2B2B")))
        
        # Initialize grid
        self.grid_size = 32
        self.show_grid = True
        self.draw_grid()
        
        # Current sprite
        self.current_sprite = None
        
    def draw_grid(self):
        if not self.show_grid:
            return
            
        pen = QPen(QColor("#3A3A3A"))
        pen.setWidth(1)
        
        # Draw vertical lines
        for x in range(0, 800, self.grid_size):
            self.scene.addLine(x, 0, x, 600, pen)
            
        # Draw horizontal lines
        for y in range(0, 600, self.grid_size):
            self.scene.addLine(0, y, 800, y, pen)
    
    def set_sprite(self, pixmap):
        self.scene.clear()
        self.draw_grid()
        if pixmap:
            self.current_sprite = self.scene.addPixmap(pixmap)
            self.current_sprite.setFlag(self.current_sprite.ItemIsMovable)
            self.current_sprite.setFlag(self.current_sprite.ItemIsSelectable)
            # Center the sprite
            self.centerOn(self.current_sprite)
    
    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            # Zoom
            factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

class SpriteEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.sprites = {}  # Dictionary to store loaded sprites
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.load_btn = QPushButton("Load Sprite")
        self.load_btn.clicked.connect(self.load_sprite)
        toolbar.addWidget(self.load_btn)
        
        self.grid_btn = QPushButton("Toggle Grid")
        self.grid_btn.clicked.connect(self.toggle_grid)
        toolbar.addWidget(self.grid_btn)
        
        layout.addLayout(toolbar)
        
        # Split view for sprite list and canvas
        splitter = QSplitter(Qt.Horizontal)
        
        # Sprite list
        self.sprite_list = QListWidget()
        self.sprite_list.itemClicked.connect(self.on_sprite_selected)
        sprite_container = QWidget()
        sprite_layout = QVBoxLayout(sprite_container)
        sprite_layout.addWidget(QLabel("Sprites"))
        sprite_layout.addWidget(self.sprite_list)
        splitter.addWidget(sprite_container)
        
        # Sprite canvas
        self.canvas = SpriteCanvas()
        splitter.addWidget(self.canvas)
        
        # Set splitter sizes
        splitter.setSizes([200, 600])
        layout.addWidget(splitter)
        
        # Properties panel
        props_group = QGroupBox("Sprite Properties")
        props_layout = QFormLayout(props_group)
        
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.1, 10.0)
        self.scale_spin.setValue(1.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.valueChanged.connect(self.update_sprite_scale)
        props_layout.addRow("Scale:", self.scale_spin)
        
        layout.addWidget(props_group)
    
    def load_sprite(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Sprite", "", "Images (*.png *.jpg *.bmp)")
        
        if file_path:
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                sprite_name = os.path.basename(file_path)
                self.sprites[sprite_name] = pixmap
                
                # Add to list
                item = QListWidgetItem(sprite_name)
                self.sprite_list.addItem(item)
                
                # Show in canvas
                self.canvas.set_sprite(pixmap)
    
    def toggle_grid(self):
        self.canvas.show_grid = not self.canvas.show_grid
        self.canvas.scene.clear()
        self.canvas.draw_grid()
        if self.canvas.current_sprite:
            self.canvas.set_sprite(self.sprites[self.sprite_list.currentItem().text()])
    
    def on_sprite_selected(self, item):
        sprite_name = item.text()
        if sprite_name in self.sprites:
            self.canvas.set_sprite(self.sprites[sprite_name])
    
    def update_sprite_scale(self, scale):
        if self.canvas.current_sprite:
            self.canvas.current_sprite.setScale(scale)
