from src.alerts.generate import generate_alerts
from src.risk_engine.resources import allocate
from src.risk_engine.scenarios import forecast_timeline, run_scenario, sector_ranking
from src.risk_engine.scoring import level_rank


def test_more_rain_never_reduces_critical_zones(dataset):
    df, _ = dataset
    counts = [run_scenario(df, r)[1]["n_critical"] for r in (50, 80, 100, 120, 150)]
    assert counts == sorted(counts)


def test_exposed_population_never_decreases_with_rain(dataset):
    df, _ = dataset
    pops = [run_scenario(df, r)[1]["population_exposed"] for r in (50, 100, 150)]
    assert pops == sorted(pops)


def test_no_rain_means_nothing_exposed(dataset):
    df, _ = dataset
    s = run_scenario(df, 0)[1]
    assert s["population_exposed"] == 0 and s["n_critical"] == 0


def test_summary_counts_add_up(dataset):
    df, _ = dataset
    s = run_scenario(df, 100)[1]
    assert sum(s["level_counts"].values()) == s["n_zones"] == len(df)


def test_timeline_has_expected_labels_and_grows(dataset):
    df, _ = dataset
    tl = forecast_timeline(df, 120)
    assert [t["label"] for t in tl] == ["T-24h", "T-12h", "T-6h", "T-3h", "T0", "T+3h", "T+6h"]
    rains = [t["cumulative_rain_mm"] for t in tl]
    assert rains == sorted(rains)


def test_allocation_respects_stock_and_levels(dataset):
    df, _ = dataset
    scored, _ = run_scenario(df, 150)
    res = allocate(scored, pumps=10, teams=5, vehicles=10)
    for kind, key in (("pumps", "pumps"), ("teams", "teams"), ("vehicles", "vehicles")):
        assert sum(a[key] for a in res["allocation"]) <= res["stock"][kind]
        assert res["remaining"][kind] >= 0
    assert all(level_rank(a["level"]) >= level_rank("élevé") for a in res["allocation"])
    assert "Simulation" in res["note"]


def test_allocation_starts_with_highest_scores(dataset):
    df, _ = dataset
    scored, _ = run_scenario(df, 150)
    res = allocate(scored, 10, 5, 10)["allocation"]
    scores = [a["score"] for a in res]
    assert scores == sorted(scores, reverse=True)


def test_no_resources_no_allocation(dataset):
    df, _ = dataset
    scored, _ = run_scenario(df, 150)
    assert allocate(scored, 0, 0, 0)["allocation"] == []


def test_alerts_only_at_or_above_threshold(dataset):
    df, _ = dataset
    scored, _ = run_scenario(df, 150)
    alerts = generate_alerts(scored, "très élevé", 10)
    assert 0 < len(alerts) <= 10
    assert all(level_rank(a["level"]) >= level_rank("très élevé") for a in alerts)
    assert generate_alerts(run_scenario(df, 0)[0]) == []


def test_sector_ranking_sorted(dataset):
    df, _ = dataset
    ranking = sector_ranking(run_scenario(df, 100)[0])
    assert ranking["score_moyen"].is_monotonic_decreasing
