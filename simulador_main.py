from __future__ import annotations

import random
import sys
from typing import TYPE_CHECKING

import pygame

from arena_background import ArenaBackground
from combat_effects import (
    ArrowProjectile,
    BloodPuddle,
    DamagePopup,
    LimbPiece,
    ShurikenProjectile,
    SplatterParticle,
)
from fighter import Fighter
from game_config import (
    ARENA_WORLD_WIDTH,
    HEIGHT,
    WIDTH,
)
from matchups import (
    ACTIVE_MATCHUP,
    MATCHUPS,
    RANDOM_MATCHUP_KEY,
    RANDOM_TARGET_POPULATION,
    UNIT_POP_COST,
    generate_random_armies,
    get_matchup_armies,
    get_matchup_label,
    normalize_kind,
)
from ui_screens import (
    build_hud_buttons,
    draw_battle_hud,
    draw_end_overlay,
    draw_pause_overlay,
    run_match_editor,
    run_start_menu,
)

if TYPE_CHECKING:
    from pygame.font import Font

# 0 = frente (más cerca del centro: lanzatonios)
# 1 = medio (swords)
# 2 = atrás (archidon)
# 3 = último / retaguardia (shadowrath)
_FORMATION_RANK: dict[str, int] = {
    "lanzatonio": 0,
    "lanzatonio_elite": 0,
    "sword": 1,
    "archidon": 2,
    "shadowrath": 3,
    "ninja": 3,
}


def _canonical_kind(raw_kind: object) -> str:
    text = str(raw_kind or "").strip().lower()
    norm = normalize_kind(text).strip().lower() if text else ""
    candidate = norm or text
    if "sword" in candidate or "espada" in candidate:
        return "sword"
    if "archi" in candidate or "arco" in candidate:
        return "archidon"
    return candidate


def _fighter_pop_cost(fighter: Fighter) -> int:
    raw_kind = getattr(fighter, "kind", "")
    kind = normalize_kind(str(raw_kind)) if raw_kind else ""
    return max(1, int(UNIT_POP_COST.get(kind, 1)))


def _team_alive_pop(fighters: list[Fighter]) -> int:
    return sum(_fighter_pop_cost(f) for f in fighters if f.alive)


def _closest_to_center_x(fighters: list[Fighter], world_w: int) -> float:
    center_x = world_w * 0.5
    closest = min(fighters, key=lambda f: abs(f.x - center_x))
    return float(closest.x)


def _resolve_formation_rank(raw_kind: str) -> int:
    norm = _canonical_kind(raw_kind)
    if norm in _FORMATION_RANK:
        return _FORMATION_RANK[norm]
    raw_low = raw_kind.strip().lower()
    if "lanza" in raw_low:
        return 0
    if "sword" in raw_low or "espada" in raw_low:
        return 1
    if "archi" in raw_low or "arco" in raw_low:
        return 2
    if "shadow" in raw_low or "ninja" in raw_low:
        return 3
    return 9


def _build_team_fighters(
    roster: list[str],
    team: str,
    ground_y: int,
    world_w: int,
    rng: random.Random,
) -> list[Fighter]:
    if not roster:
        return []

    ordered = sorted(
        enumerate(roster),
        key=lambda pair: (_resolve_formation_rank(pair[1]), pair[0]),
    )

    edge_margin = 120.0
    min_x = edge_margin
    max_x = max(edge_margin + 40.0, float(world_w) - edge_margin)

    n_units = len(ordered)
    if team == "A":
        front_x = min(world_w * 0.43, max_x - 20.0)
        avail_span = max(40.0, front_x - min_x)
    else:
        front_x = max(world_w * 0.57, min_x + 20.0)
        avail_span = max(40.0, max_x - front_x)

    ideal_step = 16.0
    ideal_gap = 24.0
    max_rank = max((_resolve_formation_rank(k) for _, k in ordered), default=0)
    needed_span = max(1.0, (n_units - 1) * ideal_step + max(0, max_rank) * ideal_gap)
    scale = min(1.0, (avail_span * 0.88) / needed_span)

    step_x = ideal_step * scale
    line_gap = ideal_gap * scale

    fighters: list[Fighter] = []
    for slot_idx, (orig_idx, raw_kind) in enumerate(ordered):
        kind = normalize_kind(raw_kind)
        rank = _resolve_formation_rank(raw_kind)
        offset = slot_idx * step_x + max(0, rank) * line_gap + rng.uniform(-2.5, 2.5)
        if team == "A":
            x = max(min_x, min(max_x, front_x - offset))
        else:
            x = max(min_x, min(max_x, front_x + offset))
        fighters.append(Fighter(kind, team, x, ground_y, orig_idx))
    return fighters


