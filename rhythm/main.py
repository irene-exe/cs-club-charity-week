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
mid_blue = (12, 5, 153)
red = (255, 0, 0)
green = (0, 255, 0)
orange = (255, 165, 0)
yellow = (255, 255, 0)
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

# Game state management
game_state = "menu"  # "menu", "playing", "end_game"
menu_selected = 0  # 0 = first option, 1 = second option
menu_animation_timer = 0  # For fade-in animation


# Button class with animation
class Button:
    def __init__(self, x, y, width, height, text, font_size=40):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        self.is_hovered = False
        self.hover_progress = 0  # 0 to 1
        self.click_animation = 0  # For click feedback
        
    def update(self, is_hovered):
        self.is_hovered = is_hovered
        # Smoothly animate hover state
        if is_hovered:
            self.hover_progress = min(1, self.hover_progress + 0.1)
        else:
            self.hover_progress = max(0, self.hover_progress - 0.1)
        
        # Animate click feedback
        if self.click_animation > 0:
            self.click_animation -= 0.1
    
    def draw(self, surface):
        # Interpolate scale based on hover state
        scale = 1 + 0.1 * self.hover_progress + 0.05 * max(0, 0.5 - self.click_animation)
        
        # Interpolate color (dull_blue to bright_blue)
        color = (
            int(dull_blue[0] + (bright_blue[0] - dull_blue[0]) * self.hover_progress),
            int(dull_blue[1] + (bright_blue[1] - dull_blue[1]) * self.hover_progress),
            int(dull_blue[2] + (bright_blue[2] - dull_blue[2]) * self.hover_progress)
        )
        
        # Draw button with scaled size
        scaled_width = int(self.width * scale)
        scaled_height = int(self.height * scale)
        offset_x = (scaled_width - self.width) // 2
        offset_y = (scaled_height - self.height) // 2
        
        rect = pygame.Rect(self.x - offset_x, self.y - offset_y, scaled_width, scaled_height)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, bright_blue, rect, 2)
        
        # Draw text with animation
        # Scale font size and change color based on hover state
        text_scale = 1 + 0.15 * self.hover_progress
        text_font_size = int(40 * text_scale)
        text_font = pygame.font.Font(None, text_font_size)
        
        
        text_surface = text_font.render(self.text, True, white)
        text_rect = text_surface.get_rect(center=(self.x+75, self.y+25))
        surface.blit(text_surface, text_rect)
    
    def is_clicked(self, mouse_pos):
        rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)
        return rect.collidepoint(mouse_pos)
    
    def trigger_click(self):
        self.click_animation = 0.5


# Menu buttons
main_menu_buttons = [
    Button(cw-70, ch - 40, 150, 50, "PLAY"),
    Button(cw-70, ch + 40, 150, 50, "QUIT")
]

end_game_buttons = [
    Button(cw-70, ch - 40, 150, 50, "RESTART"),
    Button(cw-70, ch + 40, 150, 50, "RECORD")
]

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


def draw_octagon_ring(surface, inner_radius, outer_radius, selected_quad=None, glow_timers=None):
    """Fill the space between two octagons with different colored quadrilaterals."""
    if glow_timers is None:
        glow_timers = [0] * 8
    
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
        color = mid_blue if i == selected_quad else dull_blue
        pygame.draw.polygon(surface, color, quad)
        
        # Draw pop animation if side has active timer
        if glow_timers[i] > 0:
            progress = 1 - (glow_timers[i] / 30)  # 0 at start, 1 at end
            
            # Calculate center of quadrilateral
            center_x = (quad[0][0] + quad[1][0] + quad[2][0] + quad[3][0]) / 4
            center_y = (quad[0][1] + quad[1][1] + quad[2][1] + quad[3][1]) / 4
            
            # Scale from 1.0 to 1.5 (pop effect)
            scale = 1.0 + 0.2 * progress
            
            # Create scaled quad from center
            scaled_quad = []
            for point in quad:
                scaled_x = center_x + (point[0] - center_x) * scale
                scaled_y = center_y + (point[1] - center_y) * scale
                scaled_quad.append((scaled_x, scaled_y))
            
            # Fade out (alpha decreases from 255 to 0)
            alpha = int(255 * (1 - progress) * 0.5)  # 50% opacity
            
            # Draw scaled quad with alpha
            temp_surface = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
            pygame.draw.polygon(temp_surface, (*bright_blue, alpha), scaled_quad)
            surface.blit(temp_surface, (0, 0))


