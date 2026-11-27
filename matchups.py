import random
from typing import Iterable

from game_config import GLOBAL_FIGHT_PRESETS, RANDOM_BATTLE_POPULATIONS

UNIT_POP_COST: dict[str, int] = {
    "sword": 1,
    "archidon": 2,
    "lanzatonio": 3,
    "ninja": 4,
}

RANDOM_MATCHUP_KEY = "batalla_random"
RANDOM_TARGET_POPULATION = 40

ACTIVE_MATCHUP = "patrulla_inicial"


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
    "ninja": "ninja",
    "ninjas": "ninja",
    "shadowrath": "ninja",
    "shadowraths": "ninja",
    "shinobi": "ninja",
}


def normalize_kind(kind: str) -> str:
    return _ALIASES.get(kind.strip().lower(), "sword")


def expand_roster(spec: object) -> list[str]:
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
    counts = {"sword": 0, "archidon": 0, "lanzatonio": 0, "ninja": 0}
    for raw_kind in roster:
        kind = normalize_kind(str(raw_kind))
        if kind in counts:
            counts[kind] += 1
    return counts


def roster_from_counts(counts: dict[str, int]) -> list[str]:
    return expand_roster(counts)


def expand_counts(counts: dict[str, int]) -> list[str]:
    return expand_roster(counts)


def calculate_population(counts: dict[str, int]) -> int:
    total = 0
    for raw_kind, raw_count in counts.items():
        kind = normalize_kind(str(raw_kind))
        cost = UNIT_POP_COST.get(kind, 1)
        total += max(0, int(raw_count)) * cost
    return total


def pick_random_population(rng: random.Random | None = None) -> int:
    rand = rng if rng is not None else random.Random()
    return int(rand.choice(RANDOM_BATTLE_POPULATIONS))


def generate_random_roster(
    target_pop: int | None = None,
    rng: random.Random | None = None,
) -> list[str]:
    rand = rng if rng is not None else random.Random()
    chosen_pop = (
        pick_random_population(rand) if target_pop is None else max(0, int(target_pop))
    )
    remaining = chosen_pop
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
    target_pop: int | None = None,
    rng: random.Random | None = None,
) -> tuple[list[str], list[str]]:
    rand = rng if rng is not None else random.Random()
    pop_a = (
        pick_random_population(rand) if target_pop is None else max(0, int(target_pop))
    )
    pop_b = (
        pick_random_population(rand) if target_pop is None else max(0, int(target_pop))
    )
    return (
        generate_random_roster(target_pop=pop_a, rng=rand),
        generate_random_roster(target_pop=pop_b, rng=rand),
    )


def get_matchup_armies(
    matchup_name: str | None = None,
    rng: random.Random | None = None,
) -> tuple[list[str], list[str]]:
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
    cfg = MATCHUPS.get(matchup_name, {})
    raw_label = cfg.get("label")
    if isinstance(raw_label, str) and raw_label.strip():
        return raw_label.strip()
    return matchup_name.replace("_", " ").title()