def _halve_blood_particles(
    particles: list[SplatterParticle],
    seen_ids: set[int],
    rng: random.Random,
) -> list[SplatterParticle]:
    """Reduce las partículas de sangre aproximadamente a la mitad."""
    new_particles = [p for p in particles if id(p) not in seen_ids]
    kept_new: list[SplatterParticle] = []
    for p in new_particles:
        seen_ids.add(id(p))
        if rng.random() < 0.5:
            kept_new.append(p)

    existing_ids = {id(p) for p in particles}
    seen_ids.intersection_update(existing_ids)

    existing_kept = [p for p in particles if id(p) in seen_ids]
    return existing_kept + kept_new


def _boost_flying_pieces(
    pieces: list[LimbPiece],
    boosted_ids: set[int],
    eff_dt: float,
    rng: random.Random,
) -> None:
    """Aumenta la distancia y el impulso con que salen volando armas, armaduras y accesorios."""
    existing_ids = {id(piece) for piece in pieces}
    boosted_ids.intersection_update(existing_ids)

    for piece in pieces:
        pid = id(piece)
        if pid in boosted_ids:
            continue
        boosted_ids.add(pid)

        h_scale = rng.uniform(1.85, 2.45)
        v_scale = rng.uniform(1.35, 1.75)

        for vx_attr in ("vx", "vel_x", "dx"):
            if hasattr(piece, vx_attr):
                val = getattr(piece, vx_attr)
                if isinstance(val, (int, float)):
                    if abs(val) < 15.0:
                        direction = rng.choice((-1.0, 1.0))
                        setattr(piece, vx_attr, direction * rng.uniform(140.0, 230.0))
                    else:
                        setattr(piece, vx_attr, val * h_scale)
                    break

        for vy_attr in ("vy", "vel_y", "dy"):
            if hasattr(piece, vy_attr):
                val = getattr(piece, vy_attr)
                if isinstance(val, (int, float)):
                    if val >= -20.0:
                        setattr(piece, vy_attr, -rng.uniform(170.0, 260.0))
                    else:
                        setattr(piece, vy_attr, val * v_scale)
                    break

        if eff_dt > 0.0 and hasattr(piece, "x"):
            cur_vx = 0.0
            for vx_attr in ("vx", "vel_x", "dx"):
                if hasattr(piece, vx_attr) and isinstance(getattr(piece, vx_attr), (int, float)):
                    cur_vx = float(getattr(piece, vx_attr))
                    break
            piece.x += cur_vx * eff_dt * 0.45


