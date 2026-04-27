import pygame
import sys
import random

# --- 1. CONFIGURATION ---
WIDTH, HEIGHT = 1080, 725
GRID_SIZE = 30
COLUMNS, ROWS = 10, 20
GAME_WIDTH, GAME_HEIGHT = COLUMNS * GRID_SIZE, ROWS * GRID_SIZE
OFFSET_X, OFFSET_Y = (WIDTH - GAME_WIDTH) // 2, 50

# Colors
BLACK = (2, 2, 8); CYAN = (0, 255, 255); MAGENTA = (255, 0, 255)
WHITE = (220, 220, 255); RED = (255, 50, 50); GRAY = (40, 40, 60)
DARK_BLUE = (10, 10, 45); GRID_BLUE = (0, 0, 120)

SHAPES = [
    [[1, 1, 1, 1]], [[1, 1], [1, 1]], [[0, 1, 0], [1, 1, 1]],
    [[0, 1, 1], [1, 1, 0]], [[1, 1, 0], [0, 1, 1]],
    [[1, 0, 0], [1, 1, 1]], [[0, 0, 1], [1, 1, 1]]
]

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TETRIS: NO HESITATION - ROOT ACCESS")
clock = pygame.time.Clock()
font_main = pygame.font.SysFont("monospace", 45, bold=True)
font_sub = pygame.font.SysFont("monospace", 22, bold=True)
console_font = pygame.font.SysFont("monospace", 14)

# --- 2. RENDERER ---
def draw_4d_block(surface, x, y, size, color, is_fracture=False, expiry_time=0):
    now = pygame.time.get_ticks()
    fill_surf = pygame.Surface((size - 4, size - 4))
    alpha = 160
    if is_fracture:
        time_left = expiry_time - now
        alpha = 255 if time_left < 2000 and (now // 100) % 2 else 120
    fill_surf.set_alpha(alpha); fill_surf.fill(color)
    surface.blit(fill_surf, (x + 2, y + 2))
    pygame.draw.rect(surface, color, (x + 2, y + 2, size - 4, size - 4), 2)
    p, i_s = size // 4, size // 2
    pygame.draw.rect(surface, color, (x + p, y + p, i_s, i_s), 1)
    for s_pt, e_pt in [((x+2,y+2),(x+p,y+p)), ((x+size-2,y+2),(x+p+i_s,y+p)),
                       ((x+2,y+size-2),(x+p,y+p+i_s)), ((x+size-2,y+size-2),(x+p+i_s,y+p+i_s))]:
        pygame.draw.line(surface, color, s_pt, e_pt, 1)

# --- 3. CORE LOGIC ---
class Tetromino:
    def __init__(self, shape, f_chance):
        self.shape = shape
        self.is_fracture = random.random() < f_chance
        self.color = RED if self.is_fracture else random.choice([CYAN, MAGENTA])
        self.x, self.y = COLUMNS // 2 - len(shape[0]) // 2, 0
    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]

