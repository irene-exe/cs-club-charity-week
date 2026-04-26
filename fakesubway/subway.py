import cv2
import mediapipe as mp
import pygame
import random
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

base_options = python.BaseOptions(
    model_asset_path='pose_landmarker_full.task'
)

options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    output_segmentation_masks=False
)

detector = vision.PoseLandmarker.create_from_options(options)

window_width = 1000
window_height = 700
running = True

pygame.init()
window = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("FakeSubway")

# Load enemy images
enemy_images_data = {
    "angryturt": {"file": "assets/angryturt.png", "width": 200, "height": 200, "y_displacement": 0},
    "crustybird": {"file": "assets/crustybird.png", "width": 200, "height": 200, "y_displacement": -200},
    "tree": {"file": "assets/tree.png", "width": 800, "height": 800, "y_displacement": 0}
}

# Load the actual images
enemy_images = {
    name: pygame.image.load(data["file"])
    for name, data in enemy_images_data.items()
}

white = (255, 255, 255)
black = (0, 0, 0)

baseline_torso = None
torso_center = None
prev_torso = None

# Player position
player_x = window_width // 2
player_y = window_height - 100
player_radius = 50
player_target_lane = 1  # 0=left, 1=middle, 2=right
player_target_y = window_height - 100

max_jump = 0.3
alpha = 0.5

def get_torso_center(landmarks):
    if not landmarks or len(landmarks) < 25:
        return None

    ls = landmarks[11]
    rs = landmarks[12]

    return ((ls.x + rs.x) / 2, (ls.y + rs.y) / 2)

