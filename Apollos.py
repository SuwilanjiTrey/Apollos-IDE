import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem,
                            QLabel, QSpinBox, QColorDialog, QDoubleSpinBox, 
                            QSplitter, QTextEdit, QMenuBar, QMenu, QAction,
                            QFileDialog, QFormLayout, QGroupBox, QTabWidget,
                            QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QSyntaxHighlighter, QTextCharFormat
import pygame
import json
from spritesheet import SpriteEditor

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.highlight_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#FF6B6B"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "import", "from", "class", "def", "while", "for",
            "if", "else", "elif", "try", "except", "finally",
            "with", "as", "return", "yield", "break", "continue",
            "and", "or", "not", "is", "in", "True", "False", "None"
        ]
        
        for word in keywords:
            self.highlight_rules.append((f"\\b{word}\\b", keyword_format))
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#F99157"))
        self.highlight_rules.append((r"\b[0-9]+\b", number_format))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#99C794"))
        self.highlight_rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_format))
        self.highlight_rules.append((r"'[^'\\]*(\\.[^'\\]*)*'", string_format))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#A6ACB9"))
        self.highlight_rules.append((r"#[^\n]*", comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlight_rules:
            import re
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

class GamePreviewThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, code):
        super().__init__()
        self.code = code
        self.running = True
        
    def run(self):
        try:
            # Create a dict for local variables to avoid polluting global namespace
            locals_dict = {}
            # Execute the code in the local namespace
            exec(self.code, globals(), locals_dict)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Ensure Pygame is properly quit
            try:
                pygame.display.quit()
                pygame.quit()
            except:
                pass
            self.running = False
            self.finished.emit()
            
    def stop(self):
        self.running = False
        # Force quit Pygame
        try:
            pygame.display.quit()
            pygame.quit()
        except:
            pass

class PyGameIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game_objects = []
        self.selected_object = None
        self.game_thread = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Apollos IDE')
        self.setGeometry(100, 100, 1280, 720)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (Object hierarchy and properties)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Project Explorer
        explorer_group = QGroupBox("Project Explorer")
        explorer_layout = QVBoxLayout(explorer_group)
        self.hierarchy_tree = QTreeWidget()
        self.hierarchy_tree.setHeaderLabel("Game Objects")
        self.hierarchy_tree.itemClicked.connect(self.on_select_object)
        explorer_layout.addWidget(self.hierarchy_tree)
        
        # Object creation buttons
        button_layout = QHBoxLayout()
        add_circle_btn = QPushButton("Add Circle")
        add_circle_btn.clicked.connect(lambda: self.add_game_object("circle"))
        add_rect_btn = QPushButton("Add Rectangle")
        add_rect_btn.clicked.connect(lambda: self.add_game_object("rectangle"))
        button_layout.addWidget(add_circle_btn)
        button_layout.addWidget(add_rect_btn)
        explorer_layout.addLayout(button_layout)
        
        left_layout.addWidget(explorer_group)
        
        # Properties panel
        properties_group = QGroupBox("Properties")
        self.properties_layout = QFormLayout(properties_group)
        left_layout.addWidget(properties_group)
        
        # Add left panel to splitter
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # Center panel (Game preview and Sprite Editor)
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)

        # Preview controls
        preview_controls = QHBoxLayout()
        play_btn = QPushButton("▶ Play")
        play_btn.clicked.connect(self.start_game_preview)
        stop_btn = QPushButton("⏹ Stop")
        stop_btn.clicked.connect(self.stop_game_preview)
        preview_controls.addWidget(play_btn)
        preview_controls.addWidget(stop_btn)
        center_layout.addLayout(preview_controls)

        # Sprite Editor
        self.sprite_editor = SpriteEditor()
        center_layout.addWidget(self.sprite_editor)

        # Preview area
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        preview_frame.setMinimumSize(800, 600)
        center_layout.addWidget(preview_frame)

        # Add center panel to splitter
        center_widget = QWidget()
        center_widget.setLayout(center_layout)
        splitter.addWidget(center_widget)
        
        
        
        # Right panel (Code editor)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Code editor with tabs
        editor_tabs = QTabWidget()
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.highlighter = PythonHighlighter(self.code_editor.document())
        editor_tabs.addTab(self.code_editor, "game.py")
        
        right_layout.addWidget(editor_tabs)
        
        # Add right panel to splitter
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([200, 600, 400])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Generate initial code
        self.generate_code()
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New Project', self)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        save_action = QAction('Save Project', self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        load_action = QAction('Load Project', self)
        load_action.triggered.connect(self.load_project)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('Export Game', self)
        export_action.triggered.connect(self.export_game)
        file_menu.addAction(export_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        # View menu
        view_menu = menubar.addMenu('View')
        
        # Build menu
        build_menu = menubar.addMenu('Build')
        
        # Help menu
        help_menu = menubar.addMenu('Help')
    
    def add_game_object(self, obj_type):
        obj_id = f"{obj_type}_{len(self.game_objects)}"
        
        if obj_type == "circle":
            obj = {
                "id": obj_id,
                "type": "circle",
                "x": 400,
                "y": 300,
                "radius": 20,
                "color": "#FF0000",
                "physics": {
                    "velocity_x": 0,
                    "velocity_y": 0,
                    "gravity": 0,
                    "bounce": 0.8
                }
            }
        else:  # rectangle
            obj = {
                "id": obj_id,
                "type": "rectangle",
                "x": 400,
                "y": 300,
                "width": 40,
                "height": 40,
                "color": "#00FF00",
                "physics": {
                    "velocity_x": 0,
                    "velocity_y": 0,
                    "gravity": 0,
                    "bounce": 0.8
                }
            }
        
        self.game_objects.append(obj)
        item = QTreeWidgetItem([obj_id])
        self.hierarchy_tree.addTopLevelItem(item)
        self.update_properties_panel(obj)
        self.generate_code()
    
    def on_select_object(self, item):
        obj_id = item.text(0)
        obj = next((obj for obj in self.game_objects if obj["id"] == obj_id), None)
        if obj:
            self.selected_object = obj
            self.update_properties_panel(obj)
    
    def update_properties_panel(self, obj):
        # Clear existing properties
        while self.properties_layout.rowCount() > 0:
            self.properties_layout.removeRow(0)
        
        # Add new properties
        for prop, value in obj.items():
            if prop != "id" and prop != "type":
                if isinstance(value, dict):
                    group = QGroupBox(prop.title())
                    group_layout = QFormLayout()
                    for sub_prop, sub_value in value.items():
                        self.create_property_field(sub_prop, sub_value, group_layout, obj, prop)
                    group.setLayout(group_layout)
                    self.properties_layout.addRow(group)
                else:
                    self.create_property_field(prop, value, self.properties_layout, obj)
    
    def create_property_field(self, prop, value, layout, obj, parent_prop=None):
        if isinstance(value, (int, float)):
            if prop in ["x", "y", "width", "height", "radius"]:
                spinner = QSpinBox()
                spinner.setRange(0, 1000)
                spinner.setValue(int(value))
                spinner.valueChanged.connect(
                    lambda v: self.update_object_property(prop, v, parent_prop))
                layout.addRow(f"{prop.title()}:", spinner)
            else:
                spinner = QDoubleSpinBox()
                spinner.setRange(-100, 100)
                spinner.setSingleStep(0.1)
                spinner.setValue(float(value))
                spinner.valueChanged.connect(
                    lambda v: self.update_object_property(prop, v, parent_prop))
                layout.addRow(f"{prop.title()}:", spinner)
        elif isinstance(value, str) and prop == "color":
            color_btn = QPushButton(value)
            color_btn.setStyleSheet(f"background-color: {value}")
            color_btn.clicked.connect(
                lambda: self.choose_color(prop, parent_prop))
            layout.addRow(f"{prop.title()}:", color_btn)
    
    def choose_color(self, prop, parent_prop=None):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            if parent_prop:
                self.selected_object[parent_prop][prop] = hex_color
            else:
                self.selected_object[prop] = hex_color
            self.update_properties_panel(self.selected_object)
            self.generate_code()
    
    def update_object_property(self, prop, value, parent_prop=None):
        if self.selected_object:
            if parent_prop:
                self.selected_object[parent_prop][prop] = value
            else:
                self.selected_object[prop] = value
            self.generate_code()
    
    def generate_code(self):
        code = """import pygame
import sys

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PyGame Game")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Game objects
objects = []
"""
        
        # Add object definitions
        for obj in self.game_objects:
            if obj["type"] == "circle":
                code += f"""
circle = {{
    'type': 'circle',
    'x': {obj['x']},
    'y': {obj['y']},
    'radius': {obj['radius']},
    'color': '{obj['color']}',
    'physics': {{
        'velocity_x': {obj['physics']['velocity_x']},
        'velocity_y': {obj['physics']['velocity_y']},
        'gravity': {obj['physics']['gravity']},
        'bounce': {obj['physics']['bounce']}
    }}
}}
objects.append(circle)
"""
            else:  # rectangle
                code += f"""
rectangle = {{
    'type': 'rectangle',
    'x': {obj['x']},
    'y': {obj['y']},
    'width': {obj['width']},
    'height': {obj['height']},
    'color': '{obj['color']}',
    'physics': {{
        'velocity_x': {obj['physics']['velocity_x']},
        'velocity_y': {obj['physics']['velocity_y']},
        'gravity': {obj['physics']['gravity']},
        'bounce': {obj['physics']['bounce']}
    }}
}}
objects.append(rectangle)
"""
        
        # Modified game loop to check thread running state
        code += """
# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Update physics for all objects
    for obj in objects:
        # Apply gravity
        obj['physics']['velocity_y'] += obj['physics']['gravity']
        
        # Update position based on velocity
        obj['x'] += obj['physics']['velocity_x']
        obj['y'] += obj['physics']['velocity_y']
        
        # Handle collisions with screen boundaries
        if obj['type'] == 'circle':
            if obj['y'] + obj['radius'] > HEIGHT:
                obj['y'] = HEIGHT - obj['radius']
                obj['physics']['velocity_y'] = -obj['physics']['velocity_y'] * obj['physics']['bounce']
            if obj['x'] + obj['radius'] > WIDTH or obj['x'] - obj['radius'] < 0:
                obj['physics']['velocity_x'] = -obj['physics']['velocity_x'] * obj['physics']['bounce']
        else:  # rectangle
            if obj['y'] + obj['height'] > HEIGHT:
                obj['y'] = HEIGHT - obj['height']
                obj['physics']['velocity_y'] = -obj['physics']['velocity_y'] * obj['physics']['bounce']
            if obj['x'] + obj['width'] > WIDTH or obj['x'] < 0:
                obj['physics']['velocity_x'] = -obj['physics']['velocity_x'] * obj['physics']['bounce']
    
    # Clear screen
    screen.fill((255, 255, 255))
    
    # Draw objects
    for obj in objects:
        if obj['type'] == 'circle':
            pygame.draw.circle(screen, pygame.Color(obj['color']), 
                             (int(obj['x']), int(obj['y'])), obj['radius'])
        else:  # rectangle
            pygame.draw.rect(screen, pygame.Color(obj['color']), 
                           pygame.Rect(obj['x'], obj['y'], obj['width'], obj['height']))
    
    # Update display
    pygame.display.flip()
    clock.tick(60)

# Clean up Pygame
pygame.quit()
"""
         # Update the code editor
        self.code_editor.setText(code)

    def start_game_preview(self):
        # Stop any existing game preview
        self.stop_game_preview()
        
        # Create and start new game thread
        code = self.code_editor.toPlainText()
        self.game_thread = GamePreviewThread(code)
        self.game_thread.finished.connect(self.on_game_preview_finished)
        self.game_thread.error.connect(self.on_game_preview_error)
        self.game_thread.start()

    def stop_game_preview(self):
        if self.game_thread and self.game_thread.isRunning():
            self.game_thread.stop()
            self.game_thread.wait()
            self.game_thread = None

    def on_game_preview_finished(self):
        print("Game preview finished")
        self.game_thread = None

    def on_game_preview_error(self, error_msg):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Game Preview Error", f"Error in game preview:\n{error_msg}")

    def new_project(self):
        self.game_objects = []
        self.hierarchy_tree.clear()
        self.generate_code()

    def save_project(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", "JSON Files (*.json)")
        if file_path:
            project_data = {
                "objects": self.game_objects,
                "code": self.code_editor.toPlainText()
            }
            with open(file_path, 'w') as f:
                json.dump(project_data, f)

    def load_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, 'r') as f:
                project_data = json.load(f)
            
            self.game_objects = project_data["objects"]
            self.hierarchy_tree.clear()
            
            for obj in self.game_objects:
                item = QTreeWidgetItem([obj["id"]])
                self.hierarchy_tree.addTopLevelItem(item)
            
            self.code_editor.setText(project_data["code"])

    def export_game(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Game", "", "Python Files (*.py)")
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.code_editor.toPlainText())

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create dark palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    
    app.setPalette(palette)
    
    # Apply some styling
    app.setStyleSheet("""
        QMainWindow {
            background-color: #353535;
        }
        QTreeWidget {
            background-color: #252525;
            color: white;
            border: 1px solid #555555;
        }
        QTextEdit {
            background-color: #252525;
            color: white;
            border: 1px solid #555555;
            font-family: Consolas, monospace;
        }
        QPushButton {
            background-color: #454545;
            color: white;
            border: 1px solid #555555;
            padding: 5px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #555555;
        }
        QGroupBox {
            color: white;
            border: 1px solid #555555;
            margin-top: 5px;
        }
        QGroupBox::title {
            color: white;
        }
        QSpinBox, QDoubleSpinBox {
            background-color: #252525;
            color: white;
            border: 1px solid #555555;
        }
        QLabel {
            color: white;
        }
    """)
    
    ide = PyGameIDE()
    ide.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
