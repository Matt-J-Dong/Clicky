import pygame
import sys
import json
import os
from pygame.locals import *

# Initialize Pygame
pygame.init()

# Initialize Pygame mixer for sounds
pygame.mixer.init()

# Set up display
WIDTH, HEIGHT = 800, 600  # Increased width for better UI
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Clicky!")

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
LIGHT_GRAY = (220, 220, 220)

# Set up fonts
FONT = pygame.font.SysFont("arial", 24)
BIG_FONT = pygame.font.SysFont("arial", 32)

# Game variables
coins = 0
cps = 0  # Coins per second
last_update_time = pygame.time.get_ticks()

# Upgrade costs and effects
upgrade_cost = 10
upgrade_amount = 1

# New Mega Upgrade Variables
mega_upgrade_cost = 200
mega_upgrade_amount = 10  # CPS increase

# Shop items
SHOP_ITEMS = {
    "CPS Booster": {
        "name": "CPS Booster",
        "cost": 100,
        "effect": {"cps_increase": 10, "duration": 10},  # seconds
    }
}

# Player inventory
inventory = {"CPS Booster": 0}

# Active effects
active_effects = []

# Save file path
SAVE_FILE = "savegame.json"

# Game states
MAIN_GAME = "main"
SHOP_SCREEN = "shop"
INVENTORY_SCREEN = "inventory"

current_screen = MAIN_GAME

# Sound Effects and Music
try:
    click_sound = pygame.mixer.Sound("click.wav")  # Sound when collecting coins
    purchase_sound = pygame.mixer.Sound(
        "purchase.wav"
    )  # Sound when purchasing/upgrading
    use_item_sound = pygame.mixer.Sound("use_item.wav")  # Sound when using an item
    pygame.mixer.music.load("background.mp3")  # Background music
    pygame.mixer.music.set_volume(0.5)  # Set volume (0.0 to 1.0)
    pygame.mixer.music.play(-1)  # Play background music indefinitely
except pygame.error as e:
    print(f"Error loading sound files: {e}")
    print(
        "Ensure that 'click.wav', 'purchase.wav', 'use_item.wav', and 'background.mp3' are in the same directory as the script."
    )
    # You can choose to continue without sounds or exit
    # sys.exit()


def draw_text(text, font, color, surface, x, y, center=True):
    """Utility function to draw text on the screen."""
    textobj = font.render(text, True, color)
    if center:
        textrect = textobj.get_rect(center=(x, y))
    else:
        textrect = textobj.get_rect(topleft=(x, y))
    surface.blit(textobj, textrect)


def draw_button(rect, color, text, surface=WIN):
    """Utility function to draw a button with text."""
    pygame.draw.rect(surface, color, rect)
    # Handle multi-line text
    lines = text.split("\n")
    for i, line in enumerate(lines):
        draw_text(line, FONT, BLACK, surface, rect.centerx, rect.centery - 10 + i * 25)


def save_game():
    """Saves the current game state to a JSON file."""
    game_state = {
        "coins": coins,
        "cps": cps,
        "upgrade_cost": upgrade_cost,
        "upgrade_amount": upgrade_amount,
        "mega_upgrade_cost": mega_upgrade_cost,
        "mega_upgrade_amount": mega_upgrade_amount,
        "last_update_time": last_update_time,
        "inventory": inventory,
        "active_effects": active_effects,
    }
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(game_state, f)
        print("Game saved successfully.")
        set_message("Game Saved!")
    except Exception as e:
        print(f"Error saving game: {e}")
        set_message("Save Failed!")


def load_game():
    """Loads the game state from a JSON file."""
    global coins, cps, upgrade_cost, upgrade_amount, mega_upgrade_cost, mega_upgrade_amount, last_update_time, inventory, active_effects
    if not os.path.exists(SAVE_FILE):
        print("Save file does not exist.")
        set_message("No Save Found!")
        return
    try:
        with open(SAVE_FILE, "r") as f:
            game_state = json.load(f)
        coins = game_state.get("coins", 0)
        cps = game_state.get("cps", 0)
        upgrade_cost = game_state.get("upgrade_cost", 10)
        upgrade_amount = game_state.get("upgrade_amount", 1)
        mega_upgrade_cost = game_state.get("mega_upgrade_cost", 200)
        mega_upgrade_amount = game_state.get("mega_upgrade_amount", 10)
        last_update_time = game_state.get("last_update_time", pygame.time.get_ticks())
        inventory = game_state.get("inventory", {"CPS Booster": 0})
        # Reconstruct active_effects
        loaded_active_effects = game_state.get("active_effects", [])
        active_effects = []
        current_time = pygame.time.get_ticks()
        for active in loaded_active_effects:
            if active["expires_at"] > current_time:
                active_effects.append(active)
                cps += active["effect"].get("cps_increase", 0)
        print("Game loaded successfully.")
        set_message("Game Loaded!")
    except Exception as e:
        print(f"Error loading game: {e}")
        set_message("Load Failed!")


