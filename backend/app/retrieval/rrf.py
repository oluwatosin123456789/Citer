from typing import TypeVar

T = TypeVar("T")


def rrf_merge(
    rankings: list[list[tuple[T, float]]],
    k: int = 60,
    final_k: int = 20,
) -> list[T]:
    """Reciprocal Rank Fusion: items appearing in multiple rankings rank higher.

    Works with any item type that has a hashable ``id`` attribute.
    """
    scores: dict[object, float] = {}
    chunks: dict[object, T] = {}

    for ranking in rankings:
        for rank, (chunk, _) in enumerate(ranking):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank + 1)
            chunks[chunk.id] = chunk

    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return [chunks[cid] for cid, _ in ordered[:final_k]]