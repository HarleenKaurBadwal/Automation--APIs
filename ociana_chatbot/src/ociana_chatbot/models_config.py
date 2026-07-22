from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    key: str
    name: str
    aliases: list[str] = Field(default_factory=list)


class ProjectMap(BaseModel):
    default_project_key: str = "SUP"
    projects: list[ProjectConfig] = Field(default_factory=list)

    def resolve(self, text: str, fallback: str | None = None) -> ProjectConfig | None:
        lowered = text.lower()
        for project in self.projects:
            needles = [project.key.lower(), project.name.lower(), *project.aliases]
            for needle in needles:
                if needle and needle.lower() in lowered:
                    return project
        default_key = (fallback or self.default_project_key).upper()
        for project in self.projects:
            if project.key.upper() == default_key:
                return project
        if default_key:
            return ProjectConfig(key=default_key, name=default_key, aliases=[])
        return None


class Playbook(BaseModel):
    id: str
    title: str
    intents: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    auto_fixable: bool = True
    steps: list[str] = Field(default_factory=list)
    escalation_hint: str = ""


class PlaybookCatalog(BaseModel):
    playbooks: list[Playbook] = Field(default_factory=list)

    def match(self, text: str) -> Playbook | None:
        lowered = text.lower()
        best: Playbook | None = None
        best_score = 0
        for playbook in self.playbooks:
            score = 0
            for keyword in playbook.keywords:
                if keyword.lower() in lowered:
                    score += max(1, len(keyword.split()))
            for intent in playbook.intents:
                if intent.replace("_", " ") in lowered:
                    score += 2
            if score > best_score:
                best = playbook
                best_score = score
        return best if best_score > 0 else None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_project_map(path: Path) -> ProjectMap:
    return ProjectMap.model_validate(load_json(path))


def load_playbooks(path: Path) -> PlaybookCatalog:
    return PlaybookCatalog.model_validate(load_json(path))
