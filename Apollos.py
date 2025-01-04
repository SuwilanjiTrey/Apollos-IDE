import tkinter as tk
from tkinter import ttk, scrolledtext
import pygame
import json
import os
from tkinter import filedialog
import threading
from spritesheet import SpriteSheetExtractor

class PyGameIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("PyGame IDE")
        self.root.state('zoomed')  # Start maximized
        
        # Initialize game properties
        self.game_objects = []
        self.selected_object = None
        self.game_running = False
        self.game_thread = None
        
        self.setup_ui()
        self.setup_pygame_preview()
        
    def setup_ui(self):
        # Create main container
        self.main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Object hierarchy and properties
        self.left_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.left_panel)
        
        # Hierarchy section
        self.hierarchy_label = ttk.Label(self.left_panel, text="Hierarchy")
        self.hierarchy_label.pack(pady=5)
        
        self.hierarchy_tree = ttk.Treeview(self.left_panel, height=10)
        self.hierarchy_tree.pack(fill=tk.X, padx=5)
        self.hierarchy_tree.bind('<<TreeviewSelect>>', self.on_select_object)
        
        # Add object buttons
        self.object_buttons_frame = ttk.Frame(self.left_panel)
        self.object_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.object_buttons_frame, text="Add Circle", 
                  command=lambda: self.add_game_object("circle")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.object_buttons_frame, text="Add Rectangle", 
                  command=lambda: self.add_game_object("rectangle")).pack(side=tk.LEFT, padx=2)
        
        # Properties section
        self.properties_label = ttk.Label(self.left_panel, text="Properties")
        self.properties_label.pack(pady=5)
        
        self.properties_frame = ttk.Frame(self.left_panel)
        self.properties_frame.pack(fill=tk.BOTH, padx=5)
        
        # Center panel - Game preview
        self.center_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.center_panel)
        
        # Preview controls
        self.preview_controls = ttk.Frame(self.center_panel)
        self.preview_controls.pack(fill=tk.X)
        
        ttk.Button(self.preview_controls, text="▶ Play", 
                  command=self.start_game_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.preview_controls, text="⏹ Stop", 
                  command=self.stop_game_preview).pack(side=tk.LEFT, padx=5)
        
        # Preview canvas
        self.preview_frame = ttk.Frame(self.center_panel, relief=tk.SUNKEN, borderwidth=1)
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel - Code editor
        self.right_panel = ttk.Frame(self.main_container)
        self.main_container.add(self.right_panel)
        
        self.code_editor = scrolledtext.ScrolledText(self.right_panel, wrap=tk.WORD)
        self.code_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Menu bar
        self.setup_menu()
        
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_command(label="Load Project", command=self.load_project)
        file_menu.add_separator()
        file_menu.add_command(label="Export Game", command=self.export_game)

         # Add Sprites menu
        sprites_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sprites", menu=sprites_menu)
        sprites_menu.add_command(label="Extract Sprite Sheet", command=self.extract_sprite_sheet)
    
        
    def extract_sprite_sheet(self):
        # Open file dialog to select sprite sheet
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                # Create extractor instance
                extractor = SpriteSheetExtractor()
                
                # Extract sprites
                sprites = extractor.extract_sprites(file_path)
                
                # Show success message with extraction details
                tk.messagebox.showinfo(
                    "Extraction Complete",
                    f"Successfully extracted {len(sprites)} sprites to '{extractor.output_folder}' folder"
                )
                
            except Exception as e:
                tk.messagebox.showerror(
                    "Extraction Error",
                    f"An error occurred while extracting sprites: {str(e)}"
                )

    def setup_pygame_preview(self):
        # Initialize Pygame
        pygame.init()
        self.preview_surface = pygame.Surface((800, 600))
        self.preview_running = True
        
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
        self.hierarchy_tree.insert('', 'end', obj_id, text=obj_id)
        self.update_properties_panel(obj)
        self.generate_code()
    
    def on_select_object(self, event):
        selection = self.hierarchy_tree.selection()
        if selection:
            obj_id = selection[0]
            obj = next((obj for obj in self.game_objects if obj["id"] == obj_id), None)
            if obj:
                self.selected_object = obj
                self.update_properties_panel(obj)
    
    def update_properties_panel(self, obj):
        # Clear existing properties
        for widget in self.properties_frame.winfo_children():
            widget.destroy()
        
        # Create property fields
        row = 0
        for prop, value in obj.items():
            if prop != "id" and prop != "type":
                if isinstance(value, dict):  # Handle nested properties (physics)
                    ttk.Label(self.properties_frame, text=prop.title()).grid(row=row, column=0, pady=5)
                    row += 1
                    for sub_prop, sub_value in value.items():
                        self.create_property_field(sub_prop, sub_value, row, indent=True)
                        row += 1
                else:
                    self.create_property_field(prop, value, row)
                    row += 1
    
    def create_property_field(self, prop, value, row, indent=False):
        padx = 20 if indent else 0
        ttk.Label(self.properties_frame, text=prop.title()).grid(row=row, column=0, padx=padx)
        
        if isinstance(value, bool):
            var = tk.BooleanVar(value=value)
            field = ttk.Checkbutton(self.properties_frame, variable=var)
        else:
            var = tk.StringVar(value=str(value))
            field = ttk.Entry(self.properties_frame, textvariable=var)
            
        field.grid(row=row, column=1, padx=5)
        field.bind('<Return>', lambda e: self.update_object_property(prop, var.get()))
    
    def update_object_property(self, prop, value):
        if self.selected_object:
            try:
                # Convert value to appropriate type
                if isinstance(self.selected_object[prop], int):
                    value = int(value)
                elif isinstance(self.selected_object[prop], float):
                    value = float(value)
                
                self.selected_object[prop] = value
                self.generate_code()
            except (ValueError, KeyError):
                pass
    
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
circle_{obj['id']} = {{
    'x': {obj['x']},
    'y': {obj['y']},
    'radius': {obj['radius']},
    'color': '{obj['color']}',
    'velocity_x': {obj['physics']['velocity_x']},
    'velocity_y': {obj['physics']['velocity_y']},
    'gravity': {obj['physics']['gravity']},
    'bounce': {obj['physics']['bounce']}
}}
objects.append(circle_{obj['id']})
"""
            else:  # rectangle
                code += f"""
