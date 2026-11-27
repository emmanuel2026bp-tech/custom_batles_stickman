import math
import pygame


def draw_python_shield(
    screen: pygame.Surface,
    cx: int,
    cy: int,
    facing: int,
    shield_w: int = 16,
    shield_h: int = 28,
    flash: bool = False,
) -> None:
    """Dibuja un escudo grande con el emblema de dos serpientes entrelazadas de Python."""
    rect = pygame.Rect(
        cx - shield_w // 2,
        cy - shield_h // 2,
        shield_w,
        shield_h,
    )

    rim_col = (255, 255, 255) if flash else (196, 206, 222)
    bg_col = (255, 255, 255) if flash else (28, 32, 42)
    py_blue = (255, 255, 255) if flash else (55, 118, 171)
    py_yellow = (255, 255, 255) if flash else (255, 212, 59)
    eye_col = (255, 255, 255) if flash else (245, 248, 252)

    pygame.draw.rect(screen, bg_col, rect, border_radius=5)
    pygame.draw.rect(screen, rim_col, rect, width=2, border_radius=5)

    inner_w = max(8, shield_w - 4)
    inner_h = max(14, shield_h - 6)
    ix = cx - inner_w // 2
    iy = cy - inner_h // 2
    mid_y = iy + inner_h // 2

    # Mitad superior: bloque azul de Python
    top_rect = pygame.Rect(ix, iy, inner_w, inner_h // 2)
    pygame.draw.rect(screen, py_blue, top_rect, border_radius=3)
    pygame.draw.rect(
        screen,
        py_blue,
        (ix + inner_w // 2, iy + 1, inner_w // 2, max(3, inner_h // 4)),
        border_radius=2,
    )

    # Mitad inferior: bloque amarillo de Python
    bot_rect = pygame.Rect(ix, mid_y, inner_w, inner_h - inner_h // 2)
    pygame.draw.rect(screen, py_yellow, bot_rect, border_radius=3)
    pygame.draw.rect(
        screen,
        py_yellow,
        (ix, bot_rect.bottom - max(4, inner_h // 4) - 1, inner_w // 2, max(3, inner_h // 4)),
        border_radius=2,
    )

    # Franja divisoria central diagonal/escalonada característica del logo
    pygame.draw.line(screen, bg_col, (ix + 1, mid_y), (ix + inner_w - 1, mid_y), 2)

    # Ojos característicos del logo de Python
    eye_blue_x = ix + max(2, inner_w // 4) + (facing * 1)
    eye_blue_y = iy + max(2, inner_h // 5)
    eye_yellow_x = ix + inner_w - max(3, inner_w // 4) + (facing * 1)
    eye_yellow_y = bot_rect.bottom - max(3, inner_h // 5)

    pygame.draw.circle(screen, eye_col, (eye_blue_x, eye_blue_y), 1)
    pygame.draw.circle(screen, eye_col, (eye_yellow_x, eye_yellow_y), 1)


def draw_fighter_visual(
    screen: pygame.Surface,
    cam_x: float,
    font_small: pygame.font.Font,
    *,
    kind: str,
    team: str,
    team_color: tuple[int, int, int],
    x: float,
    ground_y: int,
    hp: int,
    max_hp: int,
    walk_phase: float,
    atk_timer: float,
    cooldown: float,
    hit_flash: float,
) -> None:
    """Dibuja una unidad con sus accesorios, armaduras, cascos/sombrero y armas."""
    sx = int(round(x - cam_x))
    sy = ground_y
    if sx < -70 or sx > screen.get_width() + 70:
        return

    facing = 1 if team == "A" else -1
    flash = hit_flash > 0.0

    body_col = (255, 255, 255) if flash else team_color
    steel_col = (255, 255, 255) if flash else (222, 230, 242)
    heavy_steel_col = (255, 255, 255) if flash else (188, 200, 218)
    armor_trim_col = (255, 255, 255) if flash else (112, 128, 152)
    wood_col = (255, 255, 255) if flash else (142, 88, 42)
    strap_col = (255, 255, 255) if flash else (98, 60, 28)
    hat_col = (255, 255, 255) if flash else (52, 126, 68)
    hat_band_col = (255, 255, 255) if flash else (36, 92, 48)
    feather_col = (255, 255, 255) if flash else (226, 72, 64)

    stride = math.sin(walk_phase) * 7.0
    swing = 1.0 if atk_timer > max(0.0, cooldown - 0.16) else 0.0

    hip = (sx, sy - 15)
    shoulder = (sx, sy - 31)
    head_center = (sx, sy - 41)

    if kind == "archidon":
        quiver_top = (sx - facing * 8, sy - 36)
        quiver_bot = (sx - facing * 4, sy - 19)
        pygame.draw.line(
            screen, strap_col, quiver_top, (sx + facing * 3, sy - 21), 2
        )
        pygame.draw.line(screen, wood_col, quiver_bot, quiver_top, 6)
        pygame.draw.line(
            screen,
            strap_col,
            (sx - facing * 7, sy - 27),
            (sx - facing * 5, sy - 27),
            2,
        )
        for idx_arr, off_x in enumerate((-3, -1, 1, 3)):
            ax0 = quiver_top[0] + off_x * facing
            ay0 = quiver_top[1] - (2 if idx_arr in (1, 2) else 0)
            pygame.draw.line(
                screen,
                steel_col,
                (ax0, ay0),
                (ax0 - facing * 2, ay0 - 7),
                2,
            )

    foot_a = (sx + int(round(stride * facing)), sy)
    foot_b = (sx - int(round(stride * facing)), sy)
    pygame.draw.line(screen, body_col, hip, foot_a, 3)
    pygame.draw.line(screen, body_col, hip, foot_b, 3)
    pygame.draw.line(screen, body_col, hip, shoulder, 3)

    if kind == "sword":
        pygame.draw.line(screen, steel_col, (sx, sy - 29), (sx, sy - 19), 6)
        pygame.draw.line(
            screen, armor_trim_col, (sx - 2, sy - 24), (sx + 2, sy - 24), 2
        )
        pygame.draw.circle(screen, armor_trim_col, (sx, sy - 27), 1)
        pygame.draw.circle(screen, armor_trim_col, (sx, sy - 21), 1)
        pygame.draw.circle(
            screen, steel_col, (shoulder[0] - facing * 4, shoulder[1]), 4
        )
        pygame.draw.arc(
            screen,
            armor_trim_col,
            (shoulder[0] - facing * 4 - 4, shoulder[1] - 4, 8, 8),
            0.0,
            math.pi,
            1,
        )
    elif kind == "lanzatonio":
        chest_rect = pygame.Rect(sx - 6, sy - 31, 12, 14)
        pygame.draw.rect(screen, heavy_steel_col, chest_rect, border_radius=2)
        pygame.draw.rect(
            screen, armor_trim_col, chest_rect, width=1, border_radius=2
        )
        pygame.draw.line(
            screen, armor_trim_col, (sx - 4, sy - 24), (sx + 4, sy - 24), 2
        )
        for ry in (sy - 28, sy - 21):
            pygame.draw.circle(screen, steel_col, (sx - 3, ry), 1)
            pygame.draw.circle(screen, steel_col, (sx + 3, ry), 1)
        pygame.draw.circle(
            screen, heavy_steel_col, (shoulder[0] - facing * 5, shoulder[1]), 4
        )
        pygame.draw.circle(
            screen, steel_col, (shoulder[0] + facing * 4, shoulder[1] + 1), 3
        )

    pygame.draw.circle(screen, body_col, head_center, 6)

    if kind == "sword":
        hx, hy = head_center
        pygame.draw.arc(
            screen, steel_col, (hx - 7, hy - 8, 14, 10), 0.0, math.pi, 3
        )
        pygame.draw.arc(
            screen,
            armor_trim_col,
            (hx - 7, hy - 8, 14, 10),
            0.15,
            math.pi - 0.15,
            1,
        )
        pygame.draw.line(screen, steel_col, (hx - 7, hy - 3), (hx + 7, hy - 3), 2)
        pygame.draw.line(
            screen,
            armor_trim_col,
            (hx + facing * 2, hy - 3),
            (hx + facing * 6, hy - 3),
            2,
        )
        pygame.draw.line(
            screen, feather_col, (hx, hy - 8), (hx - facing * 5, hy - 14), 2
        )
        pygame.draw.circle(screen, steel_col, (hx, hy - 8), 2)
    elif kind == "lanzatonio":
        hx, hy = head_center
        pygame.draw.arc(
            screen,
            heavy_steel_col,
            (hx - 8, hy - 10, 16, 12),
            -0.15,
            math.pi + 0.15,
            4,
        )
        pygame.draw.arc(
            screen,
            armor_trim_col,
            (hx - 8, hy - 10, 16, 12),
            0.0,
            math.pi,
            1,
        )
        pygame.draw.line(
            screen, heavy_steel_col, (hx - 8, hy - 4), (hx + 8, hy - 4), 2
        )
        pygame.draw.line(
            screen,
            steel_col,
            (hx + facing * 6, hy - 4),
            (hx + facing * 6, hy + 2),
            2,
        )
        pygame.draw.line(
            screen,
            steel_col,
            (hx - facing * 1, hy - 10),
            (hx - facing * 8, hy - 16),
            3,
        )
        pygame.draw.line(
            screen,
            feather_col,
            (hx - facing * 6, hy - 14),
            (hx - facing * 11, hy - 18),
            2,
        )
    elif kind == "archidon":
        hx, hy = head_center
        pygame.draw.line(
            screen, hat_col, (hx - 12, hy - 5), (hx + 12, hy - 5), 2
        )
        pygame.draw.polygon(
            screen,
            hat_col,
            [
                (hx - 7, hy - 5),
                (hx, hy - 15),
                (hx + 7, hy - 5),
            ],
        )
        pygame.draw.line(
            screen, hat_band_col, (hx - 6, hy - 6), (hx + 6, hy - 6), 2
        )
        pygame.draw.line(
            screen,
            feather_col,
            (hx - facing * 3, hy - 9),
            (hx - facing * 13, hy - 18),
            2,
        )

    if kind == "sword":
        ang = -1.15 if swing > 0.0 else -0.5
        hand_x = shoulder[0] + int(round(math.cos(ang) * 10 * facing))
        hand_y = shoulder[1] + int(round(math.sin(ang) * 10))
        pygame.draw.line(screen, body_col, shoulder, (hand_x, hand_y), 3)

        tip_x = hand_x + int(round(math.cos(ang) * 18 * facing))
        tip_y = hand_y + int(round(math.sin(ang) * 18))
        pygame.draw.line(screen, steel_col, (hand_x, hand_y), (tip_x, tip_y), 3)

    elif kind == "archidon":
        hand_x = shoulder[0] + facing * 9
        hand_y = shoulder[1] + 2
        pygame.draw.line(screen, body_col, shoulder, (hand_x, hand_y), 3)

        bow_x = hand_x + facing * 4
        start_a = -math.pi * 0.45 if facing == 1 else math.pi * 0.55
        end_a = math.pi * 0.45 if facing == 1 else math.pi * 1.45
        pygame.draw.arc(
            screen,
            wood_col,
            (bow_x - 5, hand_y - 11, 10, 22),
            start_a,
            end_a,
            3,
        )
        arrow_tip_x = bow_x + facing * (12 if swing == 0.0 else 20)
        pygame.draw.line(
            screen, wood_col, (hand_x, hand_y), (arrow_tip_x, hand_y), 2
        )

    elif kind == "lanzatonio":
        thrust = int(round(swing * 10 * facing))
        hand_x = shoulder[0] + facing * 8 + thrust
        hand_y = shoulder[1] + 3
        pygame.draw.line(screen, body_col, shoulder, (hand_x, hand_y), 3)

        tail_x = hand_x - facing * 16
        tip_x = hand_x + facing * 24
        pygame.draw.line(
            screen, wood_col, (tail_x, hand_y + 1), (tip_x, hand_y + 1), 3
        )
        pygame.draw.polygon(
            screen,
            steel_col,
            [
                (tip_x, hand_y - 3),
                (tip_x + facing * 7, hand_y + 1),
                (tip_x, hand_y + 5),
            ],
        )

        shield_cx = sx + facing * (11 + int(round(swing * 4)))
        shield_cy = sy - 18
        draw_python_shield(
            screen,
            shield_cx,
            shield_cy,
            facing=facing,
            shield_w=16,
            shield_h=28,
            flash=flash,
        )

    bar_w = 26
    bar_h = 4
    bx = sx - bar_w // 2
    by = sy - 66
    pygame.draw.rect(
        screen, (20, 20, 24), (bx - 1, by - 1, bar_w + 2, bar_h + 2)
    )
    ratio = max(0.0, min(1.0, hp / max(1, max_hp)))
    pygame.draw.rect(
        screen, body_col, (bx, by, int(round(bar_w * ratio)), bar_h)
    )

    hp_txt = str(max(0, hp))
    hp_surf = font_small.render(hp_txt, True, body_col)
    hp_shadow = font_small.render(hp_txt, True, (16, 16, 20))
    tx = sx - hp_surf.get_width() // 2
    ty = sy - 80
    screen.blit(hp_shadow, (tx + 1, ty + 1))
    screen.blit(hp_surf, (tx, ty))