"""Build an inland-area minimap (land rectangle, lakes, main roads) from an OpenStreetMap Overpass extract.

For an area that is mostly inland (the Golden Circle) there is no coastline to draw, so the map is the land
rectangle plus the named lakes and the trunk/primary/secondary roads. Needs `shapely` (tooling only). The result is
merged into content/<cc>/map.yaml under `regions` and credited "(c) OpenStreetMap contributors, ODbL".

Fetch the data first (Overpass; bbox = south,west,north,east, a little larger than the view):
  curl -A "<your contact>" --data-urlencode 'data=[out:json][timeout:120];(
     way["natural"="water"]["name"](S,W,N,E);relation["natural"="water"]["name"](S,W,N,E);
     way["highway"~"^(trunk|primary|secondary)$"](S,W,N,E););out geom;' \
     https://overpass-api.de/api/interpreter -o extract.json

Usage:
  python build_region_inland.py extract.json content/is/map.yaml --id golden-circle --title "Golden Circle" \
      --west -21.45 --south 63.98 --east -19.95 --north 64.40 --center -20.7 64.2 --for-region "Golden Circle"
"""
import argparse
import json
from pathlib import Path

from shapely.geometry import LineString, MultiPolygon, Polygon, box
from shapely.ops import linemerge, polygonize, unary_union

CREDIT = "Lakes and roads: (c) OpenStreetMap contributors, ODbL (openstreetmap.org/copyright)."


def way_points(way):
    return [(p["lon"], p["lat"]) for p in way.get("geometry", [])]


def lake_polygons(elements, view, min_area):
    polys = []
    for el in elements:
        tags = el.get("tags", {})
        if tags.get("natural") != "water":
            continue
        if el["type"] == "way":
            pts = way_points(el)
            if len(pts) >= 4 and pts[0] == pts[-1]:
                polys.append(Polygon(pts))
        elif el["type"] == "relation":
            outers = [LineString([(p["lon"], p["lat"]) for p in m["geometry"]]) for m in el.get("members", [])
                      if m.get("role") == "outer" and m.get("geometry")]
            if outers:
                united = unary_union(outers)
                merged = united if united.geom_type == "LineString" else linemerge(united)
                polys += list(polygonize([merged] if merged.geom_type == "LineString" else merged))
    kept = []
    for poly in polys:
        poly = poly.buffer(0).intersection(view)
        for part in (poly.geoms if isinstance(poly, MultiPolygon) else [poly]):
            if isinstance(part, Polygon) and part.area >= min_area:
                kept.append(part)
    return kept


def road_lines(elements, view):
    lines = []
    for el in elements:
        if el["type"] == "way" and el.get("tags", {}).get("highway"):
            pts = way_points(el)
            if len(pts) >= 2:
                clipped = LineString(pts).intersection(view)
                lines += list(clipped.geoms) if hasattr(clipped, "geoms") else [clipped]
    lines = [l for l in lines if isinstance(l, LineString) and l.length > 0]
    merged = linemerge(unary_union(lines)) if lines else None
    return list(merged.geoms) if merged is not None and hasattr(merged, "geoms") else ([merged] if merged is not None else [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("extract")
    ap.add_argument("map_file")
    ap.add_argument("--id", required=True)
    ap.add_argument("--title", required=True)
    for name in ("west", "south", "east", "north"):
        ap.add_argument(f"--{name}", type=float, required=True)
    ap.add_argument("--center", type=float, nargs=2, required=True, metavar=("LON", "LAT"))
    ap.add_argument("--for-region", action="append", required=True, help="sight region names that use this map")
    ap.add_argument("--min-lake-area", type=float, default=2e-4, help="square degrees")
    args = ap.parse_args()

    elements = json.loads(Path(args.extract).read_text(encoding="utf8"))["elements"]
    view = box(args.west, args.south, args.east, args.north)
    water = lake_polygons(elements, view, args.min_lake_area)
    roads = road_lines(elements, view)

    def ring(poly):
        simple = poly.exterior.simplify(0.0004)
        return [[round(x, 4), round(y, 4)] for x, y in list(simple.coords)[:-1]]

    def line(l):
        simple = l.simplify(0.0006)
        return [[round(x, 4), round(y, 4)] for x, y in simple.coords]

    region = {"id": args.id, "title": args.title, "bbox": [args.west, args.south, args.east, args.north],
              "center": list(args.center), "forRegions": args.for_region, "credit": CREDIT,
              "land": [[[args.west, args.north], [args.east, args.north], [args.east, args.south], [args.west, args.south]]],
              "water": [ring(p) for p in water if len(p.exterior.coords) >= 4],
              "roads": [line(l) for l in roads]}
    path = Path(args.map_file)
    data = json.loads(path.read_text(encoding="utf8"))
    data["regions"] = [r for r in data.get("regions", []) if r["id"] != args.id] + [region]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf8")
    print(f"{args.id}: {len(region['water'])} lakes, {len(region['roads'])} road lines, "
          f"{sum(len(r) for r in region['water']) + sum(len(r) for r in region['roads'])} points")


if __name__ == "__main__":
    main()
