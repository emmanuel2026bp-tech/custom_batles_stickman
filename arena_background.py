import math
import os
import random
import pygame

try:
    from PIL import Image
except ImportError:
    Image = None


TERRAIN_MENU_ARMORY = "armeria_menu"
TERRAIN_MENU = "campo_verde"
TERRAIN_AMPHITHEATER = "coliseo"
TERRAIN_OCEAN = "ocean"

COMBAT_TERRAIN_VARIANTS = (TERRAIN_MENU, TERRAIN_AMPHITHEATER, TERRAIN_OCEAN)
TERRAIN_VARIANTS = (TERRAIN_MENU_ARMORY, *COMBAT_TERRAIN_VARIANTS)

C_ARMORY_CEILING = (34, 30, 38)
C_ARMORY_WALL_DARK = (62, 42, 32)
C_ARMORY_WALL_MID = (98, 66, 46)
C_ARMORY_BEAM_DARK = (72, 46, 30)
C_ARMORY_BEAM_MID = (118, 76, 48)
C_ARMORY_BEAM_HI = (158, 108, 68)
C_ARMORY_STONE = (96, 92, 98)
C_ARMORY_STONE_DARK = (66, 62, 70)
C_ARMORY_FLOOR_DARK = (58, 40, 28)
C_ARMORY_FLOOR_MID = (92, 62, 40)
C_ARMORY_FLOOR_HI = (132, 90, 56)
C_ARMORY_TORCH_GLOW = (242, 178, 74)
C_ARMORY_FIRE = (252, 126, 42)
C_ARMORY_SHIELD_RED = (188, 52, 46)
C_ARMORY_SHIELD_WHT = (224, 214, 198)
C_ARMORY_STEEL = (156, 168, 182)
C_ARMORY_IRON = (74, 78, 86)

C_FIELD_SKY_TOP = (74, 184, 226)
C_FIELD_SKY_BOT = (178, 232, 240)
C_FIELD_SUN = (255, 236, 138)
C_FIELD_CLOUD = (244, 248, 252)
C_FIELD_CLOUD_SHADE = (198, 222, 236)
C_FIELD_HILL_FAR = (96, 178, 112)
C_FIELD_HILL_MID = (66, 152, 82)
C_FIELD_GRASS_LIGHT = (92, 186, 74)
C_FIELD_GRASS_MAIN = (62, 154, 54)
C_FIELD_GRASS_SOFT = (78, 170, 64)
C_FIELD_BUSH_HI = (104, 196, 82)
C_FIELD_BUSH_MID = (56, 144, 48)
C_FIELD_BUSH_SHADE = (44, 122, 42)
C_FIELD_TRUNK_MAIN = (128, 82, 42)
C_FIELD_TRUNK_SHADE = (92, 56, 28)
C_FIELD_PATH_LIGHT = (218, 192, 132)
C_FIELD_PATH_SHADE = (182, 154, 98)
C_FIELD_FLOWER_Y = (252, 222, 64)
C_FIELD_FLOWER_W = (248, 250, 252)
C_FIELD_FLOWER_P = (236, 128, 168)
C_FIELD_HOUSE_WALL = (242, 234, 214)
C_FIELD_HOUSE_SHADE = (198, 188, 168)
C_FIELD_HOUSE_ROOF = (196, 76, 56)
C_FIELD_HOUSE_ROOF_DARK = (148, 52, 38)
C_FIELD_HOUSE_WIN = (126, 206, 236)
C_FIELD_HOUSE_DOOR = (118, 76, 40)

C_FIELD_LAKE_SHORE = (198, 178, 124)
C_FIELD_LAKE_DEEP = (46, 134, 198)
C_FIELD_LAKE_MAIN = (78, 174, 226)
C_FIELD_LAKE_HI = (182, 236, 252)

C_SKY_TOP = (46, 178, 214)
C_SKY_BOT = (158, 226, 232)

C_WALL_HI = (244, 168, 92)
C_WALL_MID = (224, 134, 68)
C_WALL_SHADE = (176, 94, 52)
C_WALL_DARK = (118, 56, 36)
C_ARCH_VOID = (36, 34, 42)
C_ARCH_DEEP = (68, 36, 34)
C_PORTAL_STONE = (232, 184, 118)
C_PORTAL_SHADOW = (148, 98, 62)

C_SAND_LIGHT = (244, 214, 136)
C_SAND_MID = (222, 188, 108)
C_FLOOR_SLATE = (78, 112, 124)
C_FLOOR_DARK = (52, 80, 92)

C_ROCK_TOP = (152, 92, 64)
C_ROCK_FACE = (116, 66, 48)
C_ROCK_SHADE = (74, 40, 32)
C_OUTLINE = (24, 20, 26)
C_BORDER = (88, 102, 126)

C_NIGHT_SKY_TOP = (8, 34, 96)
C_NIGHT_SKY_MID = (16, 66, 148)
C_NIGHT_SKY_HOR = (36, 106, 184)
C_NIGHT_MIST = (68, 134, 204)
C_STAR_WHITE = (232, 244, 255)
C_STAR_CYAN = (120, 232, 238)
C_CLOUD_DARK = (20, 52, 118)
C_CLOUD_LIGHT = (44, 88, 162)
C_MOON_CORE = (248, 252, 255)
C_MOON_CRATER = (172, 204, 238)
C_MOON_GLOW_OUTER = (28, 86, 168)
C_MOON_GLOW = (98, 178, 236)

