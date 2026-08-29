from app.retrieval.rrf import rrf_merge


class FakeChunk:
    def __init__(self, id):
        self.id = id


def test_rrf_merge_combines_rankings():
    a = FakeChunk(1)
    b = FakeChunk(2)
    c = FakeChunk(3)

    merged = rrf_merge([[(a, 0.9), (b, 0.8)], [(b, 0.7), (c, 0.6)]], final_k=3)
    assert [m.id for m in merged] == [2, 1, 3]


def test_rrf_merge_bonus_for_multi_occurrence():
    a = FakeChunk(1)
    b = FakeChunk(2)

    merged = rrf_merge([[(b, 0.8), (a, 0.7)], [(b, 0.6), (a, 0.5)]], final_k=2)
    assert [m.id for m in merged] == [2, 1]