import math
import random
from typing import TYPE_CHECKING

import pygame

from game_config import TEAM_COLORS

if TYPE_CHECKING:
    from fighter import Fighter


class SplatterParticle:
    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        radius: int,
        color: tuple[int, int, int],
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.color = color
        self.age = 0.0
        self.max_age = random.uniform(0.45, 0.85)
        self.active = True

    def update(
        self,
        dt: float,
        ground_y: int,
        stains: list["BloodPuddle"] | None = None,
    ) -> bool:
        if not self.active:
            return False
        self.age += dt
        if self.age >= self.max_age:
            self.active = False
            return False
        self.vy += 680.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y >= ground_y:
            self.y = float(ground_y)
            if stains is not None and random.random() < 0.35:
                stains.append(
                    BloodPuddle(
                        self.x,
                        ground_y + random.randint(1, 4),
                        max(4, self.radius + 2),
                        2,
                        self.color,
                    )
                )
                if len(stains) > 1600:
                    del stains[: len(stains) - 1600]
            self.vx *= 0.45
            self.vy = -abs(self.vy) * 0.25
            if abs(self.vy) < 25.0:
                self.active = False
                return False
        return True

    def draw(self, screen: pygame.Surface, cam_x: float) -> None:
        if not self.active:
            return
        sx = int(round(self.x - cam_x))
        sy = int(round(self.y))
        if sx < -20 or sx > screen.get_width() + 20:
            return
        pygame.draw.circle(screen, self.color, (sx, sy), self.radius)


class BloodPuddle:
    def __init__(
        self,
        x: float,
        y: float,
        rx: int,
        ry: int,
        color: tuple[int, int, int],
    ):
        self.x = x
        self.y = y
        self.rx = rx
        self.ry = ry
        self.color = color

    def draw(self, screen: pygame.Surface, cam_x: float) -> None:
        sx = int(round(self.x - cam_x))
        sy = int(round(self.y))
        if sx + self.rx < -20 or sx - self.rx > screen.get_width() + 20:
            return
        rect = pygame.Rect(sx - self.rx, sy - self.ry, self.rx * 2, self.ry * 2)
        pygame.draw.ellipse(screen, self.color, rect)


