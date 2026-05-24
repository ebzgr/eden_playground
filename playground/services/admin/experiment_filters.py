"""Experiment list filters for admin."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, String, cast, or_

from playground.models.experiment import Experiment


@dataclass
class ExperimentFilters:
    state: str | None = None
    assignment_scope: str | None = None
    world_id: str | None = None

    def active(self) -> bool:
        return bool(self.state or self.assignment_scope or self.world_id)

    def to_query_params(self) -> dict[str, str]:
        out: dict[str, str] = {}
        if self.state:
            out["state"] = self.state
        if self.assignment_scope:
            out["assignment_scope"] = self.assignment_scope
        if self.world_id:
            out["world_id"] = self.world_id
        return out


def apply_experiment_filters(
    stmt: Select, filters: ExperimentFilters
) -> Select:
    stmt = stmt.where(Experiment.target_scope == "scene_version")
    if filters.state:
        stmt = stmt.where(Experiment.state == filters.state)
    if filters.assignment_scope:
        stmt = stmt.where(Experiment.assignment_scope == filters.assignment_scope)
    if filters.world_id:
        # target JSON: {"world": "map_world", ...}
        world = filters.world_id
        stmt = stmt.where(
            or_(
                cast(Experiment.target, String).like(f'%"world": "{world}"%'),
                cast(Experiment.target, String).like(f'%"world":"{world}"%'),
            )
        )
    return stmt
