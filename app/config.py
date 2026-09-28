"""Configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class RegulationRef(BaseModel):
    document: str
    clause: str = "TODO_VERIFY"
    description: str = ""


class RestrictionRule(BaseModel):
    minimum_distance: float
    regulation: RegulationRef


class PlantingTypeConfig(BaseModel):
    enabled: bool = True
    min_spacing: float = 6.0
    candidate_grid_step: float = 3.0
    symbol_radius: float = 1.5
    max_count: int | None = None
    target_density: float | None = None  # plants per 1000 m² of allowed area


class PlantingRulesConfig(BaseModel):
    communication: RestrictionRule | None = None
    building: RestrictionRule | None = None
    road: RestrictionRule | None = None


class CommunicationRuleConfig(BaseModel):
    default_buffer: float = 2.0
    regulation: RegulationRef = Field(
        default_factory=lambda: RegulationRef(document="743-ПП", clause="TODO_VERIFY")
    )


class OutputConfig(BaseModel):
    planting_layer: str = "PLANTING_PROPOSED"
    tree_layer: str = "PLANTING_TREES"
    shrub_layer: str = "PLANTING_SHRUBS"
    debug_layer: str = "PLANTING_DEBUG"


class ProjectConfig(BaseModel):
    name: str = "green-planner"
    random_seed: int = 42


class LayerMapping(BaseModel):
    communications: list[str] = Field(default_factory=list)
    buildings: list[str] = Field(default_factory=list)
    roads: list[str] = Field(default_factory=list)
    boundary: list[str] = Field(default_factory=list)


class AppConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    layers: LayerMapping = Field(default_factory=LayerMapping)
    planting: dict[str, PlantingTypeConfig] = Field(default_factory=dict)
    rules: dict[str, Any] = Field(default_factory=dict)
    output: OutputConfig = Field(default_factory=OutputConfig)

    def get_planting_config(self, planting_type: str) -> PlantingTypeConfig:
        raw = self.planting.get(planting_type)
        if raw is None:
            return PlantingTypeConfig()
        if isinstance(raw, PlantingTypeConfig):
            return raw
        return PlantingTypeConfig.model_validate(raw)

    def get_type_rules(self, planting_type: str) -> PlantingRulesConfig:
        raw = self.rules.get(planting_type, {})
        if not isinstance(raw, dict):
            return PlantingRulesConfig()
        parsed: dict[str, Any] = {}
        for key in ("communication", "building", "road"):
            if key in raw and isinstance(raw[key], dict):
                parsed[key] = RestrictionRule.model_validate(raw[key])
        return PlantingRulesConfig.model_validate(parsed)

    def get_communication_buffer(self) -> float:
        comm = self.rules.get("communication", {})
        if isinstance(comm, dict):
            return float(comm.get("default_buffer", 2.0))
        return 2.0

    def get_communication_regulation(self) -> RegulationRef:
        comm = self.rules.get("communication", {})
        if isinstance(comm, dict) and "regulation" in comm:
            return RegulationRef.model_validate(comm["regulation"])
        return RegulationRef(document="743-ПП", clause="TODO_VERIFY")

    def match_layer_category(self, layer_name: str) -> str | None:
        upper = layer_name.upper()
        for category, names in self.layers.model_dump().items():
            for name in names:
                if upper == name.upper() or name.upper() in upper:
                    return category
        return None


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: Path | None = None, rules_path: Path | None = None) -> AppConfig:
    """Load configuration from YAML files."""
    base_dir = Path(__file__).resolve().parent.parent
    default_path = config_path or base_dir / "config" / "default.yaml"
    rules_file = rules_path or base_dir / "config" / "rules.yaml"

    if not default_path.exists():
        raise FileNotFoundError(f"Config file not found: {default_path}")

    with open(default_path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    if rules_file.exists():
        with open(rules_file, encoding="utf-8") as f:
            rules_data = yaml.safe_load(f) or {}
        if "layers" in rules_data:
            data = _deep_merge(data, {"layers": rules_data["layers"]})

    planting_raw = data.get("planting", {})
    planting: dict[str, PlantingTypeConfig] = {}
    for ptype, pcfg in planting_raw.items():
        planting[ptype] = PlantingTypeConfig.model_validate(pcfg)

    return AppConfig(
        project=ProjectConfig.model_validate(data.get("project", {})),
        layers=LayerMapping.model_validate(data.get("layers", {})),
        planting=planting,
        rules=data.get("rules", {}),
        output=OutputConfig.model_validate(data.get("output", {})),
    )
