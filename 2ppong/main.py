import pygame
import sys
import random
import numpy as np
import threading
import time

try:
    import serial
except ImportError:
    serial = None

# 1. Setup Constants
WIDTH, HEIGHT = 1000, 500
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 100
BALL_SIZE = 15
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Physics Constants
START_SPEED = 6
MAX_SPEED = 16
MAX_Y_SPEED = 8
ACCEL = 1.4
WINNING_SCORE = 1

CONTROLLER_PORT = 'COM3'
CONTROLLER_BAUD = 115200
PLAYER1_UP_THRESHOLD = 300
PLAYER1_DOWN_THRESHOLD = 700
PLAYER2_UP_THRESHOLD = 300
PLAYER2_DOWN_THRESHOLD = 700

controller_state = {
    "J1X": 512,
    "J1Y": 512,
    "J1SW": 1,
    "J2X": 512,
    "J2Y": 512,
    "J2SW": 1,
    "B1": 1,
    "B2": 1,
    "B3": 1,
}
controller_stop_event = threading.Event()


def read_arduino_controller():
    if serial is None:
        return

    while not controller_stop_event.is_set():
        try:
            with serial.Serial(CONTROLLER_PORT, CONTROLLER_BAUD, timeout=1) as ser:
                while not controller_stop_event.is_set():
                    raw = ser.readline()
                    if not raw:
                        continue
                    try:
                        line = raw.decode('utf-8').strip()
                    except Exception:
                        continue
                    parts = line.split(',')
                    for p in parts:
                        if '=' in p:
                            key, value = p.split('=', 1)
                            if key in controller_state:
                                try:
                                    controller_state[key] = int(value)
                                except ValueError:
                                    pass
        except Exception:
            time.sleep(1)


