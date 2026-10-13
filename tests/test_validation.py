import numpy as np
import pandas as pd

from src.processing.validation import validate_weather, validate_zones


def test_clean_data_is_valid(dataset):
    df, _ = dataset
    assert validate_zones(df).ok


def test_detects_missing_values(three_zones):
    three_zones.loc[0, "elevation_m"] = np.nan
    assert "missing_values" in validate_zones(three_zones).checks()


def test_detects_duplicates(three_zones):
    df = pd.concat([three_zones, three_zones.iloc[[0]]])
    assert "duplicates" in validate_zones(df).checks()


def test_detects_invalid_coordinates(three_zones):
    three_zones.loc[0, "lat"] = 123.0
    rep = validate_zones(three_zones)
    assert "invalid_coordinates" in rep.checks() and not rep.ok


def test_detects_out_of_range_and_units(three_zones):
    three_zones.loc[0, "drainage_quality"] = 85  # pourcentage au lieu d'un ratio 0-1
    three_zones.loc[1, "population"] = -5
    rep = validate_zones(three_zones)
    assert "out_of_range" in rep.checks()


def test_detects_outliers(dataset):
    df, _ = dataset
    df = df.copy()
    df.loc[0, "population"] = 10**9
    assert "outliers" in validate_zones(df).checks()


def test_missing_columns_reported(three_zones):
    rep = validate_zones(three_zones.drop(columns=["road_km"]))
    assert "missing_columns" in rep.checks() and not rep.ok


def test_weather_valid_series():
    df = pd.DataFrame({"time": pd.date_range("2026-10-08", periods=5, freq="h"),
                       "precipitation_mm": [0, 1.2, 5, 0.3, 0]})
    assert validate_weather(df).ok


def test_weather_detects_timestamp_and_unit_problems():
    times = ["2026-10-08T01:00", "2026-10-08T00:00", "2026-10-08T00:00", None]
    df = pd.DataFrame({"time": times, "precipitation_mm": [1, 2, -3, 900]})
    checks = validate_weather(df).checks()
    assert {"invalid_timestamps", "duplicate_timestamps", "non_monotonic_timestamps",
            "negative_rain", "suspect_units"} <= checks
