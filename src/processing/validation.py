"""Contrôles de qualité des données.

Pourquoi ? Une donnée fausse produit un score faux, sans message d'erreur.
Mieux vaut détecter les problèmes AVANT le calcul.
Chaque contrôle renvoie un 'Issue' (erreur ou avertissement).
"""
from dataclasses import asdict, dataclass, field

import pandas as pd

REQUIRED_COLUMNS = [
    "zone_id", "lon", "lat", "elevation_m", "slope_deg", "flood_history",
    "drainage_quality", "population", "hospitals", "schools", "markets", "road_km",
]

# (min, max) ; None = pas de borne
RANGES = {
    "elevation_m": (-10, 500),
    "slope_deg": (0, 90),
    "flood_history": (0, 1),
    "drainage_quality": (0, 1),
    "population": (0, None),
    "hospitals": (0, None),
    "schools": (0, None),
    "markets": (0, None),
    "road_km": (0, None),
}


@dataclass
class Issue:
    severity: str  # "error" ou "warning"
    check: str
    column: str | None
    count: int
    detail: str


@dataclass
class ValidationReport:
    n_rows: int = 0
    issues: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    def checks(self) -> set:
        return {i.check for i in self.issues}

    def to_dict(self) -> dict:
        return {"ok": self.ok, "n_rows": self.n_rows, "issues": [asdict(i) for i in self.issues]}


def validate_zones(df: pd.DataFrame, bbox: dict | None = None) -> ValidationReport:
    rep = ValidationReport(n_rows=len(df))
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        rep.issues.append(Issue("error", "missing_columns", None, len(missing_cols), ", ".join(missing_cols)))
        return rep

    # 1) valeurs manquantes
    for col in REQUIRED_COLUMNS:
        n = int(df[col].isna().sum())
        if n:
            rep.issues.append(Issue("error", "missing_values", col, n, f"{n} valeur(s) manquante(s)"))

    # 2) doublons
    n_dup = int(df["zone_id"].duplicated().sum())
    if n_dup:
        rep.issues.append(Issue("error", "duplicates", "zone_id", n_dup, "zone_id en double"))

    # 3) coordonnées invalides
    bad = ((df["lon"].abs() > 180) | (df["lat"].abs() > 90)).sum()
    if bad:
        rep.issues.append(Issue("error", "invalid_coordinates", "lon/lat", int(bad), "hors des bornes géographiques"))
    if bbox:
        out = ((df["lon"] < bbox["lon_min"]) | (df["lon"] > bbox["lon_max"]) |
               (df["lat"] < bbox["lat_min"]) | (df["lat"] > bbox["lat_max"])).sum()
        if out:
            rep.issues.append(Issue("warning", "outside_study_area", "lon/lat", int(out), "hors de la zone d'étude"))

    # 4) valeurs hors plage (unités incorrectes, erreurs de saisie)
    for col, (lo, hi) in RANGES.items():
        s = df[col].dropna()
        n = int(((s < lo) if lo is not None else (s < -1e18)).sum())
        if hi is not None:
            n += int((s > hi).sum())
        if n:
            rep.issues.append(Issue("error", "out_of_range", col, n, f"valeurs hors de [{lo}, {hi}]"))

    # 5) valeurs aberrantes (règle de l'écart interquartile)
    for col in ["population", "road_km"]:
        s = df[col].dropna()
        if len(s) >= 10:
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                n = int((s > q3 + 5 * iqr).sum())
                if n:
                    rep.issues.append(Issue("warning", "outliers", col, n, "valeurs très éloignées de la distribution"))
    return rep


def validate_weather(df: pd.DataFrame, time_col: str = "time", rain_col: str = "precipitation_mm",
                     max_hourly_mm: float = 200.0) -> ValidationReport:
    """Contrôles d'une série de pluie horaire (timestamps + unités)."""
    rep = ValidationReport(n_rows=len(df))
    for c in (time_col, rain_col):
        if c not in df.columns:
            rep.issues.append(Issue("error", "missing_columns", c, 1, f"colonne {c} absente"))
    if rep.issues:
        return rep

    ts = pd.to_datetime(df[time_col], errors="coerce")
    n_bad = int(ts.isna().sum())
    if n_bad:
        rep.issues.append(Issue("error", "invalid_timestamps", time_col, n_bad, "timestamps manquants ou illisibles"))
    n_dup = int(ts.dropna().duplicated().sum())
    if n_dup:
        rep.issues.append(Issue("error", "duplicate_timestamps", time_col, n_dup, "timestamps en double"))
    if not ts.dropna().is_monotonic_increasing:
        rep.issues.append(Issue("error", "non_monotonic_timestamps", time_col, 1, "timestamps non croissants"))

    rain = df[rain_col]
    n_na = int(rain.isna().sum())
    if n_na:
        rep.issues.append(Issue("error", "missing_values", rain_col, n_na, "pluie manquante"))
    n_neg = int((rain < 0).sum())
    if n_neg:
        rep.issues.append(Issue("error", "negative_rain", rain_col, n_neg, "pluie négative"))
    n_big = int((rain > max_hourly_mm).sum())
    if n_big:
        rep.issues.append(Issue("error", "suspect_units", rain_col, n_big,
                                f"> {max_hourly_mm} mm/h : unité probablement incorrecte"))
    return rep