rect_{obj['id']} = {{
    'x': {obj['x']},
    'y': {obj['y']},
    'width': {obj['width']},
    'height': {obj['height']},
    'color': '{obj['color']}',
    'velocity_x': {obj['physics']['velocity_x']},
    'velocity_y': {obj['physics']['velocity_y']},
    'gravity': {obj['physics']['gravity']},
    'bounce': {obj['physics']['bounce']}
}}
objects.append(rect_{obj['id']})
"""
        
        # Add game loop
        code += """
# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Update physics
    for obj in objects:
        # Apply gravity
        obj['velocity_y'] += obj['gravity']
        
        # Update position
        obj['x'] += obj['velocity_x']
        obj['y'] += obj['velocity_y']
        
        # Handle collisions with screen boundaries
        if 'radius' in obj:  # Circle
            if obj['y'] + obj['radius'] > HEIGHT:
                obj['y'] = HEIGHT - obj['radius']
                obj['velocity_y'] = -obj['velocity_y'] * obj['bounce']
            if obj['x'] + obj['radius'] > WIDTH or obj['x'] - obj['radius'] < 0:
                obj['velocity_x'] = -obj['velocity_x'] * obj['bounce']
        else:  # Rectangle
            if obj['y'] + obj['height'] > HEIGHT:
                obj['y'] = HEIGHT - obj['height']
                obj['velocity_y'] = -obj['velocity_y'] * obj['bounce']
            if obj['x'] + obj['width'] > WIDTH or obj['x'] < 0:
                obj['velocity_x'] = -obj['velocity_x'] * obj['bounce']
    
    # Clear screen
    screen.fill((255, 255, 255))
    
    # Draw objects
    for obj in objects:
        if 'radius' in obj:  # Circle
            pygame.draw.circle(screen, pygame.Color(obj['color']), 
                             (int(obj['x']), int(obj['y'])), obj['radius'])
        else:  # Rectangle
            pygame.draw.rect(screen, pygame.Color(obj['color']), 
                           pygame.Rect(obj['x'], obj['y'], obj['width'], obj['height']))
    
    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
"""
        
        self.code_editor.delete('1.0', tk.END)
        self.code_editor.insert('1.0', code)
    
    def start_game_preview(self):
        if not self.game_running:
            self.game_running = True
            self.game_thread = threading.Thread(target=self.run_game_preview)
            self.game_thread.start()
    
    def stop_game_preview(self):
        self.game_running = False
        if self.game_thread:
            self.game_thread.join()
    
    def run_game_preview(self):
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        clock = pygame.time.Clock()
        
        while self.game_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
            
            screen.fill((255, 255, 255))
            
            # Draw objects
            for obj in self.game_objects:
                if obj["type"] == "circle":
                    pygame.draw.circle(screen, pygame.Color(obj["color"]), 
                                     (int(obj["x"]), int(obj["y"])), obj["radius"])
                else:
                    pygame.draw.rect(screen, pygame.Color(obj["color"]), 
                                   pygame.Rect(obj["x"], obj["y"], obj["width"], obj["height"]))
            
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
    
    def new_project(self):
        self.game_objects = []
        self.hierarchy_tree.delete(*self.hierarchy_tree.get_children())
        self.generate_code()
    
    def save_project(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                filetypes=[("JSON files", "*.json")])
        if file_path:
            project_data = {
                "objects": self.game_objects,
                "code": self.code_editor.get('1.0', tk.END)
            }
            with open(file_path, 'w') as f:
                json.dump(project_data, f)
    
    def load_project(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as f:
                project_data = json.load(f)
                
            self.game_objects = project_data["objects"]
            self.hierarchy_tree.delete(*self.hierarchy_tree.get_children())
            
            for obj in self.game_objects:
                self.hierarchy_tree.insert('', 'end', obj["id"], text=obj["id"])
            
            self.code_editor.delete('1.0', tk.END)
            self.code_editor.insert('1.0', project_data["code"])
    
    def export_game(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".py",
                                                filetypes=[("Python files", "*.py")])
        if file_path:
            code = self.code_editor.get('1.0', tk.END)
            with open(file_path, 'w') as f:
                f.write(code)

def main():
    root = tk.Tk()
    app = PyGameIDE(root)
    root.mainloop()

if __name__ == "__main__":
    main()