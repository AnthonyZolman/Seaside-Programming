import os
import pygame
import threading
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load Gemini API key from .env file
load_dotenv("keys.env")
client = genai.Client(api_key=os.environ.get("API_KEY"))

pygame.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Seaside Programming")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 20)

# User variables
user_query = ""
ai_response = "Click the box below, type your question, and hit ENTER..."
is_loading = False
active = False

# Input box setup
input_rect = pygame.Rect(20, 600, 1240, 40)  # Made it wider for your 1280 screen
color_active = (0, 150, 0)
color_passive = (150, 150, 150)
current_color = color_passive


def call_gemini(pil_img, query):
    global ai_response, is_loading
    try:
        img_byte_arr = BytesIO()
        pil_img.save(img_byte_arr, format='PNG')

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=img_byte_arr.getvalue(), mime_type="image/png"),
                f"Context: This is the users current screen. Here is their question: {query}"
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
    screen.fill(WHITE)

    # Example Object (something for Gemini to see)
    pygame.draw.rect(screen, BLUE, (540, 200, 200, 200))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if user clicked on the input box
            if input_rect.collidepoint(event.pos):
                active = True
                current_color = color_active
            else:
                active = False
                current_color = color_passive

        # Only process typing if the box is ACTIVE
        if active and not is_loading:
            if event.type == pygame.TEXTINPUT:
                user_query += event.text

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    user_query = user_query[:-1]
                elif event.key == pygame.K_RETURN and user_query.strip() != "":
                    is_loading = True
                    # Capture the screen BEFORE clearing user_query or deactivating
                    raw_str = pygame.image.tobytes(screen, "RGB")
                    pil_img = Image.frombytes("RGB", screen.get_size(), raw_str)

                    threading.Thread(target=call_gemini, args=(pil_img, user_query)).start()
                    user_query = ""
                    active = False
                    current_color = color_passive

    # --- DRAWING THE UI ---

    # 1. Draw the Input Box
    pygame.draw.rect(screen, (240, 240, 240), input_rect)  # Light gray background for box
    pygame.draw.rect(screen, current_color, input_rect, 2)  # Colored border

    # Render the typing text
    input_text = f"Query: {user_query}" + ("|" if active else "")
    input_surface = font.render(input_text, True, BLACK)
    screen.blit(input_surface, (input_rect.x + 10, input_rect.y + 10))

    # 2. Draw the AI Response with fixed wrapping
    if is_loading:
        status_color = (150, 150, 0)  # Darker yellow for visibility on white
        display_text = "Gemini is analyzing the screen..."
    else:
        status_color = (50, 50, 50)  # Dark gray text
        display_text = ai_response

    words = display_text.split()
    lines = []
    current_line = ""
    for word in words:
        # Check if adding the next word exceeds line length (approx 100 chars for 1280 width)
        if len(current_line + word) < 100:
            current_line += word + " "
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)

    # Render up to 20 lines of response
    for i, line in enumerate(lines[:20]):
        res_surf = font.render(line, True, status_color)
        screen.blit(res_surf, (20, 20 + (i * 25)))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()