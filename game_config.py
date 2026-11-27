WIDTH = 1280
HEIGHT = 720
ARENA_WORLD_WIDTH = 2400

TEAM_COLORS: dict[str, tuple[int, int, int]] = {
    "A": (255, 214, 54),   # Amarillo (izquierda)
    "B": (245, 64, 64),    # Rojo (derecha)
}

UNIT_STATS: dict[str, dict[str, object]] = {
    "sword": {
        "label": "Sword",
        "hp": 95,
        "atk": 13,
        "range": 38.0,
        "speed": 96.0,
        "cooldown": 1.0,
        "arrow_block_chance": 0.0,
        "color": (218, 134, 64),
        "vs_mult": {
            "sword": 23.0 / 13,
            "archidon": 11.0 / 13.0,
            "lanzatonio": 15.0 / 13.0,
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
            "sword": 1.4,
            "archidon": 25.0 / 10,
            "lanzatonio": 1.0,
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

# Coste de población: Sword = 1, Archidon = 2, Lanzatonio = 3
GLOBAL_FIGHT_PRESETS: tuple[
    tuple[str, str, dict[str, int] | None, dict[str, int] | None, int], ...
] = (
    (
        "duelo_gigantes",
        "Colosos y Tiradores",
        {"sword": 3, "archidon": 3, "lanzatonio": 7},   # 3+6+21 = 30
        {"sword": 3, "archidon": 3, "lanzatonio": 7},   # 3+6+21 = 30
        30,
    ),
    (
        "tormenta_flechas",
        "Lluvia de Flechas",
        {"sword": 4, "archidon": 7, "lanzatonio": 2},   # 4+14+6 = 24
        {"sword": 6, "archidon": 6, "lanzatonio": 2},   # 6+12+6 = 24
        24,
    ),
    (
        "choque_murallas",
        "Falange vs Falange",
        {"sword": 9, "archidon": 3, "lanzatonio": 7},   # 9+6+21 = 36
        {"sword": 6, "archidon": 6, "lanzatonio": 6},   # 6+12+18 = 36
        36,
    ),
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
        {"sword": 10, "archidon": 10, "lanzatonio": 10}, # 10+20+30 = 60
        {"sword": 12, "archidon": 9, "lanzatonio": 10},  # 12+18+30 = 60
        60,
    ),
    (
        "marea_75p",
        "Marea Bélica",
        {"sword": 12, "archidon": 12, "lanzatonio": 13}, # 12+24+39 = 75
        {"sword": 15, "archidon": 12, "lanzatonio": 12}, # 15+24+36 = 75
        75,
    ),
    (
        "asedio_90p",
        "Sitio Mayor",
        {"sword": 15, "archidon": 15, "lanzatonio": 15}, # 15+30+45 = 90
        {"sword": 18, "archidon": 12, "lanzatonio": 16}, # 18+24+48 = 90
        90,
    ),
    (
        "choque_100p",
        "Choque de Campaña",
        {"sword": 16, "archidon": 15, "lanzatonio": 18}, # 16+30+54 = 100
        {"sword": 20, "archidon": 16, "lanzatonio": 16}, # 20+32+48 = 100
        100,
    ),
    (
        "ppt_lanzas_vs_espadas",
        "PPT: Lanzas vs Espadas",
        {"sword": 0, "archidon": 0, "lanzatonio": 33},  # 99 pob
        {"sword": 100, "archidon": 0, "lanzatonio": 0}, # 100 pob
        100,
    ),
    (
        "ppt_espadas_vs_arcos",
        "PPT: Espadas vs Arcos",
        {"sword": 100, "archidon": 0, "lanzatonio": 0}, # 100 pob
        {"sword": 0, "archidon": 50, "lanzatonio": 0},  # 100 pob
        100,
    ),
    (
        "ppt_arcos_vs_lanzas",
        "PPT: Arcos vs Lanzas",
        {"sword": 0, "archidon": 50, "lanzatonio": 0},  # 100 pob
        {"sword": 0, "archidon": 0, "lanzatonio": 33},  # 99 pob
        100,
    ),
    (
        "legion_120p",
        "Legión de Hierro",
        {"sword": 21, "archidon": 18, "lanzatonio": 21}, # 21+36+63 = 120
        {"sword": 24, "archidon": 18, "lanzatonio": 20}, # 24+36+60 = 120
        120,
    ),
    (
        "horda_150p",
        "Horda Desatada",
        {"sword": 27, "archidon": 24, "lanzatonio": 25}, # 27+48+75 = 150
        {"sword": 30, "archidon": 21, "lanzatonio": 26}, # 30+42+78 = 150
        150,
    ),
    (
        "titan_180p",
        "Marcha de Titanes",
        {"sword": 30, "archidon": 27, "lanzatonio": 32}, # 30+54+96 = 180
        {"sword": 36, "archidon": 24, "lanzatonio": 32}, # 36+48+96 = 180
        180,
    ),
    (
        "apocalipsis_210p",
        "Cataclismo Total",
        {"sword": 36, "archidon": 33, "lanzatonio": 36}, # 36+66+108 = 210
        {"sword": 42, "archidon": 30, "lanzatonio": 36}, # 42+60+108 = 210
        210,
    ),
)