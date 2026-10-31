"""Publication projections use returned values without statistical computation."""

from copy import deepcopy

import pytest

from market_research.publication.errors import InvalidPublicationInput
from market_research.publication.visualization import (
    materialize,
    project,
    validate_layer,
    validate_view,
)
from market_statistics import IntervalBin, IntervalCountResult, QuantileResult


def test_quantile_projection_retains_order_and_values() -> None:
    result = QuantileResult(((0.0, -1.0), (0.5, 0.0), (1.0, 3.25)), 4, "decimal_ratio")
    layer = project(result)["quantile"]
    assert layer["data"] == [{"x": 0.0, "y": -1.0}, {"x": 0.5, "y": 0.0}, {"x": 1.0, "y": 3.25}]
    assert layer["x"]["unit"] == "probability"
    assert layer["y"]["unit"] == result.unit
    validate_view(materialize(layer, "test"))


@pytest.mark.parametrize("outside", [(1, 1), (0, 0)])
def test_interval_projection_preserves_unequal_boundaries_and_values(
    outside: tuple[int, int],
) -> None:
    under, over = outside
    count = 2 + under + over
    result = IntervalCountResult(
        (0.0, 1.0, 3.0),
        (
            IntervalBin(0.0, 1.0, True, False, 1, 1 / count),
            IntervalBin(1.0, 3.0, True, True, 1, 1 / count),
        ),
        under,
        over,
        under / count,
        over / count,
        count,
        "decimal_ratio",
    )
    layers = project(result)
    for measure in ("count", "frequency"):
        layer = layers[measure]
        assert [m["x"] for m in layer["data"]] == ["< 0.0", "[0.0, 1.0)", "[1.0, 3.0]", "> 3.0"]
        assert [m["y"] for m in layer["data"]] == (
            [under, 1, 1, over]
            if measure == "count"
            else [under / count, 1 / count, 1 / count, over / count]
        )
        validate_view(materialize(layer, measure))


def test_contract_rejects_extra_fields_nonfinite_duplicates_and_wrong_axes() -> None:
    layer = project(QuantileResult(((0.0, 1.0),), 1, "unit"))["quantile"]
    bad = deepcopy(layer)
    bad["data"][0]["x"] = float("nan")
    with pytest.raises(InvalidPublicationInput):
        validate_layer(bad)
    bad = deepcopy(layer)
    bad["extra"] = True
    with pytest.raises(InvalidPublicationInput):
        validate_layer(bad)
    view = materialize(layer, "test")
    view["layers"][0]["x_axis"] = "y"
    with pytest.raises(InvalidPublicationInput):
        validate_view(view)


def test_shared_cross_language_fixtures() -> None:
    import json
    from pathlib import Path

    examples = json.loads(
        (Path(__file__).parent / "fixtures/publication_visualization_v1.json").read_text()
    )
    quantile = QuantileResult(((0.0, -1.0), (0.5, 0.0), (1.0, 3.25)), 4, "decimal_ratio")
    intervals = IntervalCountResult(
        (0.0, 1.0, 3.0),
        (
            IntervalBin(0.0, 1.0, True, False, 1, 0.25),
            IntervalBin(1.0, 3.0, True, True, 1, 0.25),
        ),
        1,
        1,
        0.25,
        0.25,
        4,
        "decimal_ratio",
    )
    expected = [
        materialize(project(quantile)["quantile"], "quantile"),
        materialize(project(intervals)["count"], "count"),
        materialize(project(intervals)["frequency"], "frequency"),
    ]
    assert examples == expected
    for view in examples:
        validate_view(view)
