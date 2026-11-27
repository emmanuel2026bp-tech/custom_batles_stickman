import random
import pygame

from arena_background import ArenaBackground
from battle_hud import (
    draw_battle_over_overlay,
    draw_combat_hud,
    draw_pause_overlay,
)
from combat_effects import (
    ArrowProjectile,
    BloodPuddle,
    DamagePopup,
    LimbPiece,
    SplatterParticle,
)
from fighter import Fighter
from game_config import ARENA_WORLD_WIDTH, HEIGHT, WIDTH
from matchups import ACTIVE_MATCHUP, counts_from_roster
from ui_screens import run_match_editor, run_start_menu

_FORMATION_RANK: dict[str, int] = {
    "lanzatonio": 0,
    "sword": 1,
    "archidon": 2,
}


def _sync_background_to_screen(
    screen: pygame.Surface, bg: ArenaBackground
) -> int:
    w, h = screen.get_size()
    new_ground_y = h - 106
    if w != bg.width or h != bg.height or new_ground_y != bg.ground_y:
        bg.width = w
        bg.height = h
        bg.ground_y = new_ground_y
        bg.terrain_surf = bg._build_terrain_surface()
    return new_ground_y


def _spawn_fighters(
    team_a_roster: list[str],
    team_b_roster: list[str],
    world_w: int,
    ground_y: int,
    rng: random.Random,
) -> list[Fighter]:
    fighters: list[Fighter] = []
    center_x = world_w * 0.5
    front_a_x = center_x - 360.0
    front_b_x = center_x + 360.0

    per_kind_a: dict[str, int] = {}
    for orig_idx, kind in enumerate(team_a_roster):
        slot = per_kind_a.get(kind, 0)
        per_kind_a[kind] = slot + 1
        rank = _FORMATION_RANK.get(kind, 1)
        depth = (
            rank * 42.0
            + (slot % 14) * 10.0
            + (slot // 14) * 6.0
            + rng.uniform(-1.5, 1.5)
        )
        x = max(80.0, min(center_x - 240.0, front_a_x - depth))
        fighters.append(Fighter(kind, "A", x, ground_y, orig_idx))

    per_kind_b: dict[str, int] = {}
    for orig_idx, kind in enumerate(team_b_roster):
        slot = per_kind_b.get(kind, 0)
        per_kind_b[kind] = slot + 1
        rank = _FORMATION_RANK.get(kind, 1)
        depth = (
            rank * 42.0
            + (slot % 14) * 10.0
            + (slot // 14) * 6.0
            + rng.uniform(-1.5, 1.5)
        )
        x = min(float(world_w - 80), max(center_x + 240.0, front_b_x + depth))
        fighters.append(Fighter(kind, "B", x, ground_y, orig_idx))

    return fighters


def _run_combat_loop(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    bg: ArenaBackground,
    rng: random.Random,
    preset_key: str,
    team_a_roster: list[str],
    team_b_roster: list[str],
) -> str:
    bg.randomize_terrain(rng)
    fighters = _spawn_fighters(
        team_a_roster, team_b_roster, bg.world_w, bg.ground_y, rng
    )
    particles: list[SplatterParticle] = []
    stains: list[BloodPuddle] = []
    pieces: list[LimbPiece] = []
    arrows: list[ArrowProjectile] = []
    popups: list[DamagePopup] = []

    paused = False
    elapsed = 0.0
    resize_ignore_timer = 0.0
    cam_x = max(0.0, (bg.world_w - screen.get_width()) * 0.5)
    font_hud = pygame.font.SysFont("consolas", 14, bold=True)
    font_small = pygame.font.SysFont("consolas", 12, bold=True)
    font_dmg = pygame.font.SysFont("consolas", 13, bold=True)
    font_crit = pygame.font.SysFont("consolas", 16, bold=True)
    font_banner = pygame.font.SysFont("consolas", 28, bold=True)

    pause_edit_btn = pygame.Rect(0, 0, 120, 34)
    pause_resume_btn = pygame.Rect(0, 0, 128, 34)
    pause_exit_btn = pygame.Rect(0, 0, 104, 34)

    edit_btn = pygame.Rect(0, 0, 126, 36)
    replay_btn = pygame.Rect(0, 0, 126, 36)
    exit_btn = pygame.Rect(0, 0, 110, 36)

    def reset_match() -> None:
        nonlocal fighters, elapsed, paused
        bg.randomize_terrain(rng)
        fighters = _spawn_fighters(
            team_a_roster, team_b_roster, bg.world_w, bg.ground_y, rng
        )
        particles.clear()
        stains.clear()
        pieces.clear()
        arrows.clear()
        popups.clear()
        elapsed = 0.0
        paused = False

    while True:
        dt = clock.tick(60) / 1000.0
        resize_ignore_timer = max(0.0, resize_ignore_timer - dt)
        screen = pygame.display.get_surface() or screen
        w, h = screen.get_size()
        max_cam = max(0.0, float(bg.world_w - w))
        mouse_pos = pygame.mouse.get_pos()

        live_a = [f for f in fighters if f.team == "A" and f.alive]
        live_b = [f for f in fighters if f.team == "B" and f.alive]
        battle_over = not live_a or not live_b
        pause_menu_open = paused and not battle_over

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.VIDEORESIZE and resize_ignore_timer <= 0.0:
                screen = pygame.display.get_surface() or screen
                new_gy = _sync_background_to_screen(screen, bg)
                for f in fighters:
                    f.ground_y = new_gy
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if pause_menu_open:
                        paused = False
                    else:
                        return "editor"
                elif event.key == pygame.K_e and battle_over:
                    return "editor"
                elif event.key == pygame.K_r and battle_over:
                    reset_match()
                elif event.key == pygame.K_r:
                    bg.randomize_terrain(rng)
                elif event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                    resize_ignore_timer = 0.2
                    screen = pygame.display.get_surface() or screen
                    new_gy = _sync_background_to_screen(screen, bg)
                    for f in fighters:
                        f.ground_y = new_gy
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if pause_menu_open:
                    if pause_edit_btn.collidepoint(event.pos):
                        return "editor"
                    if pause_resume_btn.collidepoint(event.pos):
                        paused = False
                    if pause_exit_btn.collidepoint(event.pos):
                        return "quit"
                elif battle_over:
                    if edit_btn.collidepoint(event.pos):
                        return "editor"
                    if replay_btn.collidepoint(event.pos):
                        reset_match()
                    if exit_btn.collidepoint(event.pos):
                        return "quit"

        keys = pygame.key.get_pressed()
        if not paused:
            if live_a and live_b:
                elapsed += dt

            for f in fighters:
                if f.alive or not f.death_splattered:
                    allies = live_a if f.team == "A" else live_b
                    enemies = live_b if f.team == "A" else live_a
                    f.update(
                        dt,
                        allies,
                        enemies,
                        bg.world_w,
                        particles,
                        stains,
                        pieces,
                        arrows,
                        popups,
                        rng,
                    )

            arrows = [
                a
                for a in arrows
                if a.update(
                    dt,
                    bg.ground_y,
                    live_b if a.team == "A" else live_a,
                    particles,
                    stains,
                    pieces,
                    popups,
                    rng,
                )
            ]
            particles = [
                p for p in particles if p.update(dt, bg.ground_y, stains)
            ]
            pieces = [
                piece
                for piece in pieces
                if piece.update(dt, bg.ground_y, bg.world_w)
            ]
            popups = [pop for pop in popups if pop.update(dt)]

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                cam_x = max(0.0, cam_x - 540.0 * dt)
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                cam_x = min(max_cam, cam_x + 540.0 * dt)
            elif live_a and live_b:
                avg_x = sum(f.x for f in live_a + live_b) / len(live_a + live_b)
                desired_cam = max(0.0, min(max_cam, avg_x - w * 0.5))
                cam_x += (desired_cam - cam_x) * min(1.0, dt * 4.5)

        bg.draw(screen, cam_x)

        for puddle in stains:
            puddle.draw(screen, cam_x)

        for piece in pieces:
            piece.draw(screen, cam_x)

        for p in particles:
            p.draw(screen, cam_x)

        for f in fighters:
            f.draw(screen, cam_x, font_small)

        for a in arrows:
            a.draw(screen, cam_x)

        for pop in popups:
            pop.draw(screen, cam_x, font_dmg, font_crit)

        mins, secs = draw_combat_hud(
            screen,
            w=w,
            elapsed=elapsed,
            paused=paused,
            terrain_name=bg.terrain_variant,
            live_a_count=len(live_a),
            live_b_count=len(live_b),
            font_hud=font_hud,
        )

        if pause_menu_open:
            draw_pause_overlay(
                screen,
                w=w,
                h=h,
                mouse_pos=mouse_pos,
                pause_edit_btn=pause_edit_btn,
                pause_resume_btn=pause_resume_btn,
                pause_exit_btn=pause_exit_btn,
                font_banner=font_banner,
                font_small=font_small,
            )

        if battle_over:
            draw_battle_over_overlay(
                screen,
                w=w,
                h=h,
                mins=mins,
                secs=secs,
                preset_key=preset_key,
                live_a_count=len(live_a),
                live_b_count=len(live_b),
                mouse_pos=mouse_pos,
                edit_btn=edit_btn,
                replay_btn=replay_btn,
                exit_btn=exit_btn,
                font_banner=font_banner,
                font_hud=font_hud,
                font_small=font_small,
            )

        pygame.display.flip()


def run_auto_battle(seed: int | None = None) -> None:
    pygame.init()
    pygame.display.set_caption("Arena Simulador")

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    rng = random.Random(seed)
    bg = ArenaBackground(WIDTH, HEIGHT, ARENA_WORLD_WIDTH)

    current_preset = ACTIVE_MATCHUP
    saved_counts_a: dict[str, int] | None = None
    saved_counts_b: dict[str, int] | None = None

    while True:
        _sync_background_to_screen(screen, bg)
        if not run_start_menu(screen, clock, bg):
            break

        while True:
            _sync_background_to_screen(screen, bg)
            edited = run_match_editor(
                screen,
                clock,
                bg,
                rng,
                initial_preset=current_preset,
                initial_counts_a=saved_counts_a,
                initial_counts_b=saved_counts_b,
            )
            if edited is None:
                break

            chosen_preset, roster_a, roster_b = edited
            current_preset = chosen_preset
            saved_counts_a = counts_from_roster(roster_a)
            saved_counts_b = counts_from_roster(roster_b)

            _sync_background_to_screen(screen, bg)
            action = _run_combat_loop(
                screen, clock, bg, rng, chosen_preset, roster_a, roster_b
            )
            if action == "quit":
                pygame.quit()
                return

    pygame.quit()


if __name__ == "__main__":
    run_auto_battle()