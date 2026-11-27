# Configuración general de la ventana y el mundo de batalla
WIDTH = 1280
HEIGHT = 720
ARENA_WORLD_WIDTH = 2400

# Poblaciones aleatorias simultáneas por equipo en Batalla Random
RANDOM_BATTLE_POPULATIONS: tuple[int, ...] = (
    12,
    20,
    30,
    40,
    50,
    60,
    70,
    80,
    90,
    100,
)

# Colores distintivos por bando en la arena y en el HUD
TEAM_COLORS: dict[str, tuple[int, int, int]] = {
    "A": (255, 214, 54),  # Equipo A (Amarillo)
    "B": (245, 64, 64),    # Equipo B (Rojo)
}

# Estadísticas base y multiplicadores de daño por tipo de unidad
# Referencia de población: sword = 1, archidon = 2, lanzatonio = 3, ninja (Shadowrath) = 4
UNIT_STATS: dict[str, dict[str, object]] = {
    "sword": {
        "label": "Sword",
        "hp": 95,
        "atk": 13,
        "range": 38.0,
        "speed": 88.0,
        "cooldown": 1.0,
        "arrow_block_chance": 0.0,
        "leap_attack_chance": 0.20,
        "leap_damage_mult": 1.40,
        "color": (218, 134, 64),
        "vs_mult": {
            "sword": 23.0 / 13,
            "archidon": 8.0 / 13.0,
            "lanzatonio": 13.0 / 13.0,
            "ninja": 11.0 / 13.0,
        },
    },
    "archidon": {
        "label": "Archidon",
        "hp": 75,
        "atk": 10,
        "range": 500.0,
        "speed": 82.0,
        "cooldown": 1.0,
        "arrow_block_chance": 0.0,
        "color": (92, 184, 118),
        "vs_mult": {
            "sword": 15.0 / 10.0,
            "archidon": 18.0 / 10,
            "lanzatonio": 12.0 / 10.0,
            "ninja": 1.0,
        },
    },
    "lanzatonio": {
        "label": "Lanzatonio",
        "hp": 450,
        "atk": 15,
        "range": 56.0,
        "speed": 96.0,
        "cooldown": 1.3,
        "arrow_block_chance": 0.25,
        "crit_chance": 0.20,
        "crit_damage_mult": 1.35,
        "color": (118, 152, 214),
        "vs_mult": {
            "sword": 1.0,
            "archidon": 17.0 / 15.0,
            "lanzatonio": 29.0 / 15,
            "ninja": 13.0 / 15.0,
        },
    },
    "ninja": {
        "label": "Shadowrath",
        "hp": 250,
        "atk": 26,
        "range": 46.0,
        "ranged_range": 240.0,
        "shuriken_damage_mult": 0.50,
        "speed": 124.0,
        "cooldown": 0.72,
        "arrow_block_chance": 0.15,
        "crit_chance": 0.20,
        "crit_damage_mult": 1.35,
        "color": (42, 46, 58),
        "vs_mult": {
            "sword": 29.0 / 26.0,
            "archidon": 1.35,
            "lanzatonio": 1.05,
            "ninja": 34.0 / 26.0,
        },
    },
}

# Presets globales de enfrentamientos: (clave, etiqueta, equipo_a, equipo_b, tope_poblacion)
GLOBAL_FIGHT_PRESETS: tuple[
    tuple[str, str, dict[str, int] | None, dict[str, int] | None, int], ...
] = (
    (
        "patrulla_inicial",
        "Patrulla Inicial",
        {"sword": 3, "archidon": 2, "lanzatonio": 1, "ninja": 0},
        {"sword": 0, "archidon": 2, "lanzatonio": 2, "ninja": 0},
        10,
    ),
    (
        "sword_vs_arco",
        "Sword vs Arco",
        {"sword": 20, "archidon": 0, "lanzatonio": 0, "ninja": 0},
        {"sword": 0, "archidon": 10, "lanzatonio": 0, "ninja": 0},
        20,
    ),
    (
        "arco_vs_lanza",
        "Arco vs Lanza",
        {"sword": 0, "archidon": 15, "lanzatonio": 0, "ninja": 0},
        {"sword": 0, "archidon": 0, "lanzatonio": 10, "ninja": 0},
        30,
    ),
    (
        "lanza_vs_sword",
        "Lanza vs Sword",
        {"sword": 0, "archidon": 0, "lanzatonio": 10, "ninja": 0},
        {"sword": 30, "archidon": 0, "lanzatonio": 0, "ninja": 0},
        30,
    ),
    (
        "spearcher",
        "Spearcher",
        {"sword": 0, "archidon": 10, "lanzatonio": 5, "ninja": 0},
        {"sword": 0, "archidon": 5, "lanzatonio": 8, "ninja": 0},
        35,
    ),
    (
        "ninja_vs_sword",
        "Shadowrath vs Sword",
        {"sword": 0, "archidon": 0, "lanzatonio": 0, "ninja": 10},
        {"sword": 40, "archidon": 0, "lanzatonio": 0, "ninja": 0},
        40,
    ),
    (
        "ninja_vs_arco",
        "Shadowrath vs Arco",
        {"sword": 0, "archidon": 0, "lanzatonio": 0, "ninja": 10},
        {"sword": 0, "archidon": 20, "lanzatonio": 0, "ninja": 0},
        40,
    ),
    (
        "ninja_vs_lanza",
        "Shadowrath vs Lanza",
        {"sword": 0, "archidon": 0, "lanzatonio": 0, "ninja": 10},
        {"sword": 1, "archidon": 0, "lanzatonio": 13, "ninja": 0},
        40,
    ),
    (
        "apocalipsis_210p",
        "Cataclismo Total",
        {"sword": 36, "archidon": 33, "lanzatonio": 36, "ninja": 0},
        {"sword": 42, "archidon": 30, "lanzatonio": 36, "ninja": 0},
        210,
    ),
)