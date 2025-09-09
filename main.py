import pygame as pg
import random
import time
import asyncio

pg.init()
clock = pg.time.Clock()

# Window setup
win_width, win_height = 800, 600
screen = pg.display.set_mode((win_width, win_height))
pg.display.set_caption("Falling Debris - Waves & Shop")

# Colors
black = (0, 0, 0)
gray = (150, 150, 150)  # changed to lighter gray for platforms
dark_gray = (70, 70, 70)
brown = (139, 69, 19)
white = (255, 255, 255)
red = (200, 0, 0)
green = (0, 200, 0)

# Fonts
font = pg.font.Font(None, 30)
big_font = pg.font.Font(None, 50)

# Dirt block settings
dirt_block_size = 20

# Player settings
player_size = 60
ground_y = win_height - player_size - dirt_block_size  # ground level (top of dirt)
player_pos = [win_width // 2, ground_y]
player_vel_y = 0
gravity = 0.5
jump_strength = -10
is_jumping = False

# Load images (ensure these files exist)
player_image = pg.image.load("./assets/images/Technoblade_skin.webp")
player_image = pg.transform.scale(player_image, (player_size, player_size))

obj_size = 80
obj_image = pg.image.load("./assets/images/Anvil_(N)_JE3.png")
obj_image = pg.transform.scale(obj_image, (obj_size, obj_size))

bg_image = pg.image.load("./assets/images/096fbe5269d2fae069305fe2742d5be5.jpg")
bg_image = pg.transform.scale(bg_image, (win_width, win_height))

rav_width, rav_height = 120, 60
rav_image = pg.image.load("./assets/images/Ravager_JE1.png")
rav_image = pg.transform.scale(rav_image, (rav_width, rav_height))

# Walls thickness
wall_thickness = dirt_block_size

# Create platforms (x_block, y_block, length_in_blocks)
platform_specs = [
    (5, 26, 10),
    (25, 23, 8),
    (40, 25, 6),
]

platforms = []
for start_x, start_y, length in platform_specs:
    for i in range(length):
        rect = pg.Rect(
            start_x * dirt_block_size + i * dirt_block_size,
            start_y * dirt_block_size,
            dirt_block_size,
            dirt_block_size,
        )
        platforms.append(rect)

# Game variables
score = 0
lives = 10
running = True
speed = 10  # falling speed of anvils
game_state = 1   # 1: gameplay, 2: shop

# Ravs and waves
wave = 1
ravs = []
rav_speed = 7
drop_chance = 0.02
obj_data = []

# Wave timer (30 seconds)
WAVE_DURATION = 30_000
wave_start_time = pg.time.get_ticks()

# Shop related
shop_open = False
coins = 0  # equal to score, for clarity

# Player weapons/inventory
inventory = {
    "crossbow": 0,  # ammo count
    "explosives": 0,
    "clear_all": 0
}

weapon_prices = {
    "crossbow": 5,
    "explosives": 15,
    "clear_all": 50
}

# Crossbow settings
crossbow_speed = 15
crossbow_arrows = []  # arrows flying, each arrow is dict with x, y

def spawn_ravs(num_ravs):
    ravs.clear()
    spacing = win_width // (num_ravs + 1)
    for i in range(num_ravs):
        x = -rav_width - i * (spacing // 2)
        y = 50 + (i % 2) * 30
        ravs.append({'x': x, 'y': y, 'speed': rav_speed})

spawn_ravs(wave)  # Spawn initial rav(s)

def create_object_from_rav(obj_data, rav_x, rav_y):
    if len(obj_data) < 10 and random.random() < drop_chance:
        x = rav_x + rav_width // 2 - obj_size // 2
        y = rav_y + rav_height
        obj_data.append([x, y, obj_image])

def update_objects(obj_data):
    global score
    for obj in obj_data[:]:
        obj[1] += speed
        screen.blit(obj[2], (obj[0], obj[1]))
        if obj[1] > win_height:
            obj_data.remove(obj)
            score += 1
            global coins
            coins += 1

def change_speed(score):
    global speed, rav_speed, drop_chance
    if score > 20:
        speed = 12
        rav_speed = 12
        drop_chance = 0.03
    if score > 40:
        speed = 13
        rav_speed = 14
        drop_chance = 0.04
    if score > 60:
        speed = 15
        rav_speed = 16
        drop_chance = 0.05
    if score > 100:
        speed = 20
        rav_speed = 18
        drop_chance = 0.07
    if score > 500:
        speed = 35
        rav_speed = 20
        drop_chance = 0.1

def collision_check(obj_data, player_pos):
    global running, lives
    player_rect = pg.Rect(player_pos[0], player_pos[1], player_size, player_size)
    for obj in obj_data[:]:
        obj_rect = pg.Rect(obj[0], obj[1], obj_size, obj_size)
        if player_rect.colliderect(obj_rect):
            lives -= 1
            obj_data.remove(obj)
            if lives <= 0:
                running = False
                time.sleep(2)
                break

def move_player(keys, player_pos):
    x, y = player_pos
    if keys[pg.K_LEFT]:
        x -= 7
    if keys[pg.K_RIGHT]:
        x += 7
    # Keep player inside walls
    x = max(wall_thickness, min(win_width - player_size - wall_thickness, x))
    return x, y

def player_jump_and_gravity(player_pos, velocity_y, is_jumping):
    velocity_y += gravity
    player_pos[1] += velocity_y

    player_rect = pg.Rect(player_pos[0], player_pos[1], player_size, player_size)
    on_platform = False

    # Check platform collisions (player landing on top)
    for plat in platforms:
        if player_rect.colliderect(plat) and player_pos[1] + player_size <= plat.y + 10 and velocity_y >= 0:
            player_pos[1] = plat.y - player_size
            velocity_y = 0
            is_jumping = False
            on_platform = True
            break

    # Check ground collision
    if player_pos[1] >= ground_y:
        player_pos[1] = ground_y
        velocity_y = 0
        is_jumping = False
        on_platform = True

    return player_pos, velocity_y, is_jumping, on_platform

def update_ravs():
    for rav in ravs:
        rav['x'] += rav['speed']
        if rav['x'] > win_width:
            rav['x'] = -rav_width
        screen.blit(rav_image, (rav['x'], rav['y']))

def draw_platforms():
    for block in platforms:
        pg.draw.rect(screen, gray, block)  # Changed to gray

def draw_walls():
    pg.draw.rect(screen, dark_gray, (0, 0, wall_thickness, win_height))
    pg.draw.rect(screen, dark_gray, (win_width - wall_thickness, 0, wall_thickness, win_height))

def draw_ui():
    score_text = font.render(f'Coins: {coins}', True, black)
    lives_text = font.render(f'Lives: {lives}', True, black)
    wave_text = font.render(f'Wave: {wave}', True, black)
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (10, 40))
    screen.blit(wave_text, (10, 70))
    screen.blit(font.render('Press S to open/close Shop', True, black), (10, 100))
    screen.blit(font.render('Press K to Skip Wave', True, black), (10, 130))
    screen.blit(font.render('Press C to shoot Crossbow', True, black), (10, 160))

def next_wave():
    global wave, wave_start_time
    wave += 1
    spawn_ravs(wave)  # Increase ravs by 1 each wave
    wave_start_time = pg.time.get_ticks()

# Crossbow arrow shooting
def shoot_crossbow(player_pos):
    # Arrow starts at player's top center
    arrow_x = player_pos[0] + player_size // 2
    arrow_y = player_pos[1]
    crossbow_arrows.append({'x': arrow_x, 'y': arrow_y})

def update_arrows():
    for arrow in crossbow_arrows[:]:
        arrow['y'] -= crossbow_speed
        # Draw arrow as small rectangle
        pg.draw.rect(screen, red, (arrow['x'], arrow['y'], 5, 15))
        if arrow['y'] < 0:
            crossbow_arrows.remove(arrow)
            continue
        # Check collision with ravs
        for rav in ravs[:]:
            rav_rect = pg.Rect(rav['x'], rav['y'], rav_width, rav_height)
            arrow_rect = pg.Rect(arrow['x'], arrow['y'], 5, 15)
            if rav_rect.colliderect(arrow_rect):
                ravs.remove(rav)
                if arrow in crossbow_arrows:
                    crossbow_arrows.remove(arrow)
                global score, coins
                score += 10
                coins += 10
                break

def draw_shop():
    # Dim background
    overlay = pg.Surface((win_width, win_height))
    overlay.set_alpha(180)
    overlay.fill(white)
    screen.blit(overlay, (0, 0))

    # Draw shop box
    box_rect = pg.Rect(150, 100, 500, 400)
    pg.draw.rect(screen, dark_gray, box_rect)
    pg.draw.rect(screen, black, box_rect, 3)

    title = big_font.render("SHOP - Buy Items", True, white)
    screen.blit(title, (box_rect.x + 130, box_rect.y + 20))

    # Draw items with prices and owned counts
    items = ["crossbow", "explosives", "clear_all"]
    y_start = box_rect.y + 100
    for i, item in enumerate(items):
        item_name = item.capitalize()
        price = weapon_prices[item]
        owned = inventory[item]
        text = font.render(f"{item_name} - {price} coins - Owned: {owned}", True, white)
        screen.blit(text, (box_rect.x + 50, y_start + i * 50))

    instructions = font.render("Press 1/2/3 to buy items, ESC to close shop", True, white)
    screen.blit(instructions, (box_rect.x + 30, box_rect.y + 350))

def use_explosives():
    # Destroy all ravs on screen
    global score, coins
    count = len(ravs)
    ravs.clear()
    score += 20 * count
    coins += 20 * count

def use_clear_all():
    global score, coins
    ravs.clear()
    obj_data.clear()
    score += 50
    coins += 50

def skip_wave():
    next_wave()

player_vel_y = 0

async def main():

    global running, shop_open, coins, is_jumping, player_vel_y, player_pos, game_state

    while running:

        if game_state == 1:

            keys = pg.key.get_pressed()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_s:
                        game_state = 2
                    elif event.key == pg.K_k:
                        skip_wave()
                    elif event.key == pg.K_c:
                        # Shoot crossbow if owned
                        if inventory["crossbow"] > 0:
                            shoot_crossbow(player_pos)
                            inventory["crossbow"] -= 1
                    elif event.key == pg.K_e:
                        # Use explosives if owned
                        if inventory["explosives"] > 0:
                            use_explosives()
                            inventory["explosives"] -= 1
                    elif event.key == pg.K_n:
                        # Use clear_all if owned
                        if inventory["clear_all"] > 0:
                            use_clear_all()
                            inventory["clear_all"] -= 1
                    elif event.key in (pg.K_UP, pg.K_SPACE):
                        if not is_jumping:
                            is_jumping = True
                            player_vel_y = jump_strength

            # Move player with wall constraints
            player_pos[0], player_pos[1] = move_player(keys, player_pos)

            # Jump and gravity logic with platform collision
            player_pos, player_vel_y, is_jumping, _ = player_jump_and_gravity(player_pos, player_vel_y, is_jumping)

            # Draw background first
            screen.blit(bg_image, (0, 0))

            # Draw platforms and walls
            draw_platforms()
            draw_walls()

            # Update and draw ravs
            update_ravs()

            # Drop anvils from ravs
            for rav in ravs:
                create_object_from_rav(obj_data, rav['x'], rav['y'])

            # Update and draw falling anvils
            update_objects(obj_data)

            # Check collisions with player
            collision_check(obj_data, player_pos)

            # Draw player
            screen.blit(player_image, (player_pos[0], player_pos[1]))

            # Update and draw crossbow arrows
            update_arrows()

            # Adjust difficulty by score
            change_speed(score)

            # Wave timer: increase wave every 30 seconds
            current_time = pg.time.get_ticks()
            if current_time - wave_start_time > WAVE_DURATION:
                next_wave()

            # Draw UI
            draw_ui()

            # Show owned weapons counts
            inv_text = font.render(f"Crossbow Ammo: {inventory['crossbow']}  Explosives: {inventory['explosives']} Clear-Alls: {inventory['clear_all']}", True, black)
            screen.blit(inv_text, (10, 550))

            # Instructions to use weapons
            instr_text = font.render("Press E for Explosives, N for Clear-All", True, black)
            screen.blit(instr_text, (10, 580))

        elif game_state == 2:
            keys = pg.key.get_pressed()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE or event.key == pg.K_s:
                        game_state = 1
                    elif event.key == pg.K_1:
                        # Buy crossbow
                        if coins >= weapon_prices["crossbow"]:
                            coins -= weapon_prices["crossbow"]
                            inventory["crossbow"] += 5  # 5 arrows per purchase
                    elif event.key == pg.K_2:
                        # Buy explosives
                        if coins >= weapon_prices["explosives"]:
                            coins -= weapon_prices["explosives"]
                            inventory["explosives"] += 1
                    elif event.key == pg.K_3:
                        # Buy clear_all
                        if coins >= weapon_prices["clear_all"]:
                            coins -= weapon_prices["clear_all"]
                            inventory["clear_all"] += 1
            # Draw shop overlay and UI
            draw_shop()
            
        clock.tick(30)
        pg.display.flip()

        await asyncio.sleep(0)

    pg.quit()



asyncio.run(main())
