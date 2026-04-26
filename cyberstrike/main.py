import pygame
import random
import math
import sys

# --- 1. SETTINGS ---
WIDTH, HEIGHT = 1080, 725    
FPS = 60
CYAN, YELLOW, MAGENTA = (0, 255, 255), (255, 255, 0), (255, 0, 255)
WHITE, RED, BLACK, DARK_BLUE = (255, 255, 255), (255, 50, 50), (0, 0, 0), (10, 10, 30)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cyber Strike: Overseer Edition")
clock = pygame.time.Clock()

font = pygame.font.SysFont("monospace", 24, bold=True)
small_font = pygame.font.SysFont("monospace", 18, bold=True)
large_font = pygame.font.SysFont("monospace", 50, bold=True)
console_font = pygame.font.SysFont("monospace", 18)

# --- 2. ASSET LOADING ---
def load_s(path, size):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    except: return None

s_player = load_s("assets/player.png", (45, 45))
s_core = load_s("assets/core.png", (35, 35))           
s_zigzag = load_s("assets/zigzag.png", (35, 35))       
s_pointer = load_s("assets/pointer.png", (35, 35))     
s_teleporter = load_s("assets/teleporter.png", (65, 65)) 

try:
    title_img = pygame.image.load("assets/title_bg.png").convert_alpha()
    title_img = pygame.transform.smoothscale(title_img, (WIDTH, HEIGHT))
except:
    title_img = pygame.Surface((WIDTH, HEIGHT))
    title_img.fill((5, 5, 25))

