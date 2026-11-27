import math
import random
from typing import TYPE_CHECKING
import pygame

from game_config import TEAM_COLORS

if TYPE_CHECKING:
    from simulador_main import Fighter


class DamagePopup:
    def __init__(
        self,
        x: float,
        y: float,
        text: str,
        color: tuple[int, int, int],
        vx: float = 0.0,
        vy: float = -78.0,
        is_crit: bool = False,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.text = text
        self.color = color
        self.is_crit = is_crit
        self.life = 0.72
        self.max_life = 0.72

    def update(self, dt: float) -> bool:
        self.life -= dt
        self.vy += 155.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return self.life > 0.0

    def draw(
        self,
        screen: pygame.Surface,
        cam_x: float,
        font: pygame.font.Font,
        crit_font: pygame.font.Font | None = None,
    ) -> None:
        sx = int(round(self.x - cam_x))
        sy = int(round(self.y))
        if sx < -60 or sx > screen.get_width() + 60:
            return
        active_font = crit_font if (self.is_crit and crit_font is not None) else font
        surf = active_font.render(self.text, True, self.color)
        shadow = active_font.render(self.text, True, (16, 16, 20))
        screen.blit(shadow, (sx - surf.get_width() // 2 + 1, sy + 1))
        screen.blit(surf, (sx - surf.get_width() // 2, sy))


class BloodPuddle:
    def __init__(
        self,
        x: float,
        y: int,
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
        if -50 <= sx <= screen.get_width() + 50:
            rect = pygame.Rect(
                sx - self.rx,
                self.y - self.ry // 2,
                self.rx * 2,
                max(2, self.ry),
            )
            pygame.draw.ellipse(screen, self.color, rect)


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
        self.life = 1.6

    def update(
        self,
        dt: float,
        ground_y: int,
        stains: list[BloodPuddle],
    ) -> bool:
        self.life -= dt
        if self.life <= 0.0:
            return False
        self.vy += 510.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y >= ground_y:
            rx = max(4, int(round(self.radius * 2.2 + abs(self.vx) * 0.018)))
            ry = max(2, int(round(self.radius * 0.85)))
            stains.append(BloodPuddle(self.x, ground_y + 2, rx, ry, self.color))
            if len(stains) > 1600:
                del stains[: len(stains) - 1600]
            return False
        return True

    def draw(self, screen: pygame.Surface, cam_x: float) -> None:
        sx = int(round(self.x - cam_x))
        sy = int(round(self.y))
        if -35 <= sx <= screen.get_width() + 35:
            speed = math.hypot(self.vx, self.vy)
            if speed > 12.0:
                streak_len = min(17.0, max(5.0, speed * 0.042))
                ux = self.vx / speed
                uy = self.vy / speed
                tx = int(round(sx - ux * streak_len))
                ty = int(round(sy - uy * streak_len))
                pygame.draw.line(
                    screen,
                    self.color,
                    (tx, ty),
                    (sx, sy),
                    max(2, self.radius),
                )
            pygame.draw.circle(screen, self.color, (sx, sy), max(2, self.radius))


class LimbPiece:
    def __init__(
        self,
        part_type: str,
        x: float,
        y: float,
        vx: float,
        vy: float,
        angle: float,
        ang_vel: float,
        length: float,
        width: int,
        color: tuple[int, int, int],
        life: float = 5.0,
        trim_color: tuple[int, int, int] | None = None,
    ):
        self.part_type = part_type
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.angle = angle
        self.ang_vel = ang_vel
        self.length = length
        self.width = width
        self.color = color
        self.trim_color = trim_color if trim_color is not None else color
        self.life = life
        self.max_life = life
        self.grounded = False

    def update(self, dt: float, ground_y: int, world_w: int) -> bool:
        self.life -= dt
        if self.life <= 0.0:
            return False

        if self.part_type == "head":
            margin_y = 4.0
        elif self.part_type in ("armor", "quiver", "shield"):
            margin_y = 4.0
        else:
            margin_y = 2.0

        floor_y = float(ground_y) - margin_y

        if not self.grounded:
            self.vy += 520.0 * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.angle += self.ang_vel * dt

            if self.x < 40.0:
                self.x = 40.0
                self.vx = abs(self.vx) * 0.5
            elif self.x > float(world_w - 40):
                self.x = float(world_w - 40)
                self.vx = -abs(self.vx) * 0.5

            if self.y >= floor_y:
                self.y = floor_y
                if abs(self.vy) > 95.0:
                    self.vy = -self.vy * 0.34
                    self.vx *= 0.65
                    self.ang_vel *= 0.6
                else:
                    self.vy = 0.0
                    self.vx = 0.0
                    self.ang_vel = 0.0
                    self.grounded = True
        else:
            if self.part_type in ("armor", "quiver", "shield"):
                target_ang = 0.0
            else:
                target_ang = 0.0 if math.cos(self.angle) >= 0.0 else math.pi
            diff = ((target_ang - self.angle + math.pi) % (2.0 * math.pi)) - math.pi
            self.angle += diff * min(1.0, dt * 8.0)

        return True

    def _fade_color(
        self, col: tuple[int, int, int], fade_ratio: float
    ) -> tuple[int, int, int]:
        if self.life > 1.2:
            return col
        return tuple(max(18, int(c * fade_ratio)) for c in col)

    def draw(self, screen: pygame.Surface, cam_x: float) -> None:
        sx = int(round(self.x - cam_x))
        sy = int(round(self.y))
        if sx < -80 or sx > screen.get_width() + 80:
            return

        fade_ratio = max(0.0, min(1.0, self.life / min(1.2, self.max_life)))
        col = self._fade_color(self.color, fade_ratio)
        trim = self._fade_color(self.trim_color, fade_ratio)

        if self.part_type == "head":
            pygame.draw.circle(screen, col, (sx, sy), max(3, int(self.length)))
            return

        if self.part_type == "shield":
            from unit_visuals import draw_python_shield

            draw_python_shield(
                screen,
                sx,
                sy,
                facing=1 if math.cos(self.angle) >= 0.0 else -1,
                shield_w=max(14, int(self.length)),
                shield_h=max(24, self.width * 2),
                flash=(self.life <= 1.2 and fade_ratio < 0.45),
            )
            return

        if self.part_type == "helmet":
            w_box = max(10, int(self.length))
            h_box = max(6, self.width * 2)
            pygame.draw.arc(
                screen,
                col,
                (sx - w_box // 2, sy - h_box // 2, w_box, h_box),
                0.0,
                math.pi,
                3,
            )
            pygame.draw.line(
                screen,
                trim,
                (sx - w_box // 2, sy),
                (sx + w_box // 2, sy),
                2,
            )
            return

        if self.part_type == "hat":
            w_hat = max(14, int(self.length))
            pygame.draw.line(screen, col, (sx - w_hat // 2, sy), (sx + w_hat // 2, sy), 2)
            pygame.draw.polygon(
                screen,
                col,
                [
                    (sx - w_hat // 3, sy),
                    (sx, sy - max(6, self.width * 2)),
                    (sx + w_hat // 3, sy),
                ],
            )
            pygame.draw.line(
                screen,
                trim,
                (sx - w_hat // 3, sy - 1),
                (sx + w_hat // 3, sy - 1),
                2,
            )
            return

        if self.part_type in ("armor", "quiver"):
            w_rect = max(8, int(self.length))
            h_rect = max(6, self.width * 2)
            rect = pygame.Rect(sx - w_rect // 2, sy - h_rect // 2, w_rect, h_rect)
            pygame.draw.rect(screen, col, rect, border_radius=2)
            pygame.draw.rect(screen, trim, rect, width=1, border_radius=2)
            if self.part_type == "armor":
                pygame.draw.line(
                    screen,
                    trim,
                    (rect.x + 2, rect.centery),
                    (rect.right - 2, rect.centery),
                    1,
                )
            elif self.part_type == "quiver":
                pygame.draw.line(
                    screen,
                    trim,
                    (rect.centerx - 2, rect.top),
                    (rect.centerx - 3, rect.top - 5),
                    2,
                )
                pygame.draw.line(
                    screen,
                    trim,
                    (rect.centerx + 2, rect.top),
                    (rect.centerx + 2, rect.top - 5),
                    2,
                )
            return

        half_l = self.length * 0.5
        dx = math.cos(self.angle) * half_l
        dy = math.sin(self.angle) * half_l
        p1 = (int(round(sx - dx)), int(round(sy - dy)))
        p2 = (int(round(sx + dx)), int(round(sy + dy)))
        pygame.draw.line(screen, col, p1, p2, self.width)

        if self.part_type == "spear_tip":
            perp_x = -math.sin(self.angle) * 4.0
            perp_y = math.cos(self.angle) * 4.0
            tip = (
                int(round(p2[0] + math.cos(self.angle) * 6.0)),
                int(round(p2[1] + math.sin(self.angle) * 6.0)),
            )
            b1 = (int(round(p2[0] + perp_x)), int(round(p2[1] + perp_y)))
            b2 = (int(round(p2[0] - perp_x)), int(round(p2[1] - perp_y)))
            pygame.draw.polygon(screen, col, [b1, tip, b2])


class ArrowProjectile:
    def __init__(
        self,
        x: float,
        y: float,
        target_x: float,
        target_y: float,
        damage: int,
        team: str,
        target_ref: "Fighter",
    ):
        self.x = x
        self.y = y
        self.damage = damage
        self.team = team
        self.target_ref = target_ref
        flight_time = max(0.18, min(0.75, abs(target_x - x) / 560.0))
        self.vx = (target_x - x) / flight_time
        self.vy = (target_y - y) / flight_time - 0.5 * 360.0 * flight_time
        self.life = flight_time + 0.12

    def _spawn_break_pieces(
        self,
        pieces: list[LimbPiece],
        rng: random.Random,
    ) -> None:
        wood_col = (156, 102, 48)
        tip_col = (226, 234, 245)
        base_ang = math.atan2(self.vy, self.vx)

        for _ in range(2):
            ang = base_ang + rng.uniform(-0.85, 0.85)
            spd = rng.uniform(55.0, 145.0)
            pieces.append(
                LimbPiece(
                    "limb",
                    self.x + rng.uniform(-3.0, 3.0),
                    self.y + rng.uniform(-3.0, 3.0),
                    math.cos(ang) * spd,
                    math.sin(ang) * spd - 70.0,
                    ang,
                    rng.uniform(-12.0, 12.0),
                    8.0,
                    2,
                    wood_col,
                    life=2.2,
                )
            )

        pieces.append(
            LimbPiece(
                "spear_tip",
                self.x,
                self.y,
                self.vx * 0.25 + rng.uniform(-60.0, 60.0),
                -rng.uniform(70.0, 140.0),
                base_ang + rng.uniform(-0.4, 0.4),
                rng.uniform(-10.0, 10.0),
                7.0,
                2,
                tip_col,
                life=2.2,
            )
        )
        if len(pieces) > 900:
            del pieces[: len(pieces) - 900]

    def update(
        self,
        dt: float,
        ground_y: int,
        enemies: list["Fighter"],
        particles: list[SplatterParticle],
        stains: list[BloodPuddle],
        pieces: list[LimbPiece],
        popups: list[DamagePopup],
        rng: random.Random,
    ) -> bool:
        self.life -= dt
        prev_x = self.x
        prev_y = self.y

        self.vy += 360.0 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        min_x = min(prev_x, self.x) - 10.0
        max_x = max(prev_x, self.x) + 10.0
        min_y = min(prev_y, self.y) - 6.0
        max_y = max(prev_y, self.y) + 6.0

        hit_target: "Fighter | None" = None
        for enemy in enemies:
            if not enemy.alive:
                continue
            body_top = float(enemy.ground_y) - 48.0
            body_bot = float(enemy.ground_y) + 2.0
            if min_x <= enemy.x <= max_x and not (max_y < body_top or min_y > body_bot):
                hit_target = enemy
                break

        if hit_target is not None:
            self._spawn_break_pieces(pieces, rng)
            team_col = TEAM_COLORS.get(hit_target.team, hit_target.color)
            if hit_target.try_block_arrow_from_kind("archidon", rng):
                hit_target.hit_flash = 0.08
                popups.append(
                    DamagePopup(
                        hit_target.x,
                        float(hit_target.ground_y) - 46.0,
                        "BLOQ",
                        (255, 255, 255),
                        vx=rng.uniform(-26.0, 26.0),
                        vy=-rng.uniform(75.0, 110.0),
                    )
                )
                return False

            dmg_taken = min(hit_target.hp, self.damage)
            hit_target.hp = max(0, hit_target.hp - self.damage)
            hit_target.hit_flash = 0.14
            popups.append(
                DamagePopup(
                    hit_target.x + rng.uniform(-6.0, 6.0),
                    float(hit_target.ground_y) - 44.0,
                    f"-{dmg_taken}",
                    team_col,
                    vx=rng.uniform(-42.0, 42.0),
                    vy=-rng.uniform(85.0, 135.0),
                )
            )
            died = not hit_target.alive
            hit_target.spawn_splatter(particles, stains, rng, heavy=died)
            if died and not hit_target.death_splattered:
                hit_target.death_splattered = True
                hit_target.spawn_dismantle_pieces(pieces, rng)
            return False

        if self.y >= ground_y:
            self.y = float(ground_y)
            self._spawn_break_pieces(pieces, rng)
            return False

        return self.life > 0.0

    def draw(self, screen: pygame.Surface, cam_x: float) -> None:
        sx = int(round(self.x - cam_x))
        sy = int(round(self.y))
        if sx < -40 or sx > screen.get_width() + 40:
            return
        ang = math.atan2(self.vy, self.vx)
        tail_x = int(round(sx - math.cos(ang) * 14))
        tail_y = int(round(sy - math.sin(ang) * 14))
        pygame.draw.line(screen, (238, 242, 248), (tail_x, tail_y), (sx, sy), 2)
        pygame.draw.circle(screen, (255, 255, 255), (sx, sy), 2)