from src.ingestion.open_meteo import parse_hourly, total_next_24h
from src.processing.validation import validate_weather

# Exemple de forme de réponse Open-Meteo (valeurs fictives pour le test)
SAMPLE = {"hourly": {"time": [f"2026-10-08T{h:02d}:00" for h in range(24)],
                     "precipitation": [0.0] * 10 + [2.5, 4.0, 6.5] + [0.0] * 11}}


def test_parse_hourly_and_total():
    df = parse_hourly(SAMPLE)
    assert list(df.columns) == ["time", "precipitation_mm"]
    assert len(df) == 24
    assert total_next_24h(df) == 13.0


def test_parsed_series_passes_validation():
    assert validate_weather(parse_hourly(SAMPLE)).ok
