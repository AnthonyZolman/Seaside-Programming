import os
import pygame
import threading
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- Setup ---
load_dotenv("keys.env")
client = genai.Client(api_key=os.environ.get("API_KEY"))

pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Seaside Programming - 3D Sidebar")

# --- UI Constants ---
SIDEBAR_WIDTH = 400
SIDEBAR_X = WIDTH - SIDEBAR_WIDTH  # Starts at x=880
WHITE = (255, 255, 255)
SIDEBAR_BG = (245, 245, 245)
BLACK = (20, 20, 20)
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 18)

# --- State Variables ---
user_query = ""
ai_response = "Click below to ask about the 3D scene..."
is_loading = False
active = False

# Input Box constrained to Sidebar width
input_rect = pygame.Rect(SIDEBAR_X + 20, HEIGHT - 60, SIDEBAR_WIDTH - 40, 40)
color_active = (0, 150, 0)
color_passive = (150, 150, 150)
current_color = color_passive

# --- Background images ---
bg_one = pygame.image.load('assets/lvl_one_bg.png').convert_alpha()

def call_gemini(pil_img, query):
    global ai_response, is_loading
    try:
        img_byte_arr = BytesIO()
        pil_img.save(img_byte_arr, format='PNG')
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=img_byte_arr.getvalue(), mime_type="image/png"),
                f"Context: The user is looking at the 3D render on the left. Answer whatever question"
                f" they may have even if the image does not match what is being asked Question: {query}"
            ]
        )
        ai_response = response.text
    except Exception as e:
        ai_response = f"Error: {e}"
    finally:
        is_loading = False


running = True
pygame.key.start_text_input()

while running:
    # 1. Backgrounds
    screen.fill(WHITE)  # Main 3D Area
    pygame.draw.rect(screen, SIDEBAR_BG, (SIDEBAR_X, 0, SIDEBAR_WIDTH, HEIGHT))  # Sidebar Area
    pygame.draw.line(screen, (200, 200, 200), (SIDEBAR_X, 0), (SIDEBAR_X, HEIGHT), 2)  # Divider

    screen.blit(bg_one, (0, 0))

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

        if active and not is_loading:
            if event.type == pygame.TEXTINPUT:
                user_query += event.text
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    user_query = user_query[:-1]
                elif event.key == pygame.K_RETURN and user_query.strip() != "":
                    is_loading = True
                    # Capture the WHOLE screen so Gemini sees the 3D view
                    raw_str = pygame.image.tobytes(screen, "RGB")
                    pil_img = Image.frombytes("RGB", screen.get_size(), raw_str)
                    threading.Thread(target=call_gemini, args=(pil_img, user_query)).start()
                    user_query = ""
                    active = False

    # --- RENDER SIDEBAR CONTENT ---

    # 1. Wrap AI Response to fit Sidebar
    display_text = "Gemini is thinking..." if is_loading else ai_response
    words = display_text.split()
    lines = []
    current_line = ""
    # Approx 40 characters fit in 360 pixels with 18pt Consolas
    MAX_CHARS_PER_LINE = 38

    for word in words:
        if len(current_line + word) < MAX_CHARS_PER_LINE:
            current_line += word + " "
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)

    # Draw lines inside sidebar
    for i, line in enumerate(lines[:25]):  # Show up to 25 lines
        res_surf = font.render(line, True, BLACK)
        screen.blit(res_surf, (SIDEBAR_X + 20, 20 + (i * 22)))

    # 2. Draw Input Box at bottom of Sidebar
    pygame.draw.rect(screen, (255, 255, 255), input_rect)
    pygame.draw.rect(screen, current_color, input_rect, 2)

    # Render typing text (clipped to box width)
    txt_to_show = f"> {user_query}" + ("|" if active else "")
    input_surface = font.render(txt_to_show, True, BLACK)

    screen.blit(input_surface, (input_rect.x + 5, input_rect.y + 10))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()