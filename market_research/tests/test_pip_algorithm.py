"""Independent acceptance checks for the public PIP numerical contract."""

from bisect import bisect_left
from dataclasses import FrozenInstanceError
from itertools import product

import pytest

from market_research.algorithm.pip import PipResult, find_pips


def reference(values: list[float], epsilon: float) -> tuple[tuple[int, ...], float]:
    # Reconstruct each position independently by locating its surrounding points.
    retained = [0, len(values) - 1]
    while True:
        errors = []
        for i in range(1, len(values) - 1):
            pos = bisect_left(retained, i)
            if retained[pos] == i:
                continue
            left, right = retained[pos - 1], retained[pos]
            estimate = values[left] + (
                (values[right] - values[left]) * float(i - left) / float(right - left)
            )
            errors.append((abs(values[i] - estimate), i))
        if not errors:
            return tuple(retained), 0.0
        error = max(item[0] for item in errors)
        if error <= epsilon:
            return tuple(retained), error
        retained.insert(
            bisect_left(retained, min(i for e, i in errors if e == error)),
            min(i for e, i in errors if e == error),
        )


def assert_independent_result(values: list[float], epsilon: float) -> PipResult:
    result = find_pips(values, epsilon=epsilon)
    assert result.algorithm_id == "pip_vertical_error_bounded_v1"
    assert result.indices[0] == 0 and result.indices[-1] == len(values) - 1
    assert all(
        0 <= a < b < len(values) for a, b in zip(result.indices, result.indices[1:], strict=False)
    )
    errors = []
    for a, b in zip(result.indices, result.indices[1:], strict=False):
        for i in range(a + 1, b):
            reconstruction = values[a] + (values[b] - values[a]) * float(i - a) / float(b - a)
            errors.append(abs(values[i] - reconstruction))
    assert result.max_reconstruction_error == max(errors, default=0.0)
    assert result.max_reconstruction_error <= epsilon
    assert (result.indices, result.max_reconstruction_error) == reference(values, epsilon)
    return result


@pytest.mark.parametrize(
    ("values", "epsilon", "indices", "error"),
    [
        ([2.0, 3.0], 0.1, (0, 1), 0.0),
        ([5.0] * 4, 0.1, (0, 3), 0.0),
        ([0.0, 1.0, 2.0, 3.0, 4.0], 0.1, (0, 4), 0.0),
        ([0.0, 0.0, 10.0, 0.0, 0.0], 5.0, (0, 2, 4), 5.0),
        ([0.0, 2.0, 0.0, 2.0, 0.0], 1.0, (0, 1, 2, 3, 4), 0.0),
        ([0.0, 1.0, 0.0], 1.0, (0, 2), 1.0),
        ([0.0, 1.0, 0.0], 0.5, (0, 1, 2), 0.0),
        ([0.0, 2.0, 2.0, 0.0], 1.0, (0, 1, 3), 1.0),
    ],
)
def test_examples(
    values: list[float], epsilon: float, indices: tuple[int, ...], error: float
) -> None:
    result = assert_independent_result(values, epsilon)
    assert result.indices == indices
    assert result.max_reconstruction_error == error


def test_exhaustive_small_sequences_against_reference() -> None:
    for sample in product((-1.0, 0.0, 1.0), repeat=5):
        for epsilon in (0.25, 0.5, 1.0):
            assert_independent_result(list(sample), epsilon)


def test_representable_translation_and_scaling() -> None:
    values = [0.0, 2.0, 2.0, 0.0]
    original = assert_independent_result(values, 1.0)
    translated = assert_independent_result([v + 8.0 for v in values], 1.0)
    scaled = assert_independent_result([v * 4.0 for v in values], 4.0)
    assert translated.indices == scaled.indices == original.indices
    assert translated.max_reconstruction_error == original.max_reconstruction_error
    assert scaled.max_reconstruction_error == original.max_reconstruction_error * 4.0


def test_purity_determinism_and_immutability() -> None:
    values = [0.0, 2.0, 2.0, 0.0]
    before = values.copy()
    first = find_pips(values, epsilon=1.0)
    assert first == find_pips(values, epsilon=1.0)
    assert values == before
    assert isinstance(first.indices, tuple)
    with pytest.raises(FrozenInstanceError):
        first.indices = (0, 3)  # type: ignore[misc]


@pytest.mark.parametrize("values", [None, 42, "12", b"12", {0: 1, 1: 2}, iter([1, 2])])
def test_invalid_container(values: object) -> None:
    with pytest.raises(TypeError):
        find_pips(values, epsilon=1.0)  # type: ignore[arg-type]


@pytest.mark.parametrize("values", [[], [1.0]])
def test_invalid_length(values: list[float]) -> None:
    with pytest.raises(ValueError):
        find_pips(values, epsilon=1.0)


@pytest.mark.parametrize("value", [True, False, "1", None, 1j])
def test_invalid_element_type(value: object) -> None:
    with pytest.raises(TypeError):
        find_pips([0.0, value], epsilon=1.0)  # type: ignore[list-item]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), 10**400])
def test_invalid_element_value(value: float) -> None:
    with pytest.raises(ValueError):
        find_pips([0.0, value], epsilon=1.0)


@pytest.mark.parametrize("epsilon", [True, False, "1", None, 1j])
def test_invalid_epsilon_type(epsilon: object) -> None:
    with pytest.raises(TypeError):
        find_pips([0.0, 1.0], epsilon=epsilon)  # type: ignore[arg-type]


@pytest.mark.parametrize("epsilon", [0.0, -1.0, float("nan"), float("inf"), -float("inf"), 10**400])
def test_invalid_epsilon_value(epsilon: float) -> None:
    with pytest.raises(ValueError):
        find_pips([0.0, 1.0], epsilon=epsilon)


@pytest.mark.parametrize(
    "values",
    [
        [-1e308, 0.0, 1e308],  # endpoint subtraction
        [0.0, 0.0, 0.0, 1e308],  # multiplication by index offset
        [-1e308, 1e308, -1e308],  # reconstruction error subtraction
    ],
)
def test_nonfinite_intermediate_fails(values: list[float]) -> None:
    with pytest.raises(ArithmeticError):
        find_pips(values, epsilon=1.0)
