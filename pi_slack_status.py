import os
import pygame
import time
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# --- Environment Variables ---
load_dotenv()

# --- Configuration ---
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")  # Replace with your actual token
SLACK_USER_ID = os.getenv("SLACK_USER_ID")  # Replace with your Slack user ID (find in Slack profile)
UPDATE_INTERVAL_SECONDS = 60  # How often to check Slack status

# Display settings (adjust based on your 3.5" display resolution)
DISPLAY_WIDTH = 480
DISPLAY_HEIGHT = 320 # Or 240 if landscape

# --- Initialize Pygame ---
os.environ["SDL_FBDEV"] = "/dev/fb0" # Usually /dev/fb1 for 3.5" SPI displays, or /dev/fb0 if it's the only display
os.environ["SDL_VIDEODRIVER"] = "fbcon" # Use framebuffer console driver

pygame.init()
screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.FULLSCREEN)
pygame.mouse.set_visible(False) # Hide mouse cursor
font = pygame.font.Font(None, 40) # Choose a suitable font size

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# --- Slack Client ---
slack_client = WebClient(token=SLACK_BOT_TOKEN)

def get_slack_status():
    try:
        response = slack_client.users_profile_get(user=SLACK_USER_ID)
        profile = response['profile']
        status_text = profile.get('status_text', '')
        status_emoji = profile.get('status_emoji', '')
        return status_text, status_emoji
    except SlackApiError as e:
        print(f"Error fetching Slack status: {e}")
        return "Error", "⚠️"
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "Error", "⚠️"

def draw_status(status_text, status_emoji):
    screen.fill(BLACK) # Clear screen

    # Render emoji (if any)
    if status_emoji:
        emoji_surface = font.render(status_emoji, True, WHITE)
        emoji_rect = emoji_surface.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 4))
        screen.blit(emoji_surface, emoji_rect)

    # Render status text
    status_surface = font.render(status_text if status_text else "No Status Set", True, WHITE)
    status_rect = status_surface.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2))
    screen.blit(status_surface, status_rect)

    # Optionally display last updated time
    updated_text = f"Last Updated: {time.strftime('%H:%M:%S')}"
    updated_surface = font.render(updated_text, True, BLUE)
    updated_rect = updated_surface.get_rect(center=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT - 50))
    screen.blit(updated_surface, updated_rect)

    pygame.display.flip() # Update the display

# --- Main Loop ---
last_update_time = 0
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Optional: Allow exiting with a key press (e.g., 'q')
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

    current_time = time.time()
    if current_time - last_update_time > UPDATE_INTERVAL_SECONDS:
        status_text, status_emoji = get_slack_status()
        draw_status(status_text, status_emoji)
        last_update_time = current_time

    time.sleep(0.1) # Small delay to reduce CPU usage

pygame.quit()
