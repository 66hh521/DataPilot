from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    question: str
    expected_tables: list[str] = field(default_factory=list)
    expected_columns: list[str] = field(default_factory=list)
    expected_non_empty: bool | None = None


def load_dataset(path: Path) -> list[EvaluationCase]:
    content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [EvaluationCase(**item) for item in content.get("cases", [])]
