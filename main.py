import os
import pygame
import sys
from google import genai
from dotenv import load_dotenv

pygame.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Seaside Programming")

WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
clock = pygame.time.Clock()

#Load Gemini API key from .env file
load_dotenv("keys.env")
API_KEY = os.environ.get("API_KEY")
client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how the James Webb Space Telescope works to a 5-year-old."
)

print(response.text)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill(WHITE)
    pygame.draw.rect(screen, BLUE, [350, 250, 100, 100])
    pygame.display.flip()
    clock.tick(60)
pygame.quit()
sys.exit()

