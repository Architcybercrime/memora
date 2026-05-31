"""Pure-function tests for pgvector literal encoding."""

from app.memory.long_term import _to_pgvector


def test_empty_vector():
    assert _to_pgvector([]) == "[]"


def test_single_value():
    assert _to_pgvector([0.5]) == "[0.5000000]"


def test_round_trip_shape():
    out = _to_pgvector([0.1, -0.2, 1e-7])
    assert out.startswith("[") and out.endswith("]")
    assert out.count(",") == 2


def test_no_scientific_notation():
    # Postgres pgvector parser rejects scientific notation for small floats.
    out = _to_pgvector([1e-7, 1e-8])
    assert "e" not in out and "E" not in out