def set_message(text, duration=2):
    """Sets a temporary message to be displayed on the screen."""
    global message, message_time
    message = text
    message_time = pygame.time.get_ticks() + duration * 1000


def apply_effect(effect):
    """Applies an effect to the game (e.g., CPS increase)."""
    global cps
    cps += effect.get("cps_increase", 0)
    duration = effect.get("duration", 0)
    if duration > 0:
        expiration_time = pygame.time.get_ticks() + duration * 1000
        active_effects.append({"effect": effect, "expires_at": expiration_time})
        set_message(
            f"Effect Applied: +{effect.get('cps_increase', 0)} CPS for {duration}s"
        )
    else:
        set_message(f"Permanent Effect: +{effect.get('cps_increase', 0)} CPS")
    try:
        use_item_sound.play()
    except:
        pass  # Handle cases where sound isn't loaded


def update_effects():
    """Updates active effects, removing expired ones."""
    global cps
    current_time = pygame.time.get_ticks()
    for active in active_effects[:]:
        if current_time >= active["expires_at"]:
            cps -= active["effect"].get("cps_increase", 0)
            active_effects.remove(active)
            set_message("Effect Expired!")


def handle_main_game_events(event):
    global coins, upgrade_cost, cps, current_screen, mega_upgrade_cost, mega_upgrade_amount
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = event.pos

        # Check if collect button is clicked
        if collect_button.collidepoint(mouse_pos):
            coins += 1  # Add one coin per click
            try:
                click_sound.play()
            except:
                pass  # Handle cases where sound isn't loaded

        # Check if upgrade button is clicked
        if upgrade_button.collidepoint(mouse_pos):
            if coins >= upgrade_cost:
                coins -= upgrade_cost
                cps += upgrade_amount
                # Optionally, increase the cost for next upgrade
                upgrade_cost = int(upgrade_cost * 1.5)
                set_message("Upgrade Purchased!")
                try:
                    purchase_sound.play()
                except:
                    pass
            else:
                set_message("Not enough coins!")

        # Check if mega upgrade button is clicked
        if mega_upgrade_button.collidepoint(mouse_pos):
            if coins >= mega_upgrade_cost:
                coins -= mega_upgrade_cost
                cps += mega_upgrade_amount
                # Optionally, disable the button or increase the cost
                set_message("Mega Upgrade Purchased!")
                try:
                    purchase_sound.play()
                except:
                    pass
            else:
                set_message("Not enough coins!")

        # Check if save button is clicked
        if save_button.collidepoint(mouse_pos):
            save_game()

        # Check if shop button is clicked
        if SHOP_BUTTON.collidepoint(mouse_pos):
            current_screen = SHOP_SCREEN

        # Check if inventory button is clicked
        if INVENTORY_BUTTON.collidepoint(mouse_pos):
            current_screen = INVENTORY_SCREEN


def handle_shop_events(event):
    global current_screen, coins
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = event.pos

        # Iterate through shop item buttons
        for idx, item_key in enumerate(SHOP_ITEMS):
            item = SHOP_ITEMS[item_key]
            button = shop_item_buttons[idx]
            if button.collidepoint(mouse_pos):
                if coins >= item["cost"]:
                    coins -= item["cost"]
                    inventory[item_key] += 1
                    set_message(f"Purchased {item['name']}!")
                    try:
                        purchase_sound.play()
                    except:
                        pass
                else:
                    set_message("Not enough coins!")

        # Check if back button is clicked
        if shop_back_button.collidepoint(mouse_pos):
            current_screen = MAIN_GAME


def handle_inventory_events(event):
    global current_screen
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = event.pos

        # Iterate through inventory item buttons
        for idx, item_key in enumerate(inventory):
            if inventory[item_key] > 0:
                button = inventory_item_buttons[idx]
                if button.collidepoint(mouse_pos):
                    # Use the item
                    inventory[item_key] -= 1
                    apply_effect(SHOP_ITEMS[item_key]["effect"])
                    try:
                        use_item_sound.play()
                    except:
                        pass

        # Check if back button is clicked
        if inventory_back_button.collidepoint(mouse_pos):
            current_screen = MAIN_GAME


# Define button rectangles
button_width, button_height = 120, 50
collect_button = pygame.Rect(
    WIDTH // 2 - button_width - 10, HEIGHT // 2 - 25, button_width, button_height
)
upgrade_button = pygame.Rect(
    WIDTH // 2 + 10, HEIGHT // 2 - 25, button_width, button_height
)
save_button = pygame.Rect(
    WIDTH // 2 - button_width - 10, HEIGHT // 2 + 50, button_width, button_height
)

# Define Mega Upgrade Button
mega_upgrade_button = pygame.Rect(
    WIDTH // 2 + 10, HEIGHT // 2 + 50 + 60, button_width, button_height
)  # Positioned below the save button

# Define shop and inventory buttons
SHOP_BUTTON = pygame.Rect(50, HEIGHT - 70, 100, 50)
INVENTORY_BUTTON = pygame.Rect(WIDTH - 150, HEIGHT - 70, 130, 50)

