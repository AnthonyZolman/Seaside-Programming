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

    # Fonts
    try:
        title_font = pygame.font.SysFont('calibri', 48, bold=True)
        text_font = pygame.font.SysFont('calibri', 28)
        btn_font = pygame.font.SysFont('calibri', 24, bold=True)
    except:
        title_font = pygame.font.Font(None, 64)
        text_font = pygame.font.Font(None, 36)
        btn_font = pygame.font.Font(None, 32)

    # --- The Credits Script ---
    # Format: (Text String, Font, Color)
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
        ("Art & Assets", title_font, WHITE),
        ("Josh Pascariu", text_font, BLACK),
        ("", text_font, BLACK),
        ("Special Thanks", title_font, WHITE),
        ("GrizzHack8", text_font, BLACK),
        ("https://github.com/AnthonyZolman/Seaside-Programming/tree/main", text_font, BLACK)
    ]

    # Starting Y position (starts just off the bottom of the screen)
    start_y = HEIGHT + 50
    line_spacing = 45

    # Pre-render all the text lines and calculate their starting rectangles
    credit_lines = []
    current_y = start_y

    for text, font, color in credits_text:
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(WIDTH // 2, current_y))
        # We use a float for Y to allow for super smooth, slow scrolling
        credit_lines.append({"surf": surf, "rect": rect, "y_float": float(current_y)})
        current_y += line_spacing if text == "" else line_spacing + 10

        # Back Button Setup
    back_btn_rect = pygame.Rect(40, 40, 120, 45)

    running = True
    scroll_speed = 1.0  # Pixels per frame. Increase this to make it scroll faster!

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn_rect.collidepoint(event.pos):
                    running = False  # Break the loop to return to minhmain.py!

        # --- Update Logic ---
        # Move every line up the screen
        for line in credit_lines:
            line["y_float"] -= scroll_speed
            line["rect"].centery = int(line["y_float"])

        if credit_lines[-1]["rect"].bottom < -50:
            running = False

        # --- Drawing ---
        draw_beach_gradient(screen, WIDTH, HEIGHT)

        # Draw the scrolling text
        for line in credit_lines:
            screen.blit(line["surf"], line["rect"])

        # Draw Back Button (always on top)
        mouse_pos = pygame.mouse.get_pos()
        btn_color = BTN_RED_HOVER if back_btn_rect.collidepoint(mouse_pos) else BTN_RED
        pygame.draw.rect(screen, btn_color, back_btn_rect, border_radius=8)
        back_text = btn_font.render("BACK", True, WHITE)
        screen.blit(back_text, back_text.get_rect(center=back_btn_rect.center))

        pygame.display.flip()
        clock.tick(60)