def _unstuck_edge_fighters(
    fighters_a: list[Fighter],
    fighters_b: list[Fighter],
    world_w: int,
    stuck_timers: dict[int, float],
    last_pos: dict[int, float],
    dt: float,
) -> None:
    """Libera unidades que queden atascadas contra las orillas del escenario."""
    left_edge = 95.0
    right_edge = max(left_edge + 40.0, float(world_w) - 95.0)
    center_x = world_w * 0.5

    for f in fighters_a + fighters_b:
        fid = id(f)
        if not f.alive:
            stuck_timers.pop(fid, None)
            last_pos.pop(fid, None)
            continue

        prev = last_pos.get(fid, f.x)
        moved = abs(f.x - prev)
        near_left = f.x <= left_edge + 8.0
        near_right = f.x >= right_edge - 8.0

        if (near_left or near_right) and moved < 0.35:
            stuck_timers[fid] = stuck_timers.get(fid, 0.0) + dt
        else:
            stuck_timers[fid] = 0.0

        last_pos[fid] = f.x

        if stuck_timers.get(fid, 0.0) >= 0.45:
            stuck_timers[fid] = 0.0
            inward_dir = 1.0 if f.x < center_x else -1.0
            f.x = max(left_edge + 14.0, min(right_edge - 14.0, f.x + inward_dir * 18.0))
            if hasattr(f, "vx"):
                f.vx = inward_dir * 85.0
            if hasattr(f, "facing"):
                f.facing = 1 if inward_dir > 0 else -1
            if hasattr(f, "vy") and getattr(f, "vy", 0.0) >= 0.0:
                f.vy = -120.0


def _apply_new_terrain(
    bg: ArenaBackground,
    rng: random.Random,
    fighters_a: list[Fighter],
    fighters_b: list[Fighter],
) -> int:
    bg.randomize_terrain(rng)
    new_ground_y = bg.ground_y
    for f in fighters_a + fighters_b:
        if hasattr(f, "ground_y"):
            f.ground_y = new_ground_y
        if f.alive:
            if hasattr(f, "y"):
                f.y = float(new_ground_y)
            if hasattr(f, "vy"):
                f.vy = 0.0
            if hasattr(f, "on_ground"):
                f.on_ground = True
            if hasattr(f, "is_jumping"):
                f.is_jumping = False
    return new_ground_y


def _compute_camera_x(
    fighters_a: list[Fighter],
    fighters_b: list[Fighter],
    cam_x: float,
    world_w: int,
    screen_w: int,
    rng: random.Random,
    tie_focus_team: str | None,
) -> tuple[float, str | None]:
    alive_a = [f for f in fighters_a if f.alive]
    alive_b = [f for f in fighters_b if f.alive]
    if not alive_a and not alive_b:
        return cam_x, None

    if alive_a and not alive_b:
        focus_x = _closest_to_center_x(alive_a, world_w)
        active_tie_team = None
    elif alive_b and not alive_a:
        focus_x = _closest_to_center_x(alive_b, world_w)
        active_tie_team = None
    else:
        pop_a = _team_alive_pop(alive_a)
        pop_b = _team_alive_pop(alive_b)
        if pop_a > pop_b:
            focus_x = _closest_to_center_x(alive_a, world_w)
            active_tie_team = None
        elif pop_b > pop_a:
            focus_x = _closest_to_center_x(alive_b, world_w)
            active_tie_team = None
        else:
            chosen_team = (
                tie_focus_team
                if tie_focus_team in ("A", "B")
                else rng.choice(("A", "B"))
            )
            active_tie_team = chosen_team
            chosen_group = alive_a if chosen_team == "A" else alive_b
            focus_x = _closest_to_center_x(chosen_group, world_w)

    max_cam = max(0.0, float(world_w - screen_w))
    target_cam = max(0.0, min(max_cam, focus_x - screen_w * 0.5))
    next_cam_x = cam_x + (target_cam - cam_x) * 0.12
    return next_cam_x, active_tie_team


