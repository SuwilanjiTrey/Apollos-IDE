import pygame
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

circle_circle_0 = {
    'x': 400,
    'y': 300,
    'radius': 20,
    'color': '#FF0000',
    'velocity_x': 0,
    'velocity_y': 0,
    'gravity': 0,
    'bounce': 0.8
}
objects.append(circle_circle_0)

rect_rectangle_1 = {
    'x': 400,
    'y': 300,
    'width': 40,
    'height': 40,
    'color': '#00FF00',
    'velocity_x': 0,
    'velocity_y': 0,
    'gravity': 0,
    'bounce': 0.8
}
objects.append(rect_rectangle_1)

circle_circle_2 = {
    'x': 400,
    'y': 300,
    'radius': 20,
    'color': '#FF0000',
    'velocity_x': 0,
    'velocity_y': 0,
    'gravity': 0,
    'bounce': 0.8
}
objects.append(circle_circle_2)

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

