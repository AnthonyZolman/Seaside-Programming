import os
import threading
import sys
import io
import pygame
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- Configuration & Constants ---
load_dotenv("keys.env")

COLORS = {
    "WHITE": (255, 255, 255),
    "BLACK": (20, 20, 20),
    "SIDEBAR_BG": (245, 245, 245),
    "CODE_BG": (30, 31, 28),
    "CODE_TEXT": (230, 230, 230),
    "ACCENT": (0, 150, 0),
    "INACTIVE": (150, 150, 150),
    "CURSOR": (255, 255, 255)
}

WIDTH, HEIGHT = 1280, 720
SIDEBAR_WIDTH = 400
CODE_WIN_WIDTH = 450
CODE_WIN_RECT = pygame.Rect(WIDTH - SIDEBAR_WIDTH - CODE_WIN_WIDTH, 0, CODE_WIN_WIDTH, HEIGHT)
SIDEBAR_RECT = pygame.Rect(WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)


class GeminiApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Seaside Editor: Runtime Python & Gemini")

        # --- FIXED LINE HERE ---
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("Consolas", 18)

        # API Client
        self.client = genai.Client(api_key=os.environ.get("API_KEY"))

        # State Management
        self.running = True
        self.is_loading = False
        self.focus = "chat"  # "chat" or "code"

        self.user_query = ""
        self.ai_response = "F5: Run Code | Click windows to switch focus."

        # Code Editor State
        self.python_code = ["# F5 to run this script", "print('Hello from the editor!')", "x = 10",
                            "print(f'Value is {x}')"]
        self.cursor_line = len(self.python_code) - 1

        # UI Elements
        self.input_rect = pygame.Rect(SIDEBAR_RECT.x + 20, HEIGHT - 60, SIDEBAR_WIDTH - 40, 40)
        self.bg_surface = self._load_background()

    def _load_background(self):
        try:
            return pygame.image.load('assets/bg_one.png').convert_alpha()
        except:
            surf = pygame.Surface((WIDTH - SIDEBAR_WIDTH - CODE_WIN_WIDTH, HEIGHT))
            surf.fill((40, 44, 52))
            return surf

    def _execute_python_code(self):
        """Runs the code currently in the editor and captures output."""
        full_code = "\n".join(self.python_code)
        output_buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer

        try:
            # We use an empty dict for globals/locals to keep it sandboxed
            exec(full_code, {})
            result = output_buffer.getvalue()
            self.ai_response = f"[SYSTEM OUTPUT]:\n{result}" if result else "[SYSTEM]: Code executed successfully."
        except Exception as e:
            self.ai_response = f"[PYTHON ERROR]:\n{str(e)}"
        finally:
            sys.stdout = old_stdout

    def _async_ai_call(self, image_bytes, query):
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    f"Context: Take a look at the image of the code and of the "
                    f"the background and answer the user's question to the best of your"
                    f"ability. Question: {query}"
                ]
            )
            self.ai_response = response.text
        except Exception as e:
            self.ai_response = f"Error: {str(e)}"
        finally:
            self.is_loading = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if CODE_WIN_RECT.collidepoint(event.pos):
                    self.focus = "code"
                elif self.input_rect.collidepoint(event.pos):
                    self.focus = "chat"
                else:
                    self.focus = None

            if event.type == pygame.KEYDOWN:
                # Global shortcut to run code
                if event.key == pygame.K_F5:
                    self._execute_python_code()

                # Editor Logic
                if self.focus == "code":
                    if event.key == pygame.K_BACKSPACE:
                        if len(self.python_code[self.cursor_line]) > 0:
                            self.python_code[self.cursor_line] = self.python_code[self.cursor_line][:-1]
                        elif self.cursor_line > 0:
                            old_line = self.python_code.pop(self.cursor_line)
                            self.cursor_line -= 1
                            self.python_code[self.cursor_line] += old_line
                    elif event.key == pygame.K_RETURN:
                        self.python_code.insert(self.cursor_line + 1, "")
                        self.cursor_line += 1
                    elif event.key == pygame.K_UP:
                        self.cursor_line = max(0, self.cursor_line - 1)
                    elif event.key == pygame.K_DOWN:
                        self.cursor_line = min(len(self.python_code) - 1, self.cursor_line + 1)

                # Chat Logic
                elif self.focus == "chat" and not self.is_loading:
                    if event.key == pygame.K_BACKSPACE:
                        self.user_query = self.user_query[:-1]
                    elif event.key == pygame.K_RETURN and self.user_query.strip():
                        self.is_loading = True
                        # Capture screen for Gemini
                        data = pygame.image.tostring(self.screen, "RGB")
                        img = Image.frombytes("RGB", (WIDTH, HEIGHT), data).resize((640, 360))
                        buf = BytesIO()
                        img.save(buf, format='JPEG')

                        threading.Thread(
                            target=self._async_ai_call,
                            args=(buf.getvalue(), self.user_query),
                            daemon=True
                        ).start()
                        self.user_query = ""

            if event.type == pygame.TEXTINPUT:
                if self.focus == "code":
                    self.python_code[self.cursor_line] += event.text
                elif self.focus == "chat":
                    self.user_query += event.text

    def draw(self):
        self.screen.fill(COLORS["WHITE"])
        if self.bg_surface: self.screen.blit(self.bg_surface, (0, 0))

        # 1. Draw Code Window
        pygame.draw.rect(self.screen, COLORS["CODE_BG"], CODE_WIN_RECT)
        if self.focus == "code":
            pygame.draw.rect(self.screen, COLORS["ACCENT"], CODE_WIN_RECT, 2)

        for i, line in enumerate(self.python_code):
            color = COLORS["CODE_TEXT"]
            txt = self.font.render(line, True, color)
            self.screen.blit(txt, (CODE_WIN_RECT.x + 15, 20 + (i * 25)))
            # Draw cursor
            if self.focus == "code" and i == self.cursor_line:
                cursor_x = CODE_WIN_RECT.x + 15 + self.font.size(line)[0]
                pygame.draw.line(self.screen, COLORS["CURSOR"], (cursor_x, 22 + (i * 25)), (cursor_x, 42 + (i * 25)), 2)

        # 2. Draw Sidebar
        pygame.draw.rect(self.screen, COLORS["SIDEBAR_BG"], SIDEBAR_RECT)
        self._render_wrapped_text("Gemini is thinking..." if self.is_loading else self.ai_response,
                                  SIDEBAR_RECT.x + 20, 20, SIDEBAR_WIDTH - 40)

        # 3. Draw Input Box
        box_color = COLORS["ACCENT"] if self.focus == "chat" else COLORS["INACTIVE"]
        pygame.draw.rect(self.screen, COLORS["WHITE"], self.input_rect)
        pygame.draw.rect(self.screen, box_color, self.input_rect, 2)
        input_txt = self.font.render(f"> {self.user_query}", True, COLORS["BLACK"])
        self.screen.blit(input_txt, (self.input_rect.x + 10, self.input_rect.y + 10))

        pygame.display.flip()

    def _render_wrapped_text(self, text, x, y, max_width):
        lines = text.split('\n')
        cur_y = y
        for line in lines:
            words = line.split(' ')
            cur_x = x
            for word in words:
                word_surf = self.font.render(word, True, COLORS["BLACK"])
                w_w, w_h = word_surf.get_size()
                if cur_x + w_w > x + max_width:
                    cur_x = x
                    cur_y += w_h + 5
                self.screen.blit(word_surf, (cur_x, cur_y))
                cur_x += w_w + self.font.size(' ')[0]
            cur_y += 25

    def run(self):
        pygame.key.start_text_input()
        while self.running:
            self.handle_events()
            self.draw()
            # --- FIXED LINE HERE ---
            self.clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    app = GeminiApp()
    app.run()