class Enemy:
    def __init__(self, lane, image_name):
        """
        Create an enemy in a specific lane (0, 1, or 2)
        Starts at the vanishing point and moves outward down the lane
        """
        self.lane = lane
        self.t = 0.0  # 0 = vanishing point (horizon), 1 = bottom of screen
        self.image_name = image_name
        self.image = enemy_images[image_name]
        self.data = enemy_images_data[image_name]
        self.width = self.data["width"]
        self.height = self.data["height"]
        self.y_displacement = self.data["y_displacement"]
        self.speed = 0.008  # how fast it moves down the lane
    
    def update(self):
        """Move enemy further down the lane"""
        self.t += self.speed
    
    def draw(self, window):
        """Draw enemy with perspective matching the lane structure"""
        if self.t < 0 or self.t > 1.2:
            return False  # Enemy is off screen
        
        margin = 50
        horizon_y = window_height * 0.35
        vp = (window_width // 2, int(horizon_y))
        bottom_y = window_height
        left_outer = margin
        right_outer = window_width - margin
        lane_width = (right_outer - left_outer) / 3
        
        # Lane boundaries at the bottom
        p0 = left_outer
        p1 = left_outer + lane_width
        p2 = left_outer + 2 * lane_width
        p3 = right_outer
        
        # Select the two boundaries for this lane
        lane_boundaries = [(p0, p1), (p1, p2), (p2, p3)]
        left_bound, right_bound = lane_boundaries[self.lane]
        
        # Interpolation function
        def interp(x):
            return int(x + (vp[0] - x) * (1 - self.t))
        
        # Calculate y position
        y = int(horizon_y + (bottom_y - horizon_y) * self.t)
        
        # Calculate x position - center of the lane
        left_x = interp(left_bound)
        right_x = interp(right_bound)
        x = (left_x + right_x) // 2
        
        # Scale size based on how far down the lane (closer = bigger)
        scale = 0.3 * self.t * 1.5
        width = int(self.width * scale)
        height = int(self.height * scale)
        
        # Apply y displacement
        y += self.y_displacement
        
        # Scale and draw the image
        scaled_image = pygame.transform.scale(self.image, (width, height))
        rect = scaled_image.get_rect(center=(x, y))
        window.blit(scaled_image, rect)
        
        return True

def calibrate(event):
    global baseline_torso, torso_center

    if event.type == pygame.MOUSEBUTTONDOWN:
        if calibrate_button.collidepoint(event.pos):
            if torso_center:
                baseline_torso = torso_center
                print("Calibrated:", baseline_torso)

yaction = ""
xaction = ""
font = pygame.font.Font(None, 28)

lives = 3
heart_hit_timers = [0, 0, 0]
global_xaction = ""
global_yaction = ""

'''
LOSE HEART
lives -= 1
if lives >= 0:
    heart_hit_timers[lives] = 20
'''

def draw_hearts():
    for i in range(3):
        x = 5 + 30 * i
        y = 5
        heart_size = 20

        if heart_hit_timers[i] > 0:
            heart_hit_timers[i] -= 1

            # animation - pulse effect
            scale = 1.5 - 0.02 * (20 - heart_hit_timers[i])
            heart_size = int(20 * scale)
            alpha_val = int(255 * (heart_hit_timers[i] / 20))
            
            # Draw pulsing red rectangle
            pygame.draw.rect(window, (255, 0, 0), (x - heart_size // 2, y - heart_size // 2, heart_size, heart_size))

        else:
            if i < lives:
                # Draw filled red heart
                pygame.draw.rect(window, (255, 0, 0), (x - heart_size // 2, y - heart_size // 2, heart_size, heart_size))
            else:
                # Draw empty heart outline
                pygame.draw.rect(window, (100, 100, 100), (x - heart_size // 2, y - heart_size // 2, heart_size, heart_size), 2)

def display():
    global torso_center, baseline_torso, global_yaction, global_xaction

    if baseline_torso is None or torso_center is None:
        return None, None, None, None

    bx, by = baseline_torso
    tx, ty = torso_center

    x_change = int((tx - bx) * window_width)
    y_change = int((by - ty) * window_height)

    xcolor = (255, 0, 0) if x_change > 0 else (0, 0, 255)
    ycolor = (255, 0, 0) if y_change > 0 else (0, 0, 255)

    window.blit(font.render(f"x-Change: {x_change}", True, xcolor), (400, 10))
    window.blit(font.render(f"y-Change: {y_change}", True, ycolor), (400, 50))

    global_yaction = "Jump" if y_change > 80 else "Crouch" if y_change < -80 else ""
    global_xaction = "Right" if x_change > 80 else "Left" if x_change < -80 else ""

    window.blit(font.render(f"Actions: {global_yaction} {global_xaction}", True, black), (800, 10))
    
    return x_change, y_change, global_xaction, global_yaction

def draw_minimap_user():
    if torso_center is None:
        return

    # ---------------------------
    # Mini-map settings
    # ---------------------------
    box_x = 10
    box_y = 60
    box_w = 150
    box_h = 150

    # Draw box
    pygame.draw.rect(window, (30, 30, 30), (box_x, box_y+10, box_w, box_h), 2)

    # ---------------------------
    # Normalize torso (0–1 space)
    # ---------------------------
    tx, ty = torso_center

    # clamp just in case
    tx = max(0, min(1, tx))
    ty = max(0, min(1, ty))

    # map to box
    px = int(box_x + tx * box_w)
    py = int(box_y + ty * box_h)

    # draw user dot
    pygame.draw.circle(window, black, (px, py), 5)

def check_collision():
    """Check collision between player and enemies"""
    global lives, heart_hit_timers, enemies
    
    for enemy in enemies:
        # Skip if already hit
        if hasattr(enemy, 'hit') and enemy.hit:
            continue
        
        # Get enemy position using same logic as draw
        margin = 50
        horizon_y = window_height * 0.35
        vp = (window_width // 2, int(horizon_y))
        bottom_y = window_height
        left_outer = margin
        right_outer = window_width - margin
        lane_width = (right_outer - left_outer) / 3
        
        p0 = left_outer
        p1 = left_outer + lane_width
        p2 = left_outer + 2 * lane_width
        p3 = right_outer
        
        lane_boundaries = [(p0, p1), (p1, p2), (p2, p3)]
        left_bound, right_bound = lane_boundaries[enemy.lane]
        
        def interp(x):
            return int(x + (vp[0] - x) * (1 - enemy.t))
        
        enemy_y = int(horizon_y + (bottom_y - horizon_y) * enemy.t)
        left_x = interp(left_bound)
        right_x = interp(right_bound)
        enemy_x = (left_x + right_x) // 2
        
        scale = 0.3 * enemy.t * 1.5
        enemy_width = int(enemy.data["width"] * scale)
        enemy_height = int(enemy.data["height"] * scale)
        
        enemy_y += enemy.y_displacement
        
        # Create bounding box for enemy
        enemy_rect = pygame.Rect(
            enemy_x - enemy_width // 2,
            enemy_y - enemy_height // 2,
            enemy_width,
            enemy_height
        )
        
        # Check circle-rectangle collision
        closest_x = max(enemy_rect.left, min(player_x, enemy_rect.right))
        closest_y = max(enemy_rect.top, min(player_y, enemy_rect.bottom))
        
        distance = ((player_x - closest_x) ** 2 + (player_y - closest_y) ** 2) ** 0.5
        
        if distance < player_radius:
            # Collision detected - check dodge conditions
            is_safe = False
            
            if enemy.image_name == "tree":
                # Tree: can't dodge by being in the same lane
                is_safe = False
            elif enemy.image_name == "crustybird":
                # Bird: must crouch to dodge
                is_safe = (yaction == "Crouch")
            elif enemy.image_name == "angryturt":
                # Turtle: must jump to dodge
                is_safe = (yaction == "Jump")
            
            if not is_safe:
                # Failed to dodge - lose a heart
                enemy.hit = True
                lives -= 1
                if lives >= 0:
                    heart_hit_timers[lives] = 20

def draw_player(xaction, yaction):
    """Draw the player circle at the front, moving based on actions"""
    global player_x, player_y, player_target_lane, player_target_y
    
    # Calculate lane centers
    margin = 50
    lane_width = (window_width - 2 * margin) / 3
    lane_centers = [
        margin + lane_width * 0.5,
        margin + lane_width * 1.5,
        margin + lane_width * 2.5
    ]
    
    # Update target lane based on xaction
    if xaction == "Left":
        player_target_lane = 0
    elif xaction == "Right":
        player_target_lane = 2
    else:
        player_target_lane = 1  # Default to middle
    
    # Update target y based on yaction
    default_y = window_height - 100
    if yaction == "Jump":
        player_target_y = window_height - 200  # Move up
    elif yaction == "Crouch":
        player_target_y = window_height - 50   # Move down slightly
    else:
        player_target_y = default_y
    
    # Smoothly interpolate to target positions
    player_x += (lane_centers[player_target_lane] - player_x) * 0.2
    player_y += (player_target_y - player_y) * 0.2
    
    # Draw player circle
    pygame.draw.circle(window, black, (int(player_x), int(player_y)), player_radius)

cap = cv2.VideoCapture(0)
calibrate_button = pygame.Rect(10, 10, 120, 40)

# Initialize enemies list
enemies = []
enemy_spawn_timer = 0
enemy_spawn_interval = 60  # spawn every 60 frames

def drawScreen(window):
    margin = 50
    horizon_y = window_height * 0.35
    vp = (window_width // 2, int(horizon_y))

    bottom_y = window_height

    left_outer = margin
    right_outer = window_width - margin

    lane_width = (right_outer - left_outer) / 3

    p0 = (left_outer, bottom_y)
    p1 = (left_outer + lane_width, bottom_y)
    p2 = (left_outer + 2 * lane_width, bottom_y)
    p3 = (right_outer, bottom_y)

    pygame.draw.line(window, (180, 180, 180), (0, int(horizon_y)), (window_width, int(horizon_y)), 2)

    pygame.draw.line(window, black, p0, vp, 2)
    pygame.draw.line(window, black, p1, vp, 2)
    pygame.draw.line(window, black, p2, vp, 2)
    pygame.draw.line(window, black, p3, vp, 2)

    for i in range(1, 7):
        t = i / 7  # 0 → 1 (bottom → horizon)

        y = int(bottom_y - (bottom_y - horizon_y) * t)

        def interp(x):
            return int(x + (vp[0] - x) * t)

        pygame.draw.line(
            window,
            (200, 200, 200),
            (interp(p0[0]), y),
            (interp(p3[0]), y),
            1
        )

    pygame.draw.line(window, (220, 220, 220), (vp[0], 0), (vp[0], window_height), 1)
    

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    result = detector.detect(mp_image)

    if result.pose_landmarks:
        new_torso = get_torso_center(result.pose_landmarks[0])

        if new_torso:
            if prev_torso:
                dx = new_torso[0] - prev_torso[0]
                dy = new_torso[1] - prev_torso[1]
                dist = (dx**2 + dy**2) ** 0.5

                if dist > max_jump:
                    new_torso = prev_torso

            if prev_torso:
                smoothed = (
                    prev_torso[0] + alpha * (new_torso[0] - prev_torso[0]),
                    prev_torso[1] + alpha * (new_torso[1] - prev_torso[1])
                )
            else:
                smoothed = new_torso

            prev_torso = smoothed
            torso_center = smoothed


    window.fill(white)
    drawScreen(window)

    # Spawn enemies randomly
    enemy_spawn_timer += 1
    if enemy_spawn_timer >= enemy_spawn_interval:
        lane = random.randint(0, 2)
        image_name = random.choice(list(enemy_images.keys()))
        enemies.append(Enemy(lane, image_name))
        enemy_spawn_timer = 0
    
    # Update and draw enemies
    for enemy in enemies[:]:
        enemy.update()
        if not enemy.draw(window):
            enemies.remove(enemy)

    x_change, y_change, xaction, yaction = display()
    
    draw_player(xaction, yaction)
    draw_hearts()
    check_collision()

    if torso_center:
        x = int(torso_center[0] * window_width)
        y = int(torso_center[1] * window_height)
        draw_minimap_user()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            cap.release()
            pygame.quit()
            cv2.destroyAllWindows()
            exit()

        calibrate(event)

    color = (170, 170, 170) if calibrate_button.collidepoint(pygame.mouse.get_pos()) else (200, 200, 200)

    pygame.draw.rect(window, color, calibrate_button)
    window.blit(font.render("Calibrate", True, black), (20, 20))

    pygame.display.update()