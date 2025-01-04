import cv2
import numpy as np
import os
from PIL import Image

class SpriteSheetExtractor:
    def __init__(self):
        self.min_sprite_size = 16  # Minimum sprite size to detect
        self.output_folder = "extracted_sprites"
        
    def extract_sprites(self, sprite_sheet_path):
        # Create output folder if it doesn't exist
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            
        # Read the sprite sheet
        sprite_sheet = cv2.imread(sprite_sheet_path, cv2.IMREAD_UNCHANGED)
        
        # If image has no alpha channel, convert white/checkered background to transparent
        if sprite_sheet.shape[2] == 3:
            sprite_sheet = self._remove_background(sprite_sheet)
        
        # Convert to grayscale for contour detection
        alpha_channel = sprite_sheet[:, :, 3]
        
        # Find contours
        contours, _ = cv2.findContours(alpha_channel, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Process each contour
        sprites = []
        for i, contour in enumerate(contours):
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter out too small sprites
            if w < self.min_sprite_size or h < self.min_sprite_size:
                continue
                
            # Extract sprite
            sprite = sprite_sheet[y:y+h, x:x+w]
            
            # Save sprite
            sprite_filename = f"sprite_{i}.png"
            sprite_path = os.path.join(self.output_folder, sprite_filename)
            
            # Convert from BGR to RGB
            sprite_rgb = cv2.cvtColor(sprite, cv2.COLOR_BGRA2RGBA)
            
            # Save using PIL to preserve transparency
            Image.fromarray(sprite_rgb).save(sprite_path)
            
            sprites.append({
                'path': sprite_path,
                'width': w,
                'height': h,
                'x': x,
                'y': y
            })
            
        return sprites
    
    def _remove_background(self, image):
        # Convert to RGBA
        rgba = cv2.cvtColor(image, cv2.COLOR_BGR2RGBA)
        
        # Create mask for white background
        white_mask = np.all(image >= [250, 250, 250], axis=2)
        
        # Create mask for checkered pattern
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        pattern_mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]
        
        # Combine masks
        background_mask = white_mask | (pattern_mask == 255)
        
        # Set alpha channel
        rgba[:, :, 3] = ~background_mask * 255
        
        return rgba