import pygame
import math

pygame.init()


window_width = 500
cw = window_width/2
window_height = 500
ch = window_height/2
window = pygame.display.set_mode((window_width,window_height))

pygame.display.set_caption("Rhythm Game 5000")

x = 100
y = 100
vel = 5
white = (255,255,255)
black = (0,0,0)
dull_blue = (13,15,64)
bright_blue = (0, 9, 255)
mid_blue = (29, 32, 110)
selected_quad = None
tiles = []  # List to store active tiles
spawn_counter = 0  # Counter for tile spawning
score = 0

# Rhythm game variables
font = pygame.font.Font(None, 48)
feedback_text = None  # Current feedback message
feedback_timer = 0  # Frames to display feedback
score = 0  # Player score
hit_count = {'perfect': 0, 'too_fast': 0, 'too_slow': 0, 'missed': 0}

'''
Quadrant selection using angles

def get_direction_angle():
    """Calculate the direction angle (0-360 degrees) from WASD input.
    0° = up, 90° = right, 180° = down, 270° = left
    Returns None if no keys are pressed."""
    import math
    keys = pygame.key.get_pressed()
    w = keys[pygame.K_w]
    a = keys[pygame.K_a]
    s = keys[pygame.K_s]
    d = keys[pygame.K_d]
    
    # Create a direction vector
    dx = (d - a)  # +1 for d, -1 for a
    dy = (w - s)  # +1 for w, -1 for s
    
    # If no input, return None
    if dx == 0 and dy == 0:
        return None
    
    # Calculate angle in degrees (0-360)
    angle = math.degrees(math.atan2(dy, dx)) + 90
    if angle < 0:
        angle += 360
    
    return angle


def angle_to_quadrant(angle):
    """Convert a direction angle (0-360) to quadrant index (0-7).
    Each quadrant covers 45 degrees."""
    if angle is None:
        return None
    
    quadrant = int((angle + 22.5) / 45) % 8
    return quadrant


def get_selected_quadrant():
    """Get the selected quadrant based on current input."""
    angle = get_direction_angle()
    return angle_to_quadrant(angle)

'''

def get_selected_quadrant():
    """Detect which of 8 directions are pressed and return the quadrant index."""
    keys = pygame.key.get_pressed()
    w = keys[pygame.K_w]
    a = keys[pygame.K_a]
    s = keys[pygame.K_s]
    d = keys[pygame.K_d]
    
    # Map directions to quadrants (0-7)
    if w and not a and not s and not d:
        return 5  # W (up)
    elif w and d and not a and not s:
        return 6  # WD (up-right)
    elif d and not w and not a and not s:
        return 7  # D (right)
    elif s and d and not w and not a:
        return 0  # SD (down-right)
    elif s and not w and not d and not a:
        return 1  # S (down)
    elif s and a and not w and not d:
        return 2  # AS (down-left)
    elif a and not w and not s and not d:
        return 3  # A (left)
    elif w and a and not s and not d:
        return 4  # WA (up-left)
    else:
        return None


def WASD():
    global x,y
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        y -= vel
    if keys[pygame.K_s]:
        y += vel
    if keys[pygame.K_d]:
        x += vel
    if keys[pygame.K_a]:
        x -= vel


def octagon(surface, radius, color, width=5):
    """Draw an octagon outline at the specified position."""
    points = []
    for i in range(8):
        angle = (i * math.pi / 4) + math.pi/8
        x = cw + radius * math.cos(angle)
        y = ch + radius * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(surface, color, points, width)


def draw_octagon_ring(surface, inner_radius, outer_radius, selected_quad=None):
    """Fill the space between two octagons with different colored quadrilaterals."""
    # Generate vertices for inner and outer octagons
    outer_points = []
    inner_points = []
    for i in range(8):
        angle = (i * math.pi / 4) + math.pi/8
        outer_x = cw + outer_radius * math.cos(angle)
        outer_y = ch + outer_radius * math.sin(angle)
        outer_points.append((outer_x, outer_y))
        
        inner_x = cw + inner_radius * math.cos(angle)
        inner_y = ch + inner_radius * math.sin(angle)
        inner_points.append((inner_x, inner_y))
    
    # Draw quadrilaterals between corresponding vertices
    for i in range(8):
        next_i = (i + 1) % 8
        quad = [
            outer_points[i],
            outer_points[next_i],
            inner_points[next_i],
            inner_points[i]
        ]
        # Use bright_blue if this quadrant is selected, otherwise dull_blue
        color = bright_blue if i == selected_quad else dull_blue
        pygame.draw.polygon(surface, color, quad)


