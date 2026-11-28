from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from arena_background import ArenaBackground
from game_config import (
    GLOBAL_FIGHT_PRESETS,
    RANDOM_BATTLE_POPULATIONS,
    TEAM_COLORS,
    UNIT_STATS,
)
from matchups import (
    ACTIVE_MATCHUP,
    RANDOM_MATCHUP_KEY,
    UNIT_POP_COST,
    get_matchup_label,
    roster_from_counts,
)

if TYPE_CHECKING:
    from pygame.font import Font

    from fighter import Fighter

UNIT_ORDER: tuple[str, ...] = ("sword", "archidon", "lanzatonio", "ninja")


def _unit_pop_cost(kind: str) -> int:
    return int(UNIT_POP_COST.get(kind, 1))


def _team_pop(counts: dict[str, int]) -> int:
    return sum(max(0, counts.get(k, 0)) * _unit_pop_cost(k) for k in UNIT_ORDER)


def _team_units_count(counts: dict[str, int]) -> int:
    return sum(max(0, counts.get(k, 0)) for k in UNIT_ORDER)


def _sync_bg(screen: pygame.Surface, bg: ArenaBackground) -> None:
    w, h = screen.get_size()
    new_gy = h - 106
    if w != bg.width or h != bg.height or new_gy != bg.ground_y:
        bg.width = w
        bg.height = h
        bg.ground_y = new_gy
        bg.terrain_surf = bg._build_terrain_surface()


def _fit_text(
    text: str,
    max_w: int,
    fonts: tuple[pygame.font.Font, ...],
    color: tuple[int, int, int],
) -> pygame.Surface:
    for fnt in fonts:
        surf = fnt.render(text, True, color)
        if surf.get_width() <= max_w:
            return surf
    smallest = fonts[-1]
    trimmed = text
    while (
        len(trimmed) > 1
        and smallest.render(trimmed + "...", True, color).get_width() > max_w
    ):
        trimmed = trimmed[:-1]
    return smallest.render(
        trimmed + "..." if len(trimmed) < len(text) else trimmed, True, color
    )


def _random_counts_for_cap(pop_cap: int, rng: random.Random) -> dict[str, int]:
    counts = {k: 0 for k in UNIT_ORDER}
    used = 0
    while used < pop_cap:
        affordable = [k for k in UNIT_ORDER if used + _unit_pop_cost(k) <= pop_cap]
        if not affordable:
            break
        choice = rng.choice(affordable)
        counts[choice] += 1
        used += _unit_pop_cost(choice)
    return counts


def _generate_simultaneous_random_teams(
    rng: random.Random,
) -> tuple[dict[str, int], dict[str, int], int, int]:
    pop_a = int(rng.choice(RANDOM_BATTLE_POPULATIONS))
    pop_b = int(rng.choice(RANDOM_BATTLE_POPULATIONS))
    return (
        _random_counts_for_cap(pop_a, rng),
        _random_counts_for_cap(pop_b, rng),
        pop_a,
        pop_b,
    )


def _resolve_preset_counts(
    preset_key: str,
    rng: random.Random,
) -> tuple[dict[str, int], dict[str, int], int]:
    target_preset = None
    for preset in GLOBAL_FIGHT_PRESETS:
        if preset[0] == preset_key:
            target_preset = preset
            break

    if target_preset is None:
        for preset in GLOBAL_FIGHT_PRESETS:
            if preset[0] == ACTIVE_MATCHUP:
                target_preset = preset
                break

    if target_preset is None:
        target_preset = GLOBAL_FIGHT_PRESETS[0]

    key, _, c_a, c_b, pop_cap = target_preset
    cap = max(1, int(pop_cap))

    if key == RANDOM_MATCHUP_KEY or (c_a is None and c_b is None):
        counts_a, counts_b, pop_a, pop_b = _generate_simultaneous_random_teams(rng)
        return counts_a, counts_b, max(pop_a, pop_b)

    base_a = {k: 0 for k in UNIT_ORDER}
    base_b = {k: 0 for k in UNIT_ORDER}
    if isinstance(c_a, dict):
        for k in UNIT_ORDER:
            base_a[k] = max(0, int(c_a.get(k, 0)))
    if isinstance(c_b, dict):
        for k in UNIT_ORDER:
            base_b[k] = max(0, int(c_b.get(k, 0)))
    return base_a, base_b, cap


