import pygame
import sys
import random
import gamescreen
import credit
import levelselect

# Initialize Pygame
pygame.init()

# Constants and Setup for the display
WIDTH, HEIGHT = 1280, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Seaside Programming")

# Colors
TEXT_COLOR = (40, 40, 40)
ACCENT_COLOR = (255, 165, 0)
PANEL_FG_COLOR = (255, 255, 255, 150)

# Fonts
try:
    TITLE_FONT = pygame.font.SysFont('calibri', 70, bold=True)
    SUBTITLE_FONT = pygame.font.SysFont('calibri', 30, italic=True)
    PANEL_HEADER = pygame.font.SysFont('calibri', 32, bold=True)
    PANEL_TEXT = pygame.font.SysFont('calibri', 26)
except:
    TITLE_FONT = pygame.font.Font(None, 80)
    SUBTITLE_FONT = pygame.font.Font(None, 40)
    PANEL_HEADER = pygame.font.Font(None, 40)
    PANEL_TEXT = pygame.font.Font(None, 30)

#Background
def draw_beach_gradient(surface, width, height):
    gradient = pygame.Surface((1, 3))
    gradient.set_at((0, 0), (135, 206, 235))
    gradient.set_at((0, 1), (176, 224, 230))
    gradient.set_at((0, 2), (250, 235, 215))
    gradient = pygame.transform.smoothscale(gradient, (width, height))
    surface.blit(gradient, (0, 0))

# THe cloud
class Cloud:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(20, 200)
        self.radius = random.randint(30, 60)
        self.speed = random.uniform(0.2, 0.8)

    def update(self):
        self.x += self.speed
        if self.x - self.radius > WIDTH:
            self.x = -self.radius * 2
            self.y = random.randint(20, 200)

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x) + self.radius // 1.5, int(self.y) + 10),
                           self.radius // 1.2)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x) - self.radius // 1.5, int(self.y) + 10),
                           self.radius // 1.2)


# Button style
class ModernButton:
    def __init__(self, text, x, y):
        self.text = text
        self.x = x
        self.y = y
        self.font = pygame.font.SysFont('calibri', 40)
        text_size = self.font.size(self.text)
        self.hitbox = pygame.Rect(x, y, text_size[0] + 40, text_size[1] + 10)
        self.is_hovered = False

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.hitbox.collidepoint(mouse_pos)

        dash_color = ACCENT_COLOR if self.is_hovered else (200, 200, 200)
        dash_width = 15 if self.is_hovered else 8
        dash_rect = pygame.Rect(self.x, self.y + 15, dash_width, 6)
        pygame.draw.rect(surface, dash_color, dash_rect)

        current_text_color = (0, 0, 0) if self.is_hovered else (100, 100, 100)
        text_surf = self.font.render(self.text, True, current_text_color)
        text_x_offset = 30 if self.is_hovered else 25
        surface.blit(text_surf, (self.x + text_x_offset, self.y))

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False

# Main Menu for the screen to stay so it keep looping
def main_menu():
    clock = pygame.time.Clock()

    buttons = [
        ModernButton("START ADVENTURE", 100, 300),
        ModernButton("LEVEL SELECT", 100, 380),
        ModernButton("CREDITS", 100, 460),
        ModernButton("QUIT", 100, 540)
    ]

    clouds = [Cloud() for _ in range(5)]

    panel_rect = pygame.Rect(600, 100, 600, 500)
    glass_panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
    glass_panel_surf.fill(PANEL_FG_COLOR)

    # Game Description on the right
    description_lines = [
        "Welcome to the seaside!",
        "",
        "Seaside Programming is an interactive puzzle",
        "game designed to teach core programming",
        "concepts and data structures.",
        "",
        "FEATURES:",
        "• Master algorithms like Sorting and BFS/DFS",
        "• Learn Object-Oriented Programming (OOP)",
        "• Fill in the blanks of real Python code",
        "• Guided by a smart AI Assistant",
        "",
        "Select 'START ADVENTURE' to begin Level 1."
    ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if buttons[0].is_clicked(event):  # Start Button
                running = False
                gamescreen.game_loop()
            if buttons[1].is_clicked(event):
                # This opens your new pixelated screen!
                selected = levelselect.level_select_loop(SCREEN)
                if selected is not None:
                    running = False
                    gamescreen.game_loop()
            if buttons[2].is_clicked(event):  # Credits Button
                credit.credits_loop(SCREEN)
            if buttons[3].is_clicked(event):  # Quit Button
                running = False

                # Drawing the cloud to thje screen
        draw_beach_gradient(SCREEN, WIDTH, HEIGHT)
        for cloud in clouds:
            cloud.update()
            cloud.draw(SCREEN)

        # Main Title
        title_text = TITLE_FONT.render("SEASIDE", True, TEXT_COLOR)
        title_text2 = TITLE_FONT.render("PROGRAMMING.", True, ACCENT_COLOR)
        subtitle = SUBTITLE_FONT.render("Learn logic by the ocean.", True, (100, 100, 100))
        SCREEN.blit(title_text, (100, 100))
        SCREEN.blit(title_text2, (100, 160))
        SCREEN.blit(subtitle, (100, 230))

        # Buttons
        for btn in buttons:
            btn.draw(SCREEN)

        # Right Panel
        SCREEN.blit(glass_panel_surf, (panel_rect.x, panel_rect.y))

        # We draw the text slightly inside the panel (padding)
        current_y = panel_rect.y + 40

        for line in description_lines:
            if line == "FEATURES:":
                rendered_text = PANEL_HEADER.render(line, True, TEXT_COLOR)
            else:
                rendered_text = PANEL_TEXT.render(line, True, TEXT_COLOR)

            # Making spacing for the features
            SCREEN.blit(rendered_text, (panel_rect.x + 40, current_y))
            current_y += 35

        pygame.display.flip()
        clock.tick(60)
    # Quit the game
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main_menu()