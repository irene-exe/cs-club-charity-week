import pygame
import os
import sys
import importlib

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
BLUE = (50, 150, 255)
RED = (200, 50, 50)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game Launcher")
font = pygame.font.SysFont("Arial", 24)
title_font = pygame.font.SysFont("Arial", 50, bold=True)

class Launcher:
    def __init__(self):
        self.state = "INPUT"
        self.fields = {
            "First Name (Optional)": "",
            "Last Name (Optional)": "",
            "Student Number": ""
        }
        self.active_field = "First Name (Optional)"
        
        self.games = [
            {"name": "CyberStrike", "folder": "cyberstrike", "file": "main"},
            {"name": "Rhythm 5000", "folder": "rhythm", "file": "main"},
            {"name": "Classic Tetris", "folder": "tetris", "file": "main"},
            {"name": "2P Pong", "folder": "2ppong", "file": "main"}
        ]
        self.current_idx = 0

    def save_user(self):
        filename = "log.txt"
        header = "Student Login, Name, Points\n"
        sn = self.fields["Student Number"].strip()
        fn = self.fields["First Name (Optional)"].strip() or "N/A"
        ln = self.fields["Last Name (Optional)"].strip() or "N/A"
        full_name = f"{fn} {ln}"

        # 1. Check if file exists and read it
        if os.path.exists(filename):
            with open(filename, "r") as f:
                lines = f.readlines()
        else:
            lines = [header]

        # 2. Check if the Student Number already exists
        user_exists = False
        for line in lines:
            if line.startswith(f"{sn},"):
                user_exists = True
                break
        
        # 3. If the user is new, append them with 0 points
        if not user_exists:
            with open(filename, "a") as f:
                # Format: Student Login, Name, Points
                f.write(f"{sn}, {full_name}, 0\n")

    def draw_button(self, text, rect, base_color):
        mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos)

        # --- Scale effect ---
        scale = 1.0 + (0.08 if hovered else 0)
        new_w = int(rect.width * scale)
        new_h = int(rect.height * scale)

        scaled_rect = pygame.Rect(0, 0, new_w, new_h)
        scaled_rect.center = rect.center  # keep centered

        # --- Color change ---
        color = DARK_GRAY if hovered else base_color

        # Draw button
        pygame.draw.rect(screen, color, scaled_rect, border_radius=10)

        # Text (invert on hover)
        text_color = BLACK if hovered else WHITE
        txt_surface = font.render(text, True, text_color)
        txt_rect = txt_surface.get_rect(center=scaled_rect.center)
        screen.blit(txt_surface, txt_rect)

        return scaled_rect  # important if you want accurate click detection
        
    def record_score(self, score=0):
        print("FUN")
        filename = "log.txt"
        header = "Student Login, Name, Points\n"
        
        # 1. Read existing data
        lines = []
        if os.path.exists(filename):
            with open(filename, "r") as f:
                lines = f.readlines()
        
        # Ensure header exists if file was empty
        if not lines:
            lines = [header]

        # 2. Prepare user info
        student_id = self.fields["Student Number"].strip()
        first_name = self.fields["First Name (Optional)"].strip() or "N/A"
        last_name = self.fields["Last Name (Optional)"].strip() or "N/A"
        full_name = f"{first_name} {last_name}"
        
        user_found = False
        updated_lines = [lines[0]] # Keep the header

        # 3. Search and Update
        for line in lines[1:]: # Skip header
            if line.strip():
                parts = line.strip().split(", ")
                if len(parts) >= 3:
                    current_id = parts[0]
                    current_name = parts[1]
                    current_points = float(parts[2])
                    
                    if current_id == student_id:
                        # Update existing user points
                        new_points = current_points + float(score)
                        updated_lines.append(f"{student_id}, {current_name}, {new_points}\n")
                        user_found = True
                    else:
                        updated_lines.append(line)

        # 4. If new user, add them to the list
        if not user_found:
            print("DNE")
            updated_lines.append(f"{student_id}, {full_name}, {float(score)}\n")

        # 5. Write back to file
        with open(filename, "w") as f:
            print("\n".join(updated_lines))
            f.write("\n".join(updated_lines))
            
    def run(self):
        clock = pygame.time.Clock()
        
        while True:
            screen.fill(WHITE)
            mx, my = pygame.mouse.get_pos()
            
            # Check if Student Number is provided
            id_provided = len(self.fields["Student Number"].strip()) > 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.state == "INPUT":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # Field selection detection
                        if 250 < mx < 550:
                            if 150 < my < 190: self.active_field = "First Name (Optional)"
                            if 230 < my < 270: self.active_field = "Last Name (Optional)"
                            if 310 < my < 350: self.active_field = "Student Number"
                    
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_TAB:
                            order = ["First Name (Optional)", "Last Name (Optional)", "Student Number"]
                            idx = (order.index(self.active_field) + 1) % len(order)
                            self.active_field = order[idx]
                        
                        elif event.key == pygame.K_RETURN:
                            # CRITICAL CHANGE: Only student number is required
                            if id_provided:
                                self.save_user()
                                self.state = "SCROLLER"
                        
                        elif event.key == pygame.K_BACKSPACE:
                            self.fields[self.active_field] = self.fields[self.active_field][:-1]
                        else:
                            if len(self.fields[self.active_field]) < 18:
                                self.fields[self.active_field] += event.unicode

                elif self.state == "SCROLLER":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # Arrow logic
                        if 50 < mx < 100 and 275 < my < 325:
                            self.current_idx = (self.current_idx - 1) % len(self.games)
                        if 700 < mx < 750 and 275 < my < 325:
                            self.current_idx = (self.current_idx + 1) % len(self.games)
                        
                        # Play logic
                        if 300 < mx < 500 and 450 < my < 510:
                            game = self.games[self.current_idx]
                            original_dir = os.getcwd() # Save current folder
                            try:
                                # 1. Change directory to the game's folder
                                os.chdir(game["folder"])
                                
                                # 2. Import the main file from that folder
                                # We use '.' to refer to the current directory we just entered
                                sys.path.insert(0, os.getcwd())
                                mod = importlib.import_module(game["file"])
                                importlib.reload(mod)
                                
                                # 3. Assuming your games have a main() function
                                score = 0
                                if hasattr(mod, 'main'):
                                    score = mod.main()
                                os.chdir(original_dir)
                                print(score)
                                self.record_score(score)
                                
                            except Exception as e:
                                print(f"Error launching {game['name']}: {e}")
                            finally:
                                # 4. Always switch back to the launcher folder
                                os.chdir(original_dir)
                                if os.getcwd() in sys.path:
                                    sys.path.remove(os.getcwd())
                                pygame.display.set_mode((WIDTH, HEIGHT))
                            
                        # Logout logic
                        if 680 < mx < 780 and 20 < my < 60:
                            self.fields = {k: "" for k in self.fields}
                            self.state = "INPUT"

            # --- Rendering Input Screen ---
            if self.state == "INPUT":
                instruct = font.render("Enter details (Only ID is required):", True, BLACK)
                screen.blit(instruct, (WIDTH//2 - instruct.get_width()//2, 80))
                
                y_pos = 150
                for label, value in self.fields.items():
                    lbl_surf = font.render(label, True, BLACK)
                    screen.blit(lbl_surf, (250, y_pos - 25))
                    
                    box_rect = pygame.Rect(250, y_pos, 300, 40)
                    # Use RED border if ID is empty and active, otherwise BLUE/GRAY
                    border_col = BLUE if self.active_field == label else GRAY
                    pygame.draw.rect(screen, border_col, box_rect, 2, border_radius=5)
                    
                    val_surf = font.render(value, True, BLACK)
                    screen.blit(val_surf, (box_rect.x + 10, box_rect.y + 5))
                    y_pos += 80
                
                # Dynamic Button Message
                msg = "Press ENTER to Continue" if id_provided else "Enter ID to Start"
                btn_col = BLUE if id_provided else GRAY
                self.draw_button(msg, pygame.Rect(250, 420, 300, 50), btn_col)

            # --- Rendering Scroller ---
            elif self.state == "SCROLLER":
                self.draw_button("Logout", pygame.Rect(680, 20, 100, 40), RED)
                
                # Show name if provided, otherwise show ID
                display_name = self.fields["First Name (Optional)"].strip() or f"ID: {self.fields['Student Number']}"
                welcome = font.render(f"Welcome, {display_name}", True, DARK_GRAY)
                screen.blit(welcome, (20, 20))

                title = title_font.render(self.games[self.current_idx]["name"], True, BLACK)
                screen.blit(title, (WIDTH//2 - title.get_width()//2, 250))
                
                self.draw_button("<", pygame.Rect(50, 275, 50, 50), BLUE)
                self.draw_button(">", pygame.Rect(700, 275, 50, 50), BLUE)
                self.draw_button("PLAY", pygame.Rect(300, 450, 200, 60), BLUE)

            pygame.display.flip()
            clock.tick(60)

if __name__ == "__main__":
    launcher = Launcher()
    launcher.run()