def spawn_tile(inner_radius):
    """Spawn a new tile at the inner octagon at the middle of a random side."""
    import random
    
    # Pick a random side (0-7)
    side = random.randint(0, 7)
    # Angle to the middle of this side
    angle = ((side+1) * math.pi / 4 )
    
    x = window_width/2 + inner_radius * math.cos(angle)
    y = window_height/2 + inner_radius * math.sin(angle)
    
    # Randomly assign tile color and required key
    is_blue = random.choice([True, False])
    tile_color = bright_blue if is_blue else yellow
    required_key = pygame.K_j if is_blue else pygame.K_k
    
    tile = {
        'x': x,
        'y': y,
        'angle': angle,
        'radius': inner_radius,
        'side': side,
        'captured': False,
        'anim_timer': 0,
        'color': tile_color,
        'required_key': required_key
    }
    return tile


def update_tiles(tiles, outer_radius, speed=2):
    global display_text, display_timer, lives, heart_hit_timers
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
            else:
                display_text = "Missed"
                display_timer = 0
                lives -= 1
                if lives >= 0:
                    heart_hit_timers[lives] = 20
    
    return active_tiles


def draw_tiles(surface, tiles, min_line_length=50, max_line_length=100, inner_radius=50, outer_radius=200, line_width=5):
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
            # Draw line in tile's color
            tile_color = tile.get('color', white)
            pygame.draw.line(surface, tile_color, (x1, y1), (x2, y2), line_width)
        
        
        
display_timer = 0
display_text = ""
def get_feedback_color(text):
    """Determine feedback color based on text."""
    if "Perfect" in text:
        return green
    elif "Good" in text:
        return bright_blue
    elif "Ok" in text:
        return orange
    else:  # "Too Slow" or "Missed"
        return red

def display_msg():
    global display_text, display_timer
    print("timer:",display_timer)
    
    if display_timer<10:
        font = pygame.font.Font(None, 48)  # default font, size 48
        
        # Flash effect: scale and opacity
        progress = display_timer / 10  # 0 to 1
        
        # Pop scale: start at 1.1, shrink to 1.0
        scale = 1.1 - 0.1 * progress
        
        # Get feedback-specific color
        feedback_color = get_feedback_color(display_text)
        
        # Color flash: white → feedback color
        color = (
            int(255 - (255 - feedback_color[0]) * progress),
            int(255 - (255 - feedback_color[1]) * progress),
            int(255 - (255 - feedback_color[2]) * progress)
        )
        
        # Render text with dynamic scale
        scaled_font_size = int(48 * scale)
        scaled_font = pygame.font.Font(None, scaled_font_size)
        text_surface = scaled_font.render(display_text, True, color)
        text_rect = text_surface.get_rect(center=(cw, 30))
        window.blit(text_surface, text_rect)
        display_timer+=1
    elif display_timer>=10:
        display_timer = -1
        display_text = ""

def buttonA(key_pressed):
    global display_text, display_timer, tiles, score, lives, game_state, menu_selected, menu_animation_timer, glow_timers
    if selected_quad is not None:
        istile = False
        for tile in tiles:
            if (tile['side'])==selected_quad and tile['captured']==False:
                # Check if the key pressed matches the required key for this tile
                if key_pressed != tile['required_key']:
                    continue  # Wrong key, skip this tile
                
                istile = True
                dist = (tile['radius']-50)/130
                if (dist>0.9):
                    score += 10
                    display_text = "Perfect!"
                    display_timer = 0
                elif (dist>0.7):
                    score += 5
                    display_text = "Good"
                    display_timer = 0
                elif (dist>0.4):
                    score += 1
                    display_text = "Ok"
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
                glow_timers[tile['side']] = 30  # Start glow effect
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
        

def draw_main_menu():
    """Draw the main menu with animated title and buttons."""
    global menu_animation_timer, game_state, menu_selected
    
    menu_animation_timer += 0.05
    alpha = int(255 * min(1, menu_animation_timer))
    
    # Draw title with fade-in animation
    title_font = pygame.font.Font(None, 80)
    title_surface = title_font.render("RHYTHM", True, bright_blue)
    title_surface.set_alpha(alpha)
    title_rect = title_surface.get_rect(center=(cw, 100))
    window.blit(title_surface, title_rect)
    
    subtitle_font = pygame.font.Font(None, 40)
    subtitle_surface = subtitle_font.render("5000", True, white)
    subtitle_surface.set_alpha(alpha)
    subtitle_rect = subtitle_surface.get_rect(center=(cw, 140))
    window.blit(subtitle_surface, subtitle_rect)
    
    # Update and draw buttons
    for i, button in enumerate(main_menu_buttons):
        button.update(i == menu_selected)
        button.draw(window)