class LimbPiece:
    def __init__(
        self,
        kind: str,
        x: float,
        y: float,
        vx: float,
        vy: float,
        angle: float,
        ang_vel: float,
        length: float,
        thickness: int,
        color: tuple[int, int, int],
        trim_color: tuple[int, int, int] = (112, 128, 152),
    ):
        self.kind = kind
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.angle = angle
        self.ang_vel = ang_vel
        self.length = length
        self.thickness = thickness
        self.color = color
        self.trim_color = trim_color
        self.settled = False
        self.age = 0.0

    def update(
        self,
        dt: float,
        ground_y: int,
        world_w: int | None = None,
    ) -> bool:
        self.age += dt
        if self.settled:
            return True
        self.vy += 640.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.ang_vel * dt

        if world_w is not None:
            min_x = 60.0
            max_x = float(world_w - 60)
            if self.x < min_x:
                self.x = min_x
                self.vx = abs(self.vx) * 0.45
            elif self.x > max_x:
                self.x = max_x
                self.vx = -abs(self.vx) * 0.45

        if self.y >= ground_y:
            self.y = float(ground_y)
            self.vx *= 0.42
            self.ang_vel *= 0.45
            if abs(self.vy) > 85.0:
                self.vy = -abs(self.vy) * 0.28
            else:
                self.vy = 0.0
                self.vx = 0.0
                self.ang_vel = 0.0
                self.settled = True
        return True

    def draw(self, screen: pygame.Surface, cam_x: float) -> None:
        sx = int(round(self.x - cam_x))
        sy = int(round(self.y))
        if sx < -40 or sx > screen.get_width() + 40:
            return

        if self.kind == "head":
            rad = max(3, int(round(self.length)))
            pygame.draw.circle(screen, self.color, (sx, sy - rad), rad)
            return

        if self.kind == "helmet":
            rad = max(5, int(round(self.length * 0.5)))
            pygame.draw.arc(
                screen,
                self.color,
                (sx - rad, sy - rad - 2, rad * 2, rad + 3),
                0.0,
                math.pi,
                max(2, self.thickness),
            )
            pygame.draw.line(
                screen, self.trim_color, (sx - rad, sy - 1), (sx + rad, sy - 1), 2
            )
            return

        if self.kind == "hat":
            half_w = max(8, int(round(self.length * 0.55)))
            h = max(6, int(round(self.thickness * 2.2)))
            pygame.draw.line(
                screen, self.color, (sx - half_w, sy - 2), (sx + half_w, sy - 2), 2
            )
            pygame.draw.polygon(
                screen,
                self.color,
                [
                    (sx - half_w + 4, sy - 2),
                    (sx, sy - 2 - h),
                    (sx + half_w - 4, sy - 2),
                ],
            )
            pygame.draw.line(
                screen,
                self.trim_color,
                (sx - half_w + 5, sy - 3),
                (sx + half_w - 5, sy - 3),
                2,
            )
            return

        if self.kind == "armor":
            w = max(8, int(round(self.length)))
            h = max(7, int(round(self.thickness * 1.8)))
            rect = pygame.Rect(sx - w // 2, sy - h, w, h)
            pygame.draw.rect(screen, self.color, rect, border_radius=2)
            pygame.draw.rect(
                screen, self.trim_color, rect, width=1, border_radius=2
            )
            return

        if self.kind == "shield":
            w = max(10, int(round(self.length)))
            h = max(14, int(round(self.thickness * 1.6)))
            rect = pygame.Rect(sx - w // 2, sy - h, w, h)
            pygame.draw.rect(screen, (28, 32, 42), rect, border_radius=4)
            pygame.draw.rect(
                screen, self.trim_color, rect, width=2, border_radius=4
            )
            pygame.draw.rect(
                screen,
                (55, 118, 171),
                (sx - w // 2 + 2, sy - h + 2, w - 4, h // 2 - 1),
            )
            pygame.draw.rect(
                screen,
                (255, 212, 59),
                (sx - w // 2 + 2, sy - h // 2, w - 4, h // 2 - 2),
            )
            return

        if self.kind == "quiver":
            w = max(5, int(round(self.length)))
            h = max(10, int(round(self.thickness * 2.0)))
            rect = pygame.Rect(sx - w // 2, sy - h, w, h)
            pygame.draw.rect(screen, self.color, rect, border_radius=2)
            pygame.draw.line(
                screen, self.trim_color, (sx, sy - h), (sx, sy - h - 6), 2
            )
            return

        half = self.length * 0.5
        x1 = sx - math.cos(self.angle) * half
        y1 = sy - math.sin(self.angle) * half
        x2 = sx + math.cos(self.angle) * half
        y2 = sy + math.sin(self.angle) * half
        pygame.draw.line(
            screen,
            self.color,
            (int(round(x1)), int(round(y1))),
            (int(round(x2)), int(round(y2))),
            max(2, self.thickness),
        )
        if self.kind == "spear_tip":
            tip_x = int(round(x2))
            tip_y = int(round(y2))
            perp_x = -math.sin(self.angle) * 4.0
            perp_y = math.cos(self.angle) * 4.0
            head_x = int(round(x2 + math.cos(self.angle) * 7.0))
            head_y = int(round(y2 + math.sin(self.angle) * 7.0))
            pygame.draw.polygon(
                screen,
                (222, 230, 242),
                [
                    (tip_x + int(round(perp_x)), tip_y + int(round(perp_y))),
                    (head_x, head_y),
                    (tip_x - int(round(perp_x)), tip_y - int(round(perp_y))),
                ],
            )


class ArrowProjectile:
    def __init__(
        self,
        x: float,
        y: float,
        target_x: float,
        target_y: float,
        damage: int,
        team: str,
        intended_target: "Fighter | None" = None,
    ):
        self.x = x
        self.y = y
        self.damage = damage
        self.team = team
        self.intended_target = intended_target
        self.active = True

        dx = target_x - x
        dy = target_y - y
        flight_time = max(0.22, min(0.85, abs(dx) / 560.0))
        gravity = 520.0
        self.vx = dx / flight_time
        self.vy = (dy - 0.5 * gravity * flight_time * flight_time) / flight_time
        self.gravity = gravity

    def update(
        self,
        dt: float,
        enemies: list["Fighter"],
        particles: list[SplatterParticle],
        stains: list[BloodPuddle],
        pieces: list[LimbPiece],
        popups: list["DamagePopup"],
        rng: random.Random,
        ground_y: int,
    ) -> None:
        if not self.active:
            return
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y >= ground_y + 2:
            self.active = False
            return

        for enemy in enemies:
            if not enemy.alive:
                continue
            if abs(enemy.x - self.x) <= 14.0 and (enemy.ground_y - 46) <= self.y <= (
                enemy.ground_y + 4
            ):
                if enemy.try_block_arrow_from_kind("archidon", rng):
                    self.active = False
                    enemy.hit_flash = 0.08
                    popups.append(
                        DamagePopup(
                            enemy.x + rng.uniform(-5.0, 5.0),
                            float(enemy.ground_y - 46.0),
                            "BLOQUEO!",
                            (165, 210, 255),
                            vx=rng.uniform(-24.0, 24.0),
                            vy=-rng.uniform(75.0, 105.0),
                        )
                    )
                    return

                dmg_taken = min(enemy.hp, self.damage)
                enemy.hp = max(0, enemy.hp - self.damage)
                enemy.hit_flash = 0.14
                popups.append(
                    DamagePopup(
                        enemy.x + rng.uniform(-6.0, 6.0),
                        float(enemy.ground_y - 44.0),
                        f"-{dmg_taken}",
                        enemy.team_color,
                        vx=rng.uniform(-36.0, 36.0),
                        vy=-rng.uniform(80.0, 125.0),
                    )
                )
                died = not enemy.alive
                enemy.spawn_splatter(particles, stains, rng, heavy=died)
                if died and not enemy.death_splattered:
                    enemy.death_splattered = True
                    enemy.spawn_dismantle_pieces(pieces, rng)
                self.active = False
                return

    def draw(self, screen: pygame.Surface, cam_x: float) -> None:
        if not self.active:
            return
        sx = int(round(self.x - cam_x))
        sy = int(round(self.y))
        if sx < -30 or sx > screen.get_width() + 30:
            return
        ang = math.atan2(self.vy, self.vx)
        tail_x = int(round(sx - math.cos(ang) * 14.0))
        tail_y = int(round(sy - math.sin(ang) * 14.0))
        pygame.draw.line(screen, (150, 96, 46), (tail_x, tail_y), (sx, sy), 2)
        pygame.draw.circle(screen, (224, 232, 244), (sx, sy), 2)


class ShurikenProjectile:
    def __init__(
        self,
        x: float,
        y: float,
        target_x: float,
        target_y: float,
        damage: int,
        team: str,
        is_crit: bool = False,
        intended_target: "Fighter | None" = None,
    ):
        self.x = x
        self.y = y
        self.damage = damage
        self.team = team
        self.is_crit = is_crit
        self.intended_target = intended_target
        self.active = True
        self.spin = 0.0

        dx = target_x - x
        dy = target_y - y
        dist = max(1.0, math.hypot(dx, dy))
        speed = 460.0
        self.vx = (dx / dist) * speed
        self.vy = (dy / dist) * speed
        self.max_travel = min(290.0, dist + 45.0)
        self.traveled = 0.0

    def update(
        self,
        dt: float,
        enemies: list["Fighter"],
        particles: list[SplatterParticle],
        stains: list[BloodPuddle],
        pieces: list[LimbPiece],
        popups: list["DamagePopup"],
        rng: random.Random,
        ground_y: int,
    ) -> None:
        if not self.active:
            return
        step_x = self.vx * dt
        step_y = self.vy * dt
        self.x += step_x
        self.y += step_y
        self.traveled += math.hypot(step_x, step_y)
        self.spin += 26.0 * dt

        if self.traveled >= self.max_travel or self.y >= ground_y + 4:
            self.active = False
            return

        for enemy in enemies:
            if not enemy.alive:
                continue
            if abs(enemy.x - self.x) <= 15.0 and (enemy.ground_y - 46) <= self.y <= (
                enemy.ground_y + 4
            ):
                dmg_taken = min(enemy.hp, self.damage)
                enemy.hp = max(0, enemy.hp - self.damage)
                enemy.hit_flash = 0.14
                popup_col = (255, 132, 20) if self.is_crit else enemy.team_color
                popups.append(
                    DamagePopup(
                        enemy.x + rng.uniform(-6.0, 6.0),
                        float(enemy.ground_y - 44.0),
                        f"-{dmg_taken}",
                        popup_col,
                        vx=rng.uniform(-36.0, 36.0),
                        vy=-rng.uniform(80.0, 125.0),
                        is_crit=self.is_crit,
                    )
                )
                died = not enemy.alive
                enemy.spawn_splatter(particles, stains, rng, heavy=died)
                if died and not enemy.death_splattered:
                    enemy.death_splattered = True
                    enemy.spawn_dismantle_pieces(pieces, rng)
                self.active = False
                return

    def draw(self, screen: pygame.Surface, cam_x: float) -> None:
        if not self.active:
            return
        sx = int(round(self.x - cam_x))
        sy = int(round(self.y))
        if sx < -30 or sx > screen.get_width() + 30:
            return

        blade_col = (255, 165, 64) if self.is_crit else (228, 236, 248)
        outline_col = (12, 14, 20)
        arm_len = 6.0
        for idx in range(4):
            ang = self.spin + idx * (math.pi * 0.5)
            perp = ang + math.pi * 0.5
            tip_x = sx + math.cos(ang) * arm_len
            tip_y = sy + math.sin(ang) * arm_len
            side1_x = sx + math.cos(perp) * 2.0
            side1_y = sy + math.sin(perp) * 2.0
            side2_x = sx - math.cos(perp) * 2.0
            side2_y = sy - math.sin(perp) * 2.0
            pts = [
                (sx, sy),
                (int(round(side1_x)), int(round(side1_y))),
                (int(round(tip_x)), int(round(tip_y))),
                (int(round(side2_x)), int(round(side2_y))),
            ]
            pygame.draw.polygon(screen, outline_col, pts)
            pygame.draw.polygon(screen, blade_col, pts)
        pygame.draw.circle(
            screen, TEAM_COLORS.get(self.team, (255, 214, 54)), (sx, sy), 2
        )


class DamagePopup:
    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        color: tuple[int, int, int],
        vx: float = 0.0,
        vy: float = -85.0,
        is_crit: bool = False,
    ):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.vx = vx
        self.vy = vy
        self.is_crit = is_crit
        self.age = 0.0
        self.max_age = 0.72
        self.active = True

    def update(self, dt: float) -> None:
        if not self.active:
            return
        self.age += dt
        if self.age >= self.max_age:
            self.active = False
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 190.0 * dt
        self.vx *= 0.94

    def draw(
        self,
        screen: pygame.Surface,
        cam_x: float,
        font: pygame.font.Font,
    ) -> None:
        if not self.active:
            return
        sx = int(round(self.x - cam_x))
        sy = int(round(self.y))
        if sx < -60 or sx > screen.get_width() + 60:
            return
        surf = font.render(self.text, True, self.color)
        shadow = font.render(self.text, True, (14, 14, 18))
        draw_x = sx - surf.get_width() // 2
        draw_y = sy - surf.get_height() // 2
        screen.blit(shadow, (draw_x + 1, draw_y + 1))
        screen.blit(surf, (draw_x, draw_y))