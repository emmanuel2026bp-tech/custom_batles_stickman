# Configuración general de la ventana y el mundo de batalla
WIDTH = 1280
HEIGHT = 720
ARENA_WORLD_WIDTH = 2400

# Colores distintivos por bando en la arena y en el HUD
TEAM_COLORS: dict[str, tuple[int, int, int]] = {
    "A": (255, 214, 54),  # Equipo A (Amarillo)
    "B": (245, 64, 64),    # Equipo B (Rojo)
}

# Estadísticas base y multiplicadores de daño por tipo de unidad
UNIT_STATS: dict[str, dict[str, object]] = {
    "sword": {
        "label": "Sword",
        "hp": 85,
        "atk": 13,
        "range": 38.0,
        "speed": 88.0,
        "cooldown": 1.0,
        "arrow_block_chance": 0.0,
        "color": (218, 134, 64),
        "vs_mult": {
            "sword": 23.0 / 13,
            "archidon": 8.0 / 13.0,
            "lanzatonio": 13.0 / 13.0,
        },
    },
    "archidon": {
        "label": "Archidon",
        "hp": 75,
        "atk": 10,
        "range": 380.0,
        "speed": 82.0,
        "cooldown": 1.0,
        "arrow_block_chance": 0.0,
        "color": (92, 184, 118),
        "vs_mult": {
            "sword": 15.0 / 10.0,
            "archidon": 25.0 / 10,
            "lanzatonio": 12.0 / 10.0,
        },
    },
    "lanzatonio": {
        "label": "Lanzatonio",
        "hp": 450,
        "atk": 15,
        "range": 56.0,
        "speed": 96.0,
        "cooldown": 1.3,
        "arrow_block_chance": 0.20,
        "color": (118, 152, 214),
        "vs_mult": {
            "sword": 1.0,
            "archidon": 17.0 / 15.0,
            "lanzatonio": 19.0 / 15,
        },
    },
}

# Presets globales de enfrentamientos: (clave, etiqueta, equipo_a, equipo_b, tope_poblacion)
GLOBAL_FIGHT_PRESETS: tuple[
    tuple[str, str, dict[str, int] | None, dict[str, int] | None, int], ...
] = (
    # Preset por defecto: 1 lanzatonio, 2 archidon, 3 espaderos (A) vs 2 lanzatonios, 1 archidon, 2 espaderos (B)
    (
        "patrulla_inicial",
        "Patrulla Inicial",
        {"sword": 3, "archidon": 2, "lanzatonio": 1},
        {"sword": 2, "archidon": 1, "lanzatonio": 2},
        10,
    ),
    (
        "duelo_gigantes",
        "Colosos y Tiradores",
        {"sword": 3, "archidon": 3, "lanzatonio": 7},
        {"sword": 3, "archidon": 3, "lanzatonio": 7},
        30,
    ),
    (
        "tormenta_flechas",
        "Lluvia de Flechas",
        {"sword": 4, "archidon": 7, "lanzatonio": 2},
        {"sword": 6, "archidon": 6, "lanzatonio": 2},
        24,
    ),
    (
        "choque_murallas",
        "Falange vs Falange",
        {"sword": 9, "archidon": 3, "lanzatonio": 7},
        {"sword": 6, "archidon": 6, "lanzatonio": 6},
        36,
    ),
    # None en ambos equipos indica generación aleatoria según el tope de población
    (
        "caos_arena",
        "Escaramuza Aleatoria",
        None,
        None,
        40,
    ),
    (
        "batalla_60p",
        "Frente Abierto",
        {"sword": 10, "archidon": 10, "lanzatonio": 10},
        {"sword": 12, "archidon": 9, "lanzatonio": 10},
        60,
    ),
    (
        "marea_75p",
        "Marea Bélica",
        {"sword": 12, "archidon": 12, "lanzatonio": 13},
        {"sword": 15, "archidon": 12, "lanzatonio": 12},
        75,
    ),
    (
        "asedio_90p",
        "Sitio Mayor",
        {"sword": 15, "archidon": 15, "lanzatonio": 15},
        {"sword": 18, "archidon": 12, "lanzatonio": 16},
        90,
    ),
    (
        "choque_100p",
        "Choque de Campaña",
        {"sword": 16, "archidon": 15, "lanzatonio": 18},
        {"sword": 20, "archidon": 16, "lanzatonio": 16},
        100,
    ),
    # Escenarios de prueba tipo piedra, papel o tijera (PPT)
    (
        "ppt_lanzas_vs_espadas",
        "PPT: Lanzas vs Espadas",
        {"sword": 0, "archidon": 0, "lanzatonio": 33},
        {"sword": 100, "archidon": 0, "lanzatonio": 0},
        100,
    ),
    (
        "ppt_espadas_vs_arcos",
        "PPT: Espadas vs Arcos",
        {"sword": 100, "archidon": 0, "lanzatonio": 0},
        {"sword": 0, "archidon": 50, "lanzatonio": 0},
        100,
    ),
    (
        "ppt_arcos_vs_lanzas",
        "PPT: Arcos vs Lanzas",
        {"sword": 0, "archidon": 50, "lanzatonio": 0},
        {"sword": 0, "archidon": 0, "lanzatonio": 33},
        100,
    ),
    # Batallas de gran escala
    (
        "legion_120p",
        "Legión de Hierro",
        {"sword": 21, "archidon": 18, "lanzatonio": 21},
        {"sword": 24, "archidon": 18, "lanzatonio": 20},
        120,
    ),
    (
        "horda_150p",
        "Horda Desatada",
        {"sword": 27, "archidon": 24, "lanzatonio": 25},
        {"sword": 30, "archidon": 21, "lanzatonio": 26},
        150,
    ),
    (
        "titan_180p",
        "Marcha de Titanes",
        {"sword": 30, "archidon": 27, "lanzatonio": 32},
        {"sword": 36, "archidon": 24, "lanzatonio": 32},
        180,
    ),
    (
        "apocalipsis_210p",
        "Cataclismo Total",
        {"sword": 36, "archidon": 33, "lanzatonio": 36},
        {"sword": 42, "archidon": 30, "lanzatonio": 36},
        210,
    ),
)