C_MTN_FAR_LIGHT = (72, 96, 168)
C_MTN_FAR_DARK = (44, 62, 124)
C_MTN_NEAR_LIGHT = (56, 74, 142)
C_MTN_NEAR_DARK = (32, 46, 102)
C_MTN_RIDGE_HI = (116, 144, 214)

C_LAKE_BASE = (54, 86, 158)
C_LAKE_SHORE = (94, 104, 168)
C_LAKE_SHIMMER = (218, 244, 255)
C_LAKE_RIPPLE = (126, 176, 228)

C_CLIFF_TOP = (36, 52, 118)
C_CLIFF_MID = (22, 32, 82)
C_CLIFF_DARK = (14, 20, 54)
C_CLIFF_RIM = (84, 112, 186)


def _pixelize_image_to_surface(
    image_path: str, target_w: int, target_h: int, pixel_scale: int = 4
) -> pygame.Surface | None:
    if not image_path or not os.path.isfile(image_path):
        return None
    try:
        if Image is not None:
            pil_img = Image.open(image_path).convert("RGB")
            low_w = max(120, target_w // pixel_scale)
            low_h = max(45, target_h // pixel_scale)
            low = pil_img.resize((low_w, low_h), Image.Resampling.BILINEAR)
            quant = low.quantize(
                colors=28, method=Image.Quantize.MEDIANCUT
            ).convert("RGB")
            stretched = quant.resize(
                (target_w, target_h), Image.Resampling.NEAREST
            )
            return pygame.image.frombuffer(
                stretched.tobytes(), (target_w, target_h), "RGB"
            ).convert()

        raw_surf = pygame.image.load(image_path).convert()
        low_w = max(120, target_w // pixel_scale)
        low_h = max(45, target_h // pixel_scale)
        small = pygame.transform.smoothscale(raw_surf, (low_w, low_h))
        return pygame.transform.scale(small, (target_w, target_h))
    except Exception:
        return None


def _build_procedural_8bit_menu_armory(
    scene_w: int, scene_h: int, ground_y: int, pixel_size: int = 4
) -> pygame.Surface:
    pw = max(240, scene_w // pixel_size)
    ph = max(90, scene_h // pixel_size)
    p_ground = max(20, int(round(ground_y / pixel_size)))

    low = pygame.Surface((pw, ph))
    low.fill(C_ARMORY_WALL_DARK)

    ceiling_h = max(10, int(p_ground * 0.25))
    pygame.draw.rect(low, C_ARMORY_CEILING, (0, 0, pw, ceiling_h))
    for x in range(0, pw, 16):
        pygame.draw.line(low, C_ARMORY_BEAM_DARK, (x, 0), (x + 12, ceiling_h), 1)

    wall_bot = max(ceiling_h + 10, p_ground - 4)
    pygame.draw.rect(low, C_ARMORY_WALL_MID, (0, ceiling_h, pw // 2, wall_bot - ceiling_h))
    for wy in range(ceiling_h + 3, wall_bot, 4):
        pygame.draw.line(low, C_ARMORY_WALL_DARK, (0, wy), (pw // 2, wy), 1)

    stone_x = int(pw * 0.26)
    stone_w = max(28, pw // 6)
    pygame.draw.rect(low, C_ARMORY_STONE_DARK, (stone_x, ceiling_h, stone_w, wall_bot - ceiling_h))
    for sy in range(ceiling_h + 2, wall_bot - 2, 5):
        for sx in range(stone_x + 1, stone_x + stone_w - 3, 7):
            pygame.draw.rect(low, C_ARMORY_STONE, (sx, sy, 6, 4))

    glow_cx = stone_x + stone_w // 2
    glow_cy = ceiling_h + (wall_bot - ceiling_h) // 3
    pygame.draw.circle(low, C_ARMORY_TORCH_GLOW, (glow_cx, glow_cy), 12)
    pygame.draw.circle(low, C_ARMORY_FIRE, (glow_cx, glow_cy), 5)

    furnace_x = int(pw * 0.78)
    furnace_y = max(ceiling_h + 8, wall_bot - 22)
    pygame.draw.rect(low, C_ARMORY_STONE_DARK, (furnace_x, furnace_y, 24, 22))
    pygame.draw.rect(low, C_ARMORY_FIRE, (furnace_x + 6, furnace_y + 8, 12, 12))
    pygame.draw.circle(low, C_ARMORY_TORCH_GLOW, (furnace_x + 12, furnace_y + 10), 5)

    shield_x = max(14, pw // 10)
    shield_y = ceiling_h + (wall_bot - ceiling_h) // 3
    pygame.draw.circle(low, C_ARMORY_IRON, (shield_x, shield_y), 8)
    pygame.draw.circle(low, C_ARMORY_SHIELD_RED, (shield_x, shield_y), 7)
    pygame.draw.rect(low, C_ARMORY_SHIELD_WHT, (shield_x - 7, shield_y, 7, 7))
    pygame.draw.rect(low, C_ARMORY_SHIELD_WHT, (shield_x, shield_y - 7, 7, 7))
    pygame.draw.circle(low, C_ARMORY_STEEL, (shield_x, shield_y), 2)

    rack_x = shield_x + 12
    rack_y = wall_bot - 14
    pygame.draw.rect(low, C_ARMORY_BEAM_MID, (rack_x, rack_y, 26, 14))
    for idx in range(4):
        sx = rack_x + 4 + idx * 5
        pygame.draw.rect(low, C_ARMORY_STEEL, (sx, rack_y - 9, 2, 9))
        pygame.draw.rect(low, C_ARMORY_BEAM_HI, (sx - 1, rack_y - 1, 4, 2))

    for idx in range(4):
        lx = stone_x + 5 + idx * 5
        pygame.draw.line(low, C_ARMORY_BEAM_MID, (lx, wall_bot - 2), (lx, ceiling_h + 6), 1)
        pygame.draw.rect(low, C_ARMORY_STEEL, (lx - 1, ceiling_h + 4, 3, 4))

    pillar_x = int(pw * 0.48)
    pygame.draw.rect(low, C_ARMORY_BEAM_DARK, (pillar_x, ceiling_h, 7, ph - ceiling_h))
    pygame.draw.rect(low, C_ARMORY_BEAM_MID, (pillar_x + 1, ceiling_h, 4, ph - ceiling_h))
    pygame.draw.rect(low, C_ARMORY_BEAM_HI, (pillar_x + 2, ceiling_h, 1, ph - ceiling_h))
    pygame.draw.rect(low, C_ARMORY_BEAM_MID, (0, ceiling_h + 4, pw, 4))

    pygame.draw.rect(low, C_ARMORY_FLOOR_DARK, (0, p_ground - 2, pw, ph - (p_ground - 2)))
    for fy in range(p_ground - 2, ph, 4):
        col = C_ARMORY_FLOOR_MID if (fy // 4) % 2 == 0 else C_ARMORY_FLOOR_HI
        pygame.draw.rect(low, col, (0, fy, pw, 3))
        pygame.draw.line(low, C_ARMORY_FLOOR_DARK, (0, fy + 3), (pw, fy + 3), 1)

    return pygame.transform.scale(low, (scene_w, scene_h))


def _draw_8bit_tree(
    low: pygame.Surface, tx: int, base_y: int, scale: float = 1.0
):
    trunk_w = max(2, int(round(3 * scale)))
    trunk_h = max(4, int(round(7 * scale)))
    tr_x = tx - trunk_w // 2
    tr_y = base_y - trunk_h

    pygame.draw.rect(low, C_FIELD_TRUNK_MAIN, (tr_x, tr_y, trunk_w, trunk_h))
    pygame.draw.rect(
        low,
        C_FIELD_TRUNK_SHADE,
        (tr_x + trunk_w - 1, tr_y, 1, trunk_h),
    )

    r_main = max(4, int(round(6 * scale)))
    r_sub = max(3, int(round(4 * scale)))
    cy = tr_y - r_main + 2

    pygame.draw.circle(low, C_FIELD_BUSH_SHADE, (tx, cy + 2), r_main)
    pygame.draw.circle(low, C_FIELD_BUSH_MID, (tx, cy), r_main)
    pygame.draw.circle(
        low, C_FIELD_BUSH_MID, (tx - max(2, r_main - 2), cy + 1), r_sub
    )
    pygame.draw.circle(
        low, C_FIELD_BUSH_MID, (tx + max(2, r_main - 2), cy + 1), r_sub
    )
    pygame.draw.circle(
        low,
        C_FIELD_BUSH_HI,
        (tx - max(1, r_main // 3), cy - max(1, r_main // 3)),
        max(2, r_sub - 1),
    )


def _draw_8bit_distant_house(low: pygame.Surface, hx: int, base_y: int):
    wall_w = 12
    wall_h = 7
    wx = hx - wall_w // 2
    wy = base_y - wall_h

    pygame.draw.rect(low, C_FIELD_HOUSE_WALL, (wx, wy, wall_w, wall_h))
    pygame.draw.rect(
        low, C_FIELD_HOUSE_SHADE, (wx + wall_w - 3, wy, 3, wall_h)
    )

    roof_pts = [
        (wx - 2, wy),
        (hx, wy - 5),
        (wx + wall_w + 2, wy),
    ]
    pygame.draw.polygon(low, C_FIELD_HOUSE_ROOF, roof_pts)
    pygame.draw.line(
        low, C_FIELD_HOUSE_ROOF_DARK, (hx, wy - 5), (wx + wall_w + 2, wy), 1
    )

    pygame.draw.rect(low, C_FIELD_HOUSE_DOOR, (wx + 2, wy + 3, 2, 4))
    pygame.draw.rect(low, C_FIELD_HOUSE_WIN, (wx + 6, wy + 2, 2, 2))


def _draw_8bit_field_lake(low: pygame.Surface, lx: int, ly: int, rx: int, ry: int):
    pygame.draw.ellipse(
        low,
        C_FIELD_LAKE_SHORE,
        (lx - rx - 2, ly - ry - 1, (rx + 2) * 2, (ry + 1) * 2),
    )
    pygame.draw.ellipse(low, C_FIELD_LAKE_DEEP, (lx - rx, ly - ry, rx * 2, ry * 2))
    pygame.draw.ellipse(
        low,
        C_FIELD_LAKE_MAIN,
        (lx - int(rx * 0.88), ly - int(ry * 0.78), int(rx * 1.76), int(ry * 1.50)),
    )
    for dy in range(-max(1, ry // 2), max(2, ry // 2)):
        span = max(2, int(rx * 0.55) - abs(dy) * 2)
        for ox in range(-span, span + 1, 3):
            px = lx + ox
            py = ly + dy
            if 0 <= px < low.get_width() and 0 <= py < low.get_height():
                low.set_at((px, py), C_FIELD_LAKE_HI)


def _build_procedural_8bit_green_field(
    scene_w: int, scene_h: int, ground_y: int, pixel_size: int = 4
) -> pygame.Surface:
    pw = max(240, scene_w // pixel_size)
    ph = max(90, scene_h // pixel_size)
    p_ground = max(20, int(round(ground_y / pixel_size)))

    low = pygame.Surface((pw, ph))
    low.fill(C_FIELD_GRASS_MAIN)
    rng = random.Random(1080)

    sky_h = max(12, int(p_ground * 0.62))
    for y in range(sky_h):
        t = y / sky_h
        r = int(C_FIELD_SKY_TOP[0] + (C_FIELD_SKY_BOT[0] - C_FIELD_SKY_TOP[0]) * t)
        g = int(C_FIELD_SKY_TOP[1] + (C_FIELD_SKY_BOT[1] - C_FIELD_SKY_TOP[1]) * t)
        b = int(C_FIELD_SKY_TOP[2] + (C_FIELD_SKY_BOT[2] - C_FIELD_SKY_TOP[2]) * t)
        pygame.draw.line(low, (r, g, b), (0, y), (pw, y))

    sun_x = int(pw * 0.16)
    sun_y = max(10, sky_h // 4)
    pygame.draw.circle(low, C_FIELD_SUN, (sun_x, sun_y), 7)

    cloud_span = max(76, pw // 7)
    for cx in range(22, pw - 20, cloud_span):
        cy = rng.randint(6, max(12, sky_h // 2))
        cw = rng.randint(18, 28)
        pygame.draw.rect(low, C_FIELD_CLOUD_SHADE, (cx, cy + 3, cw, 2))
        pygame.draw.rect(low, C_FIELD_CLOUD, (cx + 2, cy, max(8, cw - 4), 3))
        pygame.draw.rect(low, C_FIELD_CLOUD, (cx + cw // 3, cy - 2, 7, 2))

    far_base_y = max(14, sky_h - 6)
    for x in range(0, pw, 2):
        wave1 = math.sin(x * 0.022 + 0.4) * 6.0 + math.cos(x * 0.011) * 4.0
        y1 = min(p_ground, int(far_base_y - wave1))
        h1 = max(1, p_ground - y1 + 2)
        pygame.draw.rect(low, C_FIELD_HILL_FAR, (x, y1, 2, h1))

    mid_base_y = max(18, sky_h + 2)
    for x in range(0, pw, 2):
        wave2 = math.cos(x * 0.018 - 0.8) * 5.0 + math.sin(x * 0.009 + 1.2) * 3.0
        y2 = min(p_ground, int(mid_base_y - wave2))
        h2 = max(1, p_ground - y2 + 2)
        pygame.draw.rect(low, C_FIELD_HILL_MID, (x, y2, 2, h2))

    house_span = max(210, pw // 4)
    for hx in range(house_span // 2, pw - 24, house_span):
        wave2 = math.cos(hx * 0.018 - 0.8) * 5.0 + math.sin(hx * 0.009 + 1.2) * 3.0
        hy = min(p_ground, int(mid_base_y - wave2))
        _draw_8bit_distant_house(low, hx, hy)

    tree_span = max(58, pw // 13)
    for idx, tx in enumerate(range(24, pw - 16, tree_span)):
        jitter_x = tx + rng.randint(-6, 6)
        wave2 = (
            math.cos(jitter_x * 0.018 - 0.8) * 5.0
            + math.sin(jitter_x * 0.009 + 1.2) * 3.0
        )
        hill_y = min(p_ground, int(mid_base_y - wave2))
        tree_base_y = min(p_ground, max(hill_y + 3, p_ground - rng.randint(0, 6)))
        scale = 0.82 if idx % 3 == 0 else (1.12 if idx % 4 == 1 else 1.0)
        _draw_8bit_tree(low, jitter_x, tree_base_y, scale=scale)

    pygame.draw.rect(low, C_FIELD_GRASS_LIGHT, (0, p_ground - 3, pw, 3))
    pygame.draw.rect(low, C_FIELD_GRASS_MAIN, (0, p_ground, pw, max(2, ph - p_ground)))
    pygame.draw.rect(
        low, C_FIELD_GRASS_SOFT, (0, p_ground + 6, pw, max(1, ph - (p_ground + 6)))
    )

    lake_y = min(ph - 6, p_ground + 9)
    lake_rx = max(14, min(26, pw // 28))
    lake_ry = max(3, min(6, max(4, (ph - p_ground) // 5)))
    lake_span = max(180, pw // 3)
    for lx in range(lake_span // 2, pw - lake_rx - 8, lake_span):
        _draw_8bit_field_lake(low, lx, lake_y, lake_rx, lake_ry)

    path_y = min(ph - 8, p_ground + 2)
    pygame.draw.rect(low, C_FIELD_PATH_SHADE, (0, path_y + 2, pw, 2))
    pygame.draw.rect(low, C_FIELD_PATH_LIGHT, (0, path_y, pw, 2))

    bush_span = max(34, pw // 22)
    for bx in range(14, pw - 12, bush_span):
        by = p_ground - 1 if (bx // bush_span) % 2 == 0 else min(ph - 4, path_y + 4)
        bw = rng.randint(6, 10)
        pygame.draw.rect(low, C_FIELD_BUSH_SHADE, (bx, by + 1, bw, 2))
        pygame.draw.rect(low, C_FIELD_BUSH_MID, (bx + 1, by, max(3, bw - 2), 2))
        pygame.draw.rect(low, C_FIELD_BUSH_HI, (bx + 1, by - 1, max(2, bw // 2), 1))

    flower_palette = (C_FIELD_FLOWER_Y, C_FIELD_FLOWER_W, C_FIELD_FLOWER_P)
    for gx in range(5, pw - 4, 8):
        gy = rng.randint(max(2, p_ground - 6), min(ph - 2, p_ground + 15))
        low.set_at((gx, gy), C_FIELD_GRASS_LIGHT)
        if gx % 24 == 13:
            f_col = flower_palette[(gx // 24) % len(flower_palette)]
            low.set_at((gx + 1, gy - 1), f_col)

    return pygame.transform.scale(low, (scene_w, scene_h))


def _build_procedural_8bit_amphitheater(
    scene_w: int, scene_h: int, ground_y: int, pixel_size: int = 4
) -> pygame.Surface:
    pw = max(240, scene_w // pixel_size)
    ph = max(90, scene_h // pixel_size)
    p_ground = max(20, int(round(ground_y / pixel_size)))

    low = pygame.Surface((pw, ph))

    sky_h = max(1, int(p_ground * 0.56))
    for y in range(sky_h):
        t = y / sky_h
        r = int(C_SKY_TOP[0] + (C_SKY_BOT[0] - C_SKY_TOP[0]) * t)
        g = int(C_SKY_TOP[1] + (C_SKY_BOT[1] - C_SKY_TOP[1]) * t)
        b = int(C_SKY_TOP[2] + (C_SKY_BOT[2] - C_SKY_TOP[2]) * t)
        pygame.draw.line(low, (r, g, b), (0, y), (pw, y))

    wall_top_center = int(sky_h * 0.66)
    wall_bot_y = int(p_ground * 0.84)
    for x in range(0, pw, 2):
        nx = (x - pw * 0.5) / (pw * 0.5)
        top_y = int(wall_top_center - (nx * nx) * (sky_h * 0.42))
        col = (
            C_WALL_HI
            if nx > 0.1
            else (C_WALL_SHADE if nx < -0.55 else C_WALL_MID)
        )
        pygame.draw.rect(
            low, col, (x, top_y, 2, max(1, wall_bot_y - top_y))
        )
        pygame.draw.rect(low, C_OUTLINE, (x, top_y, 2, 1))

    win_cols = max(15, pw // 28)
    for i in range(win_cols):
        tx = (i + 0.5) / win_cols
        wx = int(tx * (pw - 16)) + 6
        nx = (wx - pw * 0.5) / (pw * 0.5)
        wy = int(wall_top_center - (nx * nx) * (sky_h * 0.42)) + 5
        pygame.draw.rect(low, C_OUTLINE, (wx - 1, wy - 1, 7, 6))
        pygame.draw.rect(low, C_SKY_BOT, (wx, wy, 5, 4))

    upper_arch_y = int(wall_top_center + 14)
    lower_arch_y = int(wall_top_center + 33)
    arch_spacing = 18
    arch_w = 9
    arch_h = 11

    for level_y in (upper_arch_y, lower_arch_y):
        for x in range(4, pw - 4, arch_spacing):
            nx = (x - pw * 0.5) / (pw * 0.5)
            curve_dy = int((nx * nx) * 6)
            ay = level_y - curve_dy
            pygame.draw.rect(
                low, C_WALL_HI, (x + arch_w, ay - 1, 4, arch_h + 2)
            )
            pygame.draw.rect(
                low, C_WALL_SHADE, (x + arch_w + 3, ay - 1, 2, arch_h + 2)
            )
            pygame.draw.rect(low, C_OUTLINE, (x, ay, arch_w, arch_h))
            pygame.draw.rect(
                low, C_ARCH_VOID, (x + 1, ay + 2, arch_w - 2, arch_h - 2)
            )
            pygame.draw.rect(low, C_ARCH_DEEP, (x + 2, ay + 1, arch_w - 4, 2))

    bal_y = lower_arch_y - 4
    pygame.draw.rect(low, C_WALL_HI, (0, bal_y, pw, 3))
    for bx in range(2, pw, 4):
        pygame.draw.rect(low, C_WALL_SHADE, (bx, bal_y, 1, 3))

    gate_w = 34
    gate_h = 34
    gate_x = pw // 2 - gate_w // 2
    gate_y = wall_bot_y - gate_h + 2
    pygame.draw.rect(
        low, C_OUTLINE, (gate_x - 2, gate_y - 3, gate_w + 4, gate_h + 3)
    )
    pygame.draw.rect(low, C_PORTAL_STONE, (gate_x, gate_y, gate_w, gate_h))
    pygame.draw.rect(
        low, C_PORTAL_SHADOW, (gate_x + gate_w - 6, gate_y, 6, gate_h)
    )
    pygame.draw.rect(low, C_WALL_HI, (gate_x - 3, gate_y - 4, gate_w + 6, 4))

    door_w = 14
    door_h = 20
    door_x = pw // 2 - door_w // 2
    door_y = gate_y + gate_h - door_h
    pygame.draw.rect(
        low, C_OUTLINE, (door_x - 1, door_y - 1, door_w + 2, door_h + 1)
    )
    pygame.draw.rect(
        low, C_ARCH_DEEP, (door_x, door_y + 4, door_w, door_h - 4)
    )
    pygame.draw.circle(low, C_ARCH_DEEP, (pw // 2, door_y + 5), door_w // 2)

    for step in range(6):
        sy = wall_bot_y + step * 2
        if sy >= p_ground:
            break
        left_w = max(10, pw // 2 - gate_w // 2 - step * 8)
        pygame.draw.rect(
            low,
            C_WALL_SHADE if step % 2 == 0 else C_WALL_MID,
            (0, sy, left_w, 2),
        )
        right_start = min(pw, pw // 2 + gate_w // 2 + step * 8)
        if right_start < pw:
            pygame.draw.rect(
                low,
                C_WALL_HI if step % 2 == 0 else C_WALL_MID,
                (right_start, sy, pw - right_start, 2),
            )

    pygame.draw.rect(
        low, C_FLOOR_SLATE, (0, p_ground - 4, pw, ph - (p_ground - 4))
    )
    sand_center_x = int(pw * 0.56)
    sand_center_y = int(p_ground + (ph - p_ground) * 0.42)
    sand_rx = int(pw * 0.46)
    sand_ry = int((ph - p_ground) * 0.46)
    pygame.draw.ellipse(
        low,
        C_SAND_MID,
        (
            sand_center_x - sand_rx,
            sand_center_y - sand_ry,
            sand_rx * 2,
            sand_ry * 2,
        ),
    )
    pygame.draw.ellipse(
        low,
        C_SAND_LIGHT,
        (
            sand_center_x - int(sand_rx * 0.92),
            sand_center_y - int(sand_ry * 0.85),
            int(sand_rx * 1.84),
            int(sand_ry * 1.70),
        ),
    )

    rng = random.Random(2026)
    for _ in range(max(14, pw // 24)):
        rx = rng.randint(pw // 5, int(pw * 0.85))
        ry = rng.randint(p_ground + 2, ph - 8)
        pygame.draw.line(
            low, C_SAND_MID, (rx, ry), (rx + rng.randint(4, 10), ry), 1
        )

    rock_specs = [
        (0, ph - 26, 36, 26),
        (36, ph - 16, 26, 16),
        (68, ph - 11, 20, 11),
        (pw - 88, ph - 11, 20, 11),
        (pw - 62, ph - 16, 26, 16),
        (pw - 36, ph - 28, 36, 28),
    ]
    for rx, ry, rw, rh in rock_specs:
        pygame.draw.rect(low, C_OUTLINE, (rx - 1, ry - 1, rw + 2, rh + 2))
        pygame.draw.rect(low, C_ROCK_FACE, (rx, ry, rw, rh))
        pygame.draw.rect(low, C_ROCK_TOP, (rx, ry, rw, 4))
        pygame.draw.rect(
            low, C_ROCK_SHADE, (rx + rw - 6, ry + 4, 6, max(1, rh - 4))
        )

    return pygame.transform.scale(low, (scene_w, scene_h))


def _build_procedural_8bit_ocean(
    scene_w: int, scene_h: int, ground_y: int, pixel_size: int = 4
) -> pygame.Surface:
    pw = max(240, scene_w // pixel_size)
    ph = max(90, scene_h // pixel_size)
    p_ground = max(20, int(round(ground_y / pixel_size)))

    low = pygame.Surface((pw, ph))
    rng = random.Random(3363)

    horizon_y = max(14, int(p_ground * 0.64))
    for y in range(horizon_y):
        t = y / horizon_y
        if t < 0.65:
            k = t / 0.65
            col = (
                int(C_NIGHT_SKY_TOP[0] + (C_NIGHT_SKY_MID[0] - C_NIGHT_SKY_TOP[0]) * k),
                int(C_NIGHT_SKY_TOP[1] + (C_NIGHT_SKY_MID[1] - C_NIGHT_SKY_TOP[1]) * k),
                int(C_NIGHT_SKY_TOP[2] + (C_NIGHT_SKY_MID[2] - C_NIGHT_SKY_TOP[2]) * k),
            )
        else:
            k = (t - 0.65) / 0.35
            col = (
                int(C_NIGHT_SKY_MID[0] + (C_NIGHT_SKY_HOR[0] - C_NIGHT_SKY_MID[0]) * k),
                int(C_NIGHT_SKY_MID[1] + (C_NIGHT_SKY_HOR[1] - C_NIGHT_SKY_MID[1]) * k),
                int(C_NIGHT_SKY_MID[2] + (C_NIGHT_SKY_HOR[2] - C_NIGHT_SKY_MID[2]) * k),
            )
        pygame.draw.line(low, col, (0, y), (pw, y))

    star_count = max(65, pw // 3)
    for _ in range(star_count):
        sx = rng.randint(2, pw - 3)
        sy = rng.randint(2, max(4, horizon_y - 6))
        scol = C_STAR_CYAN if rng.random() < 0.16 else C_STAR_WHITE
        low.set_at((sx, sy), scol)
        if rng.random() < 0.14 and 2 < sx < pw - 3 and 2 < sy < horizon_y - 4:
            low.set_at((sx + 1, sy), scol)
            low.set_at((sx - 1, sy), scol)
            low.set_at((sx, sy + 1), scol)
            low.set_at((sx, sy - 1), scol)

    cloud_span = max(85, pw // 6)
    for cx in range(18, pw - 18, cloud_span):
        cy = rng.randint(max(6, horizon_y // 4), max(12, horizon_y - 16))
        cw = rng.randint(18, 30)
        pygame.draw.rect(low, C_CLOUD_DARK, (cx, cy + 2, cw, 3))
        pygame.draw.rect(low, C_CLOUD_LIGHT, (cx + 3, cy, max(8, cw - 6), 2))
        pygame.draw.rect(low, C_CLOUD_LIGHT, (cx + cw // 3, cy - 2, 7, 2))

    for _ in range(max(6, pw // 85)):
        gx = rng.randint(12, pw - 13)
        gy = rng.randint(8, max(14, horizon_y - 8))
        pygame.draw.circle(low, C_NIGHT_SKY_HOR, (gx, gy), 6)
        pygame.draw.circle(low, C_STAR_CYAN, (gx, gy), 2)

    moon_x = int(pw * 0.72)
    moon_y = max(14, int(horizon_y * 0.40))
    moon_r = max(7, min(14, ph // 14))
    pygame.draw.circle(low, C_MOON_GLOW_OUTER, (moon_x, moon_y), moon_r + 6)
    pygame.draw.circle(low, C_MOON_GLOW, (moon_x, moon_y), moon_r + 3)
    pygame.draw.circle(low, C_MOON_CORE, (moon_x, moon_y), moon_r)
    for dx, dy, cr in (
        (-moon_r // 3, -moon_r // 4, 2),
        (moon_r // 4, -moon_r // 5, 1),
        (-moon_r // 5, moon_r // 3, 2),
        (moon_r // 3, moon_r // 4, 1),
        (0, -moon_r // 2, 1),
    ):
        pygame.draw.circle(low, C_MOON_CRATER, (moon_x + dx, moon_y + dy), cr)

    far_step = max(48, pw // 9)
    for x_start in range(-far_step, pw + far_step, far_step):
        cx = x_start + far_step // 2
        peak_h = rng.randint(12, max(18, int(horizon_y * 0.42)))
        top_y = max(10, horizon_y - peak_h)
        half_w = int(far_step * 0.65)
        pygame.draw.polygon(
            low,
            C_MTN_FAR_LIGHT,
            [(cx, top_y), (cx + half_w, horizon_y), (cx, horizon_y)],
        )
        pygame.draw.polygon(
            low,
            C_MTN_FAR_DARK,
            [(cx, top_y), (cx - half_w, horizon_y), (cx, horizon_y)],
        )

    peak_span = max(70, pw // 5)
    for idx, x_start in enumerate(range(-peak_span // 2, pw + peak_span, peak_span)):
        cx = x_start + peak_span // 2
        peak_h = rng.randint(17, max(24, int(horizon_y * 0.58)))
        top_y = max(8, horizon_y - peak_h)
        half_w = int(peak_span * 0.58)
        left_x = cx - half_w
        right_x = cx + half_w

        light_poly = [(cx, top_y), (right_x, horizon_y), (cx, horizon_y)]
        shade_poly = [(cx, top_y), (left_x, horizon_y), (cx, horizon_y)]
        pygame.draw.polygon(
            low,
            C_MTN_FAR_LIGHT if idx % 2 == 0 else C_MTN_NEAR_LIGHT,
            light_poly,
        )
        pygame.draw.polygon(
            low,
            C_MTN_FAR_DARK if idx % 2 == 0 else C_MTN_NEAR_DARK,
            shade_poly,
        )
        pygame.draw.line(
            low,
            C_MTN_RIDGE_HI,
            (cx, top_y),
            (min(pw - 1, cx + half_w // 2), min(horizon_y, top_y + peak_h // 2)),
            1,
        )

    if horizon_y - 2 >= 0:
        pygame.draw.line(low, C_NIGHT_MIST, (0, horizon_y - 2), (pw, horizon_y - 2), 1)
        pygame.draw.line(low, C_LAKE_SHORE, (0, horizon_y - 1), (pw, horizon_y - 1), 1)

    water_top = horizon_y
    water_bot = max(water_top + 4, p_ground - 2)
    lake_h = max(6, water_bot - water_top + 2)
    pygame.draw.rect(low, C_LAKE_BASE, (0, water_top, pw, lake_h))
    pygame.draw.rect(low, C_LAKE_SHORE, (0, water_bot - 1, pw, 2))

    for ry in range(water_top + 1, water_bot, 2):
        spread = 3 + (ry - water_top) // 2
        for rx in range(moon_x - spread * 2, moon_x + spread * 2 + 1, 2):
            if 0 <= rx < pw:
                dist_m = abs(rx - moon_x)
                if dist_m <= spread and rng.random() < 0.78:
                    low.set_at((rx, ry), C_LAKE_SHIMMER)
                elif dist_m <= spread * 2 and rng.random() < 0.35:
                    low.set_at((rx, ry), C_LAKE_RIPPLE)

    water_rock_step = max(36, pw // 13)
    for rx in range(16, pw - 16, water_rock_step):
        jitter_x = rx + rng.randint(-8, 8)
        rw = rng.randint(6, 13)
        rh = rng.randint(3, min(7, max(3, water_bot - water_top - 1)))
        ry = max(water_top + 1, water_bot - rh)
        poly = [
            (jitter_x, water_bot),
            (jitter_x + 1, ry + 1),
            (jitter_x + rw // 2, ry),
            (jitter_x + rw - 1, ry + 2),
            (jitter_x + rw, water_bot),
        ]
        pygame.draw.polygon(low, C_OUTLINE, poly)
        pygame.draw.polygon(low, C_CLIFF_MID, poly)
        pygame.draw.line(
            low,
            C_CLIFF_RIM,
            (jitter_x + 1, ry + 1),
            (jitter_x + rw // 2, ry),
            1,
        )
        pygame.draw.rect(
            low,
            C_CLIFF_DARK,
            (jitter_x + rw // 2, ry + 1, max(1, rw // 2), max(1, water_bot - ry - 1)),
        )
        if jitter_x - 3 >= 0:
            low.set_at((jitter_x - 2, water_bot - 1), C_LAKE_RIPPLE)
        if jitter_x + rw + 2 < pw:
            low.set_at((jitter_x + rw + 1, water_bot - 1), C_LAKE_SHIMMER)

    pygame.draw.rect(low, C_CLIFF_TOP, (0, p_ground - 2, pw, 4))
    pygame.draw.rect(low, C_CLIFF_RIM, (0, p_ground - 2, pw, 1))
    pygame.draw.rect(low, C_CLIFF_MID, (0, p_ground + 2, pw, ph - (p_ground + 2)))

    return pygame.transform.scale(low, (scene_w, scene_h))


class ArenaBackground:
    def __init__(
        self,
        width: int,
        height: int,
        world_w: int,
        image_path: str | None = None,
        terrain_variant: str | None = None,
    ):
        self.width = width
        self.height = height
        self.world_w = world_w
        self.ground_y = height - 106
        self.image_path = image_path or self._resolve_default_image()
        self.terrain_variant = (
            terrain_variant
            if terrain_variant in TERRAIN_VARIANTS
            else TERRAIN_MENU_ARMORY
        )
        self.terrain_surf = self._build_terrain_surface()

    @staticmethod
    def _resolve_default_image() -> str | None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = (
            os.path.join(base_dir, "image_2979dd.png"),
            os.path.join(base_dir, "amphitheater_8bit.png"),
            os.path.join(base_dir, "arena_8bit.png"),
            "image_2979dd.png",
        )
        for path in candidates:
            if os.path.isfile(path):
                return path
        return None

    @staticmethod
    def _resolve_menu_armory_image() -> str | None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = (
            os.path.join(base_dir, "image_344959.jpg"),
            os.path.join(base_dir, "menu_armory.jpg"),
            os.path.join(base_dir, "menu_armory.png"),
            "image_344959.jpg",
        )
        for path in candidates:
            if os.path.isfile(path):
                return path
        return None

    def set_menu_terrain(self) -> str:
        if self.terrain_variant != TERRAIN_MENU_ARMORY or self.terrain_surf is None:
            self.terrain_variant = TERRAIN_MENU_ARMORY
            self.terrain_surf = self._build_terrain_surface()
        return self.terrain_variant

    def randomize_terrain(self, rng: random.Random | None = None) -> str:
        picker = rng if rng is not None else random
        self.terrain_variant = picker.choice(COMBAT_TERRAIN_VARIANTS)
        self.terrain_surf = self._build_terrain_surface()
        return self.terrain_variant

    def _build_terrain_surface(self) -> pygame.Surface:
        if self.terrain_variant == TERRAIN_MENU_ARMORY:
            armory_path = self._resolve_menu_armory_image()
            loaded_armory = (
                _pixelize_image_to_surface(
                    armory_path, self.world_w, self.height, pixel_scale=4
                )
                if armory_path
                else None
            )
            surf = (
                loaded_armory
                if loaded_armory is not None
                else _build_procedural_8bit_menu_armory(
                    self.world_w, self.height, self.ground_y, pixel_size=4
                )
            )
        elif self.terrain_variant == TERRAIN_MENU:
            surf = _build_procedural_8bit_green_field(
                self.world_w, self.height, self.ground_y, pixel_size=4
            )
        elif self.terrain_variant == TERRAIN_OCEAN:
            surf = _build_procedural_8bit_ocean(
                self.world_w, self.height, self.ground_y, pixel_size=4
            )
        else:
            loaded_8bit = (
                _pixelize_image_to_surface(
                    self.image_path, self.world_w, self.height, pixel_scale=4
                )
                if self.image_path
                else None
            )
            surf = (
                loaded_8bit
                if loaded_8bit is not None
                else _build_procedural_8bit_amphitheater(
                    self.world_w, self.height, self.ground_y, pixel_size=4
                )
            )

        if self.terrain_variant not in (TERRAIN_MENU_ARMORY, TERRAIN_MENU):
            mid_x = self.world_w // 2
            for y in range(self.ground_y - 24, self.ground_y, 6):
                pygame.draw.rect(surf, C_BORDER, (mid_x - 2, y, 4, 4))

        return surf

    def draw(self, screen: pygame.Surface, cam_x: float):
        screen.blit(self.terrain_surf, (-int(round(cam_x)), 0))