def run_start_menu(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    bg: ArenaBackground,
) -> bool:
    font_title = pygame.font.SysFont("consolas", 40, bold=True)
    font_sub = pygame.font.SysFont("consolas", 16, bold=True)
    font_btn = pygame.font.SysFont("consolas", 18, bold=True)
    font_small = pygame.font.SysFont("consolas", 12, bold=True)

    resize_ignore_timer = 0.0
    bg.set_menu_terrain()

    while True:
        dt = clock.tick(60) / 1000.0
        resize_ignore_timer = max(0.0, resize_ignore_timer - dt)
        screen = pygame.display.get_surface() or screen
        _sync_bg(screen, bg)
        w, h = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()

        play_btn = pygame.Rect(w // 2 - 110, h // 2 - 8, 220, 44)
        quit_btn = pygame.Rect(w // 2 - 110, h // 2 + 48, 220, 40)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE and resize_ignore_timer <= 0.0:
                screen = pygame.display.get_surface() or screen
                _sync_bg(screen, bg)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                    resize_ignore_timer = 0.2
                    screen = pygame.display.get_surface() or screen
                    _sync_bg(screen, bg)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_btn.collidepoint(event.pos):
                    return True
                if quit_btn.collidepoint(event.pos):
                    return False

        bg.draw(screen, 0.0)

        veil = pygame.Surface((w, h), pygame.SRCALPHA)
        veil.fill((8, 10, 16, 145))
        screen.blit(veil, (0, 0))

        box = pygame.Rect(w // 2 - 270, h // 2 - 135, 540, 250)
        pygame.draw.rect(screen, (20, 23, 32), box, border_radius=12)
        pygame.draw.rect(screen, (246, 226, 146), box, width=2, border_radius=12)

        title_s = font_title.render("ARENA SIMULADOR", True, (248, 224, 132))
        screen.blit(
            title_s, (box.centerx - title_s.get_width() // 2, box.y + 24)
        )

        sub_s = font_sub.render(
            "Combate táctico en tiempo real • Equipos A vs B",
            True,
            (218, 222, 235),
        )
        screen.blit(sub_s, (box.centerx - sub_s.get_width() // 2, box.y + 72))

        p_col = (72, 168, 96) if play_btn.collidepoint(mouse_pos) else (52, 132, 72)
        pygame.draw.rect(screen, p_col, play_btn, border_radius=8)
        pygame.draw.rect(
            screen, (205, 248, 214), play_btn, width=2, border_radius=8
        )
        pt_s = font_btn.render("JUGAR", True, (250, 252, 250))
        screen.blit(
            pt_s,
            (
                play_btn.centerx - pt_s.get_width() // 2,
                play_btn.centery - pt_s.get_height() // 2,
            ),
        )

        q_col = (155, 52, 56) if quit_btn.collidepoint(mouse_pos) else (112, 38, 42)
        pygame.draw.rect(screen, q_col, quit_btn, border_radius=8)
        pygame.draw.rect(
            screen, (240, 185, 188), quit_btn, width=1, border_radius=8
        )
        qt_s = font_btn.render("SALIR", True, (250, 246, 246))
        screen.blit(
            qt_s,
            (
                quit_btn.centerx - qt_s.get_width() // 2,
                quit_btn.centery - qt_s.get_height() // 2,
            ),
        )

        hint_s = font_small.render(
            "Enter / Espacio: jugar • ESC: salir • F11: pantalla completa",
            True,
            (182, 188, 204),
        )
        screen.blit(hint_s, (w // 2 - hint_s.get_width() // 2, box.bottom + 10))

        pygame.display.flip()


def run_match_editor(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    bg: ArenaBackground,
    rng: random.Random,
    initial_preset: str = ACTIVE_MATCHUP,
    initial_counts_a: dict[str, int] | None = None,
    initial_counts_b: dict[str, int] | None = None,
) -> tuple[str, list[str], list[str], str] | None:
    font_title = pygame.font.SysFont("consolas", 26, bold=True)
    font_header = pygame.font.SysFont("consolas", 15, bold=True)
    font_item = pygame.font.SysFont("consolas", 14, bold=True)
    font_small = pygame.font.SysFont("consolas", 12, bold=True)
    font_tiny = pygame.font.SysFont("consolas", 10, bold=True)

    preset_keys = [p[0] for p in GLOBAL_FIGHT_PRESETS]
    current_preset = (
        initial_preset if initial_preset in preset_keys else preset_keys[0]
    )

    counts_a, counts_b, pop_cap = _resolve_preset_counts(current_preset, rng)
    preset_base_a = {k: v for k, v in counts_a.items()}
    preset_base_b = {k: v for k, v in counts_b.items()}
    is_random_mode = current_preset == RANDOM_MATCHUP_KEY

    if not is_random_mode:
        if initial_counts_a is not None:
            counts_a = {
                k: max(0, int(initial_counts_a.get(k, 0))) for k in UNIT_ORDER
            }
        if initial_counts_b is not None:
            counts_b = {
                k: max(0, int(initial_counts_b.get(k, 0))) for k in UNIT_ORDER
            }

    resize_ignore_timer = 0.0

    def _compute_match_mode() -> str:
        if is_random_mode:
            return "random"
        if counts_a != preset_base_a or counts_b != preset_base_b:
            return "custom"
        return "preset"

    def _finish_selection() -> tuple[str, list[str], list[str], str]:
        return (
            current_preset,
            roster_from_counts(counts_a),
            roster_from_counts(counts_b),
            _compute_match_mode(),
        )

    def apply_preset(key: str) -> None:
        nonlocal current_preset, counts_a, counts_b, pop_cap, preset_base_a, preset_base_b, is_random_mode
        current_preset = key
        is_random_mode = key == RANDOM_MATCHUP_KEY
        counts_a, counts_b, pop_cap = _resolve_preset_counts(key, rng)
        preset_base_a = {k: v for k, v in counts_a.items()}
        preset_base_b = {k: v for k, v in counts_b.items()}

    def randomize_both_teams() -> None:
        nonlocal counts_a, counts_b, pop_cap, is_random_mode
        is_random_mode = True
        counts_a, counts_b, pop_a, pop_b = _generate_simultaneous_random_teams(rng)
        pop_cap = max(pop_a, pop_b)

    def clear_both_teams() -> None:
        nonlocal counts_a, counts_b, is_random_mode
        is_random_mode = False
        counts_a = {k: 0 for k in UNIT_ORDER}
        counts_b = {k: 0 for k in UNIT_ORDER}

    while True:
        dt = clock.tick(60) / 1000.0
        resize_ignore_timer = max(0.0, resize_ignore_timer - dt)
        screen = pygame.display.get_surface() or screen
        _sync_bg(screen, bg)
        w, h = screen.get_size()
        mouse_pos = pygame.mouse.get_pos()

        margin_x = max(22, int(w * 0.032))
        top_y = max(36, int(h * 0.05))
        bottom_margin = max(28, int(h * 0.038))
        panel_w = max(360, w - margin_x * 2)
        panel_h = max(360, h - top_y - bottom_margin)
        panel = pygame.Rect(margin_x, top_y, panel_w, panel_h)

        top_bar_y = panel.y + 14
        prev_btn = pygame.Rect(panel.x + 16, top_bar_y, 34, 30)
        next_btn = pygame.Rect(panel.x + 56, top_bar_y, 34, 30)
        random_btn = pygame.Rect(panel.right - 138, top_bar_y, 122, 30)
        clear_btn = pygame.Rect(panel.right - 246, top_bar_y, 100, 30)

        col_gap = 18
        col_w = (panel.w - 32 - col_gap) // 2
        col_top = top_bar_y + 42
        col_h = max(136, min(220, int(panel.h * 0.32)))

        card_a = pygame.Rect(panel.x + 16, col_top, col_w, col_h)
        card_b = pygame.Rect(card_a.right + col_gap, col_top, col_w, col_h)

        row_area_h = max(92, col_h - 44)
        row_step = row_area_h / len(UNIT_ORDER)

        a_minus10_btns: dict[str, pygame.Rect] = {}
        a_minus_btns: dict[str, pygame.Rect] = {}
        a_plus_btns: dict[str, pygame.Rect] = {}
        a_plus10_btns: dict[str, pygame.Rect] = {}

        b_minus10_btns: dict[str, pygame.Rect] = {}
        b_minus_btns: dict[str, pygame.Rect] = {}
        b_plus_btns: dict[str, pygame.Rect] = {}
        b_plus10_btns: dict[str, pygame.Rect] = {}

        for idx, kind in enumerate(UNIT_ORDER):
            ry = int(round(card_a.y + 34 + idx * row_step))
            a_plus10_btns[kind] = pygame.Rect(card_a.right - 44, ry, 34, 22)
            a_plus_btns[kind] = pygame.Rect(card_a.right - 74, ry, 26, 22)
            a_minus_btns[kind] = pygame.Rect(card_a.right - 104, ry, 26, 22)
            a_minus10_btns[kind] = pygame.Rect(card_a.right - 142, ry, 34, 22)

            b_plus10_btns[kind] = pygame.Rect(card_b.right - 44, ry, 34, 22)
            b_plus_btns[kind] = pygame.Rect(card_b.right - 74, ry, 26, 22)
            b_minus_btns[kind] = pygame.Rect(card_b.right - 104, ry, 26, 22)
            b_minus10_btns[kind] = pygame.Rect(card_b.right - 142, ry, 34, 22)

        footer_btn_h = 34
        footer_y = panel.bottom - footer_btn_h - 14
        start_menu_btn = pygame.Rect(panel.x + 16, footer_y, 118, footer_btn_h)
        play_btn = pygame.Rect(0, footer_y, 230, footer_btn_h)
        play_btn.centerx = panel.centerx

        presets_label_y = card_a.bottom + 10
        presets_grid_top = presets_label_y + 18
        presets_grid_bottom = footer_y - 12
        avail_grid_h = max(56, presets_grid_bottom - presets_grid_top)

        p_cols = 6 if panel.w >= 760 else 5
        p_rows = math.ceil(len(GLOBAL_FIGHT_PRESETS) / p_cols)
        p_gap_x = 8
        p_gap_y = 6 if avail_grid_h >= p_rows * 28 else 4
        p_btn_h = max(
            20, min(30, (avail_grid_h - p_gap_y * (p_rows - 1)) // p_rows)
        )
        p_btn_w = (panel.w - 32 - p_gap_x * (p_cols - 1)) // p_cols

        preset_btns: list[tuple[pygame.Rect, str, str]] = []
        for idx, (pkey, plabel, _, _, _) in enumerate(GLOBAL_FIGHT_PRESETS):
            r = idx // p_cols
            c = idx % p_cols
            bx = panel.x + 16 + c * (p_btn_w + p_gap_x)
            by = presets_grid_top + r * (p_btn_h + p_gap_y)
            preset_btns.append((pygame.Rect(bx, by, p_btn_w, p_btn_h), pkey, plabel))

        pop_a = _team_pop(counts_a)
        pop_b = _team_pop(counts_b)
        units_a = _team_units_count(counts_a)
        units_b = _team_units_count(counts_b)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.VIDEORESIZE and resize_ignore_timer <= 0.0:
                screen = pygame.display.get_surface() or screen
                _sync_bg(screen, bg)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key == pygame.K_RETURN:
                    return _finish_selection()
                if event.key == pygame.K_LEFT:
                    idx = (preset_keys.index(current_preset) - 1) % len(preset_keys)
                    apply_preset(preset_keys[idx])
                    pop_a = _team_pop(counts_a)
                    pop_b = _team_pop(counts_b)
                    units_a = _team_units_count(counts_a)
                    units_b = _team_units_count(counts_b)
                elif event.key == pygame.K_RIGHT:
                    idx = (preset_keys.index(current_preset) + 1) % len(preset_keys)
                    apply_preset(preset_keys[idx])
                    pop_a = _team_pop(counts_a)
                    pop_b = _team_pop(counts_b)
                    units_a = _team_units_count(counts_a)
                    units_b = _team_units_count(counts_b)
                elif event.key == pygame.K_r:
                    randomize_both_teams()
                    pop_a = _team_pop(counts_a)
                    pop_b = _team_pop(counts_b)
                    units_a = _team_units_count(counts_a)
                    units_b = _team_units_count(counts_b)
                elif event.key == pygame.K_c:
                    clear_both_teams()
                    pop_a = 0
                    pop_b = 0
                    units_a = 0
                    units_b = 0
                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                    resize_ignore_timer = 0.2
                    screen = pygame.display.get_surface() or screen
                    _sync_bg(screen, bg)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if prev_btn.collidepoint(pos):
                    idx = (preset_keys.index(current_preset) - 1) % len(
                        preset_keys
                    )
                    apply_preset(preset_keys[idx])
                    pop_a = _team_pop(counts_a)
                    pop_b = _team_pop(counts_b)
                    units_a = _team_units_count(counts_a)
                    units_b = _team_units_count(counts_b)
                elif next_btn.collidepoint(pos):
                    idx = (preset_keys.index(current_preset) + 1) % len(
                        preset_keys
                    )
                    apply_preset(preset_keys[idx])
                    pop_a = _team_pop(counts_a)
                    pop_b = _team_pop(counts_b)
                    units_a = _team_units_count(counts_a)
                    units_b = _team_units_count(counts_b)
                elif clear_btn.collidepoint(pos):
                    clear_both_teams()
                    pop_a = 0
                    pop_b = 0
                    units_a = 0
                    units_b = 0
                elif random_btn.collidepoint(pos):
                    randomize_both_teams()
                    pop_a = _team_pop(counts_a)
                    pop_b = _team_pop(counts_b)
                    units_a = _team_units_count(counts_a)
                    units_b = _team_units_count(counts_b)
                elif start_menu_btn.collidepoint(pos):
                    return None
                elif play_btn.collidepoint(pos):
                    return _finish_selection()
                else:
                    handled = False
                    for kind in UNIT_ORDER:
                        if a_minus10_btns[kind].collidepoint(pos):
                            counts_a[kind] = max(0, counts_a[kind] - 10)
                            is_random_mode = False
                            pop_a = _team_pop(counts_a)
                            units_a = _team_units_count(counts_a)
                            handled = True
                            break
                        if a_minus_btns[kind].collidepoint(pos):
                            counts_a[kind] = max(0, counts_a[kind] - 1)
                            is_random_mode = False
                            pop_a = _team_pop(counts_a)
                            units_a = _team_units_count(counts_a)
                            handled = True
                            break
                        if a_plus_btns[kind].collidepoint(pos):
                            counts_a[kind] += 1
                            is_random_mode = False
                            pop_a = _team_pop(counts_a)
                            units_a = _team_units_count(counts_a)
                            handled = True
                            break
                        if a_plus10_btns[kind].collidepoint(pos):
                            counts_a[kind] += 10
                            is_random_mode = False
                            pop_a = _team_pop(counts_a)
                            units_a = _team_units_count(counts_a)
                            handled = True
                            break

                        if b_minus10_btns[kind].collidepoint(pos):
                            counts_b[kind] = max(0, counts_b[kind] - 10)
                            is_random_mode = False
                            pop_b = _team_pop(counts_b)
                            units_b = _team_units_count(counts_b)
                            handled = True
                            break
                        if b_minus_btns[kind].collidepoint(pos):
                            counts_b[kind] = max(0, counts_b[kind] - 1)
                            is_random_mode = False
                            pop_b = _team_pop(counts_b)
                            units_b = _team_units_count(counts_b)
                            handled = True
                            break
                        if b_plus_btns[kind].collidepoint(pos):
                            counts_b[kind] += 1
                            is_random_mode = False
                            pop_b = _team_pop(counts_b)
                            units_b = _team_units_count(counts_b)
                            handled = True
                            break
                        if b_plus10_btns[kind].collidepoint(pos):
                            counts_b[kind] += 10
                            is_random_mode = False
                            pop_b = _team_pop(counts_b)
                            units_b = _team_units_count(counts_b)
                            handled = True
                            break
                    if not handled:
                        for rect_p, pkey, _ in preset_btns:
                            if rect_p.collidepoint(pos):
                                apply_preset(pkey)
                                pop_a = _team_pop(counts_a)
                                pop_b = _team_pop(counts_b)
                                units_a = _team_units_count(counts_a)
                                units_b = _team_units_count(counts_b)
                                break

        bg.draw(screen, 0.0)

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((10, 12, 18, 175))
        screen.blit(overlay, (0, 0))

        title_surf = font_title.render("EDICION DE PARTIDA", True, (248, 224, 132))
        screen.blit(
            title_surf, (w // 2 - title_surf.get_width() // 2, max(8, top_y - 30))
        )

        pygame.draw.rect(screen, (20, 22, 30), panel, border_radius=10)
        pygame.draw.rect(
            screen, (236, 198, 86), panel, width=2, border_radius=10
        )

        mode_preview = _compute_match_mode()
        mode_suffix = {
            "random": "Aleatorio",
            "custom": "Customizada",
            "preset": "Preset",
        }[mode_preview]
        preset_label_txt = (
            f"Preset: {get_matchup_label(current_preset)} [{mode_suffix}] (Ref {pop_cap} Pob)"
        )
        max_preset_w = max(80, clear_btn.left - (next_btn.right + 22))
        preset_lbl = _fit_text(
            preset_label_txt,
            max_preset_w,
            (font_header, font_item, font_small),
            (240, 242, 248),
        )
        screen.blit(
            preset_lbl,
            (
                next_btn.right + 12,
                prev_btn.centery - preset_lbl.get_height() // 2,
            ),
        )

        pygame.draw.rect(screen, (26, 29, 40), card_a, border_radius=8)
        pygame.draw.rect(
            screen, TEAM_COLORS["A"], card_a, width=2, border_radius=8
        )
        pygame.draw.rect(screen, (26, 29, 40), card_b, border_radius=8)
        pygame.draw.rect(
            screen, TEAM_COLORS["B"], card_b, width=2, border_radius=8
        )

        hdr_a = _fit_text(
            f"EQUIPO A | Pob {pop_a} ({units_a})",
            max(60, card_a.w - 28),
            (font_header, font_item, font_small),
            TEAM_COLORS["A"],
        )
        hdr_b = _fit_text(
            f"EQUIPO B | Pob {pop_b} ({units_b})",
            max(60, card_b.w - 28),
            (font_header, font_item, font_small),
            TEAM_COLORS["B"],
        )
        screen.blit(hdr_a, (card_a.x + 14, card_a.y + 10))
        screen.blit(hdr_b, (card_b.x + 14, card_b.y + 10))

        for idx, kind in enumerate(UNIT_ORDER):
            ry = int(round(card_a.y + 34 + idx * row_step))
            cost = _unit_pop_cost(kind)
            label = UNIT_STATS[kind]["label"]
            max_row_txt_w = max(50, a_minus10_btns[kind].left - (card_a.x + 22))

            txt_a = _fit_text(
                f"{label} ({cost}): {counts_a[kind]}",
                max_row_txt_w,
                (font_item, font_small),
                (238, 240, 246),
            )
            screen.blit(txt_a, (card_a.x + 14, ry + 3))

            txt_b = _fit_text(
                f"{label} ({cost}): {counts_b[kind]}",
                max_row_txt_w,
                (font_item, font_small),
                (238, 240, 246),
            )
            screen.blit(txt_b, (card_b.x + 14, ry + 3))

        p_lbl = font_small.render("Peleas:", True, (214, 218, 230))
        screen.blit(p_lbl, (panel.x + 16, presets_label_y))

        for btn_r, sym in ((prev_btn, "<"), (next_btn, ">")):
            col = (84, 92, 118) if btn_r.collidepoint(mouse_pos) else (52, 58, 78)
            pygame.draw.rect(screen, col, btn_r, border_radius=5)
            pygame.draw.rect(
                screen, (215, 220, 235), btn_r, width=1, border_radius=5
            )
            s_t = font_header.render(sym, True, (248, 248, 252))
            screen.blit(
                s_t,
                (
                    btn_r.centerx - s_t.get_width() // 2,
                    btn_r.centery - s_t.get_height() // 2,
                ),
            )

        c_col = (145, 52, 52) if clear_btn.collidepoint(mouse_pos) else (105, 38, 38)
        pygame.draw.rect(screen, c_col, clear_btn, border_radius=6)
        pygame.draw.rect(
            screen, (238, 175, 175), clear_btn, width=1, border_radius=6
        )
        c_t = font_small.render("VACIAR", True, (252, 245, 245))
        screen.blit(
            c_t,
            (
                clear_btn.centerx - c_t.get_width() // 2,
                clear_btn.centery - c_t.get_height() // 2,
            ),
        )

        r_col = (66, 128, 172) if random_btn.collidepoint(mouse_pos) else (46, 92, 128)
        pygame.draw.rect(screen, r_col, random_btn, border_radius=6)
        pygame.draw.rect(
            screen, (210, 232, 248), random_btn, width=1, border_radius=6
        )
        r_t = font_small.render("ALEATORIO", True, (248, 250, 252))
        screen.blit(
            r_t,
            (
                random_btn.centerx - r_t.get_width() // 2,
                random_btn.centery - r_t.get_height() // 2,
            ),
        )

        for kind in UNIT_ORDER:
            for btn_r, sym, enabled, use_small_font in (
                (a_minus10_btns[kind], "-10", counts_a[kind] > 0, True),
                (a_minus_btns[kind], "-", counts_a[kind] > 0, False),
                (a_plus_btns[kind], "+", True, False),
                (a_plus10_btns[kind], "+10", True, True),
                (b_minus10_btns[kind], "-10", counts_b[kind] > 0, True),
                (b_minus_btns[kind], "-", counts_b[kind] > 0, False),
                (b_plus_btns[kind], "+", True, False),
                (b_plus10_btns[kind], "+10", True, True),
            ):
                if not enabled:
                    col = (36, 39, 50)
                elif btn_r.collidepoint(mouse_pos):
                    col = (92, 102, 132)
                else:
                    col = (56, 62, 82)
                pygame.draw.rect(screen, col, btn_r, border_radius=5)
                pygame.draw.rect(
                    screen,
                    (210, 215, 230) if enabled else (85, 90, 105),
                    btn_r,
                    width=1,
                    border_radius=5,
                )
                fnt_btn = font_small if use_small_font else font_header
                s_t = fnt_btn.render(
                    sym, True, (250, 250, 252) if enabled else (130, 135, 148)
                )
                screen.blit(
                    s_t,
                    (
                        btn_r.centerx - s_t.get_width() // 2,
                        btn_r.centery - s_t.get_height() // 2,
                    ),
                )

        for rect_p, pkey, plabel in preset_btns:
            selected = pkey == current_preset and mode_preview == "preset"
            hovered = rect_p.collidepoint(mouse_pos)
            if selected:
                fill_c = (78, 114, 168)
                border_c = (248, 224, 132)
            elif hovered:
                fill_c = (62, 68, 88)
                border_c = (195, 202, 222)
            else:
                fill_c = (36, 40, 54)
                border_c = (105, 112, 134)
            pygame.draw.rect(screen, fill_c, rect_p, border_radius=5)
            pygame.draw.rect(screen, border_c, rect_p, width=1, border_radius=5)
            p_t = _fit_text(
                plabel,
                max(20, rect_p.w - 8),
                (font_small, font_tiny),
                (245, 246, 250),
            )
            screen.blit(
                p_t,
                (
                    rect_p.centerx - p_t.get_width() // 2,
                    rect_p.centery - p_t.get_height() // 2,
                ),
            )

        sm_col = (
            (86, 72, 92) if start_menu_btn.collidepoint(mouse_pos) else (58, 48, 64)
        )
        pygame.draw.rect(screen, sm_col, start_menu_btn, border_radius=7)
        pygame.draw.rect(
            screen, (215, 195, 224), start_menu_btn, width=2, border_radius=7
        )
        sm_t = font_header.render("INICIO", True, (248, 245, 250))
        screen.blit(
            sm_t,
            (
                start_menu_btn.centerx - sm_t.get_width() // 2,
                start_menu_btn.centery - sm_t.get_height() // 2,
            ),
        )

        play_col = (
            (72, 168, 96) if play_btn.collidepoint(mouse_pos) else (52, 132, 72)
        )
        pygame.draw.rect(screen, play_col, play_btn, border_radius=7)
        pygame.draw.rect(
            screen, (195, 245, 205), play_btn, width=2, border_radius=7
        )
        play_t = font_header.render("INICIAR", True, (250, 252, 250))
        screen.blit(
            play_t,
            (
                play_btn.centerx - play_t.get_width() // 2,
                play_btn.centery - play_t.get_height() // 2,
            ),
        )

        hint = font_small.render(
            "Izq/Der: preset • Enter: iniciar • ESC: inicio",
            True,
            (190, 194, 208),
        )
        screen.blit(hint, (w // 2 - hint.get_width() // 2, panel.bottom + 8))

        pygame.display.flip()


def build_hud_buttons(
    screen_w: int,
    *,
    paused: bool = False,
    sim_speed: float = 1.0,
) -> dict[str, pygame.Rect]:
    _ = (screen_w, paused, sim_speed)
    btn_h = 28
    top_y = 31
    gap = 4
    start_x = 10

    speed_1 = pygame.Rect(start_x, top_y, 42, btn_h)
    speed_2 = pygame.Rect(speed_1.right + gap, top_y, 42, btn_h)
    speed_4 = pygame.Rect(speed_2.right + gap, top_y, 42, btn_h)
    restart = pygame.Rect(speed_4.right + 8, top_y, 92, btn_h)

    return {
        "speed_1": speed_1,
        "speed_2": speed_2,
        "speed_4": speed_4,
        "restart": restart,
    }


def _resolve_terrain_name(bg: ArenaBackground | None, matchup_label: str) -> str:
    if bg is not None:
        for attr in ("terrain_name", "terrain", "current_terrain", "theme", "biome"):
            val = getattr(bg, attr, None)
            if isinstance(val, str) and val.strip():
                return val.strip().upper()
    return matchup_label.strip().upper()


def _format_mode_badge(match_mode: str) -> tuple[str, tuple[int, int, int]]:
    if match_mode == "random":
        return "ALEATORIA", (135, 206, 250)
    if match_mode == "custom":
        return "CUSTOMIZADA", (255, 195, 92)
    return "PRESET", (162, 232, 168)


def draw_battle_hud(
    screen: pygame.Surface,
    font_small: Font,
    font_med: Font,
    *,
    matchup_key: str,
    matchup_label: str,
    fighters_a: list[Fighter],
    fighters_b: list[Fighter],
    elapsed_time: float,
    sim_speed: float = 1.0,
    paused: bool = False,
    buttons: dict[str, pygame.Rect] | None = None,
    bg: ArenaBackground | None = None,
    phase_label: str | None = None,
    match_mode: str = "preset",
) -> dict[str, pygame.Rect]:
    _ = (matchup_key, font_small, font_med, paused)
    sw = screen.get_width()

    mins = int(elapsed_time) // 60
    secs = int(elapsed_time) % 60
    time_str = f"{mins:02d}:{secs:02d}"

    state_str = phase_label or ("PAUSA" if paused else "COMBATE")
    terrain_str = _resolve_terrain_name(bg, matchup_label)

    alive_a = sum(1 for f in fighters_a if f.alive)
    alive_b = sum(1 for f in fighters_b if f.alive)

    hud_text = (
        f"{time_str} | {state_str} | {terrain_str} | "
        f"A(Amarillo):{alive_a} vs B(Rojo):{alive_b} | "
        "[P] Pausa [R] Reiniciar [T] Terreno [ESC] Editor"
    )

    bar_h = 26
    pygame.draw.rect(screen, (14, 17, 22), pygame.Rect(0, 0, sw, bar_h))
    pygame.draw.line(screen, (34, 40, 50), (0, bar_h), (sw, bar_h), 1)

    hud_font = pygame.font.SysFont("consolas", 14, bold=True)
    text_color = (242, 224, 138)
    surf = hud_font.render(hud_text, True, text_color)
    while surf.get_width() > sw - 16 and hud_font.get_height() > 10:
        size = max(10, hud_font.get_height() - 3)
        hud_font = pygame.font.SysFont("consolas", size, bold=True)
        surf = hud_font.render(hud_text, True, text_color)

    screen.blit(surf, (10, (bar_h - surf.get_height()) // 2))

    btn_map = buttons or build_hud_buttons(sw, paused=paused, sim_speed=sim_speed)
    btn_font = pygame.font.SysFont("consolas", 13, bold=True)
    mouse_pos = pygame.mouse.get_pos()
    speed_specs = (
        ("speed_1", "1x", 1.0),
        ("speed_2", "2x", 2.0),
        ("speed_4", "4x", 4.0),
    )

    for btn_id, label_txt, target_spd in speed_specs:
        rect = btn_map.get(btn_id)
        if rect is None:
            continue
        is_active = abs(sim_speed - target_spd) < 1e-6
        fill = (76, 108, 156) if is_active else (34, 40, 50)
        border = (158, 202, 255) if is_active else (82, 92, 108)
        pygame.draw.rect(screen, fill, rect, border_radius=4)
        pygame.draw.rect(screen, border, rect, width=1, border_radius=4)
        lbl = btn_font.render(label_txt, True, (245, 248, 252))
        screen.blit(
            lbl,
            (
                rect.centerx - lbl.get_width() // 2,
                rect.centery - lbl.get_height() // 2,
            ),
        )

    restart_rect = btn_map.get("restart")
    if restart_rect is not None:
        hovered = restart_rect.collidepoint(mouse_pos)
        r_fill = (68, 82, 104) if hovered else (48, 56, 70)
        r_border = (158, 184, 224) if hovered else (115, 132, 158)
        pygame.draw.rect(screen, r_fill, restart_rect, border_radius=4)
        pygame.draw.rect(screen, r_border, restart_rect, width=1, border_radius=4)
        r_lbl = btn_font.render("Reiniciar", True, (245, 248, 252))
        screen.blit(
            r_lbl,
            (
                restart_rect.centerx - r_lbl.get_width() // 2,
                restart_rect.centery - r_lbl.get_height() // 2,
            ),
        )

    left_controls_end = (restart_rect.right + 12) if restart_rect is not None else 150
    info_w = min(290, max(160, sw - left_controls_end - 12))
    info_x = sw - info_w - 10
    if info_x < left_controls_end:
        info_x = left_controls_end
        info_w = max(120, sw - info_x - 10)

    info_box = pygame.Rect(info_x, 30, info_w, 46)
    badge_txt, badge_col = _format_mode_badge(match_mode)
    pygame.draw.rect(screen, (18, 22, 30), info_box, border_radius=5)
    pygame.draw.rect(screen, (62, 74, 94), info_box, width=1, border_radius=5)

    title_font = pygame.font.SysFont("consolas", 15, bold=True)
    sub_font = pygame.font.SysFont("consolas", 12, bold=True)

    display_title = (
        "Partida Aleatoria"
        if match_mode == "random" and not matchup_label.strip()
        else matchup_label
    )
    title_surf = _fit_text(
        display_title,
        max(60, info_box.w - 16),
        (title_font, sub_font),
        (244, 247, 252),
    )
    screen.blit(title_surf, (info_box.x + 8, info_box.y + 5))

    meta_line = f"{badge_txt} | {time_str} | Vel: {sim_speed:.0f}x"
    meta_surf = _fit_text(
        meta_line,
        max(60, info_box.w - 16),
        (sub_font,),
        badge_col,
    )
    screen.blit(meta_surf, (info_box.x + 8, info_box.y + 25))

    return btn_map


def draw_pause_overlay(
    screen: pygame.Surface,
    font_med: Font,
    font_large: Font,
) -> None:
    sw, sh = screen.get_size()
    dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
    dim.fill((8, 10, 16, 155))
    screen.blit(dim, (0, 0))

    title = font_large.render("BATALLA EN PAUSA", True, (245, 248, 255))
    hint = font_med.render(
        "ESPACIO o ESC para continuar  |  R reiniciar  |  M menú",
        True,
        (195, 208, 228),
    )
    screen.blit(title, (sw // 2 - title.get_width() // 2, sh // 2 - 42))
    screen.blit(hint, (sw // 2 - hint.get_width() // 2, sh // 2 + 12))


def build_end_overlay_buttons(
    screen_w: int,
    screen_h: int,
) -> dict[str, pygame.Rect]:
    box_w = min(540, max(320, screen_w - 40))
    box_h = 236
    box = pygame.Rect(
        screen_w // 2 - box_w // 2,
        screen_h // 2 - box_h // 2,
        box_w,
        box_h,
    )
    btn_w = min(156, max(110, (box.w - 60) // 2))
    btn_h = 36
    gap = 18
    total_w = btn_w * 2 + gap
    start_x = box.centerx - total_w // 2
    btn_y = box.bottom - 76

    return {
        "restart": pygame.Rect(start_x, btn_y, btn_w, btn_h),
        "editor": pygame.Rect(start_x + btn_w + gap, btn_y, btn_w, btn_h),
    }


def draw_end_overlay(
    screen: pygame.Surface,
    font_small: Font,
    font_med: Font,
    font_large: Font,
    *,
    winner_team: str,
    fighters_a: list[Fighter],
    fighters_b: list[Fighter],
    elapsed_time: float,
    buttons: dict[str, pygame.Rect] | None = None,
) -> dict[str, pygame.Rect]:
    sw, sh = screen.get_size()
    dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
    dim.fill((8, 10, 16, 168))
    screen.blit(dim, (0, 0))

    if winner_team == "A":
        banner_txt = "¡VICTORIA DEL EQUIPO A!"
        banner_col = TEAM_COLORS.get("A", (255, 214, 54))
    elif winner_team == "B":
        banner_txt = "¡VICTORIA DEL EQUIPO B!"
        banner_col = TEAM_COLORS.get("B", (245, 64, 64))
    else:
        banner_txt = "¡EMPATE!"
        banner_col = (224, 232, 244)

    box_w = min(540, max(320, sw - 40))
    box_h = 236
    box = pygame.Rect(sw // 2 - box_w // 2, sh // 2 - box_h // 2, box_w, box_h)
    pygame.draw.rect(screen, (22, 27, 37), box, border_radius=10)
    pygame.draw.rect(screen, banner_col, box, width=2, border_radius=10)

    title_surf = _fit_text(
        banner_txt,
        max(120, box.w - 32),
        (font_large, font_med),
        banner_col,
    )
    screen.blit(
        title_surf, (box.centerx - title_surf.get_width() // 2, box.top + 20)
    )

    alive_a = sum(1 for f in fighters_a if f.alive)
    alive_b = sum(1 for f in fighters_b if f.alive)
    stats_surf = _fit_text(
        f"Sobrevivientes — A: {alive_a}  |  B: {alive_b}  |  {elapsed_time:.1f}s",
        max(120, box.w - 32),
        (font_med, font_small),
        (225, 233, 245),
    )
    screen.blit(
        stats_surf, (box.centerx - stats_surf.get_width() // 2, box.top + 76)
    )

    btn_map = buttons or build_end_overlay_buttons(sw, sh)
    mouse_pos = pygame.mouse.get_pos()

    btn_specs = (
        ("restart", "Reiniciar", (46, 118, 172), (68, 152, 214)),
        ("editor", "Editor", (58, 66, 92), (82, 94, 128)),
    )
    for btn_id, label_txt, base_col, hover_col in btn_specs:
        rect = btn_map.get(btn_id)
        if rect is None:
            continue
        is_hover = rect.collidepoint(mouse_pos)
        fill = hover_col if is_hover else base_col
        border = (245, 248, 252) if is_hover else (175, 188, 212)
        pygame.draw.rect(screen, fill, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, width=1, border_radius=6)
        lbl = font_med.render(label_txt, True, (250, 252, 255))
        screen.blit(
            lbl,
            (
                rect.centerx - lbl.get_width() // 2,
                rect.centery - lbl.get_height() // 2,
            ),
        )

    hint_surf = _fit_text(
        "Pulsa R para reiniciar  |  Pulsa M o ESC para volver al editor",
        max(120, box.w - 32),
        (font_small,),
        (170, 184, 206),
    )
    screen.blit(
        hint_surf, (box.centerx - hint_surf.get_width() // 2, box.bottom - 28)
    )
    return btn_map