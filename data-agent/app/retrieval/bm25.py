from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re

import jieba


def tokenize(text: str) -> list[str]:
    normalized = text.lower().strip()
    words = [word.strip() for word in jieba.lcut(normalized) if word.strip()]
    latin = re.findall(r"[a-z0-9_]+", normalized)
    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", normalized))
    bigrams = [chinese[index:index + 2] for index in range(len(chinese) - 1)]
    return list(dict.fromkeys([*words, *latin, *bigrams]))


@dataclass(frozen=True)
class SearchResult:
    item_id: str
    score: float


class BM25Index:
    def __init__(self, documents: dict[str, str], k1: float = 1.5, b: float = 0.75):
        self.documents = documents
        self.k1 = k1
        self.b = b
        self._tokens = {item_id: tokenize(text) for item_id, text in documents.items()}
        self._frequencies = {
            item_id: Counter(tokens) for item_id, tokens in self._tokens.items()
        }
        self._lengths = {item_id: len(tokens) for item_id, tokens in self._tokens.items()}
        self._avg_length = sum(self._lengths.values()) / max(len(self._lengths), 1)
        document_frequency = Counter()
        for tokens in self._tokens.values():
            document_frequency.update(set(tokens))
        count = max(len(documents), 1)
        self._idf = {
            term: math.log(1 + (count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def search(self, query: str, limit: int = 8) -> list[SearchResult]:
        query_tokens = tokenize(query)
        scores: list[SearchResult] = []
        for item_id, frequencies in self._frequencies.items():
            length = self._lengths[item_id]
            score = 0.0
            for token in query_tokens:
                frequency = frequencies.get(token, 0)
                if not frequency:
                    continue
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * length / max(self._avg_length, 1)
                )
                score += self._idf.get(token, 0.0) * frequency * (self.k1 + 1) / denominator
            if score > 0:
                scores.append(SearchResult(item_id=item_id, score=score))
        return sorted(scores, key=lambda item: item.score, reverse=True)[:limit]
