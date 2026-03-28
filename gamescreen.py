import pygame
import sys
import os
import threading
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- Gemini API Setup ---
load_dotenv("keys.env")
client = genai.Client(api_key=os.environ.get("API_KEY"))

# 1. Initialize Pygame
pygame.init()

# 2. Constants & Setup
WIDTH, HEIGHT = 1280, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Seaside Programming - IDE Layout")

# Colors
BG_MAIN = (230, 235, 240)
BG_PANEL = (255, 255, 255)
TEXT_COLOR = (40, 40, 40)
ACCENT_COLOR = (255, 165, 0)
USER_BUBBLE = (220, 240, 255)
AI_BUBBLE = (245, 245, 245)

# Button Colors
BTN_GREEN = (46, 204, 113)
BTN_GREEN_HOVER = (39, 174, 96)
BTN_RED = (231, 76, 60)
BTN_RED_HOVER = (192, 57, 43)
BTN_BLUE = (52, 152, 219)
BTN_BLUE_HOVER = (41, 128, 185)
# NEW: Gray color for the HIDE button
BTN_GRAY = (149, 165, 166)
BTN_GRAY_HOVER = (127, 140, 141)

# Fonts
try:
    UI_FONT = pygame.font.SysFont('calibri', 24, bold=True)
    CHAT_FONT = pygame.font.SysFont('calibri', 20)
    BTN_FONT = pygame.font.SysFont('calibri', 22, bold=True)
    CODE_FONT = pygame.font.SysFont('consolas', 22)
except:
    UI_FONT = pygame.font.Font(None, 32)
    CHAT_FONT = pygame.font.Font(None, 24)
    BTN_FONT = pygame.font.Font(None, 28)
    CODE_FONT = pygame.font.Font(None, 26)

# --- Global State for Chat ---
chat_log = [
    {"sender": "AI",
     "text": "Welcome to Seaside Programming! I am Gemini. I can see your screen, what are we working on?"}
]
is_waiting_for_gemini = False


# --- Backend Function: The API Thread ---
def fetch_gemini_response(pil_img, query):
    global is_waiting_for_gemini, chat_log
    try:
        img_byte_arr = BytesIO()
        pil_img.save(img_byte_arr, format='PNG')

        prompt_context = (
            f"Context: The user is looking at the game screen on the left. "
            f"Answer whatever question they may have even if the image does not match what is being asked. "
            f"Question: {query}"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=img_byte_arr.getvalue(), mime_type="image/png"),
                prompt_context
            ]
        )
        chat_log.append({"sender": "AI", "text": response.text})
    except Exception as e:
        chat_log.append({"sender": "AI", "text": f"API Error: {e}"})
    finally:
        is_waiting_for_gemini = False

    # --- Background Helper: Beach Gradient ---


def draw_beach_gradient(surface, width, height):
    gradient = pygame.Surface((1, 3))
    gradient.set_at((0, 0), (135, 206, 235))
    gradient.set_at((0, 1), (176, 224, 230))
    gradient.set_at((0, 2), (250, 235, 215))
    gradient = pygame.transform.smoothscale(gradient, (width, height))
    surface.blit(gradient, (0, 0))


# --- BULLETPROOF Helper Function: Text Wrapping ---
def wrap_text(text, font, max_width):
    text = text.replace('**', '').replace('*', '')
    raw_paragraphs = text.split('\n')
    final_lines = []
    for paragraph in raw_paragraphs:
        if paragraph.strip() == "":
            final_lines.append(" ")
            continue
        words = paragraph.split(' ')
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                final_lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            final_lines.append(' '.join(current_line))
    return final_lines


# --- OOP Class: Standard Button ---
class GameButton:
    def __init__(self, text, x, y, w, h, base_color, hover_color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.base_color = base_color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        current_color = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=8)
        text_surf = BTN_FONT.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False


