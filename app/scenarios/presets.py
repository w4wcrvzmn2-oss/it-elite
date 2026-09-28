"""Preset scenario configurations."""

from __future__ import annotations

SCENARIO_PRESETS: dict[str, dict] = {
    "dense": {
        "id": "dense",
        "name": "Плотное озеленение",
        "description": "Максимизация количества допустимых посадок при заданных ограничениях.",
        "overrides": {
            "tree_spacing": 5.0,
            "shrub_spacing": 1.5,
            "tree_target_density": 12.0,
            "shrub_target_density": 35.0,
        },
    },
    "balanced": {
        "id": "balanced",
        "name": "Сбалансированное озеленение",
        "description": "Баланс плотности, расстояний и равномерности распределения.",
        "overrides": {},
    },
    "minimal": {
        "id": "minimal",
        "name": "Минимальное вмешательство",
        "description": "Меньше посадок и больше открытого пространства.",
        "overrides": {
            "tree_max_count": 80,
            "shrub_max_count": 400,
            "tree_target_density": 4.0,
            "shrub_target_density": 10.0,
        },
    },
}
