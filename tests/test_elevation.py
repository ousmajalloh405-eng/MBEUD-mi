import numpy as np
import rasterio
from rasterio.transform import from_origin

from src.geospatial.elevation import get_elevation, get_slope


def create_test_raster(path):
    """Crée un petit raster temporaire pour les tests."""
    data = np.array(
        [
            [12.5, -9999.0],
            [8.0, 15.0],
        ],
        dtype="float32",
    )

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(-17.5, 14.8, 0.01, 0.01),
        nodata=-9999.0,
    ) as raster:
        raster.write(data, 1)


def test_get_elevation_returns_valid_value(tmp_path):
    raster_path = tmp_path / "test_elevation.tif"
    create_test_raster(raster_path)

    elevation = get_elevation(-17.495, 14.795, raster_path)

    assert elevation == 12.5


def test_get_elevation_returns_none_for_nodata(tmp_path):
    raster_path = tmp_path / "test_elevation.tif"
    create_test_raster(raster_path)

    elevation = get_elevation(-17.485, 14.795, raster_path)

    assert elevation is None


def test_get_elevation_returns_none_outside_coverage(tmp_path):
    raster_path = tmp_path / "test_elevation.tif"
    create_test_raster(raster_path)

    elevation = get_elevation(-17.2, 14.7, raster_path)

    assert elevation is None
def create_slope_test_raster(path, nodata_west=False):
    """Crée un raster projeté avec une pente connue de 45 degrés."""
    from rasterio.warp import transform

    data = np.array(
        [
            [0.0, 5.0, 10.0],
            [0.0, 5.0, 10.0],
            [0.0, 5.0, 10.0],
        ],
        dtype="float32",
    )

    if nodata_west:
        data[1, 0] = -9999.0

    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=3,
        width=3,
        count=1,
        dtype="float32",
        crs="EPSG:32628",
        transform=from_origin(500000, 1600000, 5, 5),
        nodata=-9999.0,
    ) as raster:
        raster.write(data, 1)

    # Coordonnées du centre du pixel central, converties en longitude/latitude.
    x = 500000 + 1.5 * 5
    y = 1600000 - 1.5 * 5
    lon, lat = transform("EPSG:32628", "EPSG:4326", [x], [y])

    return lon[0], lat[0]


def test_get_slope_returns_expected_slope(tmp_path):
    raster_path = tmp_path / "slope.tif"
    lon, lat = create_slope_test_raster(raster_path)

    slope = get_slope(lon, lat, raster_path)

    assert slope is not None
    assert abs(slope - 45.0) < 0.01


def test_get_slope_returns_none_when_neighbor_is_nodata(tmp_path):
    raster_path = tmp_path / "slope_nodata.tif"
    lon, lat = create_slope_test_raster(
        raster_path,
        nodata_west=True,
    )

    assert get_slope(lon, lat, raster_path) is None


def test_get_slope_returns_none_outside_coverage(tmp_path):
    raster_path = tmp_path / "slope.tif"
    create_slope_test_raster(raster_path)

    assert get_slope(-17.2, 14.7, raster_path) is None