def spawn_tile(inner_radius):
    """Spawn a new tile at the inner octagon at the middle of a random side."""
    import random
    
    # Pick a random side (0-7)
    side = random.randint(0, 7)
    # Angle to the middle of this side
    angle = ((side+1) * math.pi / 4 )
    
    x = window_width/2 + inner_radius * math.cos(angle)
    y = window_height/2 + inner_radius * math.sin(angle)
    
    tile = {
        'x': x,
        'y': y,
        'angle': angle,
        'radius': inner_radius,
        'side': side,
        'captured': False,
        'anim_timer': 0   # NEW
    }
    return tile


def update_tiles(tiles, outer_radius, speed=2):
    """Update tile positions and remove tiles that reach the outer ring."""
    active_tiles = []
    
    for tile in tiles:
        tile['radius'] += speed
        
        # Recalculate position along the same angle (middle of side)
        tile['x'] = cw + tile['radius'] * math.cos(tile['angle'])
        tile['y'] = ch + tile['radius'] * math.sin(tile['angle'])
        
        # Keep tile if it hasn't reached the outer ring
        if tile['captured']:
            if tile['anim_timer'] > 0:
                active_tiles.append(tile)
        else:
            if tile['radius'] < outer_radius - 15:
                active_tiles.append(tile)
    
    return active_tiles


def draw_tiles(surface, tiles, min_line_length=50, max_line_length=100, inner_radius=50, outer_radius=200, line_width=3):
    """Draw all active tiles as lines parallel to the octagon sides.
    Line length increases as tiles get closer to the outer octagon."""
    for tile in tiles:
        
        # Scale line length based on distance from inner to outer radius
        progress = (tile['radius'] - inner_radius) / (outer_radius - inner_radius)
        progress = max(0, min(1, progress))  # Clamp between 0 and 1
        line_length = min_line_length + (max_line_length - min_line_length) * progress
        
        # Draw line parallel to the octagon sides (tangent direction)
        tangent_angle = tile['angle'] + math.pi / 2
        half_length = line_length / 2
        
        x1 = tile['x'] + half_length * math.cos(tangent_angle)
        y1 = tile['y'] + half_length * math.sin(tangent_angle)
        x2 = tile['x'] - half_length * math.cos(tangent_angle)
        y2 = tile['y'] - half_length * math.sin(tangent_angle)
        
        if tile['captured']:
            if tile['anim_timer'] > 0:
                tile['anim_timer'] -= 1

                # --- animation effects ---
                t = tile['anim_timer'] / 15

                # length "pop"
                anim_length = line_length * (1.2 + 0.5 * (1 - t))

                # fade out
                alpha = int(255 * t)

                # color flash (blue → white)
                color = (
                    int(bright_blue[0] * t + 255 * (1 - t)),
                    int(bright_blue[1] * t + 255 * (1 - t)),
                    int(bright_blue[2] * t + 255 * (1 - t))
                )

                # recompute endpoints with new length
                half_length = anim_length / 2

                x1 = tile['x'] + half_length * math.cos(tangent_angle)
                y1 = tile['y'] + half_length * math.sin(tangent_angle)
                x2 = tile['x'] - half_length * math.cos(tangent_angle)
                y2 = tile['y'] - half_length * math.sin(tangent_angle)

                # draw on temp surface for alpha
                temp = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
                pygame.draw.line(temp, (*color, alpha), (x1, y1), (x2, y2), line_width + 2)
                surface.blit(temp, (0, 0))

        else: 
            font = pygame.font.Font(None, 48)  # default font, size 48
            #text = font.render(str(tile['side']), True, white)
            pygame.draw.line(surface, white, (x1, y1), (x2, y2), line_width)
            #window.blit(text, (x1, y1))
        
        
        