# --- 3. VARIABLES ---
game_state = "START_MENU" 
player_pos = [WIDTH // 2, HEIGHT - 100]
player_speed = 7
score, start_time = 0, 0
bullets, enemies = [], []

total_shots, last_shot_time = 0, 0
reload_threshold = 12  
base_fire_delay = 110  
grid_scroll = 0
can_shoot_manual, space_enabled = True, True

show_console, console_input = False, ""
admin_log = ["SYSTEM OVERSEER ONLINE", "TYPE 'HELP' FOR COMMANDS"]

rig_percent = 100 # New: 0 to 100 scale
global_velocity = 1.4 
spawn_rates = {0: 1500, 1: 2800, 2: 4000, 3: 6000}
last_spawn_times = {0: 0, 1: 0, 2: 0, 3: 0}

# --- 4. VISUAL FUNCTIONS ---
def draw_background_grid(speed_mult):
    global grid_scroll
    grid_color = (20, 20, 65)
    grid_scroll += 3 * speed_mult
    if grid_scroll >= 40: grid_scroll = 0
    for i in range(-15, 30):
        start_x = (WIDTH // 10) * i
        pygame.draw.line(screen, grid_color, (start_x, 0), (start_x + (i-7)*115, HEIGHT), 1)
    for i in range(25):
        y = (i * 40) + grid_scroll
        pygame.draw.line(screen, grid_color, (0, y), (WIDTH, y), 1)

def draw_glitch(img, intensity=0.15, alpha=255):
    if not img: return
    jx = int(max(1, 40 * intensity))
    temp_surf = img.copy()
    temp_surf.set_alpha(alpha)
    screen.blit(temp_surf, (random.randint(-jx, jx), random.randint(-4, 4)))
    if random.random() < (intensity * 1.5):
        for _ in range(random.randint(2, 5)):
            sy, sh = random.randint(0, HEIGHT), random.randint(5, 20)
            pygame.draw.rect(screen, random.choice([MAGENTA, BLACK, (0,0,50)]), (0, sy, WIDTH, sh))

# --- 5. MAIN LOOP ---
running = True
while running:
    screen.fill(BLACK) 
    current_ticks = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSLASH and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                game_state, space_enabled = "START_MENU", True
                admin_log.append("SYSTEM REBOOTED")

            if event.key == pygame.K_BACKQUOTE:
                show_console, console_input = not show_console, ""

            elif show_console:
                if event.key == pygame.K_RETURN:
                    parts = console_input.lower().split()
                    if parts:
                        cmd = parts[0]
                        if cmd == "help": 
                            admin_log.append("RIG [%], KILL, SPWN [T] [MS], SPEED [V], TIME [S], CLEAR")
                        
                        elif cmd == "rig": 
                            try:
                                # Accepts rig 0, rig 50, rig 100 etc.
                                rig_percent = max(0, min(100, int(parts[1])))
                                admin_log.append(f"RIGGING SET TO: {rig_percent}%")
                            except:
                                # Default toggle if no number provided
                                rig_percent = 100 if rig_percent == 0 else 0
                                admin_log.append(f"RIGGING TOGGLED: {rig_percent}%")
                        
                        elif cmd == "kill": 
                            enemies = []
                            admin_log.append("ENEMIES PURGED")

                        elif cmd == "spwn":
                            try:
                                t, ms = int(parts[1]), int(parts[2])
                                if t in spawn_rates:
                                    spawn_rates[t] = ms
                                    admin_log.append(f"TIER {t} RATE: {ms}MS")
                                else: admin_log.append("ERR: TIER 0-3 ONLY")
                            except: admin_log.append("USAGE: SPWN [T] [MS]")

                        elif cmd == "speed":
                            try:
                                global_velocity = float(parts[1])
                                admin_log.append(f"SPEED SET: {global_velocity}")
                            except: admin_log.append("USAGE: SPEED [V]")

                        elif cmd == "time":
                            try:
                                t_val = int(parts[1])
                                start_time = current_ticks - (t_val * 1000)
                                admin_log.append(f"TIME SET: {t_val}S")
                            except: admin_log.append("USAGE: TIME [S]")

                        elif cmd == "clear": 
                            admin_log = ["LOG CLEARED"]
                    console_input = ""
                elif event.key == pygame.K_BACKSPACE: console_input = console_input[:-1]
                else: console_input += event.unicode

            elif event.key == pygame.K_SPACE and game_state == "START_MENU" and space_enabled:
                game_state, start_time = "PLAYING", current_ticks
                enemies, bullets, score, total_shots = [], [], 0, 0
                last_spawn_times = {k: current_ticks for k in spawn_rates}
            
            if event.key == pygame.K_SPACE: can_shoot_manual = True

    if game_state == "START_MENU":
        draw_background_grid(0.5)
        draw_glitch(title_img, 0.1, alpha=180)
        
        # This was the problematic line — now fixed:
        txt = font.render("AWAITING SYSTEM AUTHORIZATION...", True, RED)
        screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT-100)))
        
        if space_enabled:
            sub = font.render("[PRESS SPACE TO BEGIN]", True, WHITE)
            screen.blit(sub, sub.get_rect(center=(WIDTH//2, HEIGHT-60)))
            
    elif game_state == "PLAYING":
        elapsed = (current_ticks - start_time) // 1000
        reloads = total_shots // reload_threshold
        
        # --- ADJUSTABLE RIGGING LOGIC ---
        rig_factor = rig_percent / 100.0
        
        # Wall start time scales from 30s (0% rig) down to 10s (100% rig)
        wall_start = 30 - (20 * rig_factor)
        
        if elapsed < wall_start:
            ramp = (elapsed / wall_start) * 0.5
            extreme_mult = 1.0
        else:
            # How fast it hits "Extreme" depends on rig_factor
            climb_speed = 5.0 if rig_factor > 0.5 else 15.0
            ramp = min(1.0, 0.5 + (elapsed - wall_start) / climb_speed) 
            extreme_mult = 1.0 + (elapsed - wall_start) * (0.1 + (0.2 * rig_factor))

        # Stability drain scales with rig_percent
        # At 0%, stability is basically infinite/ignored. At 100%, it drops fast.
        stability_drain = (reloads * 20) * rig_factor
        stability = max(0, 100 - stability_drain) if rig_factor > 0 else 100
        
        # Trigger "Overload" state based on the calculated wall
        is_overload = elapsed > wall_start

        # Stability Multipliers
        stability_mult = 1.0
        if stability <= 0: stability_mult = 4.5
        elif stability <= 20: stability_mult = 2.5
        elif stability <= 40: stability_mult = 1.5
        
        # Semi-auto toggle
        force_semi = (stability <= 20 or (is_overload and rig_factor > 0.5))

        speed_mod = (1.0 + (ramp * 3.0)) * stability_mult * extreme_mult
        draw_background_grid(speed_mod)
        draw_glitch(title_img, 0.02 + ((100 - stability) / 100.0) if elapsed > 5 else 0.02, alpha=120)

        # Player Controls
        if not show_console:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a] and player_pos[0] > 30: player_pos[0] -= player_speed
            if keys[pygame.K_d] and player_pos[0] < WIDTH-30: player_pos[0] += player_speed
            if keys[pygame.K_w] and player_pos[1] > 30: player_pos[1] -= player_speed
            if keys[pygame.K_s] and player_pos[1] < HEIGHT-30: player_pos[1] += player_speed
            
            # Fire delay only really gets bad if rigged
            fire_delay = base_fire_delay + ((reloads * 300) * ramp * rig_factor)
            if keys[pygame.K_SPACE] and current_ticks - last_shot_time > fire_delay:
                if not force_semi or (force_semi and can_shoot_manual):
                    bullets.append([player_pos[0], player_pos[1]])
                    total_shots += 1; last_shot_time = current_ticks; can_shoot_manual = False
            if not keys[pygame.K_SPACE] and total_shots > 0: total_shots -= 0.08

        # Spawning Logic
        for tier, ms in spawn_rates.items():
            unlock_time = 2 + (tier * 3) if rig_factor > 0.5 else 5 + (tier * 8)
            if elapsed < unlock_time: continue
            
            spawn_intensity = (1.0 + (ramp * 2.0)) * extreme_mult
            if stability <= 0 and rig_factor > 0: spawn_intensity *= 2.0
            
            if current_ticks - last_spawn_times[tier] > (ms / (spawn_intensity * speed_mod)):
                ex = player_pos[0] if tier == 3 else random.randint(50, WIDTH-50)
                ey = player_pos[1] if tier == 3 else -50
                enemies.append([ex, ey, tier, 1 + (elapsed // 10), current_ticks])
                last_spawn_times[tier] = current_ticks

        # Logic & Collisions
        rem_e = []
        for e in enemies:
            t_alive = current_ticks - e[4]
            if e[2] == 3:
                if t_alive > 4000: rem_e.append(e) 
            else:
                e_spd = global_velocity * speed_mod
                if e[2] == 0: e[1] += e_spd
                elif e[2] == 1: e[1] += e_spd; e[0] += math.sin(current_ticks/300) * (3 * speed_mod)
                elif e[2] == 2: e[1] += e_spd * 1.3; e[0] += math.cos(e[1]/120) * (5 * speed_mod)
            
            if (e[2] != 3 or t_alive > 3000) and math.hypot(e[0]-player_pos[0], e[1]-player_pos[1]) < 30:
                game_state, space_enabled = "GAME_OVER", False

        # Bullet Logic
        rem_b = []
        for b in bullets:
            b[1] -= 20
            pygame.draw.rect(screen, YELLOW, (b[0]-2, b[1], 4, 15))
            for e in enemies:
                if e[2] == 3 and current_ticks - e[4] < 3000: continue
                if math.hypot(b[0]-e[0], b[1]-e[1]) < 25:
                    rem_b.append(b); e[3] -= 1
                    if e[3] <= 0 and e not in rem_e: rem_e.append(e); score += 1
        
        bullets = [b for b in bullets if b not in rem_b and b[1] > -20]
        enemies = [e for e in enemies if e not in rem_e and e[1] < HEIGHT + 50]

        # Draw Player/Enemies
        if s_player: screen.blit(s_player, (player_pos[0]-22, player_pos[1]-22))
        else: pygame.draw.circle(screen, CYAN, (int(player_pos[0]), int(player_pos[1])), 20, 2)

        for e in enemies:
            t_a, ex, ey = current_ticks - e[4], int(e[0]), int(e[1])
            if e[2] == 3:
                if t_a < 3000:
                    timer = max(0, (3000 - t_a) / 1000.0)
                    warn = small_font.render(f"PHANTOM LOCK: {timer:.1f}s", True, MAGENTA)
                    screen.blit(warn, (ex-80, ey-60))
                    pygame.draw.rect(screen, (80, 0, 80), (ex-25, ey-25, 50, 50), 1)
                else:
                    if s_teleporter: screen.blit(s_teleporter, (ex-32, ey-32))
                    else: pygame.draw.rect(screen, MAGENTA, (ex-25, ey-25, 50, 50), 3)
                    life = max(0, 40 - ((t_a - 3000) // 25))
                    pygame.draw.rect(screen, CYAN, (ex-20, ey-40, life, 4))
            else:
                img = [s_core, s_zigzag, s_pointer][e[2]]
                if img: screen.blit(img, (ex-17, ey-17))

        screen.blit(font.render(f"DATA: {score}", True, YELLOW), (20, 20))
        link_color = RED if (stability < 40 or is_overload) else CYAN
        screen.blit(font.render(f"LINK: {int(stability)}%", True, link_color), (20, 55))
        
        if is_overload:
            msg_text = "!! SYSTEM OVERLOAD !!" if rig_factor > 0 else "MAX DIFFICULTY"
            msg = small_font.render(msg_text, True, RED)
            screen.blit(msg, (WIDTH - 250, 20))
            
        if score >= 100: game_state = "GAME_OVER"

    elif game_state == "GAME_OVER":
        draw_background_grid(0.1); draw_glitch(title_img, 0.5, alpha=150)
        msg = large_font.render("CONNECTION LOST", True, RED)
        screen.blit(msg, msg.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
        screen.blit(font.render(f"FINAL DATA: {score}", True, YELLOW), (WIDTH//2-80, HEIGHT//2+20))

    if show_console:
        con_surf = pygame.Surface((WIDTH, 240)); con_surf.set_alpha(200); con_surf.fill((5, 5, 15))
        screen.blit(con_surf, (0, HEIGHT-240))
        for i, log in enumerate(admin_log[-8:]):
            screen.blit(console_font.render(f"> {log}", True, MAGENTA), (20, HEIGHT - 225 + (i*24)))
        screen.blit(console_font.render(f"CMD: {console_input}_", True, WHITE), (20, HEIGHT - 35))

    pygame.display.flip(); clock.tick(FPS)