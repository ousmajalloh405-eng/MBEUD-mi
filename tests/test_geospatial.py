from shapely.geometry import Point, shape

from src.config import settings
from src.geospatial.grid import LAND, build_grid, cell_area_km2, nearest_locality


def test_land_polygon_is_valid():
    assert LAND.is_valid


def test_grid_cells_inside_bbox_with_unique_ids():
    bbox = settings()["grid"]["bbox"]
    zones = build_grid(bbox, 1000)
    assert len(zones) > 100
    assert len({z["zone_id"] for z in zones}) == len(zones)
    for z in zones:
        assert bbox["lon_min"] - 0.01 <= z["lon"] <= bbox["lon_max"] + 0.01
        assert LAND.contains(Point(z["lon"], z["lat"]))


def test_smaller_cells_give_more_zones():
    bbox = settings()["grid"]["bbox"]
    assert len(build_grid(bbox, 500)) > len(build_grid(bbox, 1000))


def test_cell_area_is_close_to_nominal():
    bbox = settings()["grid"]["bbox"]
    z = build_grid(bbox, 1000)[0]
    # aire approximative en km2 : degrés -> km
    import math
    minx, miny, maxx, maxy = shape(z["geometry"]).bounds
    area = (maxx - minx) * 111.32 * math.cos(math.radians(z["lat"])) * (maxy - miny) * 111.32
    assert abs(area - cell_area_km2(1000)) < 0.05


def test_nearest_locality_is_known_place():
    assert nearest_locality(-17.39, 14.755) == "Pikine"
