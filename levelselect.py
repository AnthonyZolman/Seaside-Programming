import pygame
import sys
import os

# --- Constants ---
WIDTH, HEIGHT = 1280, 720
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
# Retro Seaside Palette
BTN_LOCKED = (100, 110, 120)  # Dark gray for locked levels
BTN_UNLOCKED = (46, 204, 113)  # Green for playable levels
BTN_HOVER = (39, 174, 96)  # Darker green for hover
BORDER_COLOR = (20, 50, 20)  # Chunky dark border
# --- Add these to the top of levelselect.py ---
BTN_RED = (231, 76, 60)
BTN_RED_HOVER = (192, 57, 43)


def draw_beach_gradient(surface, width, height):
    gradient = pygame.Surface((1, 3))
    gradient.set_at((0, 0), (135, 206, 235))
    gradient.set_at((0, 1), (176, 224, 230))
    gradient.set_at((0, 2), (250, 235, 215))
    gradient = pygame.transform.smoothscale(gradient, (width, height))
    surface.blit(gradient, (0, 0))


# --- The Pixel Text Trick ---
def render_pixel_text(text, color, scale=3):
    """Renders small text and scales it up to make it chunky and pixelated."""
    # Use a basic system font, size 12
    base_font = pygame.font.SysFont('courier new', 12, bold=True)
    # False = turn off anti-aliasing (smoothing) so the edges stay sharp!
    small_surf = base_font.render(text, False, color)

    # Scale it up
    new_width = small_surf.get_width() * scale
    new_height = small_surf.get_height() * scale
    pixel_surf = pygame.transform.scale(small_surf, (new_width, new_height))
    return pixel_surf


# --- OOP Class: Pixel Button ---
class PixelButton:
    def __init__(self, x, y, w, h, level_num, title, is_locked=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.level_num = level_num
        self.title = title  # <--- New variable for the topic
        self.is_locked = is_locked
        self.is_hovered = False

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mouse_pos)

        if self.is_locked:
            fill_color = BTN_LOCKED
        else:
            fill_color = BTN_HOVER if self.is_hovered else BTN_UNLOCKED

        # Draw Chunky Border
        pygame.draw.rect(surface, BORDER_COLOR, (self.rect.x - 4, self.rect.y - 4, self.rect.w + 8, self.rect.h + 8))
        pygame.draw.rect(surface, fill_color, self.rect)

        # Draw Text
        if self.is_locked:
            text_surf = render_pixel_text("LOCKED", (200, 200, 200), scale=2)
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)
        else:
            # Draw "LEVEL X" small at the top
            num_surf = render_pixel_text(f"LEVEL {self.level_num}", WHITE, scale=1)
            # Draw the Title larger in the middle
            title_surf = render_pixel_text(self.title, WHITE, scale=2)

            num_rect = num_surf.get_rect(midtop=(self.rect.centerx, self.rect.y + 15))
            title_rect = title_surf.get_rect(center=(self.rect.centerx, self.rect.centery + 10))

            surface.blit(num_surf, num_rect)
            surface.blit(title_surf, title_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and not self.is_locked:
                return True
        return False

# --- NEW: Save File Helper ---
def get_unlocked_level():
    """Reads the save file to see how far the player has gotten."""
    if os.path.exists("save.txt"):
        try:
            with open("save.txt", "r") as f:
                return int(f.read().strip())
        except:
            return 1 # If the file is corrupted, default to level 1
    return 1 # If no save file exists yet, default to level 1

def level_select_loop(screen):
    clock = pygame.time.Clock()

    # --- UPDATED: 6 Levels with Grid Math ---
    level_data = [
        "SORTING", "KNAPSACK", "DFS/BFS",
        "ARRAYS", "LOGIC", "OBJECTS"
    ]

    buttons = []
    # Starting position for the grid
    start_x = 240
    start_y = 200  # Moved up to make room for two rows
    spacing_x = 300
    spacing_y = 220  # Gap between top and bottom row

    unlocked_max = get_unlocked_level()
    for i in range(6):
        # Grid Math:
        # row 0 for first three, row 1 for next three
        row = i // 3
        # col 0, 1, 2 for each row
        col = i % 3

        x = start_x + (col * spacing_x)
        y = start_y + (row * spacing_y)

        # --- 2. Check if this button should be locked ---
        # If the level number (i + 1) is greater than their progress, lock it!
        is_locked = True if (i + 1) > unlocked_max else False

        buttons.append(PixelButton(x, y, 200, 100, i + 1, level_data[i], is_locked))
    # Back Button
    back_btn_rect = pygame.Rect(40, 40, 120, 45)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Check Back Button
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn_rect.collidepoint(event.pos):
                    return None  # Return None means "Go back to menu"

            # Check Level Buttons
            for btn in buttons:
                if btn.is_clicked(event):
                    return btn.level_num  # Return the level number clicked!

        # --- Drawing ---
        draw_beach_gradient(screen, WIDTH, HEIGHT)

        # Title
        title_surf = render_pixel_text("SELECT LEVEL", (255, 165, 0), scale=5)
        title_shadow = render_pixel_text("SELECT LEVEL", BORDER_COLOR, scale=5)

        # Draw shadow then text for a retro pop
        screen.blit(title_shadow, title_shadow.get_rect(center=(WIDTH // 2 + 4, 84)))
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 80)))

        # Draw Buttons
        for btn in buttons:
            btn.draw(screen)

        # Draw Back Button
        mouse_pos = pygame.mouse.get_pos()
        btn_color = BTN_RED_HOVER if back_btn_rect.collidepoint(mouse_pos) else BTN_RED
        pygame.draw.rect(screen, BORDER_COLOR,
                         (back_btn_rect.x - 2, back_btn_rect.y - 2, back_btn_rect.w + 4, back_btn_rect.h + 4))
        pygame.draw.rect(screen, btn_color, back_btn_rect)

        back_text = render_pixel_text("BACK", WHITE, scale=2)
        screen.blit(back_text, back_text.get_rect(center=back_btn_rect.center))

        pygame.display.flip()
        clock.tick(60)
