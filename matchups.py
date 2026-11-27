import random
from typing import Iterable

from game_config import GLOBAL_FIGHT_PRESETS

UNIT_POP_COST: dict[str, int] = {
    "sword": 1,
    "archidon": 2,
    "lanzatonio": 3,
}

RANDOM_MATCHUP_KEY = "caos_arena"
RANDOM_TARGET_POPULATION = 40

ACTIVE_MATCHUP = "choque_100p"


def _build_matchups_from_presets() -> dict[str, dict[str, object]]:
    built: dict[str, dict[str, object]] = {}
    for key, label, c_a, c_b, pop_cap in GLOBAL_FIGHT_PRESETS:
        built[key] = {
            "label": label,
            "pop_cap": int(pop_cap),
            "team_a": dict(c_a) if isinstance(c_a, dict) else {},
            "team_b": dict(c_b) if isinstance(c_b, dict) else {},
        }
    return built


MATCHUPS: dict[str, dict[str, object]] = _build_matchups_from_presets()

_ALIASES = {
    "sword": "sword",
    "swordwrath": "sword",
    "espada": "sword",
    "espadero": "sword",
    "espaderos": "sword",
    "archidon": "archidon",
    "archidones": "archidon",
    "archer": "archidon",
    "arquero": "archidon",
    "arqueros": "archidon",
    "lanzatonio": "lanzatonio",
    "spearman": "lanzatonio",
    "lanza": "lanzatonio",
    "lanzas": "lanzatonio",
}


def normalize_kind(kind: str) -> str:
    return _ALIASES.get(kind.strip().lower(), "sword")


def expand_roster(spec: object) -> list[str]:
    """Convierte un dict o iterable de unidades en una lista plana."""
    roster: list[str] = []
    if isinstance(spec, dict):
        for raw_kind, raw_count in spec.items():
            if str(raw_kind) == "label":
                continue
            kind = normalize_kind(str(raw_kind))
            count = max(0, int(raw_count))
            roster.extend([kind] * count)
    elif isinstance(spec, Iterable) and not isinstance(spec, (str, bytes)):
        for raw_kind in spec:
            roster.append(normalize_kind(str(raw_kind)))
    return roster


def counts_from_roster(roster: Iterable[str]) -> dict[str, int]:
    """Devuelve el conteo por unidad a partir de una lista plana."""
    counts = {"sword": 0, "archidon": 0, "lanzatonio": 0}
    for raw_kind in roster:
        kind = normalize_kind(str(raw_kind))
        if kind in counts:
            counts[kind] += 1
    return counts


def roster_from_counts(counts: dict[str, int]) -> list[str]:
    """Convierte un diccionario de cantidades en una lista plana de unidades."""
    return expand_roster(counts)


def expand_counts(counts: dict[str, int]) -> list[str]:
    """Expande un diccionario de cantidades en una lista plana de unidades."""
    return expand_roster(counts)


def calculate_population(counts: dict[str, int]) -> int:
    """Calcula la población total según el coste de cada tipo de unidad."""
    total = 0
    for raw_kind, raw_count in counts.items():
        kind = normalize_kind(str(raw_kind))
        cost = UNIT_POP_COST.get(kind, 1)
        total += max(0, int(raw_count)) * cost
    return total


def generate_random_roster(
    target_pop: int = RANDOM_TARGET_POPULATION,
    rng: random.Random | None = None,
) -> list[str]:
    """Genera una lista aleatoria cuya población no supera target_pop."""
    rand = rng if rng is not None else random.Random()
    remaining = max(0, int(target_pop))
    roster: list[str] = []
    kinds = tuple(UNIT_POP_COST.keys())

    while remaining > 0:
        affordable = [k for k in kinds if UNIT_POP_COST[k] <= remaining]
        if not affordable:
            break
        chosen = rand.choice(affordable)
        roster.append(chosen)
        remaining -= UNIT_POP_COST[chosen]

    rand.shuffle(roster)
    return roster


def generate_random_armies(
    target_pop: int = RANDOM_TARGET_POPULATION,
    rng: random.Random | None = None,
) -> tuple[list[str], list[str]]:
    """Genera dos ejércitos aleatorios independientes con target_pop."""
    rand = rng if rng is not None else random.Random()
    return (
        generate_random_roster(target_pop=target_pop, rng=rand),
        generate_random_roster(target_pop=target_pop, rng=rand),
    )


def get_matchup_armies(
    matchup_name: str | None = None,
    rng: random.Random | None = None,
) -> tuple[list[str], list[str]]:
    """Devuelve (team_a_army, team_b_army) para el preset o ACTIVE_MATCHUP."""
    key = matchup_name if matchup_name in MATCHUPS else ACTIVE_MATCHUP
    cfg = MATCHUPS.get(key) or next(iter(MATCHUPS.values()))
    pop_cap = max(1, int(cfg.get("pop_cap", RANDOM_TARGET_POPULATION)))
    spec_a = cfg.get("team_a", {})
    spec_b = cfg.get("team_b", {})
    roster_a = expand_roster(spec_a)
    roster_b = expand_roster(spec_b)
    if not roster_a and not roster_b:
        return generate_random_armies(target_pop=pop_cap, rng=rng)
    return roster_a, roster_b


def get_matchup_label(matchup_name: str) -> str:
    """Devuelve el nombre visible para el preset indicado."""
    cfg = MATCHUPS.get(matchup_name, {})
    raw_label = cfg.get("label")
    if isinstance(raw_label, str) and raw_label.strip():
        return raw_label.strip()
    return matchup_name.replace("_", " ").title()