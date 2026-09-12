from dataclasses import dataclass, field


@dataclass(frozen=True)
class SemanticMetric:
    name: str
    display_name: str
    description: str
    expression: str
    base_table: str
    required_columns: list[str]
    aliases: list[str] = field(default_factory=list)
    dimensions: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class JoinRelationship:
    left: str
    right: str
    join_type: str = "INNER"

    @property
    def left_table(self) -> str:
        return self.left.split(".", 1)[0]

    @property
    def right_table(self) -> str:
        return self.right.split(".", 1)[0]


@dataclass
class SemanticLayerConfig:
    metrics: list[SemanticMetric] = field(default_factory=list)
    joins: list[JoinRelationship] = field(default_factory=list)
