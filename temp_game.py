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

circle = {
    'type': 'circle',
    'x': 400,
    'y': 300,
    'radius': 20,
    'color': '#FF0000',
    'physics': {
        'velocity_x': 10,
        'velocity_y': 2,
        'gravity': 0,
        'bounce': 1.8
    }
}
objects.append(circle)

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

