import pygame
import sys

# --- Constants ---
WIDTH, HEIGHT = 1280, 720
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
ACCENT_COLOR = (255, 165, 0)
BTN_RED = (231, 76, 60)
BTN_RED_HOVER = (192, 57, 43)


# --- Beach Gradient Helper ---
def draw_beach_gradient(surface, width, height):
    gradient = pygame.Surface((1, 3))
    gradient.set_at((0, 0), (135, 206, 235))
    gradient.set_at((0, 1), (176, 224, 230))
    gradient.set_at((0, 2), (250, 235, 215))
    gradient = pygame.transform.smoothscale(gradient, (width, height))
    surface.blit(gradient, (0, 0))


def credits_loop(screen):
    clock = pygame.time.Clock()

    # --- Fonts ---
    try:
        title_font = pygame.font.SysFont('calibri', 48, bold=True)
        text_font = pygame.font.SysFont('calibri', 28)
        btn_font = pygame.font.SysFont('calibri', 24, bold=True)
    except:
        title_font = pygame.font.Font(None, 64)
        text_font = pygame.font.Font(None, 36)
        btn_font = pygame.font.Font(None, 32)

    # --- Sprite Loading ---
    sprite_names = ["assets/Anthony.png", "assets/Joshua.png", "assets/Minh.png"]
    sprites = []
    for name in sprite_names:
        try:
            # .convert_alpha() is essential for PNG transparency
            img = pygame.image.load(name).convert_alpha()
            # Optional: Resize them if they are massive
            img = pygame.transform.scale(img, (120, 120))
            sprites.append(img)
        except:
            # Fallback if image is missing
            surf = pygame.Surface((100, 100))
            surf.fill((200, 0, 0))
            sprites.append(surf)

    # --- The Credits Script ---
    credits_text = [
        ("SEASIDE PROGRAMMING", title_font, ACCENT_COLOR),
        ("", text_font, BLACK),
        ("Lead Developers", title_font, WHITE),
        ("Minh Phan & Anthony Zolman", text_font, BLACK),
        ("", text_font, BLACK),
        ("AI Integration", title_font, WHITE),
        ("Powered by Google Gemini", text_font, BLACK),
        ("Flash-Lite Optimization", text_font, BLACK),
        ("", text_font, BLACK),
        ("Art, Assets and Sound Design", title_font, WHITE),
        ("Josh Pascariu", text_font, BLACK),
        ("", text_font, BLACK),
        ("Special Thanks", title_font, WHITE),
        ("GrizzHack8", text_font, BLACK),
        ("https://github.com/AnthonyZolman/Seaside-Programming", text_font, BLACK)
    ]

    # --- Positioning Logic ---
    current_y = HEIGHT + 50
    line_spacing = 45
    credit_items = []

    # 1. Process Text Lines
    for text, font, color in credits_text:
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(WIDTH // 2, current_y))
        credit_items.append({"surf": surf, "rect": rect, "y_float": float(current_y)})
        current_y += line_spacing if text == "" else line_spacing + 10

    # 2. Process Sprites (Horizontal Row)
    current_y += 80  # Space between last text and sprites
    sprite_spacing = 180
    total_width = (len(sprites) - 1) * sprite_spacing
    start_x = (WIDTH - total_width) // 2

    sprite_list = []
    for i, img in enumerate(sprites):
        pos_x = start_x + (i * sprite_spacing)
        rect = img.get_rect(center=(pos_x, current_y))
        sprite_list.append({"surf": img, "rect": rect, "y_float": float(current_y)})

    # Back Button
    back_btn_rect = pygame.Rect(40, 40, 120, 45)

    running = True
    scroll_speed = 1.2

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn_rect.collidepoint(event.pos):
                    running = False

                    # --- Update Logic ---
        # Move text
        for item in credit_items:
            item["y_float"] -= scroll_speed
            item["rect"].centery = int(item["y_float"])

        # Move sprites
        for item in sprite_list:
            item["y_float"] -= scroll_speed
            item["rect"].centery = int(item["y_float"])

        # End if the last sprite has left the top of the screen
        if sprite_list[-1]["rect"].bottom < -50:
            running = False

        # --- Drawing ---
        draw_beach_gradient(screen, WIDTH, HEIGHT)

        for item in credit_items:
            screen.blit(item["surf"], item["rect"])

        for item in sprite_list:
            screen.blit(item["surf"], item["rect"])

        # Draw Back Button
        mouse_pos = pygame.mouse.get_pos()
        btn_color = BTN_RED_HOVER if back_btn_rect.collidepoint(mouse_pos) else BTN_RED
        pygame.draw.rect(screen, btn_color, back_btn_rect, border_radius=8)
        back_text = btn_font.render("BACK", True, WHITE)
        screen.blit(back_text, back_text.get_rect(center=back_btn_rect.center))

        pygame.display.flip()
        clock.tick(60)


# Main Entry Point (for testing)
if __name__ == "__main__":
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Credits")
    credits_loop(win)
    pygame.quit()