import math

from riail.embedding.keyword import KeywordEmbedder


def test_same_text_gives_same_vector():
    e = KeywordEmbedder()
    assert e.embed(["too many steps"]) == e.embed(["too many steps"])


def test_vectors_have_fixed_length_and_unit_size():
    vectors = KeywordEmbedder(size=64).embed(["handpass", "a much longer sentence about the sliotar"])
    assert all(len(v) == 64 for v in vectors)
    assert all(math.isclose(sum(x * x for x in v), 1.0) for v in vectors)


def test_empty_text_gives_zero_vector_without_crashing():
    assert sum(KeywordEmbedder().embed([""])[0]) == 0


def test_similar_texts_score_higher_than_unrelated_ones():
    a, b, c = KeywordEmbedder().embed(["carrying the ball steps", "too many steps carrying", "sideline puck"])
    dot = lambda x, y: sum(i * j for i, j in zip(x, y))
    assert dot(a, b) > dot(a, c)
