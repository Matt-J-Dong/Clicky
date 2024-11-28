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
BLUE_COLOR = (0, 0, 255)  # Renamed to avoid conflict with enemy 'Blue Slime'
YELLOW = (255, 255, 0)
LIGHT_GRAY = (220, 220, 220)
DARK_RED = (139, 0, 0)
DARK_GREEN = (0, 100, 0)

# Set up fonts
FONT = pygame.font.SysFont('arial', 24)
BIG_FONT = pygame.font.SysFont('arial', 32)

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
    'CPS Booster': {
        'name': 'CPS Booster',
        'cost': 100,
        'effect': {
            'cps_increase': 10,
            'duration': 10  # seconds
        },
        'category': 'Consumables'
    },
    'Potion': {
        'name': 'Potion',
        'cost': 100,
        'category': 'Battle Items'
    },
    'Revive': {
        'name': 'Revive',
        'cost': 1000,
        'category': 'Battle Items'
    }
}

# Player inventory
inventory = {
    'Consumables': {
        'CPS Booster': 0
    },
    'Enemy Drops': {
        'Blue Slime Chunk': 0
    },
    'Battle Items': {
        'Potion': 0,
        'Revive': 0
    }
}

# Active effects
active_effects = []

# Combat variables
player_max_hp = 100
player_hp = player_max_hp
enemy_max_hp = 10
enemy_hp = enemy_max_hp
in_combat = False
combat_start_time = 0
last_combat_update = 0

# Save file path
SAVE_FILE = "savegame.json"

# Game states
MAIN_GAME = 'main'
SHOP_SCREEN = 'shop'
INVENTORY_SCREEN = 'inventory'
COMBAT_SCREEN = 'combat'

current_screen = MAIN_GAME

# Sound Effects and Music
try:
    click_sound = pygame.mixer.Sound('click.wav')  # Sound when collecting coins
    purchase_sound = pygame.mixer.Sound('purchase.wav')  # Sound when purchasing/upgrading
    use_item_sound = pygame.mixer.Sound('use_item.wav')  # Sound when using an item
    pygame.mixer.music.load('background.mp3')  # Background music
    pygame.mixer.music.set_volume(0.5)  # Set volume (0.0 to 1.0)
    pygame.mixer.music.play(-1)  # Play background music indefinitely
except pygame.error as e:
    print(f"Error loading sound files: {e}")
    print("Ensure that 'click.wav', 'purchase.wav', 'use_item.wav', and 'background.mp3' are in the same directory as the script.")
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
    lines = text.split('\n')
    for i, line in enumerate(lines):
        draw_text(line, FONT, BLACK, surface, rect.centerx, rect.centery - 10 + i*25)

def save_game():
    """Saves the current game state to a JSON file."""
    game_state = {
        'coins': coins,
        'cps': cps,
        'upgrade_cost': upgrade_cost,
        'upgrade_amount': upgrade_amount,
        'mega_upgrade_cost': mega_upgrade_cost,
        'mega_upgrade_amount': mega_upgrade_amount,
        'last_update_time': last_update_time,
        'inventory': inventory,
        'active_effects': active_effects,
        'player_hp': player_hp,
        'enemy_hp': enemy_hp,
        'in_combat': in_combat,
        'combat_start_time': combat_start_time,
        'last_combat_update': last_combat_update
    }
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(game_state, f)
        print("Game saved successfully.")
        set_message("Game Saved!")
    except Exception as e:
        print(f"Error saving game: {e}")
        set_message("Save Failed!")

def load_game():
    """Loads the game state from a JSON file."""
    global coins, cps, upgrade_cost, upgrade_amount, mega_upgrade_cost, mega_upgrade_amount
    global last_update_time, inventory, active_effects
    global player_hp, enemy_hp, in_combat, combat_start_time, last_combat_update
    if not os.path.exists(SAVE_FILE):
        print("Save file does not exist.")
        set_message("No Save Found!")
        return
    try:
        with open(SAVE_FILE, 'r') as f:
            game_state = json.load(f)
        coins = game_state.get('coins', 0)
        cps = game_state.get('cps', 0)
        upgrade_cost = game_state.get('upgrade_cost', 10)
        upgrade_amount = game_state.get('upgrade_amount', 1)
        mega_upgrade_cost = game_state.get('mega_upgrade_cost', 200)
        mega_upgrade_amount = game_state.get('mega_upgrade_amount', 10)
        last_update_time = game_state.get('last_update_time', pygame.time.get_ticks())
        inventory = game_state.get('inventory', {
            'Consumables': {'CPS Booster': 0},
            'Enemy Drops': {'Blue Slime Chunk': 0},
            'Battle Items': {'Potion': 0, 'Revive': 0}
        })
        # Reconstruct active_effects
        loaded_active_effects = game_state.get('active_effects', [])
        active_effects = []
        current_time = pygame.time.get_ticks()
        cps = 0  # Reset CPS and re-apply active effects
        for active in loaded_active_effects:
            if active['expires_at'] > current_time:
                active_effects.append(active)
                cps += active['effect'].get('cps_increase', 0)
        # Load combat state
        player_hp = game_state.get('player_hp', 100)
        enemy_hp = game_state.get('enemy_hp', 10)
        in_combat = game_state.get('in_combat', False)
        combat_start_time = game_state.get('combat_start_time', 0)
        last_combat_update = game_state.get('last_combat_update', 0)
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
    cps += effect.get('cps_increase', 0)
    duration = effect.get('duration', 0)
    if duration > 0:
        expiration_time = pygame.time.get_ticks() + duration * 1000
        active_effects.append({'effect': effect, 'expires_at': expiration_time})
        set_message(f"Effect Applied: +{effect.get('cps_increase', 0)} CPS for {duration}s")
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
        if current_time >= active['expires_at']:
            cps -= active['effect'].get('cps_increase', 0)
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

        # Check if fight button is clicked
        if FIGHT_BUTTON.collidepoint(mouse_pos):
            current_screen = COMBAT_SCREEN
            start_combat()

def handle_shop_events(event):
    global current_screen, coins
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = event.pos

        # Iterate through shop item buttons
        for idx, item_key in enumerate(SHOP_ITEMS):
            item = SHOP_ITEMS[item_key]
            button = shop_item_buttons[idx]
            if button.collidepoint(mouse_pos):
                if coins >= item['cost']:
                    coins -= item['cost']
                    category = item['category']
                    inventory[category][item_key] += 1
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

        # Iterate through battle item buttons
        for idx, item_key in enumerate(inventory['Battle Items']):
            if inventory['Battle Items'][item_key] > 0:
                button = battle_item_buttons[idx]
                if button.collidepoint(mouse_pos):
                    if item_key == 'Potion':
                        use_potion()
                    elif item_key == 'Revive':
                        # Revives are auto-used, no manual use
                        set_message("Revives are auto-used upon death.")
        
        # Iterate through enemy drop buttons (read-only for now)
        # No action required
        
        # Check if back button is clicked
        if inventory_back_button.collidepoint(mouse_pos):
            current_screen = MAIN_GAME

def handle_combat_events(event):
    global player_hp, enemy_hp, in_combat, combat_start_time, last_combat_update, coins
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = event.pos

        # Check if use potion button is clicked
        if use_potion_button.collidepoint(mouse_pos):
            use_potion()

def use_potion():
    global player_hp, inventory
    if inventory['Battle Items']['Potion'] > 0:
        inventory['Battle Items']['Potion'] -= 1
        player_hp += 50
        if player_hp > player_max_hp:
            player_hp = player_max_hp
        set_message("Potion used! Healed 50 HP.")
        try:
            use_item_sound.play()
        except:
            pass
    else:
        set_message("No Potions available!")

def start_combat():
    global in_combat, player_hp, enemy_hp, combat_start_time, last_combat_update
    in_combat = True
    player_hp = 100  # Reset player HP or keep current HP
    enemy_hp = 10
    combat_start_time = pygame.time.get_ticks()
    last_combat_update = combat_start_time

def update_combat():
    global player_hp, enemy_hp, in_combat, coins
    current_time = pygame.time.get_ticks()
    elapsed_since_last_update = (current_time - last_combat_update) / 1000  # seconds

    if elapsed_since_last_update >= 1:
        # Player deals damage
        enemy_hp -= 1
        # Enemy deals damage
        player_hp -= 1
        set_message("You dealt 1 damage. Enemy dealt 1 damage.")
        try:
            click_sound.play()
        except:
            pass

        # Update last_combat_update
        global last_combat_update
        last_combat_update = current_time

        # Check for combat outcomes
        if enemy_hp <= 0:
            # Enemy defeated
            in_combat = False
            set_message("Blue Slime defeated! Obtained Blue Slime Chunk.")
            inventory['Enemy Drops']['Blue Slime Chunk'] += 1
            try:
                purchase_sound.play()
            except:
                pass
        elif player_hp <= 0:
            # Player defeated
            if inventory['Battle Items']['Revive'] > 0:
                inventory['Battle Items']['Revive'] -= 1
                player_hp = 25  # Revive heals 25 HP
                set_message("Revived! Healed 25 HP.")
                try:
                    use_item_sound.play()
                except:
                    pass
            else:
                # Player dies and loses half their coins
                lost_coins = coins // 2
                coins -= lost_coins
                set_message(f"You died! Lost {lost_coins} coins.")
                in_combat = False

