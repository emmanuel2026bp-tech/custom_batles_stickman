import math
import random
from typing import TYPE_CHECKING

from combat_effects import (
    ArrowProjectile,
    BloodPuddle,
    DamagePopup,
    LimbPiece,
    ShurikenProjectile,
    SplatterParticle,
)
from game_config import TEAM_COLORS, UNIT_STATS
from unit_visuals import draw_fighter_visual

if TYPE_CHECKING:
    import pygame

LEAP_POPUP_COLOR: tuple[int, int, int] = (255, 140, 24)
CRIT_POPUP_COLOR: tuple[int, int, int] = (255, 132, 20)


class Fighter:
    def __init__(
        self, kind: str, team: str, x: float, ground_y: int, idx: int
    ):
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
        self.ranged_range = float(cfg.get("ranged_range", 0.0))
        self.shuriken_damage_mult = float(cfg.get("shuriken_damage_mult", 0.50))
        self.speed = float(cfg["speed"])
        self.cooldown = float(cfg["cooldown"])
        self.arrow_block_chance = float(cfg.get("arrow_block_chance", 0.0))
        self.leap_attack_chance = float(cfg.get("leap_attack_chance", 0.20))
        self.leap_damage_mult = float(cfg.get("leap_damage_mult", 1.40))
        self.crit_chance = float(cfg.get("crit_chance", 0.0))
        self.crit_damage_mult = float(cfg.get("crit_damage_mult", 1.35))
        self.color: tuple[int, int, int] = cfg["color"]
        self.team_color: tuple[int, int, int] = TEAM_COLORS.get(
            team, (255, 214, 54)
        )
        self.vs_mult: dict[str, float] = dict(cfg.get("vs_mult", {}))
        self.atk_timer = 0.0
        self.hit_flash = 0.0
        self.walk_phase = float(idx) * 0.7
        self.death_splattered = False
        self.leap_timer = 0.0
        self.leap_duration = 0.28
        self.leap_height = 18.0
        self.pile_offset_y = 0.0
        self.last_attack_was_leap = False
        self.last_attack_was_crit = False

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def compute_damage_against(
        self,
        target: "Fighter",
        rng: random.Random | None = None,
        damage_mult: float = 1.0,
    ) -> int:
        mult = self.vs_mult.get(target.kind, 1.0)
        leap_mult = 1.0
        crit_mult = 1.0
        self.last_attack_was_leap = False
        self.last_attack_was_crit = False
        roll_rng = rng if rng is not None else random

        if self.kind == "sword" and self.leap_attack_chance > 0.0:
            if roll_rng.random() < self.leap_attack_chance:
                leap_mult = self.leap_damage_mult
                self.last_attack_was_leap = True
                self.leap_timer = self.leap_duration

        if self.kind in ("lanzatonio", "ninja") and self.crit_chance > 0.0:
            if roll_rng.random() < self.crit_chance:
                crit_mult = self.crit_damage_mult
                self.last_attack_was_crit = True

        return max(
            1,
            int(round(self.atk * mult * leap_mult * crit_mult * damage_mult)),
        )

    def try_block_arrow_from_kind(
        self, attacker_kind: str, rng: random.Random
    ) -> bool:
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
            speed = (
                rng.uniform(110.0, 320.0)
                if heavy
                else rng.uniform(75.0, 225.0)
            )
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            rad = rng.randint(2, 4) if heavy else rng.randint(2, 3)
            particles.append(
                SplatterParticle(self.x, hit_y, vx, vy, rad, dark_blood)
            )

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
                BloodPuddle(
                    sx, self.ground_y + rng.randint(1, 5), rx, ry, puddle_col
                )
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
        elif self.kind == "ninja":
            pieces.append(
                LimbPiece(
                    "hat",
                    self.x + rng.uniform(-4.0, 4.0),
                    sy - 45.0,
                    rng.uniform(-150.0, 150.0),
                    rng.uniform(-245.0, -120.0),
                    rng.uniform(-0.7, 0.7),
                    rng.uniform(-12.0, 12.0),
                    22.0,
                    3,
                    (28, 30, 38),
                    trim_color=self.team_color,
                )
            )
            pieces.append(
                LimbPiece(
                    "limb",
                    self.x + rng.uniform(-5.0, 5.0),
                    sy - 30.0,
                    rng.uniform(-155.0, 155.0),
                    rng.uniform(-225.0, -100.0),
                    rng.uniform(-1.0, 1.0),
                    rng.uniform(-13.0, 13.0),
                    27.0,
                    2,
                    wood_col,
                )
            )
            pieces.append(
                LimbPiece(
                    "limb",
                    self.x + rng.uniform(-5.0, 5.0),
                    sy - 27.0,
                    rng.uniform(-160.0, 160.0),
                    rng.uniform(-215.0, -95.0),
                    rng.uniform(-1.0, 1.0),
                    rng.uniform(-14.0, 14.0),
                    21.0,
                    2,
                    steel_col,
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
        # Separación compacta para que las unidades se apelotonen en un cúmulo denso
        min_sep = 7.0
        push = 0.0
        for other in allies + enemies:
            if other is self or not other.alive or other.kind == "archidon":
                continue
            dx = self.x - other.x
            adx = abs(dx)
            if 0.0 < adx < min_sep:
                strength = (min_sep - adx) / min_sep
                if other is target:
                    push += math.copysign(strength * 0.08, dx)
                else:
                    push += math.copysign(strength * 0.22, dx)
            elif adx == 0.0:
                push += 0.05 if (self.idx % 2 == 0) else -0.05
        return max(-0.35, min(0.35, push))

    def _update_pile_offset(
        self,
        dt: float,
        allies: list["Fighter"],
        enemies: list["Fighter"],
        dist_to_target: float,
    ) -> None:
        if self.kind == "archidon":
            self.pile_offset_y = max(0.0, self.pile_offset_y - 45.0 * dt)
            return

        in_mosh = dist_to_target <= max(self.attack_range + 16.0, 54.0)
        if not in_mosh:
            target_offset = 0.0
        else:
            neighbors = 0
            for other in allies + enemies:
                if other is self or not other.alive or other.kind == "archidon":
                    continue
                if abs(other.x - self.x) <= 18.0:
                    neighbors += 1
            # Apilamiento escalonado en montículo compacto según densidad en el choque
            tier = min(4, neighbors // 2)
            slot_wave = abs(math.sin(self.idx * 1.7 + neighbors * 0.65))
            target_offset = -min(14.0, tier * 2.6 + slot_wave * 3.2)

        blend = min(1.0, dt * 11.0)
        self.pile_offset_y += (target_offset - self.pile_offset_y) * blend

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
        buffer_px = 6.0
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
        shurikens: list[ShurikenProjectile] | None = None,
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
        self._update_pile_offset(dt, allies, enemies, dist)

        can_throw_shuriken = (
            self.kind == "ninja"
            and shurikens is not None
            and self.attack_range < dist <= self.ranged_range
        )

        if can_throw_shuriken:
            move_vx = direction * (self.speed * 0.65) + crowd_push * (
                self.speed * 0.25
            )
            prev_x = self.x
            next_x = max(60.0, min(float(world_w - 60), self.x + move_vx * dt))
            self.x = self._clamp_behind_allied_lanzatonios(next_x, allies)
            if abs(self.x - prev_x) > 0.05:
                self.walk_phase += dt * (self.speed * 0.14)

            if self.atk_timer <= 0.0:
                self.atk_timer = self.cooldown
                shuriken_dmg = self.compute_damage_against(
                    target, rng, damage_mult=self.shuriken_damage_mult
                )
                shurikens.append(
                    ShurikenProjectile(
                        self.x + direction * 11.0,
                        float(self.ground_y - 29.0),
                        target.x,
                        float(self.ground_y - 24.0),
                        shuriken_dmg,
                        self.team,
                        is_crit=self.last_attack_was_crit,
                        intended_target=target,
                    )
                )
        elif dist > self.attack_range:
            move_vx = direction * self.speed + crowd_push * (self.speed * 0.25)
            prev_x = self.x
            next_x = self.x + move_vx * dt
            next_x = max(60.0, min(float(world_w - 60), next_x))
            self.x = self._clamp_behind_allied_lanzatonios(next_x, allies)
            if abs(self.x - prev_x) > 0.05:
                self.walk_phase += dt * (self.speed * 0.14)
        else:
            if self.kind != "archidon" and abs(crowd_push) > 0.05:
                adjusted_x = self.x + crowd_push * (self.speed * 0.20) * dt
                adjusted_x = max(60.0, min(float(world_w - 60), adjusted_x))
                adjusted_x = self._clamp_behind_allied_lanzatonios(
                    adjusted_x, allies
                )
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
                    if self.last_attack_was_leap:
                        popup_txt = f"SALTO -{dmg_taken}!"
                        popup_col = LEAP_POPUP_COLOR
                        is_crit = False
                    elif self.last_attack_was_crit:
                        popup_txt = f"-{dmg_taken}"
                        popup_col = CRIT_POPUP_COLOR
                        is_crit = True
                    else:
                        popup_txt = f"-{dmg_taken}"
                        popup_col = target.team_color
                        is_crit = False
                    popups.append(
                        DamagePopup(
                            target.x + rng.uniform(-6.0, 6.0),
                            float(target.ground_y - 44.0),
                            popup_txt,
                            popup_col,
                            vx=rng.uniform(-42.0, 42.0),
                            vy=-rng.uniform(85.0, 135.0),
                            is_crit=is_crit,
                        )
                    )
                    died = not target.alive
                    target.spawn_splatter(particles, stains, rng, heavy=died)
                    if died and not target.death_splattered:
                        target.death_splattered = True
                        target.spawn_dismantle_pieces(pieces, rng)

    def draw(
        self,
        screen: "pygame.Surface",
        cam_x: float,
        font_small: "pygame.font.Font",
    ) -> None:
        if not self.alive:
            return
        leap_offset = 0.0
        if self.leap_timer > 0.0 and self.leap_duration > 0.0:
            progress = 1.0 - (self.leap_timer / self.leap_duration)
            leap_offset = math.sin(progress * math.pi) * self.leap_height
        effective_ground_y = int(
            round(self.ground_y - leap_offset + self.pile_offset_y)
        )
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