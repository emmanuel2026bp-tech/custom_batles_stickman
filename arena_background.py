import os
import random
import pygame

from terrain_builders import (
    C_BORDER,
    build_procedural_8bit_amphitheater,
    build_procedural_8bit_green_field,
    build_procedural_8bit_menu_armory,
    build_procedural_8bit_ocean,
    pixelize_image_to_surface,
)

TERRAIN_MENU_ARMORY = "armeria_menu"
TERRAIN_MENU = "campo_verde"
TERRAIN_AMPHITHEATER = "coliseo"
TERRAIN_OCEAN = "ocean"

COMBAT_TERRAIN_VARIANTS = (TERRAIN_MENU, TERRAIN_AMPHITHEATER, TERRAIN_OCEAN)
TERRAIN_VARIANTS = (TERRAIN_MENU_ARMORY, *COMBAT_TERRAIN_VARIANTS)


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
        if (
            self.terrain_variant != TERRAIN_MENU_ARMORY
            or self.terrain_surf is None
        ):
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
                pixelize_image_to_surface(
                    armory_path, self.world_w, self.height, pixel_scale=4
                )
                if armory_path
                else None
            )
            surf = (
                loaded_armory
                if loaded_armory is not None
                else build_procedural_8bit_menu_armory(
                    self.world_w, self.height, self.ground_y, pixel_size=4
                )
            )
        elif self.terrain_variant == TERRAIN_MENU:
            surf = build_procedural_8bit_green_field(
                self.world_w, self.height, self.ground_y, pixel_size=4
            )
        elif self.terrain_variant == TERRAIN_OCEAN:
            surf = build_procedural_8bit_ocean(
                self.world_w, self.height, self.ground_y, pixel_size=4
            )
        else:
            loaded_8bit = (
                pixelize_image_to_surface(
                    self.image_path, self.world_w, self.height, pixel_scale=4
                )
                if self.image_path
                else None
            )
            surf = (
                loaded_8bit
                if loaded_8bit is not None
                else build_procedural_8bit_amphitheater(
                    self.world_w, self.height, self.ground_y, pixel_size=4
                )
            )

        if self.terrain_variant not in (TERRAIN_MENU_ARMORY, TERRAIN_MENU):
            mid_x = self.world_w // 2
            for y in range(self.ground_y - 24, self.ground_y, 6):
                pygame.draw.rect(surf, C_BORDER, (mid_x - 2, y, 4, 4))

        return surf

    def draw(self, screen: pygame.Surface, cam_x: float) -> None:
        screen.blit(self.terrain_surf, (-int(round(cam_x)), 0))