# Define shop back button
shop_back_button = pygame.Rect(50, HEIGHT - 70, 100, 50)

# Define inventory back button
inventory_back_button = pygame.Rect(50, HEIGHT - 70, 100, 50)

# Define shop item buttons (dynamic)
shop_item_buttons = []


def create_shop_item_buttons():
    global shop_item_buttons
    shop_item_buttons = []
    start_x = WIDTH // 2 - 200
    start_y = 100
    spacing_y = 120
    for idx, item_key in enumerate(SHOP_ITEMS):
        rect = pygame.Rect(start_x, start_y + idx * spacing_y, 200, 80)
        shop_item_buttons.append(rect)


create_shop_item_buttons()

# Define inventory item buttons (dynamic)
inventory_item_buttons = []


def create_inventory_item_buttons():
    global inventory_item_buttons
    inventory_item_buttons = []
    start_x = WIDTH // 2 - 200
    start_y = 100
    spacing_y = 120
    for idx, item_key in enumerate(inventory):
        rect = pygame.Rect(start_x, start_y + idx * spacing_y, 200, 80)
        inventory_item_buttons.append(rect)


create_inventory_item_buttons()

# Initialize message variables
message = ""
message_time = 0  # Time when the message should disappear

# Auto-load the game on start
load_game()

# Game loop
clock = pygame.time.Clock()
FPS = 60  # Frames per second

running = True
while running:
    clock.tick(FPS)  # Maintain frame rate

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            running = False

        if current_screen == MAIN_GAME:
            handle_main_game_events(event)
        elif current_screen == SHOP_SCREEN:
            handle_shop_events(event)
        elif current_screen == INVENTORY_SCREEN:
            handle_inventory_events(event)

    # Update coins based on CPS
    current_time = pygame.time.get_ticks()
    elapsed_time = (current_time - last_update_time) / 1000  # Convert to seconds
    if elapsed_time >= 1:
        coins += cps * int(elapsed_time)
        last_update_time = current_time

        # Check if it's time to auto-save (optional)
        # For example, auto-save every 60 seconds
        AUTO_SAVE_INTERVAL = 60  # seconds
        if (
            current_time - getattr(load_game, "last_auto_save_time", 0)
        ) / 1000 >= AUTO_SAVE_INTERVAL:
            save_game()
            load_game.last_auto_save_time = current_time

    # Update active effects
    update_effects()

    # Draw everything based on current screen
    WIN.fill(WHITE)

    if current_screen == MAIN_GAME:
        # Display coins and CPS
        draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH // 2, 30)
        draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH // 2, 60)

        # Draw buttons
        draw_button(collect_button, GREEN, "Collect")
        draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
        draw_button(save_button, BLUE, "Save")
        draw_button(
            mega_upgrade_button, RED, f"Mega Upgrade\nCost: {mega_upgrade_cost}"
        )
        draw_button(SHOP_BUTTON, YELLOW, "Shop")
        draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")

    elif current_screen == SHOP_SCREEN:
        # Title
        draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH // 2, 50)

        # Draw shop items
        for idx, item_key in enumerate(SHOP_ITEMS):
            item = SHOP_ITEMS[item_key]
            button = shop_item_buttons[idx]
            pygame.draw.rect(WIN, LIGHT_GRAY, button)
            draw_text(item["name"], FONT, BLACK, WIN, button.centerx, button.y + 20)
            draw_text(
                f"Cost: {item['cost']} coins",
                FONT,
                BLACK,
                WIN,
                button.centerx,
                button.y + 50,
            )
            draw_text(
                f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s",
                FONT,
                BLACK,
                WIN,
                button.centerx,
                button.y + 80,
            )

        # Draw back button
        draw_button(shop_back_button, RED, "Back")

    elif current_screen == INVENTORY_SCREEN:
        # Title
        draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH // 2, 50)

        # Draw inventory items
        for idx, item_key in enumerate(inventory):
            item = SHOP_ITEMS.get(item_key, {})
            button = inventory_item_buttons[idx]
            pygame.draw.rect(WIN, LIGHT_GRAY, button)
            draw_text(item_key, FONT, BLACK, WIN, button.centerx, button.y + 20)
            draw_text(
                f"Quantity: {inventory[item_key]}",
                FONT,
                BLACK,
                WIN,
                button.centerx,
                button.y + 50,
            )
            if inventory[item_key] > 0:
                draw_text(
                    "Click to Use", FONT, BLACK, WIN, button.centerx, button.y + 80
                )

        # Draw back button
        draw_button(inventory_back_button, RED, "Back")

    # Draw message if any
    if message and pygame.time.get_ticks() < message_time:
        draw_text(message, FONT, RED, WIN, WIDTH // 2, HEIGHT - 30)
    elif pygame.time.get_ticks() >= message_time:
        message = ""

    # Update the display
    pygame.display.flip()

pygame.quit()
sys.exit()
