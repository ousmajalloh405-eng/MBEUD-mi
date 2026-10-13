import copy

import pytest

from src.config import risk_config
from src.risk_engine.scoring import classify, compute_risk, hazard_index, normalize_weights


def test_zero_rain_gives_zero_score(three_zones):
    out = compute_risk(three_zones, 0)
    assert (out["score"] == 0).all()
    assert (out["level"] == "faible").all()


def test_score_increases_with_rain(three_zones):
    s50 = compute_risk(three_zones, 50)["score"].sum()
    s100 = compute_risk(three_zones, 100)["score"].sum()
    s150 = compute_risk(three_zones, 150)["score"].sum()
    assert s50 < s100 < s150


def test_worse_zone_scores_higher(three_zones):
    out = compute_risk(three_zones, 100).set_index("zone_id")
    assert out.loc["A", "score"] < out.loc["B", "score"] < out.loc["C", "score"]


def test_score_always_between_0_and_100(dataset):
    df, _ = dataset
    for rain in (0, 30, 100, 250, 500):
        out = compute_risk(df, rain)
        assert out["score"].between(0, 100).all()


def test_blocks_are_between_0_and_1(dataset):
    df, _ = dataset
    out = compute_risk(df, 100)
    for col in ("hazard", "vulnerability", "exposure"):
        assert out[col].between(0, 1).all()


def test_hazard_index_values():
    assert hazard_index(0) == 0
    assert hazard_index(75) == pytest.approx(0.5)
    assert hazard_index(1000) == 1  # plafonné
    with pytest.raises(ValueError):
        hazard_index(-1)


def test_weights_are_relative():
    assert normalize_weights({"a": 2, "b": 2}) == {"a": 0.5, "b": 0.5}
    with pytest.raises(ValueError):
        normalize_weights({"a": 0, "b": 0})


def test_doubling_all_weights_changes_nothing(three_zones):
    cfg = copy.deepcopy(risk_config())
    base = compute_risk(three_zones, 100, cfg)["score"].tolist()
    for key in ("block_weights", "vulnerability_weights", "exposure_weights"):
        cfg[key] = {k: v * 2 for k, v in cfg[key].items()}
    assert compute_risk(three_zones, 100, cfg)["score"].tolist() == base


def test_changing_weights_changes_ranking_inputs(three_zones):
    cfg = copy.deepcopy(risk_config())
    cfg["block_weights"] = {"hazard": 0.0, "vulnerability": 1.0, "exposure": 0.0}
    out = compute_risk(three_zones, 100, cfg).set_index("zone_id")
    assert out.loc["C", "score"] == pytest.approx(100 * out.loc["C", "vulnerability"], abs=0.1)


def test_multiplicative_method_zero_hazard_zero_risk(three_zones):
    cfg = copy.deepcopy(risk_config())
    cfg["method"] = "multiplicative"
    assert (compute_risk(three_zones, 0, cfg)["score"] == 0).all()
    assert compute_risk(three_zones, 150, cfg)["score"].max() > 0


def test_unknown_method_raises(three_zones):
    cfg = copy.deepcopy(risk_config())
    cfg["method"] = "magic"
    with pytest.raises(ValueError):
        compute_risk(three_zones, 100, cfg)


@pytest.mark.parametrize("score,expected", [
    (0, "faible"), (20, "faible"), (20.1, "modéré"), (40, "modéré"), (41, "élevé"),
    (60, "élevé"), (61, "très élevé"), (80, "très élevé"), (81, "critique"), (100, "critique"),
])
def test_classification_thresholds(score, expected):
    assert classify(score) == expected