def draw_end_game_menu():
    """Draw the end game menu with score and buttons."""
    global menu_animation_timer, game_state, menu_selected, score
    
    menu_animation_timer += 0.05
    alpha = int(255 * min(1, menu_animation_timer))
    
    # Draw "GAME OVER" text with animation
    game_over_font = pygame.font.Font(None, 80)
    game_over_surface = game_over_font.render("GAME OVER", True, bright_blue)
    game_over_surface.set_alpha(alpha)
    game_over_rect = game_over_surface.get_rect(center=(cw, 100))
    window.blit(game_over_surface, game_over_rect)
    
    # Draw score with pop animation
    score_scale = 1 + 0.3 * max(0, 1 - menu_animation_timer / 0.3)
    score_font = pygame.font.Font(None, int(50 * score_scale))
    score_surface = score_font.render(f"Score: {score}", True, white)
    score_surface.set_alpha(alpha)
    score_rect = score_surface.get_rect(center=(cw, 160))
    window.blit(score_surface, score_rect)
    
    # Update and draw buttons
    for i, button in enumerate(end_game_buttons):
        button.update(i == menu_selected)
        button.draw(window)


def reset_game():
    """Reset game variables for a new game."""
    global tiles, score, lives, spawn_counter, timeeeee, heart_hit_timers, display_timer, display_text
    global menu_animation_timer, menu_selected, glow_timers
    
    
    tiles = []
    score = 0
    lives = 3
    spawn_counter = 0
    timeeeee = 80
    heart_hit_timers = [0, 0, 0]
    display_timer = 0
    display_text = ""
    menu_animation_timer = 0
    menu_selected = 0
    glow_timers = [0, 0, 0, 0, 0, 0, 0, 0]


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

clock = pygame.time.Clock()
FPS = 60

def main():
    global score, game_state, tiles, feedback_text, feedback_timer, hit_count, selected_quad, spawn_counter, menu_selected, menu_animation_timer
    global main_menu_buttons, end_game_buttons, display_timer, display_text, running, heart_filled, heart_outline, lives, timeeeee, heart_hit_timers, clock, FPS
    while running:
        clock.tick(FPS)
        window.fill(black)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if game_state == "menu":
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        menu_selected = (menu_selected - 1) % len(main_menu_buttons)
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        menu_selected = (menu_selected + 1) % len(main_menu_buttons)
                    elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        if menu_selected == 0:  # PLAY
                            game_state = "playing"
                            reset_game()
                        elif menu_selected == 1:  # QUIT
                            running = False
                
                elif game_state == "end_game":
                    if event.key == pygame.K_w or event.key == pygame.K_UP:
                        menu_selected = (menu_selected - 1) % len(end_game_buttons)
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        menu_selected = (menu_selected + 1) % len(end_game_buttons)
                    elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        if menu_selected == 0:  # RESTART
                            game_state = "playing"
                            reset_game()
                        elif menu_selected == 1:
                            running = False
                            return score
                
                elif game_state == "playing":
                    if event.key == pygame.K_j:
                        buttonA(pygame.K_j)
                    elif event.key == pygame.K_k:
                        buttonA(pygame.K_k)
        
        # Draw based on game state
        if game_state == "menu":
            draw_main_menu()
        
        elif game_state == "playing":
            font = pygame.font.Font(None, 28)
            text_surface = font.render("Score: " + str(score), True, white)
            text_rect = text_surface.get_rect(center=(430, 20))
            window.blit(text_surface, text_rect)
            
            draw_hearts()
            
            selected_quad = get_selected_quadrant()
            
            # Update glow timers
            for i in range(8):
                if glow_timers[i] > 0:
                    glow_timers[i] -= 1
            
            draw_octagon_ring(window, 50, 200, selected_quad, glow_timers)
            octagon(window, 50, white)
            octagon(window, 200, white, 2)
            
            # Spawn tiles every 10 frames
            spawn_counter += 1
            if spawn_counter >= timeeeee:
                tiles.append(spawn_tile(50))
                spawn_counter = 0
                timeeeee *= 0.97
                timeeeee = max(18, timeeeee)
            
            # Update tiles
            tiles = update_tiles(tiles, 200, speed=2)
            
            # Draw tiles
            draw_tiles(window, tiles, min_line_length=10, max_line_length=50, inner_radius=50, outer_radius=200)
            
            if display_text != "":
                display_msg()
            
            # Check if game over
            if lives < 0:
                game_state = "end_game"
                menu_selected = 0
                menu_animation_timer = 0
        
        elif game_state == "end_game":
            draw_end_game_menu()
        
        pygame.display.update()

    pygame.quit()