class TetrisGame:
    def __init__(self):
        self.grid = [[None for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.fracture_timers = {}
        # RESET DEFAULT ADMIN VALUES
        self.fracture_chance = 0.20
        self.fracture_duration = 7000
        self.base_speed = 900.0 
        self.speed_decay = 0.85
        self.pts_row = 4.0
        self.pts_save = 0.2
        self.latency_gain = 0.06
        self.latency_reduction = 12.0
        
        self.generate_junk()
        self.score, self.latency = 0.0, 0
        self.last_speed_bump = pygame.time.get_ticks()
        self.last_drop_time = pygame.time.get_ticks()
        self.speed_level = 0
        self.game_over = False
        self.queue = [self.new_piece() for _ in range(3)]
        self.current_piece = self.queue.pop(0)

    def generate_junk(self):
        # Restored 20% height junk profile
        for y in range(ROWS - 6, ROWS):
            hole = random.randint(0, COLUMNS - 1)
            for x in range(COLUMNS):
                if x != hole: 
                    self.grid[y][x] = {"color": random.choice([CYAN, MAGENTA, GRAY]), "fracture": False}

    def new_piece(self): 
        p = Tetromino(random.choice(SHAPES), self.fracture_chance)
        for _ in range(random.randint(0, 3)): p.rotate()
        return p
    
    def valid_move(self, piece, dx, dy):
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    nx, ny = piece.x + x + dx, piece.y + y + dy
                    if not (0 <= nx < COLUMNS and 0 <= ny < ROWS) or (ny >= 0 and self.grid[ny][nx]):
                        return False
        return True

    def lock_piece(self):
        now = pygame.time.get_ticks()
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    gy, gx = self.current_piece.y + y, self.current_piece.x + x
                    self.grid[gy][gx] = {"color": self.current_piece.color, "fracture": self.current_piece.is_fracture}
                    if self.current_piece.is_fracture: self.fracture_timers[(gy, gx)] = now + self.fracture_duration
        self.clear_lines()
        self.current_piece = self.queue.pop(0); self.queue.append(self.new_piece())
        if not self.valid_move(self.current_piece, 0, 0): self.game_over = True

    def clear_lines(self):
        cleared = 0
        for y in range(ROWS):
            if all(self.grid[y]):
                for k in [k for k in self.fracture_timers if k[0] == y]: del self.fracture_timers[k]
                del self.grid[y]; self.grid.insert(0, [None for _ in range(COLUMNS)])
                nt = {}
                for (ty, tx), time in self.fracture_timers.items():
                    nt[(ty + 1, tx) if ty < y else (ty, tx)] = time
                self.fracture_timers = nt; cleared += 1
        if cleared:
            combo = {1: self.pts_row, 2: self.pts_row*2.5, 3: self.pts_row*4.5, 4: self.pts_row*7.5}
            self.score += combo.get(cleared, cleared * self.pts_row)
            self.latency = min(100, self.latency + (cleared * 10))

    def update(self):
        if self.game_over: return
        now = pygame.time.get_ticks()
        for pos in [p for p, t in self.fracture_timers.items() if now > t]:
            self.grid[pos[0]][pos[1]] = None; del self.fracture_timers[pos]
        if now - self.last_speed_bump > 5000:
            self.base_speed *= self.speed_decay; self.speed_level += 1; self.last_speed_bump = now
        self.latency = min(100, self.latency + self.latency_gain)
        delay = max(25, self.base_speed - (self.latency * 5))
        if now - self.last_drop_time > delay:
            if self.valid_move(self.current_piece, 0, 1): self.current_piece.y += 1
            else: self.lock_piece()
            self.last_drop_time = now

# --- 4. ENGINE ---
game = TetrisGame(); state = "TITLE"
show_console, console_input = False, ""
admin_log = ["--- SYSTEM OVERRIDE ACTIVE ---", "USE '|' TO HARD REBOOT"]

while True:
    screen.fill(BLACK); now = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            # HIDDEN HARD REBOOT
            if event.unicode == "|": 
                state = "TITLE"; game.__init__(); admin_log.append("HARD REBOOT EXECUTED")
            
            if event.key == pygame.K_BACKQUOTE: show_console = not show_console
            elif show_console:
                if event.key == pygame.K_RETURN:
                    p = console_input.lower().split()
                    if p:
                        cmd = p[0]
                        try:
                            if cmd == "help": 
                                admin_log.extend([
                                    "spawn [0-100]  : Fracture chance %",
                                    "speed [ms]     : Initial fall delay",
                                    "rate [0.0-1.0] : Gravity decay per 5s",
                                    "row_pts [val]  : Points per row",
                                    "save_pts [val] : Points per hard drop",
                                    "lat_inc [val]  : Passive heat gain",
                                    "lat_dec [val]  : Heat removed on slam",
                                    "fr_time [ms]   : Fracture lifetime"
                                ])
                            elif cmd == "spawn": game.fracture_chance = int(p[1])/100.0; admin_log.append(f"SPAWN: {p[1]}%")
                            elif cmd == "speed": game.base_speed = float(p[1]); admin_log.append(f"SPEED: {p[1]}ms")
                            elif cmd == "rate": game.speed_decay = float(p[1]); admin_log.append(f"RATE: {p[1]}")
                            elif cmd == "row_pts": game.pts_row = float(p[1]); admin_log.append(f"ROW: {p[1]}pts")
                            elif cmd == "save_pts": game.pts_save = float(p[1]); admin_log.append(f"SAVE: {p[1]}pts")
                            elif cmd == "lat_inc": game.latency_gain = float(p[1]); admin_log.append(f"LAT+: {p[1]}")
                            elif cmd == "lat_dec": game.latency_reduction = float(p[1]); admin_log.append(f"LAT-: {p[1]}")
                            elif cmd == "fr_time": game.fracture_duration = int(p[1]); admin_log.append(f"FRAC: {p[1]}ms")
                            else: admin_log.append(f"ERR: {cmd} NOT FOUND")
                        except: admin_log.append("ERR: PARAM INVALID")
                    console_input = ""
                elif event.key == pygame.K_BACKSPACE: console_input = console_input[:-1]
                else: console_input += event.unicode
            elif state == "TITLE" and event.key == pygame.K_SPACE: state = "PLAYING"
            elif state == "PLAYING":
                if event.key == pygame.K_LEFT and game.valid_move(game.current_piece, -1, 0): game.current_piece.x -= 1
                if event.key == pygame.K_RIGHT and game.valid_move(game.current_piece, 1, 0): game.current_piece.x += 1
                if event.key == pygame.K_UP:
                    game.latency = max(0, game.latency - game.latency_reduction); game.score += game.pts_save
                    while game.valid_move(game.current_piece, 0, 1): game.current_piece.y += 1
                    game.lock_piece()
                if event.key == pygame.K_SPACE:
                    game.current_piece.rotate()
                    if not game.valid_move(game.current_piece, 0, 0): 
                        for _ in range(3): game.current_piece.rotate()

    if state == "TITLE":
        t1 = font_main.render("TETRIS: NO HESITATION", True, CYAN)
        t2 = font_sub.render("SUB_ROUTINE: DEEP_STATE", True, MAGENTA)
        screen.blit(t1, (WIDTH//2 - t1.get_width()//2, HEIGHT//2 - 50))
        if (now // 500) % 2:
            t3 = font_sub.render("[ PRESS SPACE TO START ]", True, WHITE)
            screen.blit(t3, (WIDTH//2 - t3.get_width()//2, HEIGHT//2 + 50))
    elif state == "PLAYING":
        if not show_console: game.update()
        pygame.draw.rect(screen, DARK_BLUE, (OFFSET_X-5, OFFSET_Y-5, GAME_WIDTH+10, GAME_HEIGHT+10), 3)
        for i, p_next in enumerate(game.queue):
            for y, row in enumerate(p_next.shape):
                for x, cell in enumerate(row):
                    if cell: draw_4d_block(screen, OFFSET_X+GAME_WIDTH+60+x*20, OFFSET_Y+400+i*80+y*20, 20, p_next.color, p_next.is_fracture, 0)
        for y, row in enumerate(game.grid):
            for x, cell in enumerate(row):
                if cell: draw_4d_block(screen, OFFSET_X+x*GRID_SIZE, OFFSET_Y+y*GRID_SIZE, GRID_SIZE, cell["color"], cell["fracture"], game.fracture_timers.get((y,x),0))
        p = game.current_piece
        for y, row in enumerate(p.shape):
            for x, cell in enumerate(row):
                if cell: draw_4d_block(screen, OFFSET_X+(p.x+x)*GRID_SIZE, OFFSET_Y+(p.y+y)*GRID_SIZE, GRID_SIZE, p.color, p.is_fracture)
        bar_x = OFFSET_X + GAME_WIDTH + 40
        pygame.draw.rect(screen, DARK_BLUE, (bar_x, OFFSET_Y, 20, 300), 2)
        f = (game.latency / 100) * 300; lc = RED if game.latency > 80 else CYAN
        pygame.draw.rect(screen, lc, (bar_x, OFFSET_Y+300-f, 20, f))
        screen.blit(font_sub.render(f"POINTS: {game.score:.1f}", True, WHITE), (OFFSET_X - 180, OFFSET_Y))
        sw = (now - game.last_speed_bump > 4000); lvc = RED if sw and (now // 100) % 2 else MAGENTA
        screen.blit(font_sub.render(f"LVL: {game.speed_level}", True, lvc), (OFFSET_X - 180, OFFSET_Y + 40))
        if game.game_over: state = "GAME_OVER"
    elif state == "GAME_OVER":
        ov = font_main.render("SYSTEM FAILURE", True, RED); sc = font_sub.render(f"FINAL POINTS: {game.score:.1f}", True, WHITE)
        screen.blit(ov, (WIDTH//2 - ov.get_width()//2, HEIGHT//2 - 60)); screen.blit(sc, (WIDTH//2 - sc.get_width()//2, HEIGHT//2))

    if show_console:
        s = pygame.Surface((WIDTH, 260), pygame.SRCALPHA); s.fill((2, 2, 8, 245)); screen.blit(s, (0, HEIGHT-260))
        pygame.draw.line(screen, MAGENTA, (0, HEIGHT-260), (WIDTH, HEIGHT-260), 2)
        for i, log in enumerate(admin_log[-10:]): screen.blit(console_font.render(f"> {log}", True, MAGENTA), (20, HEIGHT-245 + i*20))
        screen.blit(console_font.render(f"root@system:~# {console_input}|", True, WHITE), (20, HEIGHT-35))

    pygame.display.flip(); clock.tick(60)