# --- OOP Class: Text Input Box ---
class TextInputBox:
    def __init__(self, x, y, w, h, is_code=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (220, 220, 220)
        self.color_active = ACCENT_COLOR
        self.color = self.color_inactive
        self.text = ""
        self.active = False
        self.font = CODE_FONT if is_code else CHAT_FONT

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.color = self.color_active
            else:
                self.active = False
                self.color = self.color_inactive

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                message = self.text
                self.text = ""
                return message
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < 70:
                    self.text += event.unicode
        return None

    def draw(self, surface):
        pygame.draw.rect(surface, (250, 250, 250), self.rect, border_radius=10)
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=10)
        text_surface = self.font.render(self.text, True, TEXT_COLOR)

        cursor = "|" if self.active and pygame.time.get_ticks() % 1000 < 500 else ""
        cursor_surface = self.font.render(cursor, True, self.color)

        surface.blit(text_surface, (self.rect.x + 15, self.rect.y + 10))
        surface.blit(cursor_surface, (self.rect.x + 15 + text_surface.get_width(), self.rect.y + 10))


# --- The Main Game Loop ---
def game_loop():
    global is_waiting_for_gemini, chat_log
    clock = pygame.time.Clock()

    # Layout Math
    left_x, left_y = 20, 20
    left_w, left_h = 800, 600

    right_x = left_x + left_w + 20
    right_y = 20
    right_w = WIDTH - right_x - 20
    right_h = 600
    chat_panel_rect = pygame.Rect(right_x, right_y, right_w, right_h)

    is_script_open = False
    script_panel_rect = pygame.Rect(left_x + 50, left_y + 50, left_w - 100, left_h - 100)

    blank_box = TextInputBox(script_panel_rect.x + 230, script_panel_rect.y + 200, 250, 40, is_code=True)
    chat_input_box = TextInputBox(right_x, left_y + left_h + 20, right_w, 45)

    # --- UPDATED BUTTONS ---
    code_button = GameButton(" CODE", left_x, left_y + left_h + 20, 180, 45, BTN_BLUE, BTN_BLUE_HOVER)
    run_button = GameButton("RUN CODE", left_x, left_y + left_h + 20, 160, 45, BTN_GREEN, BTN_GREEN_HOVER)
    clear_button = GameButton("CLEAR", left_x + 180, left_y + left_h + 20, 120, 45, BTN_RED, BTN_RED_HOVER)
    # NEW: The Hide Button sits next to the Clear Button
    hide_button = GameButton("HIDE", left_x + 320, left_y + left_h + 20, 100, 45, BTN_GRAY, BTN_GRAY_HOVER)

    try:
        bg_one = pygame.image.load('assets/Grizzhacks Background.png').convert_alpha()
        bg_one = pygame.transform.smoothscale(bg_one, (left_w, left_h))
    except (FileNotFoundError, pygame.error):
        bg_one = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # --- Chat Input Handling ---
            new_chat_message = chat_input_box.handle_event(event)
            if new_chat_message and not is_waiting_for_gemini:
                chat_log.append({"sender": "User", "text": new_chat_message})
                is_waiting_for_gemini = True
                raw_str = pygame.image.tobytes(SCREEN, "RGB")
                pil_img = Image.frombytes("RGB", SCREEN.get_size(), raw_str)
                threading.Thread(target=fetch_gemini_response, args=(pil_img, new_chat_message)).start()

            # --- Toggle State Handling ---
            if not is_script_open:
                if code_button.is_clicked(event):
                    is_script_open = True
            else:
                blank_box.handle_event(event)

                # RUN NO LONGER CLOSES THE SCRIPT
                if run_button.is_clicked(event):
                    print(f"User submitted code: {blank_box.text}")
                    if not is_waiting_for_gemini:
                        msg = f"I wrote '{blank_box.text}' to swap the array values. Is that correct?"
                        chat_log.append({"sender": "User", "text": msg})
                        is_waiting_for_gemini = True
                        raw_str = pygame.image.tobytes(SCREEN, "RGB")
                        pil_img = Image.frombytes("RGB", SCREEN.get_size(), raw_str)
                        threading.Thread(target=fetch_gemini_response, args=(pil_img, msg)).start()

                if clear_button.is_clicked(event):
                    blank_box.text = ""

                    # NEW: HIDE BUTTON CLOSES THE SCRIPT
                if hide_button.is_clicked(event):
                    is_script_open = False

        # --- DRAWING ---
        draw_beach_gradient(SCREEN, WIDTH, HEIGHT)

        # Draw the Left Panel (Game Background)
        if bg_one:
            pygame.draw.rect(SCREEN, (210, 215, 220), (left_x + 4, left_y + 4, left_w, left_h), border_radius=12)
            SCREEN.blit(bg_one, (left_x, left_y))
            pygame.draw.rect(SCREEN, (200, 200, 200), (left_x, left_y, left_w, left_h), 2)
        else:
            pygame.draw.rect(SCREEN, BG_PANEL, (left_x, left_y, left_w, left_h), border_radius=12)

        # --- DRAW UI BASED ON STATE ---
        if not is_script_open:
            code_button.draw(SCREEN)
        else:
            run_button.draw(SCREEN)
            clear_button.draw(SCREEN)
            # NEW: Draw the hide button
            hide_button.draw(SCREEN)

            overlay = pygame.Surface((left_w, left_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            SCREEN.blit(overlay, (left_x, left_y))

            pygame.draw.rect(SCREEN, (30, 30, 35), script_panel_rect, border_radius=12)
            pygame.draw.rect(SCREEN, (60, 60, 70), script_panel_rect, 2, border_radius=12)

            title = UI_FONT.render("Level 1: Sorting Arrays", True, ACCENT_COLOR)
            SCREEN.blit(title, (script_panel_rect.x + 30, script_panel_rect.y + 30))

            # line1 = CODE_FONT.render("def bubble_sort(arr):", True, (200, 200, 200))
            # line2 = CODE_FONT.render("    for i in range(len(arr) - 1):", True, (200, 200, 200))
            # line3 = CODE_FONT.render("        if arr[i] > arr[i+1]:", True, (200, 200, 200))
            # line4 = CODE_FONT.render("            # Swap the variables below", True, (100, 200, 100))
            # line5 = CODE_FONT.render("            arr[i], arr[i+1] =", True, (200, 200, 200))
            #
            # SCREEN.blit(line1, (script_panel_rect.x + 30, script_panel_rect.y + 80))
            # SCREEN.blit(line2, (script_panel_rect.x + 30, script_panel_rect.y + 110))
            # SCREEN.blit(line3, (script_panel_rect.x + 30, script_panel_rect.y + 140))
            # SCREEN.blit(line4, (script_panel_rect.x + 30, script_panel_rect.y + 170))
            # SCREEN.blit(line5, (script_panel_rect.x + 30, script_panel_rect.y + 208))

            blank_box.draw(SCREEN)

        # Draw the Chat Panel
        pygame.draw.rect(SCREEN, (210, 215, 220), (right_x + 4, right_y + 4, right_w, right_h), border_radius=12)
        pygame.draw.rect(SCREEN, BG_PANEL, chat_panel_rect, border_radius=12)

        header_surf = UI_FONT.render("Gemini Assistant", True, ACCENT_COLOR)
        SCREEN.blit(header_surf, (right_x + 20, right_y + 20))
        pygame.draw.line(SCREEN, (235, 235, 235), (right_x + 20, right_y + 50), (right_x + right_w - 20, right_y + 50),
                         2)

        current_y = chat_panel_rect.bottom - 20

        display_log = list(chat_log)
        if is_waiting_for_gemini:
            display_log.append({"sender": "AI", "text": "Typing..."})

        for message in reversed(display_log):
            wrapped_lines = wrap_text(message["text"], CHAT_FONT, right_w - 90)
            bubble_height = len(wrapped_lines) * 25 + 20
            current_y -= bubble_height

            if current_y < right_y + 60:
                break

            if message["sender"] == "User":
                bubble_color = USER_BUBBLE
                bubble_x = right_x + 60
            else:
                bubble_color = AI_BUBBLE
                bubble_x = right_x + 20

            bubble_rect = pygame.Rect(bubble_x, current_y, right_w - 80, bubble_height)
            pygame.draw.rect(SCREEN, bubble_color, bubble_rect, border_radius=12)

            for i, line in enumerate(wrapped_lines):
                text_surf = CHAT_FONT.render(line, True, TEXT_COLOR)
                SCREEN.blit(text_surf, (bubble_x + 15, current_y + 10 + (i * 25)))

        chat_input_box.draw(SCREEN)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    game_loop()