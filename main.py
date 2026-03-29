import os
import threading
import pygame
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- Configuration & Constants ---
load_dotenv("keys.env")

# Colors & Style
COLORS = {
    "WHITE": (255, 255, 255),
    "BLACK": (20, 20, 20),
    "SIDEBAR_BG": (245, 245, 245),
    "CODE_BG": (30, 31, 28),
    "CODE_TEXT": (230, 230, 230),
    "ACCENT": (0, 150, 0),
    "INACTIVE": (150, 150, 150)
}

WIDTH, HEIGHT = 1280, 720
SIDEBAR_WIDTH = 400
CODE_WIN_WIDTH = 400
CODE_WIN_RECT = pygame.Rect(WIDTH - SIDEBAR_WIDTH - CODE_WIN_WIDTH, 0, CODE_WIN_WIDTH, HEIGHT)
SIDEBAR_RECT = pygame.Rect(WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, HEIGHT)


class GeminiApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Seaside Programming")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 18)

        # API Client
        self.client = genai.Client(api_key=os.environ.get("API_KEY"))

        # State
        self.running = True
        self.is_loading = False
        self.active = False
        self.user_query = ""
        self.ai_response = "Ask a question about the screen..."
        self.python_script = ["print('Hello World!')", "# Type here...", "# Press Enter to ask Gemini"]

        # UI Elements
        self.input_rect = pygame.Rect(SIDEBAR_RECT.x + 20, HEIGHT - 60, SIDEBAR_WIDTH - 40, 40)
        self.bg_surface = self._load_background()

    def _load_background(self):
        try:
            return pygame.image.load('assets/bg_one.png').convert_alpha()
        except:
            surf = pygame.Surface((WIDTH - SIDEBAR_WIDTH - CODE_WIN_WIDTH, HEIGHT))
            surf.fill((100, 100, 250))
            return surf

    def _get_screen_capture(self):
        """Converts pygame surface to compressed PIL image for API."""
        data = pygame.image.tostring(self.screen, "RGB")
        img = Image.frombytes("RGB", (WIDTH, HEIGHT), data)
        img = img.resize((640, 360), Image.Resampling.LANCZOS)

        buf = BytesIO()
        img.save(buf, format='JPEG', quality=80)
        return buf.getvalue()

    def _async_ai_call(self, image_bytes, query):
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",  # Updated to a stable 2.0 version
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    f"Context: UI Screenshot. Question: {query}"
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
                self.active = self.input_rect.collidepoint(event.pos)

            if self.active and not self.is_loading:
                if event.type == pygame.TEXTINPUT:
                    self.user_query += event.text
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        self.user_query = self.user_query[:-1]
                    elif event.key == pygame.K_RETURN and self.user_query.strip():
                        self.is_loading = True
                        img_data = self._get_screen_capture()
                        threading.Thread(
                            target=self._async_ai_call,
                            args=(img_data, self.user_query),
                            daemon=True
                        ).start()
                        self.user_query = ""

    def draw(self):
        # 1. Background & Layout
        self.screen.fill(COLORS["WHITE"])
        self.screen.blit(self.bg_surface, (0, 0))
        pygame.draw.rect(self.screen, COLORS["CODE_BG"], CODE_WIN_RECT)
        pygame.draw.rect(self.screen, COLORS["SIDEBAR_BG"], SIDEBAR_RECT)

        # 2. Render Code Lines
        for i, line in enumerate(self.python_script):
            txt = self.font.render(line, True, COLORS["CODE_TEXT"])
            self.screen.blit(txt, (CODE_WIN_RECT.x + 15, 20 + (i * 25)))

        # 3. Render AI Response (Wrapped)
        display_text = "Gemini is thinking..." if self.is_loading else self.ai_response
        self._render_wrapped_text(display_text, SIDEBAR_RECT.x + 20, 20, SIDEBAR_WIDTH - 40)

        # 4. Input Box
        box_color = COLORS["ACCENT"] if self.active else COLORS["INACTIVE"]
        pygame.draw.rect(self.screen, COLORS["WHITE"], self.input_rect)
        pygame.draw.rect(self.screen, box_color, self.input_rect, 2)

        input_txt = self.font.render(f"> {self.user_query}", True, COLORS["BLACK"])
        self.screen.blit(input_txt, (self.input_rect.x + 10, self.input_rect.y + 10))

        pygame.display.flip()

    def _render_wrapped_text(self, text, x, y, max_width):
        words = text.split(' ')
        space_width = self.font.size(' ')[0]
        cur_x, cur_y = x, y

        for word in words:
            word_surf = self.font.render(word, True, COLORS["BLACK"])
            w_w, w_h = word_surf.get_size()
            if cur_x + w_w > x + max_width:
                cur_x = x
                cur_y += w_h + 5
            self.screen.blit(word_surf, (cur_x, cur_y))
            cur_x += w_w + space_width

    def run(self):
        pygame.key.start_text_input()
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(60)
        pygame.quit()


if __name__ == "__main__":
    app = GeminiApp()
    app.run()