display_timer = 0
display_text = ""
def display_msg():
    global display_text, display_timer
    print("timer:",display_timer)
    
    if display_timer<10:
        font = pygame.font.Font(None, 48)  # default font, size 48
        text_surface = font.render(display_text, True, white)
        window.blit(text_surface, (cw - 55, 30))
        display_timer+=1
    elif display_timer>=10:
        display_timer = -1
        display_text = ""

def buttonA():
    global display_text, display_timer, tiles, score, lives
    keys = pygame.key.get_pressed()
    
    print("pressed")
    if selected_quad is not None:
        istile = False
        for tile in tiles:
            if (tile['side'])==selected_quad and tile['captured']==False:
                istile = True
                dist = (tile['radius']-50)/130
                if (dist>0.95):
                    score += 10
                    display_text = "Perfect!"
                    display_timer = 0
                elif (dist>0.8):
                    score += 5
                    display_text = "Ok"
                    display_timer = 0
                elif (dist>0.5):
                    score += 1
                    display_text = "Slow"
                    display_timer = 0
                else:
                    display_text = "Too Slow"
                    display_timer = 0
                    lives -= 1
                    if lives >= 0:
                        heart_hit_timers[lives] = 20
                    
                print("side", tile['side'], "quad side", selected_quad)
                tile['captured']=True
                tile['anim_timer'] = 15
                break
        if not istile:
            display_text = "Missed"
            display_timer = 0
            lives -= 1
            if lives >= 0:
                heart_hit_timers[lives] = 20
    else:
        display_text = "Missed"
        display_timer = 0
        lives -= 1
        if lives >= 0:
            heart_hit_timers[lives] = 20
        

running = True
def draw_hearts():
    for i in range(3):
        x = 5 + 30 * i
        y = 5

        if heart_hit_timers[i] > 0:
            heart_hit_timers[i] -= 1

            # animation
            scale = 1.5 - 0.02 * (20 - heart_hit_timers[i])
            alpha = int(255 * (heart_hit_timers[i] / 20))

            img = heart_filled.copy()

            new_size = int(27 * scale)
            img = pygame.transform.smoothscale(img, (new_size, new_size))
            img.set_alpha(alpha)

            draw_x = x - (new_size - 27) // 2
            draw_y = y - (new_size - 27) // 2

            window.blit(img, (draw_x, draw_y))

        else:
            if i < lives:
                window.blit(heart_filled, (x, y))
            else:
                window.blit(heart_outline, (x, y))
                
heart_filled = pygame.image.load("heart_filled.png").convert_alpha()
heart_filled = pygame.transform.smoothscale(heart_filled, (27, 27))
heart_outline = pygame.image.load("heart_outline.png").convert_alpha()
heart_outline = pygame.transform.smoothscale(heart_outline, (30, 30))
lives = 3
timeeeee = 80
heart_hit_timers = [0, 0, 0]  # one per heart
while running:
    window.fill(black)
    
    font = pygame.font.Font(None, 28)  # default font, size 48
    text_surface = font.render("Score: "+ str(score), True, white)
    window.blit(text_surface, (400, 10))
    
    draw_hearts()
    ############################################################################
    
    selected_quad = get_selected_quadrant()
    draw_octagon_ring(window, 50, 200, selected_quad)
    octagon(window, 50, white)
    octagon(window, 200, white, 2)
    
    # Spawn tiles every 10 frames
    spawn_counter += 1
    if spawn_counter >= timeeeee:
        tiles.append(spawn_tile(50))
        spawn_counter = 0
        timeeeee *= 0.95
        timeeeee = max(15, timeeeee)
    
    # Update tiles
    tiles = update_tiles(tiles, 200, speed=2)
    
    # Draw tiles
    draw_tiles(window, tiles, min_line_length=10, max_line_length=50, inner_radius=50, outer_radius=200)
    
    if display_text != "":
        display_msg()
        
    #print(len(tiles))
    print(score)
    
    
    ############################################################################
    
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_SPACE:
                buttonA()
        if event.type == pygame.QUIT:
            running = False
                
    
    pygame.display.update()
                

pygame.quit()