def _run_combat_loop(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    font_small: Font,
    font_med: Font,
    font_large: Font,
    bg: ArenaBackground,
    matchup_key: str,
    matchup_label: str,
    match_mode: str,
    roster_a: list[str],
    roster_b: list[str],
    rng: random.Random,
) -> str:
    bg.randomize_terrain(rng)
    world_w = bg.world_w
    ground_y = bg.ground_y

    fighters_a = _build_team_fighters(roster_a, "A", ground_y, world_w, rng)
    fighters_b = _build_team_fighters(roster_b, "B", ground_y, world_w, rng)

    stuck_timers: dict[int, float] = {}
    last_pos: dict[int, float] = {
        id(f): f.x for f in fighters_a + fighters_b
    }

    particles: list[SplatterParticle] = []
    seen_particle_ids: set[int] = set()
    stains: list[BloodPuddle] = []
    pieces: list[LimbPiece] = []
    boosted_piece_ids: set[int] = set()
    arrows: list[ArrowProjectile] = []
    shurikens: list[ShurikenProjectile] = []
    popups: list[DamagePopup] = []

    cam_x = max(
        0.0,
        min(
            float(world_w - screen.get_width()),
            world_w * 0.5 - screen.get_width() * 0.5,
        ),
    )
    tie_focus_team: str | None = None
    sim_speed = 1.0
    paused = False
    winner_team: str | None = None
    elapsed_time = 0.0

    while True:
        raw_dt = clock.tick(60) / 1000.0
        dt = min(0.05, max(0.0, raw_dt))

        hud_buttons = build_hud_buttons(
            screen.get_width(),
            paused=paused,
            sim_speed=sim_speed,
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
                elif event.key in (pygame.K_SPACE, pygame.K_p):
                    if winner_team is None:
                        paused = not paused
                elif event.key == pygame.K_r:
                    return "restart"
                elif event.key == pygame.K_m:
                    return "menu"
                elif event.key in (pygame.K_t, pygame.K_g):
                    ground_y = _apply_new_terrain(bg, rng, fighters_a, fighters_b)
                elif event.key == pygame.K_1:
                    sim_speed = 1.0
                elif event.key == pygame.K_2:
                    sim_speed = 2.0
                elif event.key == pygame.K_3:
                    sim_speed = 4.0
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                for btn_id, rect in hud_buttons.items():
                    if rect.collidepoint(mx, my):
                        if btn_id == "pause" and winner_team is None:
                            paused = not paused
                        elif btn_id == "speed_1":
                            sim_speed = 1.0
                        elif btn_id == "speed_2":
                            sim_speed = 2.0
                        elif btn_id == "speed_4":
                            sim_speed = 4.0
                        elif btn_id == "restart":
                            return "restart"
                        elif btn_id == "menu":
                            return "menu"

        if not paused:
            eff_dt = dt * sim_speed
            if winner_team is None:
                elapsed_time += eff_dt

            for f in fighters_a:
                f.update(
                    eff_dt,
                    fighters_a,
                    fighters_b,
                    world_w,
                    particles,
                    stains,
                    pieces,
                    arrows,
                    popups,
                    rng,
                    shurikens=shurikens,
                )
            for f in fighters_b:
                f.update(
                    eff_dt,
                    fighters_b,
                    fighters_a,
                    world_w,
                    particles,
                    stains,
                    pieces,
                    arrows,
                    popups,
                    rng,
                    shurikens=shurikens,
                )

            _unstuck_edge_fighters(
                fighters_a,
                fighters_b,
                world_w,
                stuck_timers,
                last_pos,
                eff_dt if eff_dt > 0.0 else dt,
            )

            for arrow in arrows:
                enemies_for_arrow = fighters_b if arrow.team == "A" else fighters_a
                arrow.update(
                    eff_dt,
                    enemies_for_arrow,
                    particles,
                    stains,
                    pieces,
                    popups,
                    rng,
                    ground_y,
                )
            arrows = [a for a in arrows if a.active]

            for shuriken in shurikens:
                enemies_for_shuriken = (
                    fighters_b if shuriken.team == "A" else fighters_a
                )
                shuriken.update(
                    eff_dt,
                    enemies_for_shuriken,
                    particles,
                    stains,
                    pieces,
                    popups,
                    rng,
                    ground_y,
                )
            shurikens = [s for s in shurikens if s.active]

            particles = _halve_blood_particles(particles, seen_particle_ids, rng)
            _boost_flying_pieces(pieces, boosted_piece_ids, eff_dt, rng)

            particles = [
                p for p in particles if p.update(eff_dt, ground_y, stains)
            ]
            pieces = [
                piece for piece in pieces if piece.update(eff_dt, ground_y, world_w)
            ]
            for popup in popups:
                popup.update(eff_dt)
            popups = [pop for pop in popups if pop.active]

            alive_a = sum(1 for f in fighters_a if f.alive)
            alive_b = sum(1 for f in fighters_b if f.alive)
            if winner_team is None:
                if alive_a == 0 and alive_b == 0:
                    winner_team = "DRAW"
                elif alive_a == 0:
                    winner_team = "B"
                elif alive_b == 0:
                    winner_team = "A"

        cam_x, tie_focus_team = _compute_camera_x(
            fighters_a,
            fighters_b,
            cam_x,
            world_w,
            screen.get_width(),
            rng,
            tie_focus_team,
        )

        bg.draw(screen, cam_x)
        for stain in stains:
            stain.draw(screen, cam_x)
        for piece in pieces:
            piece.draw(screen, cam_x)
        for f in fighters_a:
            f.draw(screen, cam_x, font_small)
        for f in fighters_b:
            f.draw(screen, cam_x, font_small)
        for arrow in arrows:
            arrow.draw(screen, cam_x)
        for shuriken in shurikens:
            shuriken.draw(screen, cam_x)
        for particle in particles:
            particle.draw(screen, cam_x)
        for popup in popups:
            popup.draw(screen, cam_x, font_small)

        phase_str = None
        if winner_team is not None:
            phase_str = "FIN"

        draw_battle_hud(
            screen,
            font_small,
            font_med,
            matchup_key=matchup_key,
            matchup_label=matchup_label,
            fighters_a=fighters_a,
            fighters_b=fighters_b,
            elapsed_time=elapsed_time,
            sim_speed=sim_speed,
            paused=paused,
            buttons=hud_buttons,
            bg=bg,
            phase_label=phase_str,
            match_mode=match_mode,
        )

        if paused and winner_team is None:
            draw_pause_overlay(screen, font_med, font_large)
        elif winner_team is not None:
            draw_end_overlay(
                screen,
                font_small,
                font_med,
                font_large,
                winner_team=winner_team,
                fighters_a=fighters_a,
                fighters_b=fighters_b,
                elapsed_time=elapsed_time,
            )

        pygame.display.flip()


def run_auto_battle() -> None:
    pygame.init()
    pygame.display.set_caption("Simulador de Batallas Stickman")
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    clock = pygame.time.Clock()

    font_small = pygame.font.SysFont("consolas", 11, bold=True)
    font_med = pygame.font.SysFont("consolas", 20, bold=True)
    font_large = pygame.font.SysFont("consolas", 36, bold=True)

    bg = ArenaBackground(
        width=WIDTH,
        height=HEIGHT,
        world_w=ARENA_WORLD_WIDTH,
    )
    rng = random.Random()
    last_preset = ACTIVE_MATCHUP

    while True:
        if not run_start_menu(screen, clock, bg):
            break

        selected = run_match_editor(
            screen,
            clock,
            bg,
            rng,
            initial_preset=last_preset,
        )
        if selected is None:
            continue

        preset_key, roster_a, roster_b, match_mode = selected
        last_preset = preset_key
        matchup_label = (
            "Partida Aleatoria"
            if match_mode == "random"
            else get_matchup_label(preset_key)
        )

        while True:
            action = _run_combat_loop(
                screen,
                clock,
                font_small,
                font_med,
                font_large,
                bg,
                matchup_key=preset_key,
                matchup_label=matchup_label,
                match_mode=match_mode,
                roster_a=roster_a,
                roster_b=roster_b,
                rng=rng,
            )
            if action == "restart":
                if match_mode == "random" or preset_key == RANDOM_MATCHUP_KEY:
                    roster_a, roster_b = generate_random_armies(
                        target_pop=RANDOM_TARGET_POPULATION, rng=rng
                    )
                elif match_mode == "custom":
                    pass
                elif preset_key in MATCHUPS:
                    roster_a, roster_b = get_matchup_armies(preset_key, rng=rng)
                continue
            bg.set_menu_terrain()
            break

    pygame.quit()


if __name__ == "__main__":
    run_auto_battle()