def handle_combat_logic():
    if in_combat:
        update_combat()

def draw_main_game():
    # Display coins and CPS
    draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH//2, 30)
    draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH//2, 60)

    # Draw buttons
    draw_button(collect_button, GREEN, "Collect")
    draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
    draw_button(mega_upgrade_button, DARK_GREEN, f"Mega Upgrade\nCost: {mega_upgrade_cost}")
    draw_button(save_button, BLUE, "Save")
    draw_button(SHOP_BUTTON, YELLOW, "Shop")
    draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")
    draw_button(FIGHT_BUTTON, RED, "Fight")

def draw_shop_screen():
    # Title
    draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw shop items
    for idx, item_key in enumerate(SHOP_ITEMS):
        item = SHOP_ITEMS[item_key]
        button = shop_item_buttons[idx]
        pygame.draw.rect(WIN, LIGHT_GRAY, button)
        draw_text(item['name'], FONT, BLACK, WIN, button.centerx, button.y + 20)
        draw_text(f"Cost: {item['cost']} coins", FONT, BLACK, WIN, button.centerx, button.y + 50)
        if item['category'] == 'Consumables':
            draw_text(f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s", FONT, BLACK, WIN, button.centerx, button.y + 80)
        elif item['category'] == 'Battle Items':
            if item_key == 'Potion':
                draw_text("Heals 50 HP", FONT, BLACK, WIN, button.centerx, button.y + 80)
            elif item_key == 'Revive':
                draw_text("Auto-heal upon death", FONT, BLACK, WIN, button.centerx, button.y + 80)

    # Draw back button
    draw_button(shop_back_button, DARK_RED, "Back")

def draw_inventory_screen():
    # Title
    draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw Consumables
    draw_text("Consumables:", FONT, BLACK, WIN, 150, 100, center=False)
    for idx, item_key in enumerate(inventory['Consumables']):
        qty = inventory['Consumables'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 130 + idx * 30, center=False)

    # Draw Enemy Drops
    draw_text("Enemy Drops:", FONT, BLACK, WIN, 150, 200, center=False)
    for idx, item_key in enumerate(inventory['Enemy Drops']):
        qty = inventory['Enemy Drops'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 230 + idx * 30, center=False)

    # Draw Battle Items
    draw_text("Battle Items:", FONT, BLACK, WIN, 550, 100, center=False)
    for idx, item_key in enumerate(inventory['Battle Items']):
        qty = inventory['Battle Items'][item_key]
        action = ""
        if item_key == 'Potion':
            action = "Use Potion"
        elif item_key == 'Revive':
            action = "Auto-Use Revive"
        draw_text(f"{item_key}: {qty} ({action})", FONT, BLACK, WIN, 550, 130 + idx * 30, center=False)

    # Draw back button
    draw_button(inventory_back_button, DARK_RED, "Back")

def draw_combat_screen():
    # Title
    draw_text("Combat", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw player and enemy HP
    draw_text(f"Player HP: {player_hp}/100", FONT, BLACK, WIN, WIDTH//2, 150)
    draw_text(f"Blue Slime HP: {enemy_hp}/10", FONT, BLACK, WIN, WIDTH//2, 200)

    # Draw use potion button if player has potions
    if inventory['Battle Items']['Potion'] > 0:
        draw_button(use_potion_button, DARK_GREEN, "Use Potion")
    else:
        # Draw disabled button
        pygame.draw.rect(WIN, GRAY, use_potion_button)
        draw_text("No Potions", FONT, BLACK, WIN, use_potion_button.centerx, use_potion_button.centery)

def handle_combat_events(event):
    global player_hp, enemy_hp, in_combat, combat_start_time, last_combat_update, coins
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = event.pos

        # Check if use potion button is clicked
        if use_potion_button.collidepoint(mouse_pos):
            use_potion()

def use_potion():
    global player_hp, inventory
    if inventory['Battle Items']['Potion'] > 0:
        inventory['Battle Items']['Potion'] -= 1
        player_hp += 50
        if player_hp > player_max_hp:
            player_hp = player_max_hp
        set_message("Potion used! Healed 50 HP.")
        try:
            use_item_sound.play()
        except:
            pass
    else:
        set_message("No Potions available!")

def start_combat():
    global in_combat, player_hp, enemy_hp, combat_start_time, last_combat_update
    in_combat = True
    player_hp = 100  # Reset player HP or keep current HP
    enemy_hp = 10
    combat_start_time = pygame.time.get_ticks()
    last_combat_update = combat_start_time

def update_combat():
    global player_hp, enemy_hp, in_combat, coins
    current_time = pygame.time.get_ticks()
    elapsed_since_last_update = (current_time - last_combat_update) / 1000  # seconds

    if elapsed_since_last_update >= 1:
        # Player deals damage
        enemy_hp -= 1
        # Enemy deals damage
        player_hp -= 1
        set_message("You dealt 1 damage. Enemy dealt 1 damage.")
        try:
            click_sound.play()
        except:
            pass

        # Update last_combat_update
        global last_combat_update
        last_combat_update = current_time

        # Check for combat outcomes
        if enemy_hp <= 0:
            # Enemy defeated
            in_combat = False
            set_message("Blue Slime defeated! Obtained Blue Slime Chunk.")
            inventory['Enemy Drops']['Blue Slime Chunk'] += 1
            try:
                purchase_sound.play()
            except:
                pass
        elif player_hp <= 0:
            # Player defeated
            if inventory['Battle Items']['Revive'] > 0:
                inventory['Battle Items']['Revive'] -= 1
                player_hp = 25  # Revive heals 25 HP
                set_message("Revived! Healed 25 HP.")
                try:
                    use_item_sound.play()
                except:
                    pass
            else:
                # Player dies and loses half their coins
                lost_coins = coins // 2
                coins -= lost_coins
                set_message(f"You died! Lost {lost_coins} coins.")
                in_combat = False

def handle_combat_logic():
    if in_combat:
        update_combat()

def draw_main_game():
    # Display coins and CPS
    draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH//2, 30)
    draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH//2, 60)

    # Draw buttons
    draw_button(collect_button, GREEN, "Collect")
    draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
    draw_button(mega_upgrade_button, DARK_GREEN, f"Mega Upgrade\nCost: {mega_upgrade_cost}")
    draw_button(save_button, BLUE, "Save")
    draw_button(SHOP_BUTTON, YELLOW, "Shop")
    draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")
    draw_button(FIGHT_BUTTON, RED, "Fight")

def draw_shop_screen():
    # Title
    draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw shop items
    for idx, item_key in enumerate(SHOP_ITEMS):
        item = SHOP_ITEMS[item_key]
        button = shop_item_buttons[idx]
        pygame.draw.rect(WIN, LIGHT_GRAY, button)
        draw_text(item['name'], FONT, BLACK, WIN, button.centerx, button.y + 20)
        draw_text(f"Cost: {item['cost']} coins", FONT, BLACK, WIN, button.centerx, button.y + 50)
        if item['category'] == 'Consumables':
            draw_text(f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s", FONT, BLACK, WIN, button.centerx, button.y + 80)
        elif item['category'] == 'Battle Items':
            if item_key == 'Potion':
                draw_text("Heals 50 HP", FONT, BLACK, WIN, button.centerx, button.y + 80)
            elif item_key == 'Revive':
                draw_text("Auto-heal upon death", FONT, BLACK, WIN, button.centerx, button.y + 80)

    # Draw back button
    draw_button(shop_back_button, DARK_RED, "Back")

def draw_inventory_screen():
    # Title
    draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw Consumables
    draw_text("Consumables:", FONT, BLACK, WIN, 150, 100, center=False)
    for idx, item_key in enumerate(inventory['Consumables']):
        qty = inventory['Consumables'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 130 + idx * 30, center=False)

    # Draw Enemy Drops
    draw_text("Enemy Drops:", FONT, BLACK, WIN, 150, 200, center=False)
    for idx, item_key in enumerate(inventory['Enemy Drops']):
        qty = inventory['Enemy Drops'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 230 + idx * 30, center=False)

    # Draw Battle Items
    draw_text("Battle Items:", FONT, BLACK, WIN, 550, 100, center=False)
    for idx, item_key in enumerate(inventory['Battle Items']):
        qty = inventory['Battle Items'][item_key]
        action = ""
        if item_key == 'Potion':
            action = "Use Potion"
        elif item_key == 'Revive':
            action = "Auto-Use Revive"
        draw_text(f"{item_key}: {qty} ({action})", FONT, BLACK, WIN, 550, 130 + idx * 30, center=False)

    # Draw back button
    draw_button(inventory_back_button, DARK_RED, "Back")

def draw_combat_screen():
    # Title
    draw_text("Combat", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw player and enemy HP
    draw_text(f"Player HP: {player_hp}/100", FONT, BLACK, WIN, WIDTH//2, 150)
    draw_text(f"Blue Slime HP: {enemy_hp}/10", FONT, BLACK, WIN, WIDTH//2, 200)

    # Draw use potion button if player has potions
    if inventory['Battle Items']['Potion'] > 0:
        draw_button(use_potion_button, DARK_GREEN, "Use Potion")
    else:
        # Draw disabled button
        pygame.draw.rect(WIN, GRAY, use_potion_button)
        draw_text("No Potions", FONT, BLACK, WIN, use_potion_button.centerx, use_potion_button.centery)

    # Optionally, add a 'Quit Combat' button
    # For simplicity, combat ends when player or enemy is defeated

def handle_combat_events(event):
    global player_hp, enemy_hp, in_combat, combat_start_time, last_combat_update, coins
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = event.pos

        # Check if use potion button is clicked
        if use_potion_button.collidepoint(mouse_pos):
            use_potion()

def use_potion():
    global player_hp, inventory
    if inventory['Battle Items']['Potion'] > 0:
        inventory['Battle Items']['Potion'] -= 1
        player_hp += 50
        if player_hp > player_max_hp:
            player_hp = player_max_hp
        set_message("Potion used! Healed 50 HP.")
        try:
            use_item_sound.play()
        except:
            pass
    else:
        set_message("No Potions available!")

def start_combat():
    global in_combat, player_hp, enemy_hp, combat_start_time, last_combat_update
    in_combat = True
    player_hp = 100  # Reset player HP or keep current HP
    enemy_hp = 10
    combat_start_time = pygame.time.get_ticks()
    last_combat_update = combat_start_time

def update_combat():
    global player_hp, enemy_hp, in_combat, coins
    current_time = pygame.time.get_ticks()
    elapsed_since_last_update = (current_time - last_combat_update) / 1000  # seconds

    if elapsed_since_last_update >= 1:
        # Player deals damage
        enemy_hp -= 1
        # Enemy deals damage
        player_hp -= 1
        set_message("You dealt 1 damage. Enemy dealt 1 damage.")
        try:
            click_sound.play()
        except:
            pass

        # Update last_combat_update
        global last_combat_update
        last_combat_update = current_time

        # Check for combat outcomes
        if enemy_hp <= 0:
            # Enemy defeated
            in_combat = False
            set_message("Blue Slime defeated! Obtained Blue Slime Chunk.")
            inventory['Enemy Drops']['Blue Slime Chunk'] += 1
            try:
                purchase_sound.play()
            except:
                pass
        elif player_hp <= 0:
            # Player defeated
            if inventory['Battle Items']['Revive'] > 0:
                inventory['Battle Items']['Revive'] -= 1
                player_hp = 25  # Revive heals 25 HP
                set_message("Revived! Healed 25 HP.")
                try:
                    use_item_sound.play()
                except:
                    pass
            else:
                # Player dies and loses half their coins
                lost_coins = coins // 2
                coins -= lost_coins
                set_message(f"You died! Lost {lost_coins} coins.")
                in_combat = False

def handle_combat_logic():
    if in_combat:
        update_combat()

def draw_main_game():
    # Display coins and CPS
    draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH//2, 30)
    draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH//2, 60)

    # Draw buttons
    draw_button(collect_button, GREEN, "Collect")
    draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
    draw_button(mega_upgrade_button, DARK_GREEN, f"Mega Upgrade\nCost: {mega_upgrade_cost}")
    draw_button(save_button, BLUE, "Save")
    draw_button(SHOP_BUTTON, YELLOW, "Shop")
    draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")
    draw_button(FIGHT_BUTTON, RED, "Fight")

def draw_shop_screen():
    # Title
    draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw shop items
    for idx, item_key in enumerate(SHOP_ITEMS):
        item = SHOP_ITEMS[item_key]
        button = shop_item_buttons[idx]
        pygame.draw.rect(WIN, LIGHT_GRAY, button)
        draw_text(item['name'], FONT, BLACK, WIN, button.centerx, button.y + 20)
        draw_text(f"Cost: {item['cost']} coins", FONT, BLACK, WIN, button.centerx, button.y + 50)
        if item['category'] == 'Consumables':
            draw_text(f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s", FONT, BLACK, WIN, button.centerx, button.y + 80)
        elif item['category'] == 'Battle Items':
            if item_key == 'Potion':
                draw_text("Heals 50 HP", FONT, BLACK, WIN, button.centerx, button.y + 80)
            elif item_key == 'Revive':
                draw_text("Auto-heal upon death", FONT, BLACK, WIN, button.centerx, button.y + 80)

    # Draw back button
    draw_button(shop_back_button, DARK_RED, "Back")

def draw_inventory_screen():
    # Title
    draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw Consumables
    draw_text("Consumables:", FONT, BLACK, WIN, 150, 100, center=False)
    for idx, item_key in enumerate(inventory['Consumables']):
        qty = inventory['Consumables'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 130 + idx * 30, center=False)

    # Draw Enemy Drops
    draw_text("Enemy Drops:", FONT, BLACK, WIN, 150, 200, center=False)
    for idx, item_key in enumerate(inventory['Enemy Drops']):
        qty = inventory['Enemy Drops'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 230 + idx * 30, center=False)

    # Draw Battle Items
    draw_text("Battle Items:", FONT, BLACK, WIN, 550, 100, center=False)
    for idx, item_key in enumerate(inventory['Battle Items']):
        qty = inventory['Battle Items'][item_key]
        action = ""
        if item_key == 'Potion':
            action = "Use Potion"
        elif item_key == 'Revive':
            action = "Auto-Use Revive"
        draw_text(f"{item_key}: {qty} ({action})", FONT, BLACK, WIN, 550, 130 + idx * 30, center=False)

    # Draw back button
    draw_button(inventory_back_button, DARK_RED, "Back")

def draw_combat_screen():
    # Title
    draw_text("Combat", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw player and enemy HP
    draw_text(f"Player HP: {player_hp}/100", FONT, BLACK, WIN, WIDTH//2, 150)
    draw_text(f"Blue Slime HP: {enemy_hp}/10", FONT, BLACK, WIN, WIDTH//2, 200)

    # Draw use potion button if player has potions
    if inventory['Battle Items']['Potion'] > 0:
        draw_button(use_potion_button, DARK_GREEN, "Use Potion")
    else:
        # Draw disabled button
        pygame.draw.rect(WIN, GRAY, use_potion_button)
        draw_text("No Potions", FONT, BLACK, WIN, use_potion_button.centerx, use_potion_button.centery)

    # Optionally, add a 'Quit Combat' button
    # For simplicity, combat ends when player or enemy is defeated

def handle_combat_events(event):
    global player_hp, enemy_hp, in_combat, combat_start_time, last_combat_update, coins
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = event.pos

        # Check if use potion button is clicked
        if use_potion_button.collidepoint(mouse_pos):
            use_potion()

def use_potion():
    global player_hp, inventory
    if inventory['Battle Items']['Potion'] > 0:
        inventory['Battle Items']['Potion'] -= 1
        player_hp += 50
        if player_hp > player_max_hp:
            player_hp = player_max_hp
        set_message("Potion used! Healed 50 HP.")
        try:
            use_item_sound.play()
        except:
            pass
    else:
        set_message("No Potions available!")

def start_combat():
    global in_combat, player_hp, enemy_hp, combat_start_time, last_combat_update
    in_combat = True
    player_hp = 100  # Reset player HP or keep current HP
    enemy_hp = 10
    combat_start_time = pygame.time.get_ticks()
    last_combat_update = combat_start_time

def update_combat():
    global player_hp, enemy_hp, in_combat, coins
    current_time = pygame.time.get_ticks()
    elapsed_since_last_update = (current_time - last_combat_update) / 1000  # seconds

    if elapsed_since_last_update >= 1:
        # Player deals damage
        enemy_hp -= 1
        # Enemy deals damage
        player_hp -= 1
        set_message("You dealt 1 damage. Enemy dealt 1 damage.")
        try:
            click_sound.play()
        except:
            pass

        # Update last_combat_update
        global last_combat_update
        last_combat_update = current_time

        # Check for combat outcomes
        if enemy_hp <= 0:
            # Enemy defeated
            in_combat = False
            set_message("Blue Slime defeated! Obtained Blue Slime Chunk.")
            inventory['Enemy Drops']['Blue Slime Chunk'] += 1
            try:
                purchase_sound.play()
            except:
                pass
        elif player_hp <= 0:
            # Player defeated
            if inventory['Battle Items']['Revive'] > 0:
                inventory['Battle Items']['Revive'] -= 1
                player_hp = 25  # Revive heals 25 HP
                set_message("Revived! Healed 25 HP.")
                try:
                    use_item_sound.play()
                except:
                    pass
            else:
                # Player dies and loses half their coins
                lost_coins = coins // 2
                coins -= lost_coins
                set_message(f"You died! Lost {lost_coins} coins.")
                in_combat = False

def handle_combat_logic():
    if in_combat:
        update_combat()

def draw_main_game():
    # Display coins and CPS
    draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH//2, 30)
    draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH//2, 60)

    # Draw buttons
    draw_button(collect_button, GREEN, "Collect")
    draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
    draw_button(mega_upgrade_button, DARK_GREEN, f"Mega Upgrade\nCost: {mega_upgrade_cost}")
    draw_button(save_button, BLUE, "Save")
    draw_button(SHOP_BUTTON, YELLOW, "Shop")
    draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")
    draw_button(FIGHT_BUTTON, RED, "Fight")

def draw_shop_screen():
    # Title
    draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw shop items
    for idx, item_key in enumerate(SHOP_ITEMS):
        item = SHOP_ITEMS[item_key]
        button = shop_item_buttons[idx]
        pygame.draw.rect(WIN, LIGHT_GRAY, button)
        draw_text(item['name'], FONT, BLACK, WIN, button.centerx, button.y + 20)
        draw_text(f"Cost: {item['cost']} coins", FONT, BLACK, WIN, button.centerx, button.y + 50)
        if item['category'] == 'Consumables':
            draw_text(f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s", FONT, BLACK, WIN, button.centerx, button.y + 80)
        elif item['category'] == 'Battle Items':
            if item_key == 'Potion':
                draw_text("Heals 50 HP", FONT, BLACK, WIN, button.centerx, button.y + 80)
            elif item_key == 'Revive':
                draw_text("Auto-heal upon death", FONT, BLACK, WIN, button.centerx, button.y + 80)

    # Draw back button
    draw_button(shop_back_button, DARK_RED, "Back")

def draw_inventory_screen():
    # Title
    draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw Consumables
    draw_text("Consumables:", FONT, BLACK, WIN, 150, 100, center=False)
    for idx, item_key in enumerate(inventory['Consumables']):
        qty = inventory['Consumables'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 130 + idx * 30, center=False)

    # Draw Enemy Drops
    draw_text("Enemy Drops:", FONT, BLACK, WIN, 150, 200, center=False)
    for idx, item_key in enumerate(inventory['Enemy Drops']):
        qty = inventory['Enemy Drops'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 230 + idx * 30, center=False)

    # Draw Battle Items
    draw_text("Battle Items:", FONT, BLACK, WIN, 550, 100, center=False)
    for idx, item_key in enumerate(inventory['Battle Items']):
        qty = inventory['Battle Items'][item_key]
        action = ""
        if item_key == 'Potion':
            action = "Use Potion"
        elif item_key == 'Revive':
            action = "Auto-Use Revive"
        draw_text(f"{item_key}: {qty} ({action})", FONT, BLACK, WIN, 550, 130 + idx * 30, center=False)

    # Draw back button
    draw_button(inventory_back_button, DARK_RED, "Back")

def draw_combat_screen():
    # Title
    draw_text("Combat", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw player and enemy HP
    draw_text(f"Player HP: {player_hp}/100", FONT, BLACK, WIN, WIDTH//2, 150)
    draw_text(f"Blue Slime HP: {enemy_hp}/10", FONT, BLACK, WIN, WIDTH//2, 200)

    # Draw use potion button if player has potions
    if inventory['Battle Items']['Potion'] > 0:
        draw_button(use_potion_button, DARK_GREEN, "Use Potion")
    else:
        # Draw disabled button
        pygame.draw.rect(WIN, GRAY, use_potion_button)
        draw_text("No Potions", FONT, BLACK, WIN, use_potion_button.centerx, use_potion_button.centery)

def handle_combat_events(event):
    if in_combat:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Check if use potion button is clicked
            if use_potion_button.collidepoint(mouse_pos):
                use_potion()

def use_potion():
    global player_hp, inventory
    if inventory['Battle Items']['Potion'] > 0:
        inventory['Battle Items']['Potion'] -= 1
        player_hp += 50
        if player_hp > player_max_hp:
            player_hp = player_max_hp
        set_message("Potion used! Healed 50 HP.")
        try:
            use_item_sound.play()
        except:
            pass
    else:
        set_message("No Potions available!")

def start_combat():
    global in_combat, player_hp, enemy_hp, combat_start_time, last_combat_update
    in_combat = True
    player_hp = 100  # Reset player HP or keep current HP
    enemy_hp = 10
    combat_start_time = pygame.time.get_ticks()
    last_combat_update = combat_start_time

def update_combat():
    global player_hp, enemy_hp, in_combat, coins
    current_time = pygame.time.get_ticks()
    elapsed_since_last_update = (current_time - last_combat_update) / 1000  # seconds

    if elapsed_since_last_update >= 1:
        # Player deals damage
        enemy_hp -= 1
        # Enemy deals damage
        player_hp -= 1
        set_message("You dealt 1 damage. Enemy dealt 1 damage.")
        try:
            click_sound.play()
        except:
            pass

        # Update last_combat_update
        global last_combat_update
        last_combat_update = current_time

        # Check for combat outcomes
        if enemy_hp <= 0:
            # Enemy defeated
            in_combat = False
            set_message("Blue Slime defeated! Obtained Blue Slime Chunk.")
            inventory['Enemy Drops']['Blue Slime Chunk'] += 1
            try:
                purchase_sound.play()
            except:
                pass
        elif player_hp <= 0:
            # Player defeated
            if inventory['Battle Items']['Revive'] > 0:
                inventory['Battle Items']['Revive'] -= 1
                player_hp = 25  # Revive heals 25 HP
                set_message("Revived! Healed 25 HP.")
                try:
                    use_item_sound.play()
                except:
                    pass
            else:
                # Player dies and loses half their coins
                lost_coins = coins // 2
                coins -= lost_coins
                set_message(f"You died! Lost {lost_coins} coins.")
                in_combat = False

def handle_combat_logic():
    if in_combat:
        update_combat()

def draw_main_game():
    # Display coins and CPS
    draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH//2, 30)
    draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH//2, 60)

    # Draw buttons
    draw_button(collect_button, GREEN, "Collect")
    draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
    draw_button(mega_upgrade_button, DARK_GREEN, f"Mega Upgrade\nCost: {mega_upgrade_cost}")
    draw_button(save_button, BLUE, "Save")
    draw_button(SHOP_BUTTON, YELLOW, "Shop")
    draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")
    draw_button(FIGHT_BUTTON, RED, "Fight")

def draw_shop_screen():
    # Title
    draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw shop items
    for idx, item_key in enumerate(SHOP_ITEMS):
        item = SHOP_ITEMS[item_key]
        button = shop_item_buttons[idx]
        pygame.draw.rect(WIN, LIGHT_GRAY, button)
        draw_text(item['name'], FONT, BLACK, WIN, button.centerx, button.y + 20)
        draw_text(f"Cost: {item['cost']} coins", FONT, BLACK, WIN, button.centerx, button.y + 50)
        if item['category'] == 'Consumables':
            draw_text(f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s", FONT, BLACK, WIN, button.centerx, button.y + 80)
        elif item['category'] == 'Battle Items':
            if item_key == 'Potion':
                draw_text("Heals 50 HP", FONT, BLACK, WIN, button.centerx, button.y + 80)
            elif item_key == 'Revive':
                draw_text("Auto-heal upon death", FONT, BLACK, WIN, button.centerx, button.y + 80)

    # Draw back button
    draw_button(shop_back_button, DARK_RED, "Back")

def draw_inventory_screen():
    # Title
    draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw Consumables
    draw_text("Consumables:", FONT, BLACK, WIN, 150, 100, center=False)
    for idx, item_key in enumerate(inventory['Consumables']):
        qty = inventory['Consumables'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 130 + idx * 30, center=False)

    # Draw Enemy Drops
    draw_text("Enemy Drops:", FONT, BLACK, WIN, 150, 200, center=False)
    for idx, item_key in enumerate(inventory['Enemy Drops']):
        qty = inventory['Enemy Drops'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 230 + idx * 30, center=False)

    # Draw Battle Items
    draw_text("Battle Items:", FONT, BLACK, WIN, 550, 100, center=False)
    for idx, item_key in enumerate(inventory['Battle Items']):
        qty = inventory['Battle Items'][item_key]
        action = ""
        if item_key == 'Potion':
            action = "Use Potion"
        elif item_key == 'Revive':
            action = "Auto-Use Revive"
        draw_text(f"{item_key}: {qty} ({action})", FONT, BLACK, WIN, 550, 130 + idx * 30, center=False)

    # Draw back button
    draw_button(inventory_back_button, DARK_RED, "Back")

def draw_combat_screen():
    # Title
    draw_text("Combat", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw player and enemy HP
    draw_text(f"Player HP: {player_hp}/100", FONT, BLACK, WIN, WIDTH//2, 150)
    draw_text(f"Blue Slime HP: {enemy_hp}/10", FONT, BLACK, WIN, WIDTH//2, 200)

    # Draw use potion button if player has potions
    if inventory['Battle Items']['Potion'] > 0:
        draw_button(use_potion_button, DARK_GREEN, "Use Potion")
    else:
        # Draw disabled button
        pygame.draw.rect(WIN, GRAY, use_potion_button)
        draw_text("No Potions", FONT, BLACK, WIN, use_potion_button.centerx, use_potion_button.centery)

def handle_combat_events(event):
    if in_combat:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Check if use potion button is clicked
            if use_potion_button.collidepoint(mouse_pos):
                use_potion()

def use_potion():
    global player_hp, inventory
    if inventory['Battle Items']['Potion'] > 0:
        inventory['Battle Items']['Potion'] -= 1
        player_hp += 50
        if player_hp > player_max_hp:
            player_hp = player_max_hp
        set_message("Potion used! Healed 50 HP.")
        try:
            use_item_sound.play()
        except:
            pass
    else:
        set_message("No Potions available!")

def start_combat():
    global in_combat, player_hp, enemy_hp, combat_start_time, last_combat_update
    in_combat = True
    player_hp = 100  # Reset player HP or keep current HP
    enemy_hp = 10
    combat_start_time = pygame.time.get_ticks()
    last_combat_update = combat_start_time

def update_combat():
    global player_hp, enemy_hp, in_combat, coins
    current_time = pygame.time.get_ticks()
    elapsed_since_last_update = (current_time - last_combat_update) / 1000  # seconds

    if elapsed_since_last_update >= 1:
        # Player deals damage
        enemy_hp -= 1
        # Enemy deals damage
        player_hp -= 1
        set_message("You dealt 1 damage. Enemy dealt 1 damage.")
        try:
            click_sound.play()
        except:
            pass

        # Update last_combat_update
        global last_combat_update
        last_combat_update = current_time

        # Check for combat outcomes
        if enemy_hp <= 0:
            # Enemy defeated
            in_combat = False
            set_message("Blue Slime defeated! Obtained Blue Slime Chunk.")
            inventory['Enemy Drops']['Blue Slime Chunk'] += 1
            try:
                purchase_sound.play()
            except:
                pass
        elif player_hp <= 0:
            # Player defeated
            if inventory['Battle Items']['Revive'] > 0:
                inventory['Battle Items']['Revive'] -= 1
                player_hp = 25  # Revive heals 25 HP
                set_message("Revived! Healed 25 HP.")
                try:
                    use_item_sound.play()
                except:
                    pass
            else:
                # Player dies and loses half their coins
                lost_coins = coins // 2
                coins -= lost_coins
                set_message(f"You died! Lost {lost_coins} coins.")
                in_combat = False

def handle_combat_logic():
    if in_combat:
        update_combat()

def draw_main_game():
    # Display coins and CPS
    draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH//2, 30)
    draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH//2, 60)

    # Draw buttons
    draw_button(collect_button, GREEN, "Collect")
    draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
    draw_button(mega_upgrade_button, DARK_GREEN, f"Mega Upgrade\nCost: {mega_upgrade_cost}")
    draw_button(save_button, BLUE, "Save")
    draw_button(SHOP_BUTTON, YELLOW, "Shop")
    draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")
    draw_button(FIGHT_BUTTON, RED, "Fight")

def draw_shop_screen():
    # Title
    draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw shop items
    for idx, item_key in enumerate(SHOP_ITEMS):
        item = SHOP_ITEMS[item_key]
        button = shop_item_buttons[idx]
        pygame.draw.rect(WIN, LIGHT_GRAY, button)
        draw_text(item['name'], FONT, BLACK, WIN, button.centerx, button.y + 20)
        draw_text(f"Cost: {item['cost']} coins", FONT, BLACK, WIN, button.centerx, button.y + 50)
        if item['category'] == 'Consumables':
            draw_text(f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s", FONT, BLACK, WIN, button.centerx, button.y + 80)
        elif item['category'] == 'Battle Items':
            if item_key == 'Potion':
                draw_text("Heals 50 HP", FONT, BLACK, WIN, button.centerx, button.y + 80)
            elif item_key == 'Revive':
                draw_text("Auto-heal upon death", FONT, BLACK, WIN, button.centerx, button.y + 80)

    # Draw back button
    draw_button(shop_back_button, DARK_RED, "Back")

def draw_inventory_screen():
    # Title
    draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw Consumables
    draw_text("Consumables:", FONT, BLACK, WIN, 150, 100, center=False)
    for idx, item_key in enumerate(inventory['Consumables']):
        qty = inventory['Consumables'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 130 + idx * 30, center=False)

    # Draw Enemy Drops
    draw_text("Enemy Drops:", FONT, BLACK, WIN, 150, 200, center=False)
    for idx, item_key in enumerate(inventory['Enemy Drops']):
        qty = inventory['Enemy Drops'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 230 + idx * 30, center=False)

    # Draw Battle Items
    draw_text("Battle Items:", FONT, BLACK, WIN, 550, 100, center=False)
    for idx, item_key in enumerate(inventory['Battle Items']):
        qty = inventory['Battle Items'][item_key]
        action = ""
        if item_key == 'Potion':
            action = "Use Potion"
        elif item_key == 'Revive':
            action = "Auto-Use Revive"
        draw_text(f"{item_key}: {qty} ({action})", FONT, BLACK, WIN, 550, 130 + idx * 30, center=False)

    # Draw back button
    draw_button(inventory_back_button, DARK_RED, "Back")

def draw_combat_screen():
    # Title
    draw_text("Combat", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw player and enemy HP
    draw_text(f"Player HP: {player_hp}/100", FONT, BLACK, WIN, WIDTH//2, 150)
    draw_text(f"Blue Slime HP: {enemy_hp}/10", FONT, BLACK, WIN, WIDTH//2, 200)

    # Draw use potion button if player has potions
    if inventory['Battle Items']['Potion'] > 0:
        draw_button(use_potion_button, DARK_GREEN, "Use Potion")
    else:
        # Draw disabled button
        pygame.draw.rect(WIN, GRAY, use_potion_button)
        draw_text("No Potions", FONT, BLACK, WIN, use_potion_button.centerx, use_potion_button.centery)

    # Optionally, add a 'Quit Combat' button
    # For simplicity, combat ends when player or enemy is defeated

def handle_combat_events(event):
    if in_combat:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Check if use potion button is clicked
            if use_potion_button.collidepoint(mouse_pos):
                use_potion()

def use_potion():
    global player_hp, inventory
    if inventory['Battle Items']['Potion'] > 0:
        inventory['Battle Items']['Potion'] -= 1
        player_hp += 50
        if player_hp > player_max_hp:
            player_hp = player_max_hp
        set_message("Potion used! Healed 50 HP.")
        try:
            use_item_sound.play()
        except:
            pass
    else:
        set_message("No Potions available!")

def start_combat():
    global in_combat, player_hp, enemy_hp, combat_start_time, last_combat_update
    in_combat = True
    player_hp = 100  # Reset player HP or keep current HP
    enemy_hp = 10
    combat_start_time = pygame.time.get_ticks()
    last_combat_update = combat_start_time

def update_combat():
    global player_hp, enemy_hp, in_combat, coins
    current_time = pygame.time.get_ticks()
    elapsed_since_last_update = (current_time - last_combat_update) / 1000  # seconds

    if elapsed_since_last_update >= 1:
        # Player deals damage
        enemy_hp -= 1
        # Enemy deals damage
        player_hp -= 1
        set_message("You dealt 1 damage. Enemy dealt 1 damage.")
        try:
            click_sound.play()
        except:
            pass

        # Update last_combat_update
        global last_combat_update
        last_combat_update = current_time

        # Check for combat outcomes
        if enemy_hp <= 0:
            # Enemy defeated
            in_combat = False
            set_message("Blue Slime defeated! Obtained Blue Slime Chunk.")
            inventory['Enemy Drops']['Blue Slime Chunk'] += 1
            try:
                purchase_sound.play()
            except:
                pass
        elif player_hp <= 0:
            # Player defeated
            if inventory['Battle Items']['Revive'] > 0:
                inventory['Battle Items']['Revive'] -= 1
                player_hp = 25  # Revive heals 25 HP
                set_message("Revived! Healed 25 HP.")
                try:
                    use_item_sound.play()
                except:
                    pass
            else:
                # Player dies and loses half their coins
                lost_coins = coins // 2
                coins -= lost_coins
                set_message(f"You died! Lost {lost_coins} coins.")
                in_combat = False

def handle_combat_logic():
    if in_combat:
        update_combat()

def draw_main_game():
    # Display coins and CPS
    draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH//2, 30)
    draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH//2, 60)

    # Draw buttons
    draw_button(collect_button, GREEN, "Collect")
    draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
    draw_button(mega_upgrade_button, DARK_GREEN, f"Mega Upgrade\nCost: {mega_upgrade_cost}")
    draw_button(save_button, BLUE, "Save")
    draw_button(SHOP_BUTTON, YELLOW, "Shop")
    draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")
    draw_button(FIGHT_BUTTON, RED, "Fight")

def draw_shop_screen():
    # Title
    draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw shop items
    for idx, item_key in enumerate(SHOP_ITEMS):
        item = SHOP_ITEMS[item_key]
        button = shop_item_buttons[idx]
        pygame.draw.rect(WIN, LIGHT_GRAY, button)
        draw_text(item['name'], FONT, BLACK, WIN, button.centerx, button.y + 20)
        draw_text(f"Cost: {item['cost']} coins", FONT, BLACK, WIN, button.centerx, button.y + 50)
        if item['category'] == 'Consumables':
            draw_text(f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s", FONT, BLACK, WIN, button.centerx, button.y + 80)
        elif item['category'] == 'Battle Items':
            if item_key == 'Potion':
                draw_text("Heals 50 HP", FONT, BLACK, WIN, button.centerx, button.y + 80)
            elif item_key == 'Revive':
                draw_text("Auto-heal upon death", FONT, BLACK, WIN, button.centerx, button.y + 80)

    # Draw back button
    draw_button(shop_back_button, DARK_RED, "Back")

def draw_inventory_screen():
    # Title
    draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw Consumables
    draw_text("Consumables:", FONT, BLACK, WIN, 150, 100, center=False)
    for idx, item_key in enumerate(inventory['Consumables']):
        qty = inventory['Consumables'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 130 + idx * 30, center=False)

    # Draw Enemy Drops
    draw_text("Enemy Drops:", FONT, BLACK, WIN, 150, 200, center=False)
    for idx, item_key in enumerate(inventory['Enemy Drops']):
        qty = inventory['Enemy Drops'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 230 + idx * 30, center=False)

    # Draw Battle Items
    draw_text("Battle Items:", FONT, BLACK, WIN, 550, 100, center=False)
    for idx, item_key in enumerate(inventory['Battle Items']):
        qty = inventory['Battle Items'][item_key]
        action = ""
        if item_key == 'Potion':
            action = "Use Potion"
        elif item_key == 'Revive':
            action = "Auto-Use Revive"
        draw_text(f"{item_key}: {qty} ({action})", FONT, BLACK, WIN, 550, 130 + idx * 30, center=False)

    # Draw back button
    draw_button(inventory_back_button, DARK_RED, "Back")

def draw_combat_screen():
    # Title
    draw_text("Combat", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw player and enemy HP
    draw_text(f"Player HP: {player_hp}/100", FONT, BLACK, WIN, WIDTH//2, 150)
    draw_text(f"Blue Slime HP: {enemy_hp}/10", FONT, BLACK, WIN, WIDTH//2, 200)

    # Draw use potion button if player has potions
    if inventory['Battle Items']['Potion'] > 0:
        draw_button(use_potion_button, DARK_GREEN, "Use Potion")
    else:
        # Draw disabled button
        pygame.draw.rect(WIN, GRAY, use_potion_button)
        draw_text("No Potions", FONT, BLACK, WIN, use_potion_button.centerx, use_potion_button.centery)

def handle_combat_events(event):
    if in_combat:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Check if use potion button is clicked
            if use_potion_button.collidepoint(mouse_pos):
                use_potion()

def use_potion():
    global player_hp, inventory
    if inventory['Battle Items']['Potion'] > 0:
        inventory['Battle Items']['Potion'] -= 1
        player_hp += 50
        if player_hp > player_max_hp:
            player_hp = player_max_hp
        set_message("Potion used! Healed 50 HP.")
        try:
            use_item_sound.play()
        except:
            pass
    else:
        set_message("No Potions available!")

def start_combat():
    global in_combat, player_hp, enemy_hp, combat_start_time, last_combat_update
    in_combat = True
    player_hp = 100  # Reset player HP or keep current HP
    enemy_hp = 10
    combat_start_time = pygame.time.get_ticks()
    last_combat_update = combat_start_time

def update_combat():
    global player_hp, enemy_hp, in_combat, coins
    current_time = pygame.time.get_ticks()
    elapsed_since_last_update = (current_time - last_combat_update) / 1000  # seconds

    if elapsed_since_last_update >= 1:
        # Player deals damage
        enemy_hp -= 1
        # Enemy deals damage
        player_hp -= 1
        set_message("You dealt 1 damage. Enemy dealt 1 damage.")
        try:
            click_sound.play()
        except:
            pass

        # Update last_combat_update
        global last_combat_update
        last_combat_update = current_time

        # Check for combat outcomes
        if enemy_hp <= 0:
            # Enemy defeated
            in_combat = False
            set_message("Blue Slime defeated! Obtained Blue Slime Chunk.")
            inventory['Enemy Drops']['Blue Slime Chunk'] += 1
            try:
                purchase_sound.play()
            except:
                pass
        elif player_hp <= 0:
            # Player defeated
            if inventory['Battle Items']['Revive'] > 0:
                inventory['Battle Items']['Revive'] -= 1
                player_hp = 25  # Revive heals 25 HP
                set_message("Revived! Healed 25 HP.")
                try:
                    use_item_sound.play()
                except:
                    pass
            else:
                # Player dies and loses half their coins
                lost_coins = coins // 2
                coins -= lost_coins
                set_message(f"You died! Lost {lost_coins} coins.")
                in_combat = False

def handle_combat_logic():
    if in_combat:
        update_combat()

def draw_main_game():
    # Display coins and CPS
    draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH//2, 30)
    draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH//2, 60)

    # Draw buttons
    draw_button(collect_button, GREEN, "Collect")
    draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
    draw_button(mega_upgrade_button, DARK_GREEN, f"Mega Upgrade\nCost: {mega_upgrade_cost}")
    draw_button(save_button, BLUE, "Save")
    draw_button(SHOP_BUTTON, YELLOW, "Shop")
    draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")
    draw_button(FIGHT_BUTTON, RED, "Fight")

def draw_shop_screen():
    # Title
    draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw shop items
    for idx, item_key in enumerate(SHOP_ITEMS):
        item = SHOP_ITEMS[item_key]
        button = shop_item_buttons[idx]
        pygame.draw.rect(WIN, LIGHT_GRAY, button)
        draw_text(item['name'], FONT, BLACK, WIN, button.centerx, button.y + 20)
        draw_text(f"Cost: {item['cost']} coins", FONT, BLACK, WIN, button.centerx, button.y + 50)
        if item['category'] == 'Consumables':
            draw_text(f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s", FONT, BLACK, WIN, button.centerx, button.y + 80)
        elif item['category'] == 'Battle Items':
            if item_key == 'Potion':
                draw_text("Heals 50 HP", FONT, BLACK, WIN, button.centerx, button.y + 80)
            elif item_key == 'Revive':
                draw_text("Auto-heal upon death", FONT, BLACK, WIN, button.centerx, button.y + 80)

    # Draw back button
    draw_button(shop_back_button, DARK_RED, "Back")

def draw_inventory_screen():
    # Title
    draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw Consumables
    draw_text("Consumables:", FONT, BLACK, WIN, 150, 100, center=False)
    for idx, item_key in enumerate(inventory['Consumables']):
        qty = inventory['Consumables'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 130 + idx * 30, center=False)

    # Draw Enemy Drops
    draw_text("Enemy Drops:", FONT, BLACK, WIN, 150, 200, center=False)
    for idx, item_key in enumerate(inventory['Enemy Drops']):
        qty = inventory['Enemy Drops'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 230 + idx * 30, center=False)

    # Draw Battle Items
    draw_text("Battle Items:", FONT, BLACK, WIN, 550, 100, center=False)
    for idx, item_key in enumerate(inventory['Battle Items']):
        qty = inventory['Battle Items'][item_key]
        action = ""
        if item_key == 'Potion':
            action = "Use Potion"
        elif item_key == 'Revive':
            action = "Auto-Use Revive"
        draw_text(f"{item_key}: {qty} ({action})", FONT, BLACK, WIN, 550, 130 + idx * 30, center=False)

    # Draw back button
    draw_button(inventory_back_button, DARK_RED, "Back")

def draw_combat_screen():
    # Title
    draw_text("Combat", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw player and enemy HP
    draw_text(f"Player HP: {player_hp}/100", FONT, BLACK, WIN, WIDTH//2, 150)
    draw_text(f"Blue Slime HP: {enemy_hp}/10", FONT, BLACK, WIN, WIDTH//2, 200)

    # Draw use potion button if player has potions
    if inventory['Battle Items']['Potion'] > 0:
        draw_button(use_potion_button, DARK_GREEN, "Use Potion")
    else:
        # Draw disabled button
        pygame.draw.rect(WIN, GRAY, use_potion_button)
        draw_text("No Potions", FONT, BLACK, WIN, use_potion_button.centerx, use_potion_button.centery)

def handle_combat_events(event):
    if in_combat:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Check if use potion button is clicked
            if use_potion_button.collidepoint(mouse_pos):
                use_potion()

def use_potion():
    global player_hp, inventory
    if inventory['Battle Items']['Potion'] > 0:
        inventory['Battle Items']['Potion'] -= 1
        player_hp += 50
        if player_hp > player_max_hp:
            player_hp = player_max_hp
        set_message("Potion used! Healed 50 HP.")
        try:
            use_item_sound.play()
        except:
            pass
    else:
        set_message("No Potions available!")

def start_combat():
    global in_combat, player_hp, enemy_hp, combat_start_time, last_combat_update
    in_combat = True
    player_hp = 100  # Reset player HP or keep current HP
    enemy_hp = 10
    combat_start_time = pygame.time.get_ticks()
    last_combat_update = combat_start_time

def update_combat():
    global player_hp, enemy_hp, in_combat, coins
    current_time = pygame.time.get_ticks()
    elapsed_since_last_update = (current_time - last_combat_update) / 1000  # seconds

    if elapsed_since_last_update >= 1:
        # Player deals damage
        enemy_hp -= 1
        # Enemy deals damage
        player_hp -= 1
        set_message("You dealt 1 damage. Enemy dealt 1 damage.")
        try:
            click_sound.play()
        except:
            pass

        # Update last_combat_update
        global last_combat_update
        last_combat_update = current_time

        # Check for combat outcomes
        if enemy_hp <= 0:
            # Enemy defeated
            in_combat = False
            set_message("Blue Slime defeated! Obtained Blue Slime Chunk.")
            inventory['Enemy Drops']['Blue Slime Chunk'] += 1
            try:
                purchase_sound.play()
            except:
                pass
        elif player_hp <= 0:
            # Player defeated
            if inventory['Battle Items']['Revive'] > 0:
                inventory['Battle Items']['Revive'] -= 1
                player_hp = 25  # Revive heals 25 HP
                set_message("Revived! Healed 25 HP.")
                try:
                    use_item_sound.play()
                except:
                    pass
            else:
                # Player dies and loses half their coins
                lost_coins = coins // 2
                coins -= lost_coins
                set_message(f"You died! Lost {lost_coins} coins.")
                in_combat = False

def handle_combat_logic():
    if in_combat:
        update_combat()

def draw_main_game():
    # Display coins and CPS
    draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH//2, 30)
    draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH//2, 60)

    # Draw buttons
    draw_button(collect_button, GREEN, "Collect")
    draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
    draw_button(mega_upgrade_button, DARK_GREEN, f"Mega Upgrade\nCost: {mega_upgrade_cost}")
    draw_button(save_button, BLUE, "Save")
    draw_button(SHOP_BUTTON, YELLOW, "Shop")
    draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")
    draw_button(FIGHT_BUTTON, RED, "Fight")

def draw_shop_screen():
    # Title
    draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw shop items
    for idx, item_key in enumerate(SHOP_ITEMS):
        item = SHOP_ITEMS[item_key]
        button = shop_item_buttons[idx]
        pygame.draw.rect(WIN, LIGHT_GRAY, button)
        draw_text(item['name'], FONT, BLACK, WIN, button.centerx, button.y + 20)
        draw_text(f"Cost: {item['cost']} coins", FONT, BLACK, WIN, button.centerx, button.y + 50)
        if item['category'] == 'Consumables':
            draw_text(f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s", FONT, BLACK, WIN, button.centerx, button.y + 80)
        elif item['category'] == 'Battle Items':
            if item_key == 'Potion':
                draw_text("Heals 50 HP", FONT, BLACK, WIN, button.centerx, button.y + 80)
            elif item_key == 'Revive':
                draw_text("Auto-heal upon death", FONT, BLACK, WIN, button.centerx, button.y + 80)

    # Draw back button
    draw_button(shop_back_button, DARK_RED, "Back")

def draw_inventory_screen():
    # Title
    draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw Consumables
    draw_text("Consumables:", FONT, BLACK, WIN, 150, 100, center=False)
    for idx, item_key in enumerate(inventory['Consumables']):
        qty = inventory['Consumables'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 130 + idx * 30, center=False)

    # Draw Enemy Drops
    draw_text("Enemy Drops:", FONT, BLACK, WIN, 150, 200, center=False)
    for idx, item_key in enumerate(inventory['Enemy Drops']):
        qty = inventory['Enemy Drops'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 230 + idx * 30, center=False)

    # Draw Battle Items
    draw_text("Battle Items:", FONT, BLACK, WIN, 550, 100, center=False)
    for idx, item_key in enumerate(inventory['Battle Items']):
        qty = inventory['Battle Items'][item_key]
        action = ""
        if item_key == 'Potion':
            action = "Use Potion"
        elif item_key == 'Revive':
            action = "Auto-Use Revive"
        draw_text(f"{item_key}: {qty} ({action})", FONT, BLACK, WIN, 550, 130 + idx * 30, center=False)

    # Draw back button
    draw_button(inventory_back_button, DARK_RED, "Back")

def draw_combat_screen():
    # Title
    draw_text("Combat", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw player and enemy HP
    draw_text(f"Player HP: {player_hp}/100", FONT, BLACK, WIN, WIDTH//2, 150)
    draw_text(f"Blue Slime HP: {enemy_hp}/10", FONT, BLACK, WIN, WIDTH//2, 200)

    # Draw use potion button if player has potions
    if inventory['Battle Items']['Potion'] > 0:
        draw_button(use_potion_button, DARK_GREEN, "Use Potion")
    else:
        # Draw disabled button
        pygame.draw.rect(WIN, GRAY, use_potion_button)
        draw_text("No Potions", FONT, BLACK, WIN, use_potion_button.centerx, use_potion_button.centery)

def handle_combat_events(event):
    if in_combat:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Check if use potion button is clicked
            if use_potion_button.collidepoint(mouse_pos):
                use_potion()

def use_potion():
    global player_hp, inventory
    if inventory['Battle Items']['Potion'] > 0:
        inventory['Battle Items']['Potion'] -= 1
        player_hp += 50
        if player_hp > player_max_hp:
            player_hp = player_max_hp
        set_message("Potion used! Healed 50 HP.")
        try:
            use_item_sound.play()
        except:
            pass
    else:
        set_message("No Potions available!")

def start_combat():
    global in_combat, player_hp, enemy_hp, combat_start_time, last_combat_update
    in_combat = True
    player_hp = 100  # Reset player HP or keep current HP
    enemy_hp = 10
    combat_start_time = pygame.time.get_ticks()
    last_combat_update = combat_start_time

def update_combat():
    global player_hp, enemy_hp, in_combat, coins
    current_time = pygame.time.get_ticks()
    elapsed_since_last_update = (current_time - last_combat_update) / 1000  # seconds

    if elapsed_since_last_update >= 1:
        # Player deals damage
        enemy_hp -= 1
        # Enemy deals damage
        player_hp -= 1
        set_message("You dealt 1 damage. Enemy dealt 1 damage.")
        try:
            click_sound.play()
        except:
            pass

        # Update last_combat_update
        global last_combat_update
        last_combat_update = current_time

        # Check for combat outcomes
        if enemy_hp <= 0:
            # Enemy defeated
            in_combat = False
            set_message("Blue Slime defeated! Obtained Blue Slime Chunk.")
            inventory['Enemy Drops']['Blue Slime Chunk'] += 1
            try:
                purchase_sound.play()
            except:
                pass
        elif player_hp <= 0:
            # Player defeated
            if inventory['Battle Items']['Revive'] > 0:
                inventory['Battle Items']['Revive'] -= 1
                player_hp = 25  # Revive heals 25 HP
                set_message("Revived! Healed 25 HP.")
                try:
                    use_item_sound.play()
                except:
                    pass
            else:
                # Player dies and loses half their coins
                lost_coins = coins // 2
                coins -= lost_coins
                set_message(f"You died! Lost {lost_coins} coins.")
                in_combat = False

def handle_combat_logic():
    if in_combat:
        update_combat()

def draw_main_game():
    # Display coins and CPS
    draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH//2, 30)
    draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH//2, 60)

    # Draw buttons
    draw_button(collect_button, GREEN, "Collect")
    draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
    draw_button(mega_upgrade_button, DARK_GREEN, f"Mega Upgrade\nCost: {mega_upgrade_cost}")
    draw_button(save_button, BLUE, "Save")
    draw_button(SHOP_BUTTON, YELLOW, "Shop")
    draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")
    draw_button(FIGHT_BUTTON, RED, "Fight")

def draw_shop_screen():
    # Title
    draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw shop items
    for idx, item_key in enumerate(SHOP_ITEMS):
        item = SHOP_ITEMS[item_key]
        button = shop_item_buttons[idx]
        pygame.draw.rect(WIN, LIGHT_GRAY, button)
        draw_text(item['name'], FONT, BLACK, WIN, button.centerx, button.y + 20)
        draw_text(f"Cost: {item['cost']} coins", FONT, BLACK, WIN, button.centerx, button.y + 50)
        if item['category'] == 'Consumables':
            draw_text(f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s", FONT, BLACK, WIN, button.centerx, button.y + 80)
        elif item['category'] == 'Battle Items':
            if item_key == 'Potion':
                draw_text("Heals 50 HP", FONT, BLACK, WIN, button.centerx, button.y + 80)
            elif item_key == 'Revive':
                draw_text("Auto-heal upon death", FONT, BLACK, WIN, button.centerx, button.y + 80)

    # Draw back button
    draw_button(shop_back_button, DARK_RED, "Back")

def draw_inventory_screen():
    # Title
    draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw Consumables
    draw_text("Consumables:", FONT, BLACK, WIN, 150, 100, center=False)
    for idx, item_key in enumerate(inventory['Consumables']):
        qty = inventory['Consumables'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 130 + idx * 30, center=False)

    # Draw Enemy Drops
    draw_text("Enemy Drops:", FONT, BLACK, WIN, 150, 200, center=False)
    for idx, item_key in enumerate(inventory['Enemy Drops']):
        qty = inventory['Enemy Drops'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 230 + idx * 30, center=False)

    # Draw Battle Items
    draw_text("Battle Items:", FONT, BLACK, WIN, 550, 100, center=False)
    for idx, item_key in enumerate(inventory['Battle Items']):
        qty = inventory['Battle Items'][item_key]
        action = ""
        if item_key == 'Potion':
            action = "Use Potion"
        elif item_key == 'Revive':
            action = "Auto-Use Revive"
        draw_text(f"{item_key}: {qty} ({action})", FONT, BLACK, WIN, 550, 130 + idx * 30, center=False)

    # Draw back button
    draw_button(inventory_back_button, DARK_RED, "Back")

def draw_combat_screen():
    # Title
    draw_text("Combat", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw player and enemy HP
    draw_text(f"Player HP: {player_hp}/100", FONT, BLACK, WIN, WIDTH//2, 150)
    draw_text(f"Blue Slime HP: {enemy_hp}/10", FONT, BLACK, WIN, WIDTH//2, 200)

    # Draw use potion button if player has potions
    if inventory['Battle Items']['Potion'] > 0:
        draw_button(use_potion_button, DARK_GREEN, "Use Potion")
    else:
        # Draw disabled button
        pygame.draw.rect(WIN, GRAY, use_potion_button)
        draw_text("No Potions", FONT, BLACK, WIN, use_potion_button.centerx, use_potion_button.centery)

    # Optionally, add a 'Quit Combat' button
    # For simplicity, combat ends when player or enemy is defeated

def handle_combat_events(event):
    if in_combat:
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            # Check if use potion button is clicked
            if use_potion_button.collidepoint(mouse_pos):
                use_potion()

def use_potion():
    global player_hp, inventory
    if inventory['Battle Items']['Potion'] > 0:
        inventory['Battle Items']['Potion'] -= 1
        player_hp += 50
        if player_hp > player_max_hp:
            player_hp = player_max_hp
        set_message("Potion used! Healed 50 HP.")
        try:
            use_item_sound.play()
        except:
            pass
    else:
        set_message("No Potions available!")

def start_combat():
    global in_combat, player_hp, enemy_hp, combat_start_time, last_combat_update
    in_combat = True
    player_hp = 100  # Reset player HP or keep current HP
    enemy_hp = 10
    combat_start_time = pygame.time.get_ticks()
    last_combat_update = combat_start_time

def update_combat():
    global player_hp, enemy_hp, in_combat, coins
    current_time = pygame.time.get_ticks()
    elapsed_since_last_update = (current_time - last_combat_update) / 1000  # seconds

    if elapsed_since_last_update >= 1:
        # Player deals damage
        enemy_hp -= 1
        # Enemy deals damage
        player_hp -= 1
        set_message("You dealt 1 damage. Enemy dealt 1 damage.")
        try:
            click_sound.play()
        except:
            pass

        # Update last_combat_update
        global last_combat_update
        last_combat_update = current_time

        # Check for combat outcomes
        if enemy_hp <= 0:
            # Enemy defeated
            in_combat = False
            set_message("Blue Slime defeated! Obtained Blue Slime Chunk.")
            inventory['Enemy Drops']['Blue Slime Chunk'] += 1
            try:
                purchase_sound.play()
            except:
                pass
        elif player_hp <= 0:
            # Player defeated
            if inventory['Battle Items']['Revive'] > 0:
                inventory['Battle Items']['Revive'] -= 1
                player_hp = 25  # Revive heals 25 HP
                set_message("Revived! Healed 25 HP.")
                try:
                    use_item_sound.play()
                except:
                    pass
            else:
                # Player dies and loses half their coins
                lost_coins = coins // 2
                coins -= lost_coins
                set_message(f"You died! Lost {lost_coins} coins.")
                in_combat = False

def handle_combat_logic():
    if in_combat:
        update_combat()

def draw_main_game():
    # Display coins and CPS
    draw_text(f"Coins: {coins}", FONT, BLACK, WIN, WIDTH//2, 30)
    draw_text(f"CPS: {cps}", FONT, BLACK, WIN, WIDTH//2, 60)

    # Draw buttons
    draw_button(collect_button, GREEN, "Collect")
    draw_button(upgrade_button, GRAY, f"Upgrade\nCost: {upgrade_cost}")
    draw_button(mega_upgrade_button, DARK_GREEN, f"Mega Upgrade\nCost: {mega_upgrade_cost}")
    draw_button(save_button, BLUE, "Save")
    draw_button(SHOP_BUTTON, YELLOW, "Shop")
    draw_button(INVENTORY_BUTTON, YELLOW, "Inventory")
    draw_button(FIGHT_BUTTON, RED, "Fight")

def draw_shop_screen():
    # Title
    draw_text("Shop", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw shop items
    for idx, item_key in enumerate(SHOP_ITEMS):
        item = SHOP_ITEMS[item_key]
        button = shop_item_buttons[idx]
        pygame.draw.rect(WIN, LIGHT_GRAY, button)
        draw_text(item['name'], FONT, BLACK, WIN, button.centerx, button.y + 20)
        draw_text(f"Cost: {item['cost']} coins", FONT, BLACK, WIN, button.centerx, button.y + 50)
        if item['category'] == 'Consumables':
            draw_text(f"+{item['effect']['cps_increase']} CPS\nfor {item['effect']['duration']}s", FONT, BLACK, WIN, button.centerx, button.y + 80)
        elif item['category'] == 'Battle Items':
            if item_key == 'Potion':
                draw_text("Heals 50 HP", FONT, BLACK, WIN, button.centerx, button.y + 80)
            elif item_key == 'Revive':
                draw_text("Auto-heal upon death", FONT, BLACK, WIN, button.centerx, button.y + 80)

    # Draw back button
    draw_button(shop_back_button, DARK_RED, "Back")

def draw_inventory_screen():
    # Title
    draw_text("Inventory", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw Consumables
    draw_text("Consumables:", FONT, BLACK, WIN, 150, 100, center=False)
    for idx, item_key in enumerate(inventory['Consumables']):
        qty = inventory['Consumables'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 130 + idx * 30, center=False)

    # Draw Enemy Drops
    draw_text("Enemy Drops:", FONT, BLACK, WIN, 150, 200, center=False)
    for idx, item_key in enumerate(inventory['Enemy Drops']):
        qty = inventory['Enemy Drops'][item_key]
        draw_text(f"{item_key}: {qty}", FONT, BLACK, WIN, 150, 230 + idx * 30, center=False)

    # Draw Battle Items
    draw_text("Battle Items:", FONT, BLACK, WIN, 550, 100, center=False)
    for idx, item_key in enumerate(inventory['Battle Items']):
        qty = inventory['Battle Items'][item_key]
        action = ""
        if item_key == 'Potion':
            action = "Use Potion"
        elif item_key == 'Revive':
            action = "Auto-Use Revive"
        draw_text(f"{item_key}: {qty} ({action})", FONT, BLACK, WIN, 550, 130 + idx * 30, center=False)

    # Draw back button
    draw_button(inventory_back_button, DARK_RED, "Back")

def draw_combat_screen():
    # Title
    draw_text("Combat", BIG_FONT, BLACK, WIN, WIDTH//2, 50)

    # Draw player and enemy HP
    draw_text(f"Player HP: {player_hp}/100", FONT, BLACK, WIN, WIDTH//2, 150)
    draw_text(f"Blue Slime HP: {enemy_hp}/10", FONT, BLACK, WIN, WIDTH//2, 200)

    # Draw use potion button if player has potions
    if inventory['Battle Items']['Potion'] > 0:
        draw_button(use_potion_button, DARK_GREEN
