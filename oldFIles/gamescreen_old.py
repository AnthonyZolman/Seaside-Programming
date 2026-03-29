import pygame
import sys
import os
import threading
import io
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- Gemini API Setup ---
load_dotenv("../keys.env")
client = genai.Client(api_key=os.environ.get("API_KEY"))

# 1. Initialize Pygame
pygame.init()

# 2. Constants & Setup
WIDTH, HEIGHT = 1280, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Seaside Programming")

# Colors
BG_PANEL = (255, 255, 255)
TEXT_COLOR = (40, 40, 40)
ACCENT_COLOR = (255, 165, 0)
USER_BUBBLE = (220, 240, 255)
AI_BUBBLE = (245, 245, 245)

# Button Colors
BTN_GREEN = (46, 204, 113);
BTN_GREEN_HOVER = (39, 174, 96)
BTN_RED = (231, 76, 60);
BTN_RED_HOVER = (192, 57, 43)
BTN_BLUE = (52, 152, 219);
BTN_BLUE_HOVER = (41, 128, 185)
BTN_GRAY = (149, 165, 166);
BTN_GRAY_HOVER = (127, 140, 141)

# Fonts
try:
    UI_FONT = pygame.font.SysFont('calibri', 24, bold=True)
    CHAT_FONT = pygame.font.SysFont('calibri', 20)
    BTN_FONT = pygame.font.SysFont('calibri', 22, bold=True)
    CODE_FONT = pygame.font.SysFont('consolas', 20)
except:
    UI_FONT = pygame.font.Font(None, 32)
    CHAT_FONT = pygame.font.Font(None, 24)
    BTN_FONT = pygame.font.Font(None, 28)
    CODE_FONT = pygame.font.Font(None, 24)

# --- Global State for Chat ---
chat_log = [{"sender": "AI", "text": "I can now see your full script and line numbers. How can I help?"}]
is_waiting_for_gemini = False


def fetch_gemini_response(pil_img, query, full_script_text):
    global is_waiting_for_gemini, chat_log
    try:
        pil_img = pil_img.resize((640, 360), Image.Resampling.LANCZOS)
        img_byte_arr = BytesIO()
        pil_img.save(img_byte_arr, format='JPEG', quality=80)
        image_bytes = img_byte_arr.getvalue()

        prompt_context = (
            f"Context: The user is coding in a Python editor.\n"
            f"Full Script Content (Raw Text):\n{full_script_text}\n\n"
            f"User Question: {query}"
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"), prompt_context]
        )
        chat_log.append({"sender": "AI", "text": response.text})
    except Exception as e:
        chat_log.append({"sender": "AI", "text": f"API Error: {e}"})
    finally:
        is_waiting_for_gemini = False


def draw_beach_gradient(surface, width, height):
    gradient = pygame.Surface((1, 3))
    gradient.set_at((0, 0), (135, 206, 235))
    gradient.set_at((0, 1), (176, 224, 230))
    gradient.set_at((0, 2), (250, 235, 215))
    gradient = pygame.transform.smoothscale(gradient, (width, height))
    surface.blit(gradient, (0, 0))


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
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered


class TextInputBox:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (220, 220, 220)
        self.color_active = ACCENT_COLOR
        self.color = self.color_inactive
        self.text = ""
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                msg = self.text;
                self.text = "";
                return msg
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < 70: self.text += event.unicode
        return None

    def draw(self, surface):
        pygame.draw.rect(surface, (250, 250, 250), self.rect, border_radius=10)
        pygame.draw.rect(surface, self.color, self.rect, 2, border_radius=10)
        text_surface = CHAT_FONT.render(self.text, True, TEXT_COLOR)
        cursor = "|" if self.active and pygame.time.get_ticks() % 1000 < 500 else ""
        surface.blit(text_surface, (self.rect.x + 15, self.rect.y + 10))
        surface.blit(CHAT_FONT.render(cursor, True, self.color),
                     (self.rect.x + 15 + text_surface.get_width(), self.rect.y + 10))


