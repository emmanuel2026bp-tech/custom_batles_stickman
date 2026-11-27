import math
import random
import pygame

from arena_background import ArenaBackground
from game_config import (
    GLOBAL_FIGHT_PRESETS,
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

UNIT_ORDER: tuple[str, ...] = ("sword", "archidon", "lanzatonio")


def _unit_pop_cost(kind: str) -> int:
    return int(UNIT_POP_COST.get(kind, 1))


def _team_pop(counts: dict[str, int]) -> int:
    return sum(max(0, counts.get(k, 0)) * _unit_pop_cost(k) for k in UNIT_ORDER)


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
    while len(trimmed) > 1 and smallest.render(trimmed + "...", True, color).get_width() > max_w:
        trimmed = trimmed[:-1]
    return smallest.render(trimmed + "..." if len(trimmed) < len(text) else trimmed, True, color)


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
        return (
            _random_counts_for_cap(cap, rng),
            _random_counts_for_cap(cap, rng),
            cap,
        )

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
) -> tuple[str, list[str], list[str]] | None:
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
    if current_preset != RANDOM_MATCHUP_KEY:
        if initial_counts_a is not None:
            counts_a = {
                k: max(0, int(initial_counts_a.get(k, 0))) for k in UNIT_ORDER
            }
        if initial_counts_b is not None:
            counts_b = {
                k: max(0, int(initial_counts_b.get(k, 0))) for k in UNIT_ORDER
            }

    resize_ignore_timer = 0.0

    def apply_preset(key: str) -> None:
        nonlocal current_preset, counts_a, counts_b, pop_cap
        current_preset = key
        counts_a, counts_b, pop_cap = _resolve_preset_counts(key, rng)

    def randomize_both_teams() -> None:
        nonlocal counts_a, counts_b
        counts_a = _random_counts_for_cap(pop_cap, rng)
        counts_b = _random_counts_for_cap(pop_cap, rng)

    def clear_both_teams() -> None:
        nonlocal counts_a, counts_b
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
        col_h = max(124, min(205, int(panel.h * 0.29)))

        card_a = pygame.Rect(panel.x + 16, col_top, col_w, col_h)
        card_b = pygame.Rect(card_a.right + col_gap, col_top, col_w, col_h)

        row_area_h = max(78, col_h - 44)
        row_step = row_area_h / len(UNIT_ORDER)

        a_minus_btns: dict[str, pygame.Rect] = {}
        a_plus_btns: dict[str, pygame.Rect] = {}
        b_minus_btns: dict[str, pygame.Rect] = {}
        b_plus_btns: dict[str, pygame.Rect] = {}

        for idx, kind in enumerate(UNIT_ORDER):
            ry = int(round(card_a.y + 36 + idx * row_step))
            a_minus_btns[kind] = pygame.Rect(card_a.right - 74, ry, 26, 24)
            a_plus_btns[kind] = pygame.Rect(card_a.right - 40, ry, 26, 24)
            b_minus_btns[kind] = pygame.Rect(card_b.right - 74, ry, 26, 24)
            b_plus_btns[kind] = pygame.Rect(card_b.right - 40, ry, 26, 24)

        footer_btn_h = 34
        footer_y = panel.bottom - footer_btn_h - 14
        start_menu_btn = pygame.Rect(panel.x + 16, footer_y, 118, footer_btn_h)
        play_btn = pygame.Rect(0, footer_y, 230, footer_btn_h)
        play_btn.centerx = panel.centerx

        presets_label_y = card_a.bottom + 10
        presets_grid_top = presets_label_y + 18
        presets_grid_bottom = footer_y - 12
        avail_grid_h = max(66, presets_grid_bottom - presets_grid_top)

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
                    return (
                        current_preset,
                        roster_from_counts(counts_a),
                        roster_from_counts(counts_b),
                    )
                if event.key == pygame.K_LEFT:
                    idx = (preset_keys.index(current_preset) - 1) % len(preset_keys)
                    apply_preset(preset_keys[idx])
                    pop_a = _team_pop(counts_a)
                    pop_b = _team_pop(counts_b)
                elif event.key == pygame.K_RIGHT:
                    idx = (preset_keys.index(current_preset) + 1) % len(preset_keys)
                    apply_preset(preset_keys[idx])
                    pop_a = _team_pop(counts_a)
                    pop_b = _team_pop(counts_b)
                elif event.key == pygame.K_r:
                    randomize_both_teams()
                    pop_a = _team_pop(counts_a)
                    pop_b = _team_pop(counts_b)
                elif event.key == pygame.K_c:
                    clear_both_teams()
                    pop_a = 0
                    pop_b = 0
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
                elif next_btn.collidepoint(pos):
                    idx = (preset_keys.index(current_preset) + 1) % len(
                        preset_keys
                    )
                    apply_preset(preset_keys[idx])
                    pop_a = _team_pop(counts_a)
                    pop_b = _team_pop(counts_b)
                elif clear_btn.collidepoint(pos):
                    clear_both_teams()
                    pop_a = 0
                    pop_b = 0
                elif random_btn.collidepoint(pos):
                    randomize_both_teams()
                    pop_a = _team_pop(counts_a)
                    pop_b = _team_pop(counts_b)
                elif start_menu_btn.collidepoint(pos):
                    return None
                elif play_btn.collidepoint(pos):
                    return (
                        current_preset,
                        roster_from_counts(counts_a),
                        roster_from_counts(counts_b),
                    )
                else:
                    handled = False
                    for kind in UNIT_ORDER:
                        if a_minus_btns[kind].collidepoint(pos):
                            counts_a[kind] = max(0, counts_a[kind] - 1)
                            pop_a = _team_pop(counts_a)
                            handled = True
                            break
                        if a_plus_btns[kind].collidepoint(pos):
                            if pop_a + _unit_pop_cost(kind) <= pop_cap:
                                counts_a[kind] += 1
                                pop_a = _team_pop(counts_a)
                            handled = True
                            break
                        if b_minus_btns[kind].collidepoint(pos):
                            counts_b[kind] = max(0, counts_b[kind] - 1)
                            pop_b = _team_pop(counts_b)
                            handled = True
                            break
                        if b_plus_btns[kind].collidepoint(pos):
                            if pop_b + _unit_pop_cost(kind) <= pop_cap:
                                counts_b[kind] += 1
                                pop_b = _team_pop(counts_b)
                            handled = True
                            break
                    if not handled:
                        for rect_p, pkey, _ in preset_btns:
                            if rect_p.collidepoint(pos):
                                apply_preset(pkey)
                                pop_a = _team_pop(counts_a)
                                pop_b = _team_pop(counts_b)
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

        preset_label_txt = (
            f"Preset: {get_matchup_label(current_preset)} ({pop_cap} Pob)"
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
            f"EQUIPO A | Pob {pop_cap} ({pop_a})",
            max(60, card_a.w - 28),
            (font_header, font_item, font_small),
            TEAM_COLORS["A"],
        )
        hdr_b = _fit_text(
            f"EQUIPO B | Pob {pop_cap} ({pop_b})",
            max(60, card_b.w - 28),
            (font_header, font_item, font_small),
            TEAM_COLORS["B"],
        )
        screen.blit(hdr_a, (card_a.x + 14, card_a.y + 10))
        screen.blit(hdr_b, (card_b.x + 14, card_b.y + 10))

        for idx, kind in enumerate(UNIT_ORDER):
            ry = int(round(card_a.y + 36 + idx * row_step))
            cost = _unit_pop_cost(kind)
            label = UNIT_STATS[kind]["label"]
            max_row_txt_w = max(50, a_minus_btns[kind].left - (card_a.x + 22))

            txt_a = _fit_text(
                f"{label} ({cost}): {counts_a[kind]}",
                max_row_txt_w,
                (font_item, font_small),
                (238, 240, 246),
            )
            screen.blit(txt_a, (card_a.x + 14, ry + 4))

            txt_b = _fit_text(
                f"{label} ({cost}): {counts_b[kind]}",
                max_row_txt_w,
                (font_item, font_small),
                (238, 240, 246),
            )
            screen.blit(txt_b, (card_b.x + 14, ry + 4))

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
            for btn_r, sym, enabled in (
                (a_minus_btns[kind], "-", counts_a[kind] > 0),
                (
                    a_plus_btns[kind],
                    "+",
                    pop_a + _unit_pop_cost(kind) <= pop_cap,
                ),
                (b_minus_btns[kind], "-", counts_b[kind] > 0),
                (
                    b_plus_btns[kind],
                    "+",
                    pop_b + _unit_pop_cost(kind) <= pop_cap,
                ),
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
                s_t = font_header.render(
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
            selected = pkey == current_preset
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