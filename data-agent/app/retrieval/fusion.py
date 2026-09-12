from dataclasses import dataclass


@dataclass(frozen=True)
class FusedResult:
    item_id: str
    score: float
    sources: tuple[str, ...]


def reciprocal_rank_fusion(
    rankings: dict[str, list[str]], k: int = 60, limit: int = 8
) -> list[FusedResult]:
    scores: dict[str, float] = {}
    sources: dict[str, set[str]] = {}
    for source, item_ids in rankings.items():
        seen: set[str] = set()
        for rank, item_id in enumerate(item_ids, start=1):
            if item_id in seen:
                continue
            seen.add(item_id)
            scores[item_id] = scores.get(item_id, 0.0) + 1 / (k + rank)
            sources.setdefault(item_id, set()).add(source)

    ranked = sorted(scores, key=lambda item_id: (-scores[item_id], item_id))[:limit]
    return [
        FusedResult(
            item_id=item_id,
            score=scores[item_id],
            sources=tuple(sorted(sources[item_id])),
        )
        for item_id in ranked
    ]