def game_loop():
    global is_waiting_for_gemini, chat_log
    clock = pygame.time.Clock()

    left_x, left_y, left_w, left_h = 20, 20, 800, 600
    right_x, right_y, right_w, right_h = left_x + left_w + 20, 20, WIDTH - (left_x + left_w + 20) - 20, 600

    chat_panel_rect = pygame.Rect(right_x, right_y, right_w, right_h)
    script_panel_rect = pygame.Rect(left_x + 50, left_y + 50, left_w - 100, left_h - 100)

    # --- State ---
    scroll_y = 0
    line_height = 24
    is_script_open = False

    try:
        with open("../Scripts/mergeSort.py", "r") as f:
            python_code = [line.rstrip('\n') for line in f]
    except:
        python_code = ["# Type your code here!"]

    cursor_line = len(python_code) - 1

    chat_input_box = TextInputBox(right_x, left_y + left_h + 20, right_w, 45)
    code_button = GameButton(" OPEN CODE", left_x, left_y + left_h + 20, 180, 45, BTN_BLUE, BTN_BLUE_HOVER)
    run_button = GameButton(" RUN CODE", left_x, left_y + left_h + 20, 160, 45, BTN_GREEN, BTN_GREEN_HOVER)
    clear_button = GameButton(" CLEAR", left_x + 180, left_y + left_h + 20, 120, 45, BTN_RED, BTN_RED_HOVER)
    hide_button = GameButton(" HIDE", left_x + 320, left_y + left_h + 20, 100, 45, BTN_GRAY, BTN_GRAY_HOVER)

    try:
        bg_one = pygame.image.load('../assets/Grizzhacks Background.png').convert_alpha()
        bg_one = pygame.transform.smoothscale(bg_one, (left_w, left_h))
    except:
        bg_one = None

    pygame.key.start_text_input()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEWHEEL and is_script_open:
                scroll_y += event.y * 30
                max_scroll = min(0, -(len(python_code) * line_height - (script_panel_rect.height - 100)))
                if scroll_y < max_scroll: scroll_y = max_scroll
                if scroll_y > 0: scroll_y = 0

            new_chat_message = chat_input_box.handle_event(event)
            if new_chat_message and not is_waiting_for_gemini:
                chat_log.append({"sender": "User", "text": new_chat_message})
                is_waiting_for_gemini = True
                raw_str = pygame.image.tobytes(SCREEN, "RGB")
                pil_img = Image.frombytes("RGB", SCREEN.get_size(), raw_str)
                full_script_str = "\n".join(python_code)
                threading.Thread(target=fetch_gemini_response,
                                 args=(pil_img, new_chat_message, full_script_str)).start()

            if not is_script_open:
                if code_button.is_clicked(event): is_script_open = True
            else:
                if not chat_input_box.active:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_BACKSPACE:
                            if len(python_code[cursor_line]) > 0:
                                python_code[cursor_line] = python_code[cursor_line][:-1]
                            elif cursor_line > 0:
                                old_line = python_code.pop(cursor_line)
                                cursor_line -= 1
                                python_code[cursor_line] += old_line
                        elif event.key == pygame.K_RETURN:
                            python_code.insert(cursor_line + 1, "")
                            cursor_line += 1
                        elif event.key == pygame.K_UP:
                            cursor_line = max(0, cursor_line - 1)
                        elif event.key == pygame.K_DOWN:
                            cursor_line = min(len(python_code) - 1, cursor_line + 1)
                    if event.type == pygame.TEXTINPUT:
                        python_code[cursor_line] += event.text

                if run_button.is_clicked(event):
                    full_code = "\n".join(python_code)
                    output_buffer = io.StringIO()
                    old_stdout = sys.stdout
                    sys.stdout = output_buffer
                    try:
                        exec(full_code, {})
                        sys_output = output_buffer.getvalue()
                        chat_log.append({"sender": "AI",
                                         "text": f"[SYSTEM OUTPUT]:\n{sys_output}" if sys_output else "[SYSTEM]: Success."})
                    except Exception as e:
                        chat_log.append({"sender": "AI", "text": f"[PYTHON ERROR]:\n{str(e)}"})
                    finally:
                        sys.stdout = old_stdout

                if clear_button.is_clicked(event):
                    python_code = [""];
                    cursor_line = 0;
                    scroll_y = 0
                if hide_button.is_clicked(event):
                    is_script_open = False

        # --- DRAWING ---
        draw_beach_gradient(SCREEN, WIDTH, HEIGHT)
        if bg_one:
            SCREEN.blit(bg_one, (left_x, left_y))
            pygame.draw.rect(SCREEN, (200, 200, 200), (left_x, left_y, left_w, left_h), 2)

        if not is_script_open:
            code_button.draw(SCREEN)
        else:
            run_button.draw(SCREEN)
            clear_button.draw(SCREEN)
            hide_button.draw(SCREEN)

            overlay = pygame.Surface((left_w, left_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            SCREEN.blit(overlay, (left_x, left_y))

            pygame.draw.rect(SCREEN, (30, 30, 35), script_panel_rect, border_radius=12)
            pygame.draw.rect(SCREEN, (60, 60, 70), script_panel_rect, 2, border_radius=12)
            SCREEN.blit(UI_FONT.render("Level Script Editor", True, ACCENT_COLOR),
                        (script_panel_rect.x + 30, script_panel_rect.y + 20))

            # --- CLIPPED CODE AREA WITH LINE NUMBERS ---
            view_rect = pygame.Rect(script_panel_rect.x + 30, script_panel_rect.y + 65,
                                    script_panel_rect.width - 60, script_panel_rect.height - 95)

            try:
                editor_surface = SCREEN.subsurface(view_rect)
                line_number_w = 45  # Gutter width

                for i, line in enumerate(python_code):
                    y_pos = (i * line_height) + scroll_y
                    if -line_height < y_pos < view_rect.height:
                        # Draw Line Numbers
                        num_surf = CODE_FONT.render(f"{i + 1:2}", True, (100, 100, 110))
                        editor_surface.blit(num_surf, (0, y_pos))

                        # Draw Code
                        txt = CODE_FONT.render(line, True, (230, 230, 230))
                        editor_surface.blit(txt, (line_number_w, y_pos))

                        # Draw Cursor
                        if i == cursor_line and not chat_input_box.active:
                            if pygame.time.get_ticks() % 1000 < 500:
                                cx = line_number_w + CODE_FONT.size(line)[0]
                                pygame.draw.line(editor_surface, (255, 255, 255), (cx, y_pos + 2), (cx, y_pos + 20), 2)
            except:
                pass

        # --- DRAW CHAT ---
        pygame.draw.rect(SCREEN, BG_PANEL, chat_panel_rect, border_radius=12)
        SCREEN.blit(UI_FONT.render("Gemini Assistant", True, ACCENT_COLOR), (right_x + 20, right_y + 20))

        current_y = chat_panel_rect.bottom - 20
        display_log = list(chat_log)
        if is_waiting_for_gemini: display_log.append({"sender": "AI", "text": "Typing..."})

        for message in reversed(display_log):
            wrapped_lines = wrap_text(message["text"], CHAT_FONT, right_w - 90)
            bubble_h = len(wrapped_lines) * 25 + 20
            current_y -= bubble_h
            if current_y < right_y + 60: break

            bx = right_x + 60 if message["sender"] == "User" else right_x + 20
            pygame.draw.rect(SCREEN, (USER_BUBBLE if message["sender"] == "User" else AI_BUBBLE),
                             (bx, current_y, right_w - 80, bubble_h), border_radius=12)
            for i, line in enumerate(wrapped_lines):
                SCREEN.blit(CHAT_FONT.render(line, True, TEXT_COLOR), (bx + 15, current_y + 10 + (i * 25)))

        chat_input_box.draw(SCREEN)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    game_loop()