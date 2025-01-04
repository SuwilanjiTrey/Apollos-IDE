import tkinter as tk
from tkinter import ttk, scrolledtext
import pygame
import json
import os
import re
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
        self.updating_code = False  # Flag to prevent recursive updates
        
        
        
        self.setup_ui()
        self.setup_pygame_preview()

        # Bind code editor changes to property updates
        self.code_editor.bind('<<Modified>>', self.on_code_changed)
        
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
    
    def create_property_field(self, prop, value, row, indent=False, parent_prop=None):
        padx = 20 if indent else 0
        ttk.Label(self.properties_frame, text=prop.title()).grid(row=row, column=0, padx=padx)
        
        if isinstance(value, bool):
            var = tk.BooleanVar(value=value)
            field = ttk.Checkbutton(self.properties_frame, variable=var, 
                                command=lambda: self.refresh_property(prop, var.get(), parent_prop))
        else:
            var = tk.StringVar(value=str(value))
            field = ttk.Entry(self.properties_frame, textvariable=var)
            # Bind both Enter key and focus-out events
            field.bind('<Return>', lambda e: self.refresh_property(prop, var.get(), parent_prop))
            field.bind('<FocusOut>', lambda e: self.refresh_property(prop, var.get(), parent_prop))
            
            # Optional: For auto-refresh while typing
            var.trace('w', lambda *args: self.refresh_property(prop, var.get(), parent_prop))
            
        field.grid(row=row, column=1, padx=5)
        return field, var

    def on_code_changed(self, event):
        if not self.updating_code:  # Prevent recursive updates
            try:
                # Get the code from editor
                code = self.code_editor.get('1.0', tk.END)
                
                # Parse objects from code
                self.parse_objects_from_code(code)
                
                # Update properties panel if needed
                if self.selected_object:
                    obj_id = self.selected_object['id']
                    updated_obj = next((obj for obj in self.game_objects if obj['id'] == obj_id), None)
                    if updated_obj:
                        self.selected_object = updated_obj
                        self.update_properties_panel(updated_obj)
            except Exception as e:
                print(f"Error parsing code: {e}")
            
            # Reset modified flag
            self.code_editor.edit_modified(False)
    
    def parse_objects_from_code(self, code):
        """Parse game objects from the code text"""
        try:
            # Updated patterns to capture nested dictionaries
            circle_pattern = r"circle = ({[^}]*'physics':\s*{[^}]*}[^}]*})"
            rect_pattern = r"rectangle = ({[^}]*'physics':\s*{[^}]*}[^}]*})"
            
            # Parse circles
            circles = re.finditer(circle_pattern, code)
            new_objects = []
            
            for i, match in enumerate(circles):
                obj_str = match.group(1)
                try:
                    # Clean up the string for eval
                    obj_str = obj_str.replace("'type': 'circle'", "'type':'circle'")
                    obj_str = obj_str.replace("'physics':", "'physics':")
                    
                    # Create safe globals for eval
                    safe_globals = {
                        '__builtins__': {
                            'dict': dict,
                            'float': float,
                            'int': int,
                            'str': str,
                            'True': True,
                            'False': False
                        }
                    }
                    
                    # Evaluate the string to create object dictionary
                    obj_dict = eval(f"dict({obj_str})", safe_globals, {})
                    obj_dict['type'] = 'circle'
                    obj_dict['id'] = f'circle_{i}'
                    new_objects.append(obj_dict)
                except Exception as e:
                    print(f"Error parsing circle object: {e}")
            
            # Parse rectangles
            rects = re.finditer(rect_pattern, code)
            for i, match in enumerate(rects):
                obj_str = match.group(1)
                try:
                    # Clean up the string for eval
                    obj_str = obj_str.replace("'type': 'rectangle'", "'type':'rectangle'")
                    obj_str = obj_str.replace("'physics':", "'physics':")
                    
                    # Evaluate the string to create object dictionary
                    obj_dict = eval(f"dict({obj_str})", safe_globals, {})
                    obj_dict['type'] = 'rectangle'
                    obj_dict['id'] = f'rectangle_{i}'
                    new_objects.append(obj_dict)
                except Exception as e:
                    print(f"Error parsing rectangle object: {e}")
            
            # Update game objects if we successfully parsed any
            if new_objects:
                self.game_objects = new_objects
                self.update_hierarchy_tree()
                
        except Exception as e:
            print(f"Error parsing objects from code: {e}")
    
    def parse_object_dict(self, obj_str):
        """Parse object properties from string"""
        # Convert string to actual dictionary using safer eval
        # Remove quotes around property names
        obj_str = re.sub(r"'(\w+)':", r"\1:", obj_str)
        
        # Create a restricted globals dictionary
        safe_globals = {
            '__builtins__': {
                'True': True,
                'False': False,
                'dict': dict,
                'float': float,
                'int': int,
                'str': str
            }
        }
        
        try:
            obj_dict = eval(f"dict({obj_str})", safe_globals)
            return obj_dict
        except Exception as e:
            print(f"Error parsing object properties: {e}")
            return {}
    
    def update_hierarchy_tree(self):
        """Update the hierarchy tree to reflect current objects"""
        self.hierarchy_tree.delete(*self.hierarchy_tree.get_children())
        for obj in self.game_objects:
            self.hierarchy_tree.insert('', 'end', obj['id'], text=obj['id'])
    
    def refresh_property(self, prop, value, parent_prop=None):
        if self.selected_object:
            try:
                if parent_prop:  # Handle nested properties
                    current_value = self.selected_object[parent_prop][prop]
                    # Convert value to the appropriate type
                    if isinstance(current_value, int):
                        value = int(float(value))
                    elif isinstance(current_value, float):
                        value = float(value)
                    
                    self.selected_object[parent_prop][prop] = value
                else:  # Handle top-level properties
                    current_value = self.selected_object[prop]
                    # Convert value to the appropriate type
                    if isinstance(current_value, int):
                        value = int(float(value))
                    elif isinstance(current_value, float):
                        value = float(value)
                    
                    self.selected_object[prop] = value
                
                # Find and update the object in game_objects list
                for obj in self.game_objects:
                    if obj['id'] == self.selected_object['id']:
                        if parent_prop:
                            obj[parent_prop][prop] = value
                        else:
                            obj[prop] = value
                        break
                
                # Set flag to prevent recursive updates
                self.updating_code = True
                # Update the code
                self.generate_code()
                # Reset flag
                self.updating_code = False
                
            except (ValueError, KeyError) as e:
                print(f"Error updating property: {e}")
                self.update_properties_panel(self.selected_object)

    def refresh_game_preview(self):
        """Refresh the game preview to show updated properties"""
        if self.game_running:
            # If the game is running, restart it to apply changes
            self.stop_game_preview()
            self.start_game_preview()

    def update_properties_panel(self, obj):
        # Clear existing properties
        for widget in self.properties_frame.winfo_children():
            widget.destroy()
        
        # Create property fields
        row = 0
        property_fields = {}  # Store references to fields and variables
        
        for prop, value in obj.items():
            if prop != "id" and prop != "type":
                if isinstance(value, dict):  # Handle nested properties (physics)
                    ttk.Label(self.properties_frame, text=prop.title()).grid(row=row, column=0, pady=5)
                    row += 1
                    for sub_prop, sub_value in value.items():
                        field, var = self.create_property_field(sub_prop, sub_value, row, indent=True, parent_prop=prop)
                        property_fields[f"{prop}.{sub_prop}"] = (field, var)
                        row += 1
                else:
                    field, var = self.create_property_field(prop, value, row)
                    property_fields[prop] = (field, var)
                    row += 1
        
        return property_fields

    def update_object_property(self, prop, value, parent_prop=None):
        if self.selected_object:
            try:
                if parent_prop:  # Handle nested properties
                    # Convert value to appropriate type
                    if isinstance(self.selected_object[parent_prop][prop], int):
                        value = int(value)
                    elif isinstance(self.selected_object[parent_prop][prop], float):
                        value = float(value)
                    
                    self.selected_object[parent_prop][prop] = value
                else:  # Handle top-level properties
                    # Convert value to appropriate type
                    if isinstance(self.selected_object[prop], int):
                        value = int(value)
                    elif isinstance(self.selected_object[prop], float):
                        value = float(value)
                    
                    self.selected_object[prop] = value
                
                self.generate_code()
            except (ValueError, KeyError) as e:
                print(f"Error updating property: {e}")

    def on_select_object(self, event):
        selection = self.hierarchy_tree.selection()
        if selection:
            obj_id = selection[0]
            obj = next((obj for obj in self.game_objects if obj["id"] == obj_id), None)
            if obj:
                self.selected_object = obj
                self.property_fields = self.update_properties_panel(obj)
    
    
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
        
         # Add object definitions with consistent formatting
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
        
        # Add game loop with physics
        code += """
# Game loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()
    
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
"""
        
         # Update the code editor with the new code
            # Update the code editor
        self.updating_code = True
        self.code_editor.delete('1.0', tk.END)
        self.code_editor.insert('1.0', code)
        self.updating_code = False
    
    def start_game_preview(self):
        if not self.game_running:
            self.game_running = True
            # Get the current code from the editor
            code = self.code_editor.get('1.0', tk.END)
            # Create a temporary file to execute
            with open('temp_game.py', 'w') as f:
                f.write(code)
            # Run the game in a separate thread
            self.game_thread = threading.Thread(target=self.run_game_from_code)
            self.game_thread.start()

    def run_game_from_code(self):
        try:
            # Execute the generated code
            exec(self.code_editor.get('1.0', tk.END))
        except Exception as e:
            print(f"Error running game: {e}")
        finally:
            self.game_running = False
    
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
            
            # Update and draw objects
            with self.property_update_lock:  # Use lock when accessing objects
                for obj in self.game_objects:
                    # Apply physics
                    obj["physics"]["velocity_y"] += obj["physics"]["gravity"]
                    obj["y"] += obj["physics"]["velocity_y"]
                    obj["x"] += obj["physics"]["velocity_x"]
                    
                    # Handle collisions
                    if obj["type"] == "circle":
                        if obj["y"] + obj["radius"] > 600:  # Screen height
                            obj["y"] = 600 - obj["radius"]
                            obj["physics"]["velocity_y"] = -obj["physics"]["velocity_y"] * obj["physics"]["bounce"]
                        if obj["x"] + obj["radius"] > 800 or obj["x"] - obj["radius"] < 0:  # Screen width
                            obj["physics"]["velocity_x"] = -obj["physics"]["velocity_x"] * obj["physics"]["bounce"]
                    else:  # rectangle
                        if obj["y"] + obj["height"] > 600:
                            obj["y"] = 600 - obj["height"]
                            obj["physics"]["velocity_y"] = -obj["physics"]["velocity_y"] * obj["physics"]["bounce"]
                        if obj["x"] + obj["width"] > 800 or obj["x"] < 0:
                            obj["physics"]["velocity_x"] = -obj["physics"]["velocity_x"] * obj["physics"]["bounce"]
                    
                    # Draw object
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