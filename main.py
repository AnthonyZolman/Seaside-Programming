import os
import pygame
import threading
import time
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- Setup ---
load_dotenv("keys.env")
# Make sure your API_KEY is set in keys.env
client = genai.Client(api_key=os.environ.get("API_KEY"))

pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Seaside Programming - 3D Sidebar (Rate-Limit Optimized)")

# --- UI Constants ---
SIDEBAR_WIDTH = 400
SIDEBAR_X = WIDTH - SIDEBAR_WIDTH
CODE_WIN_WIDTH = 400
CODE_WIN_X = SIDEBAR_X - CODE_WIN_WIDTH
CODE_WIN_RECT = pygame.Rect(CODE_WIN_X, 0, CODE_WIN_WIDTH, HEIGHT)

# Colors
WHITE = (255, 255, 255)
SIDEBAR_BG = (245, 245, 245)
CODE_BG = (30, 31, 28)
BLACK = (20, 20, 20)
GRAY = (200, 200, 200)
CODE_TEXT = (230, 230, 230)

clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 18)

# --- State Variables ---
user_query = ""
ai_response = "Type a question and press Enter..."
is_loading = False
active = False
scroll_y = 0
line_height = 22

# Mock Script
python_script = "import os\nimport pygame\n\n# Optimized for 2026 Gemini API\n# Handling 429 Resource Exhausted errors...\n" + \
                "\n".join([f"# Line padding {i}" for i in range(50)])
code_lines = python_script.split('\n')

# Input Box
input_rect = pygame.Rect(SIDEBAR_X + 20, HEIGHT - 60, SIDEBAR_WIDTH - 40, 40)
color_active = (0, 150, 0)
color_passive = (150, 150, 150)
current_color = color_passive

# Background fallback
try:
    bg_one = pygame.image.load('assets/bg_one.png').convert_alpha()
except:
    bg_one = pygame.Surface((CODE_WIN_X, HEIGHT))
    bg_one.fill((100, 100, 250))


def call_gemini(pil_img, query):
    global ai_response, is_loading
    max_retries = 3

    # OPTIMIZATION: Downscale and compress to stay under TPM/RPM limits
    # High-res images consume significantly more tokens.
    pil_img = pil_img.resize((640, 360), Image.Resampling.LANCZOS)
    img_byte_arr = BytesIO()
    pil_img.save(img_byte_arr, format='JPEG', quality=80)
    image_bytes = img_byte_arr.getvalue()

    for attempt in range(max_retries):
        try:
            # Using Flash-Lite or Flash is safer for high-frequency UI tasks
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    f"Context: 3D Scene capture. Question: {query}"
                ]
            )
            ai_response = response.text
            break  # Exit loop on success
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                ai_response = f"Rate limit hit. Retrying in {wait_time}s..."
                time.sleep(wait_time)
            else:
                ai_response = f"Error: {e}"
                break

    is_loading = False


running = True
pygame.key.start_text_input()

while running:
    screen.fill(WHITE)
    screen.blit(bg_one, (0, 0))

    # UI Windows
    pygame.draw.rect(screen, CODE_BG, CODE_WIN_RECT)
    pygame.draw.rect(screen, SIDEBAR_BG, (SIDEBAR_X, 0, SIDEBAR_WIDTH, HEIGHT))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if input_rect.collidepoint(event.pos):
                active = True
                current_color = color_active
            else:
                active = False
                current_color = color_passive

            if CODE_WIN_RECT.collidepoint(event.pos):
                if event.button == 4: scroll_y = min(0, scroll_y + 40)
                if event.button == 5:
                    max_scroll = -(len(code_lines) * line_height - HEIGHT + 100)
                    scroll_y = max(max_scroll, scroll_y - 40)

        if active and not is_loading:
            if event.type == pygame.TEXTINPUT:
                user_query += event.text
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    user_query = user_query[:-1]
                elif event.key == pygame.K_RETURN and user_query.strip() != "":
                    is_loading = True
                    # Capture current screen state
                    raw_str = pygame.image.tobytes(screen, "RGB")
                    pil_img = Image.frombytes("RGB", screen.get_size(), raw_str)

                    # Offload to thread so UI doesn't hang
                    threading.Thread(target=call_gemini, args=(pil_img, user_query), daemon=True).start()
                    user_query = ""
                    active = False

    # Render Code Window (Clipped)
    screen.set_clip(CODE_WIN_RECT)
    for i, line in enumerate(code_lines):
        y_pos = 20 + (i * line_height) + scroll_y
        if -line_height < y_pos < HEIGHT:
            code_surf = font.render(line, True, CODE_TEXT)
            screen.blit(code_surf, (CODE_WIN_X + 15, y_pos))
    screen.set_clip(None)

    # Render AI Response with wrapping
    display_text = "Gemini is thinking..." if is_loading else ai_response
    words = display_text.split()
    lines, current_line = [], ""
    for word in words:
        if len(current_line + word) < 35:
            current_line += word + " "
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)

    for i, line in enumerate(lines[:25]):
        res_surf = font.render(line, True, BLACK)
        screen.blit(res_surf, (SIDEBAR_X + 20, 20 + (i * 22)))

    # Input Box UI
    pygame.draw.rect(screen, WHITE, input_rect)
    pygame.draw.rect(screen, current_color, input_rect, 2)
    input_surface = font.render(f"> {user_query}" + ("|" if active else ""), True, BLACK)
    screen.blit(input_surface, (input_rect.x + 5, input_rect.y + 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()