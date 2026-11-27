import math
import random
import pygame

from arena_background import ArenaBackground
from combat_effects import (
    ArrowProjectile,
    BloodPuddle,
    DamagePopup,
    LimbPiece,
    SplatterParticle,
)
from game_config import (
    ARENA_WORLD_WIDTH,
    HEIGHT,
    TEAM_COLORS,
    UNIT_STATS,
    WIDTH,
)
from matchups import (
    ACTIVE_MATCHUP,
    counts_from_roster,
    get_matchup_label,
)
from ui_screens import run_match_editor, run_start_menu
from unit_visuals import draw_fighter_visual

_FORMATION_RANK: dict[str, int] = {
    "lanzatonio": 0,
    "sword": 1,
    "archidon": 2,
}

LEAP_POPUP_COLOR: tuple[int, int, int] = (255, 140, 24)


def _sync_background_to_screen(screen: pygame.Surface, bg: ArenaBackground) -> int:
    w, h = screen.get_size()
    new_ground_y = h - 106
    if w != bg.width or h != bg.height or new_ground_y != bg.ground_y:
        bg.width = w
        bg.height = h
        bg.ground_y = new_ground_y
        bg.terrain_surf = bg._build_terrain_surface()
    return new_ground_y


class Fighter:
    def __init__(self, kind: str, team: str, x: float, ground_y: int, idx: int):
        cfg = UNIT_STATS.get(kind, UNIT_STATS["sword"])
        self.kind = kind
        self.team = team
        self.x = x
        self.ground_y = ground_y
        self.idx = idx
        self.max_hp = int(cfg["hp"])
        self.hp = self.max_hp
        self.atk = int(cfg["atk"])
        self.attack_range = float(cfg["range"])
        self.speed = float(cfg["speed"])
        self.cooldown = float(cfg["cooldown"])
        self.arrow_block_chance = float(cfg.get("arrow_block_chance", 0.0))
        self.leap_attack_chance = float(cfg.get("leap_attack_chance", 0.20))
        self.leap_damage_mult = float(cfg.get("leap_damage_mult", 1.40))
        self.color: tuple[int, int, int] = cfg["color"]
        self.team_color: tuple[int, int, int] = TEAM_COLORS.get(team, (255, 214, 54))
        self.vs_mult: dict[str, float] = dict(cfg.get("vs_mult", {}))
        self.atk_timer = 0.0
        self.hit_flash = 0.0
        self.walk_phase = float(idx) * 0.7
        self.death_splattered = False
        self.leap_timer = 0.0
        self.leap_duration = 0.28
        self.leap_height = 18.0
        self.last_attack_was_leap = False

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def compute_damage_against(
        self, target: "Fighter", rng: random.Random | None = None
    ) -> int:
        mult = self.vs_mult.get(target.kind, 1.0)
        leap_mult = 1.0
        self.last_attack_was_leap = False
        if self.kind == "sword" and self.leap_attack_chance > 0.0:
            roll_rng = rng if rng is not None else random
            if roll_rng.random() < self.leap_attack_chance:
                leap_mult = self.leap_damage_mult
                self.last_attack_was_leap = True
                self.leap_timer = self.leap_duration
        return max(1, int(round(self.atk * mult * leap_mult)))

    def try_block_arrow_from_kind(self, attacker_kind: str, rng: random.Random) -> bool:
        if attacker_kind != "archidon" or self.arrow_block_chance <= 0.0:
            return False
        return rng.random() < self.arrow_block_chance

    def spawn_splatter(
        self,
        particles: list[SplatterParticle],
        stains: list[BloodPuddle],
        rng: random.Random,
        heavy: bool = False,
    ) -> None:
        hit_y = float(self.ground_y - rng.randint(16, 44))

        count = rng.randint(24, 38) if heavy else rng.randint(10, 16)
        for _ in range(count):
            dark_blood = (
                rng.randint(78, 132),
                rng.randint(5, 15),
                rng.randint(8, 20),
            )
            angle = rng.uniform(-math.pi * 0.96, -math.pi * 0.04)
            speed = rng.uniform(110.0, 320.0) if heavy else rng.uniform(75.0, 225.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            rad = rng.randint(2, 4) if heavy else rng.randint(2, 3)
            particles.append(SplatterParticle(self.x, hit_y, vx, vy, rad, dark_blood))

        puddle_count = 8 if heavy else 3
        for _ in range(puddle_count):
            puddle_col = (
                rng.randint(68, 115),
                rng.randint(4, 12),
                rng.randint(6, 16),
            )
            sx = self.x + rng.uniform(-26.0, 26.0)
            rx = rng.randint(8, 16) if heavy else rng.randint(5, 11)
            ry = rng.randint(2, 4)
            stains.append(
                BloodPuddle(sx, self.ground_y + rng.randint(1, 5), rx, ry, puddle_col)
            )
        if len(stains) > 1600:
            del stains[: len(stains) - 1600]

    def spawn_dismantle_pieces(
        self,
        pieces: list[LimbPiece],
        rng: random.Random,
    ) -> None:
        body_col = self.team_color
        steel_col = (222, 230, 242)
        heavy_steel_col = (188, 200, 218)
        trim_col = (112, 128, 152)
        wood_col = (142, 88, 42)
        hat_col = (52, 126, 68)
        hat_band_col = (36, 92, 48)
        sy = float(self.ground_y)

        pieces.append(
            LimbPiece(
                "head",
                self.x + rng.uniform(-3.0, 3.0),
                sy - 41.0,
                rng.uniform(-130.0, 130.0),
                rng.uniform(-240.0, -120.0),
                rng.uniform(0.0, math.tau),
                rng.uniform(-9.0, 9.0),
                6.0,
                3,
                body_col,
            )
        )

        pieces.append(
            LimbPiece(
                "limb",
                self.x,
                sy - 23.0,
                rng.uniform(-95.0, 95.0),
                rng.uniform(-180.0, -70.0),
                math.pi * 0.5 + rng.uniform(-0.4, 0.4),
                rng.uniform(-7.0, 7.0),
                16.0,
                3,
                body_col,
            )
        )

        for _ in range(4):
            pieces.append(
                LimbPiece(
                    "limb",
                    self.x + rng.uniform(-6.0, 6.0),
                    sy - rng.uniform(12.0, 30.0),
                    rng.uniform(-165.0, 165.0),
                    rng.uniform(-220.0, -85.0),
                    rng.uniform(0.0, math.tau),
                    rng.uniform(-12.0, 12.0),
                    13.0,
                    3,
                    body_col,
                )
            )

        if self.kind == "sword":
            pieces.append(
                LimbPiece(
                    "helmet",
                    self.x + rng.uniform(-4.0, 4.0),
                    sy - 47.0,
                    rng.uniform(-145.0, 145.0),
                    rng.uniform(-245.0, -120.0),
                    rng.uniform(-0.6, 0.6),
                    rng.uniform(-11.0, 11.0),
                    14.0,
                    5,
                    steel_col,
                    trim_color=trim_col,
                )
            )
            pieces.append(
                LimbPiece(
                    "armor",
                    self.x + rng.uniform(-4.0, 4.0),
                    sy - 25.0,
                    rng.uniform(-125.0, 125.0),
                    rng.uniform(-210.0, -90.0),
                    rng.uniform(-0.4, 0.4),
                    rng.uniform(-8.0, 8.0),
                    10.0,
                    5,
                    steel_col,
                    trim_color=trim_col,
                )
            )
            pieces.append(
                LimbPiece(
                    "limb",
                    self.x + rng.uniform(-6.0, 6.0),
                    sy - 31.0,
                    rng.uniform(-140.0, 140.0),
                    rng.uniform(-215.0, -95.0),
                    rng.uniform(-0.8, 0.8),
                    rng.uniform(-10.0, 10.0),
                    8.0,
                    4,
                    steel_col,
                )
            )
            pieces.append(
                LimbPiece(
                    "limb",
                    self.x + rng.uniform(-5.0, 5.0),
                    sy - 28.0,
                    rng.uniform(-150.0, 150.0),
                    rng.uniform(-230.0, -100.0),
                    rng.uniform(-1.0, 1.0),
                    rng.uniform(-14.0, 14.0),
                    18.0,
                    3,
                    steel_col,
                )
            )
        elif self.kind == "archidon":
            pieces.append(
                LimbPiece(
                    "hat",
                    self.x + rng.uniform(-4.0, 4.0),
                    sy - 47.0,
                    rng.uniform(-145.0, 145.0),
                    rng.uniform(-245.0, -120.0),
                    rng.uniform(-0.6, 0.6),
                    rng.uniform(-10.0, 10.0),
                    22.0,
                    5,
                    hat_col,
                    trim_color=hat_band_col,
                )
            )
            pieces.append(
                LimbPiece(
                    "quiver",
                    self.x + rng.uniform(-6.0, 6.0),
                    sy - 28.0,
                    rng.uniform(-130.0, 130.0),
                    rng.uniform(-205.0, -90.0),
                    rng.uniform(-0.5, 0.5),
                    rng.uniform(-9.0, 9.0),
                    8.0,
                    7,
                    wood_col,
                    trim_color=steel_col,
                )
            )
            pieces.append(
                LimbPiece(
                    "limb",
                    self.x + rng.uniform(-5.0, 5.0),
                    sy - 28.0,
                    rng.uniform(-140.0, 140.0),
                    rng.uniform(-210.0, -90.0),
                    rng.uniform(-1.0, 1.0),
                    rng.uniform(-11.0, 11.0),
                    18.0,
                    3,
                    wood_col,
                )
            )
        elif self.kind == "lanzatonio":
            pieces.append(
                LimbPiece(
                    "helmet",
                    self.x + rng.uniform(-4.0, 4.0),
                    sy - 48.0,
                    rng.uniform(-140.0, 140.0),
                    rng.uniform(-240.0, -115.0),
                    rng.uniform(-0.6, 0.6),
                    rng.uniform(-10.0, 10.0),
                    16.0,
                    6,
                    heavy_steel_col,
                    trim_color=trim_col,
                )
            )
            pieces.append(
                LimbPiece(
                    "armor",
                    self.x + rng.uniform(-4.0, 4.0),
                    sy - 25.0,
                    rng.uniform(-120.0, 120.0),
                    rng.uniform(-205.0, -85.0),
                    rng.uniform(-0.4, 0.4),
                    rng.uniform(-8.0, 8.0),
                    12.0,
                    6,
                    heavy_steel_col,
                    trim_color=trim_col,
                )
            )
            pieces.append(
                LimbPiece(
                    "shield",
                    self.x + rng.uniform(-7.0, 7.0),
                    sy - 20.0,
                    rng.uniform(-135.0, 135.0),
                    rng.uniform(-210.0, -90.0),
                    rng.uniform(-0.35, 0.35),
                    rng.uniform(-6.0, 6.0),
                    16.0,
                    14,
                    heavy_steel_col,
                    trim_color=trim_col,
                )
            )
            pieces.append(
                LimbPiece(
                    "limb",
                    self.x + rng.uniform(-6.0, 6.0),
                    sy - 31.0,
                    rng.uniform(-145.0, 145.0),
                    rng.uniform(-220.0, -95.0),
                    rng.uniform(-0.8, 0.8),
                    rng.uniform(-10.0, 10.0),
                    9.0,
                    4,
                    heavy_steel_col,
                )
            )
            pieces.append(
                LimbPiece(
                    "spear_tip",
                    self.x + rng.uniform(-6.0, 6.0),
                    sy - 28.0,
                    rng.uniform(-155.0, 155.0),
                    rng.uniform(-225.0, -95.0),
                    rng.uniform(-0.8, 0.8),
                    rng.uniform(-10.0, 10.0),
                    28.0,
                    3,
                    wood_col,
                )
            )

        if len(pieces) > 900:
            del pieces[: len(pieces) - 900]

    def _compute_crowd_push(
        self,
        allies: list["Fighter"],
        enemies: list["Fighter"],
        target: "Fighter",
    ) -> float:
        if self.kind == "archidon":
            return 0.0
        min_sep = 16.0
        push = 0.0
        for other in allies + enemies:
            if other is self or not other.alive or other.kind == "archidon":
                continue
            dx = self.x - other.x
            adx = abs(dx)
            if 0.0 < adx < min_sep:
                strength = (min_sep - adx) / min_sep
                if other is target:
                    push += math.copysign(strength * 0.25, dx)
                else:
                    push += math.copysign(strength * 0.65, dx)
            elif adx == 0.0:
                push += 0.2 if (self.idx % 2 == 0) else -0.2
        return max(-0.85, min(0.85, push))

    def _clamp_behind_allied_lanzatonios(
        self,
        next_x: float,
        allies: list["Fighter"],
    ) -> float:
        if self.kind != "sword":
            return next_x
        lanzatonios = [a for a in allies if a.alive and a.kind == "lanzatonio"]
        if not lanzatonios:
            return next_x
        buffer_px = 14.0
        if self.team == "A":
            front_lanz_x = max(a.x for a in lanzatonios)
            return min(next_x, front_lanz_x - buffer_px)
        front_lanz_x = min(a.x for a in lanzatonios)
        return max(next_x, front_lanz_x + buffer_px)

    def update(
        self,
        dt: float,
        allies: list["Fighter"],
        enemies: list["Fighter"],
        world_w: int,
        particles: list[SplatterParticle],
        stains: list[BloodPuddle],
        pieces: list[LimbPiece],
        arrows: list[ArrowProjectile],
        popups: list[DamagePopup],
        rng: random.Random,
    ) -> None:
        if not self.alive:
            if not self.death_splattered:
                self.death_splattered = True
                self.spawn_splatter(particles, stains, rng, heavy=True)
                self.spawn_dismantle_pieces(pieces, rng)
            return

        self.atk_timer = max(0.0, self.atk_timer - dt)
        self.hit_flash = max(0.0, self.hit_flash - dt)
        self.leap_timer = max(0.0, self.leap_timer - dt)

        live_enemies = [e for e in enemies if e.alive]
        if not live_enemies:
            return

        target = min(live_enemies, key=lambda e: abs(e.x - self.x))
        dist = abs(target.x - self.x)
        direction = 1.0 if target.x >= self.x else -1.0
        crowd_push = self._compute_crowd_push(allies, enemies, target)

        if dist > self.attack_range:
            move_vx = direction * self.speed + crowd_push * (self.speed * 0.45)
            prev_x = self.x
            next_x = self.x + move_vx * dt
            next_x = max(60.0, min(float(world_w - 60), next_x))
            self.x = self._clamp_behind_allied_lanzatonios(next_x, allies)
            if abs(self.x - prev_x) > 0.05:
                self.walk_phase += dt * (self.speed * 0.14)
        else:
            if self.kind != "archidon" and abs(crowd_push) > 0.08:
                adjusted_x = self.x + crowd_push * (self.speed * 0.35) * dt
                adjusted_x = max(60.0, min(float(world_w - 60), adjusted_x))
                adjusted_x = self._clamp_behind_allied_lanzatonios(adjusted_x, allies)
                if abs(target.x - adjusted_x) <= self.attack_range:
                    self.x = adjusted_x
            if self.atk_timer <= 0.0:
                self.atk_timer = self.cooldown
                dmg = self.compute_damage_against(target, rng)
                if self.kind == "archidon":
                    arrows.append(
                        ArrowProjectile(
                            self.x + direction * 12.0,
                            float(self.ground_y - 31.0),
                            target.x,
                            float(self.ground_y - 24.0),
                            dmg,
                            self.team,
                            target,
                        )
                    )
                else:
                    dmg_taken = min(target.hp, dmg)
                    target.hp = max(0, target.hp - dmg)
                    target.hit_flash = 0.14
                    popup_txt = (
                        f"SALTO -{dmg_taken}!"
                        if self.last_attack_was_leap
                        else f"-{dmg_taken}"
                    )
                    popup_col = (
                        LEAP_POPUP_COLOR
                        if self.last_attack_was_leap
                        else target.team_color
                    )
                    popups.append(
                        DamagePopup(
                            target.x + rng.uniform(-6.0, 6.0),
                            float(target.ground_y - 44.0),
                            popup_txt,
                            popup_col,
                            vx=rng.uniform(-42.0, 42.0),
                            vy=-rng.uniform(85.0, 135.0),
                        )
                    )
                    died = not target.alive
                    target.spawn_splatter(particles, stains, rng, heavy=died)
                    if died and not target.death_splattered:
                        target.death_splattered = True
                        target.spawn_dismantle_pieces(pieces, rng)

    def draw(
        self,
        screen: pygame.Surface,
        cam_x: float,
        font_small: pygame.font.Font,
    ) -> None:
        if not self.alive:
            return
        leap_offset = 0.0
        if self.leap_timer > 0.0 and self.leap_duration > 0.0:
            progress = 1.0 - (self.leap_timer / self.leap_duration)
            leap_offset = math.sin(progress * math.pi) * self.leap_height
        effective_ground_y = int(round(self.ground_y - leap_offset))
        draw_fighter_visual(
            screen,
            cam_x,
            font_small,
            kind=self.kind,
            team=self.team,
            team_color=self.team_color,
            x=self.x,
            ground_y=effective_ground_y,
            hp=self.hp,
            max_hp=self.max_hp,
            walk_phase=self.walk_phase,
            atk_timer=self.atk_timer,
            cooldown=self.cooldown,
            hit_flash=self.hit_flash,
        )


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
    font_banner = pygame.font.SysFont("consolas", 28, bold=True)

    pause_edit_btn = pygame.Rect(0, 0, 120, 34)
    pause_resume_btn = pygame.Rect(0, 0, 128, 34)
    pause_exit_btn = pygame.Rect(0, 0, 104, 34)

    edit_btn = pygame.Rect(0, 0, 126, 36)
    replay_btn = pygame.Rect(0, 0, 126, 36)
    exit_btn = pygame.Rect(0, 0, 110, 36)

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
                piece for piece in pieces if piece.update(dt, bg.ground_y, bg.world_w)
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
            pop.draw(screen, cam_x, font_dmg)

        hud_rect = pygame.Rect(0, 0, w, 34)
        pygame.draw.rect(screen, (18, 20, 26), hud_rect)
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        state_txt = "PAUSA" if paused else "COMBATE"
        hud_line = (
            f"{mins:02d}:{secs:02d} | {state_txt} | "
            f"{bg.terrain_variant.upper()} | "
            f"A(Amarillo):{len(live_a)} vs B(Rojo):{len(live_b)} | "
            f"[P] Pausa [R] Terreno [ESC] Editor"
        )
        hud_surf = font_hud.render(hud_line, True, (246, 226, 146))
        screen.blit(hud_surf, (12, 9))

        if pause_menu_open:
            veil = pygame.Surface((w, h), pygame.SRCALPHA)
            veil.fill((10, 12, 18, 125))
            screen.blit(veil, (0, 0))

            panel_w, panel_h = min(420, max(280, w - 32)), 126
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            pygame.draw.rect(
                panel,
                (22, 25, 36, 205),
                pygame.Rect(0, 0, panel_w, panel_h),
                border_radius=8,
            )
            pygame.draw.rect(
                panel,
                (246, 226, 146, 210),
                pygame.Rect(0, 0, panel_w, panel_h),
                width=2,
                border_radius=8,
            )
            panel_rect = pygame.Rect(
                w // 2 - panel_w // 2, h // 2 - panel_h // 2, panel_w, panel_h
            )
            screen.blit(panel, panel_rect.topleft)

            title_surf = font_banner.render("PAUSA", True, (246, 226, 146))
            screen.blit(
                title_surf,
                (panel_rect.centerx - title_surf.get_width() // 2, panel_rect.y + 14),
            )

            btn_gap = 10
            avail_btn_w = max(180, panel_w - 32 - btn_gap * 2)
            pause_edit_btn.width = max(60, int(avail_btn_w * 0.32))
            pause_resume_btn.width = max(72, int(avail_btn_w * 0.38))
            pause_exit_btn.width = max(
                56, avail_btn_w - pause_edit_btn.width - pause_resume_btn.width
            )
            pause_edit_btn.height = 34
            pause_resume_btn.height = 34
            pause_exit_btn.height = 34

            total_pw = (
                pause_edit_btn.width
                + pause_resume_btn.width
                + pause_exit_btn.width
                + btn_gap * 2
            )
            p_start_x = panel_rect.centerx - total_pw // 2
            p_btn_y = panel_rect.y + 68

            pause_edit_btn.topleft = (p_start_x, p_btn_y)
            pause_resume_btn.topleft = (pause_edit_btn.right + btn_gap, p_btn_y)
            pause_exit_btn.topleft = (pause_resume_btn.right + btn_gap, p_btn_y)

            for r_btn, txt, base_c, hov_c in (
                (pause_edit_btn, "Editar", (58, 66, 92), (82, 94, 128)),
                (pause_resume_btn, "Continuar", (44, 122, 82), (62, 156, 108)),
                (pause_exit_btn, "Salir", (142, 48, 52), (178, 64, 68)),
            ):
                col = hov_c if r_btn.collidepoint(mouse_pos) else base_c
                pygame.draw.rect(screen, col, r_btn, border_radius=6)
                pygame.draw.rect(
                    screen, (235, 236, 242), r_btn, width=1, border_radius=6
                )
                t_s = font_small.render(txt, True, (250, 250, 252))
                screen.blit(
                    t_s,
                    (
                        r_btn.centerx - t_s.get_width() // 2,
                        r_btn.centery - t_s.get_height() // 2,
                    ),
                )

        if battle_over:
            if not live_a and not live_b:
                win_msg = "EMPATE"
                win_col = (240, 224, 150)
            elif live_a:
                win_msg = "VICTORIA EQUIPO A"
                win_col = TEAM_COLORS["A"]
            else:
                win_msg = "VICTORIA EQUIPO B"
                win_col = TEAM_COLORS["B"]

            box_w = min(440, max(280, w - 32))
            box = pygame.Rect(w // 2 - box_w // 2, h // 2 - 68, box_w, 136)
            pygame.draw.rect(screen, (22, 20, 30), box, border_radius=8)
            pygame.draw.rect(screen, win_col, box, width=2, border_radius=8)

            b_surf = font_banner.render(win_msg, True, win_col)
            screen.blit(
                b_surf, (box.centerx - b_surf.get_width() // 2, box.y + 14)
            )
            sub_surf = font_hud.render(
                f"{get_matchup_label(preset_key)} • {mins:02d}:{secs:02d}",
                True,
                (235, 232, 224),
            )
            screen.blit(
                sub_surf, (box.centerx - sub_surf.get_width() // 2, box.y + 50)
            )

            btn_gap = 10
            avail_end_w = max(180, box_w - 32 - btn_gap * 2)
            edit_btn.width = max(64, int(avail_end_w * 0.34))
            replay_btn.width = max(72, int(avail_end_w * 0.36))
            exit_btn.width = max(
                56, avail_end_w - edit_btn.width - replay_btn.width
            )
            edit_btn.height = 34
            replay_btn.height = 34
            exit_btn.height = 34

            total_w = edit_btn.width + replay_btn.width + exit_btn.width + btn_gap * 2
            start_x = box.centerx - total_w // 2
            btn_y = box.y + 84

            edit_btn.topleft = (start_x, btn_y)
            replay_btn.topleft = (edit_btn.right + btn_gap, btn_y)
            exit_btn.topleft = (replay_btn.right + btn_gap, btn_y)

            for r_btn, txt, base_c, hov_c in (
                (edit_btn, "Editar (E)", (58, 66, 92), (82, 94, 128)),
                (replay_btn, "Repetir (R)", (46, 118, 172), (68, 152, 214)),
                (exit_btn, "Salir", (142, 48, 52), (178, 64, 68)),
            ):
                col = hov_c if r_btn.collidepoint(mouse_pos) else base_c
                pygame.draw.rect(screen, col, r_btn, border_radius=6)
                pygame.draw.rect(
                    screen, (226, 224, 235), r_btn, width=1, border_radius=6
                )
                t_s = font_small.render(txt, True, (248, 248, 252))
                screen.blit(
                    t_s,
                    (
                        r_btn.centerx - t_s.get_width() // 2,
                        r_btn.centery - t_s.get_height() // 2,
                    ),
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