def main():
    pygame.init()
    pygame.font.init()
    
    def reset_game():
        nonlocal score1, score2, ball_dx, ball_dy, game_over, reset_timer, is_initial_start
        score1, score2 = 0, 0
        ball.center = (WIDTH//2, HEIGHT//2)
        ball_dx, ball_dy = 0, 0
        game_over = False
        reset_timer = 180
        is_initial_start = True
    
    button_font = pygame.font.SysFont("monospace", 40, bold=True)

    restart_btn = pygame.Rect(WIDTH//2 - 170, HEIGHT//2, 180, 70)
    quit_btn    = pygame.Rect(WIDTH//2 + 30,  HEIGHT//2, 140, 70)
    
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Two-Player Pong")
    
    # Use a pixel-style system font
    font = pygame.font.SysFont("monospace", 60, bold=True)
    clock = pygame.time.Clock()

    # 2. Game Objects
    player1 = pygame.Rect(50, HEIGHT//2 - PADDLE_HEIGHT//2, PADDLE_WIDTH, PADDLE_HEIGHT)
    player2 = pygame.Rect(WIDTH - 50 - PADDLE_WIDTH, HEIGHT//2 - PADDLE_HEIGHT//2, PADDLE_WIDTH, PADDLE_HEIGHT)
    ball = pygame.Rect(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2, BALL_SIZE, BALL_SIZE)

    # State
    score1, score2 = 0, 0
    ball_dx = 0 # Start at 0 for initial countdown
    ball_dy = 0
    player_speed = 10
    game_over = False
    
    # Timers for non-blocking pauses
    # Set to 180 (3 seconds * 60 FPS) for the start
    reset_timer = 180 
    is_initial_start = True

    if serial is not None:
        threading.Thread(target=read_arduino_controller, daemon=True).start()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                controller_stop_event.set()
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and game_over:
                if restart_btn.collidepoint(event.pos):
                    reset_game()
                elif quit_btn.collidepoint(event.pos):
                    return 75

        # 1. Paddle Movement (Always active)
        keys = pygame.key.get_pressed()
        ctrl_j1y = controller_state.get("J1Y", 512)
        ctrl_j2y = controller_state.get("J2Y", 512)
        controller_j1_up = ctrl_j1y < PLAYER1_UP_THRESHOLD
        controller_j1_down = ctrl_j1y > PLAYER1_DOWN_THRESHOLD
        controller_j2_up = ctrl_j2y < PLAYER2_UP_THRESHOLD
        controller_j2_down = ctrl_j2y > PLAYER2_DOWN_THRESHOLD

        if (keys[pygame.K_w] or controller_j1_up) and player1.top > 0:
            player1.y -= player_speed
        if (keys[pygame.K_s] or controller_j1_down) and player1.bottom < HEIGHT:
            player1.y += player_speed
        if (keys[pygame.K_UP] or controller_j2_up) and player2.top > 0:
            player2.y -= player_speed
        if (keys[pygame.K_DOWN] or controller_j2_down) and player2.bottom < HEIGHT:
            player2.y += player_speed

        if not game_over:
            if reset_timer > 0:
                # Ball stays at center while timer counts down
                ball.center = (WIDTH//2, HEIGHT//2)
                reset_timer -= 1
                
                # Only show numbers during the initial 3-second start
                if is_initial_start:
                    countdown_val = (reset_timer // 60) + 1
                else:
                    countdown_val = None
            else:
                # Timer finished, launch ball if it's currently stopped
                if ball_dx == 0:
                    is_initial_start = False
                    ball_dx = START_SPEED * random.choice([-1, 1])
                    ball_dy = START_SPEED * random.choice([-1, 1])

                # 2. Ball Movement
                ball.x += ball_dx
                ball.y += ball_dy

                # Wall Collisions
                if ball.top <= 0 or ball.bottom >= HEIGHT:
                    ball_dy *= -1

                # Paddle Collisions + Jitter Fix (Snapping)
                if ball.colliderect(player1):
                    ball_dx = abs(ball_dx) * ACCEL
                    ball.left = player1.right      
                    ball_dy += (ball.centery - player1.centery) * 0.5
                
                elif ball.colliderect(player2):
                    ball_dx = -abs(ball_dx) * ACCEL
                    ball.right = player2.left       
                    ball_dy += (ball.y - player2.centery) * 0.5  

                # Clamps
                if abs(ball_dx) > MAX_SPEED: ball_dx = MAX_SPEED * np.sign(ball_dx)
                if abs(ball_dy) > MAX_Y_SPEED: ball_dy = MAX_Y_SPEED * np.sign(ball_dy)

                # 3. Scoring Logic
                if ball.left <= 0 or ball.right >= WIDTH:
                    if ball.left <= 0: score2 += 1
                    else: score1 += 1

                    if score1 >= WINNING_SCORE or score2 >= WINNING_SCORE:
                        game_over = True
                    else:
                        ball_dx, ball_dy = 0, 0
                        reset_timer = 60 # 1 second delay (no number shown)

        # 4. Drawing
        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, player1)
        pygame.draw.rect(screen, WHITE, player2)
        pygame.draw.ellipse(screen, WHITE, ball)
        pygame.draw.aaline(screen, WHITE, (WIDTH//2, 0), (WIDTH//2, HEIGHT))

        # Scores
        p1_s = font.render(str(score1), True, WHITE)
        p2_s = font.render(str(score2), True, WHITE)
        screen.blit(p1_s, (WIDTH//4 - p1_s.get_width()//2, 20))
        screen.blit(p2_s, (WIDTH*3//4 - p2_s.get_width()//2, 20))

        # Draw Countdown Number (Only for start)
        if not game_over and reset_timer > 0 and is_initial_start:
            txt = font.render(str(countdown_val), True, WHITE)
            screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 50))

        if game_over:
            screen.fill((0,0,0))
            win_msg = "P1 WINS" if score1 >= WINNING_SCORE else "P2 WINS"
            win_surf = font.render(win_msg, True, WHITE)
            screen.blit(win_surf, (WIDTH//2 - win_surf.get_width()//2, HEIGHT//2 - 80))

            mouse_pos = pygame.mouse.get_pos()

            restart_hover = restart_btn.collidepoint(mouse_pos)
            quit_hover = quit_btn.collidepoint(mouse_pos)
            
            # Restart Button
            if restart_hover:
                pygame.draw.rect(screen, WHITE, restart_btn)  # filled
                restart_text = button_font.render("Restart", True, BLACK)
            else:
                pygame.draw.rect(screen, WHITE, restart_btn, 2)  # outline
                restart_text = button_font.render("Restart", True, WHITE)

            screen.blit(restart_text, (
                restart_btn.x + restart_btn.width//2 - restart_text.get_width()//2,
                restart_btn.y + restart_btn.height//2 - restart_text.get_height()//2
            ))


            # Quit Button
            if quit_hover:
                pygame.draw.rect(screen, WHITE, quit_btn)
                quit_text = button_font.render("Quit", True, BLACK)
            else:
                pygame.draw.rect(screen, WHITE, quit_btn, 2)
                quit_text = button_font.render("Quit", True, WHITE)

            screen.blit(quit_text, (
                quit_btn.x + quit_btn.width//2 - quit_text.get_width()//2,
                quit_btn.y + quit_btn.height//2 - quit_text.get_height()//2
            ))
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
