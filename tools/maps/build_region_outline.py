"""Build a local-area land outline for a minimap from OpenStreetMap coastline ways.

Needs `shapely` (tooling only; the site itself is buildless). OSM coastline ways run with land on
the LEFT, which is how the land side is told apart from the sea. The result is merged into
content/<cc>/map.yaml under `regions` and is credited "(c) OpenStreetMap contributors, ODbL".

Fetch the ways first (Overpass, bbox = south,west,north,east, a little larger than the view):
  curl -A "<your contact>" --data-urlencode 'data=[out:json];way["natural"="coastline"](S,W,N,E);out geom;' \
       https://overpass-api.de/api/interpreter -o coast.json

Usage:
  python build_region_outline.py coast.json content/is/map.yaml --id capital-area \
      --title "Reykjavik area" --west -22.03 --south 64.10 --east -21.80 --north 64.175 \
      --center -21.9426 64.1466 --radius-km 15
"""
import argparse
import json
from pathlib import Path

from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import linemerge, polygonize, unary_union

CREDIT = "Coastline: (c) OpenStreetMap contributors, ODbL (openstreetmap.org/copyright)."


def land_polygons(elements, view):
    lines = []
    for way in elements:
        pts = [(p["lon"], p["lat"]) for p in way.get("geometry", [])]
        if len(pts) >= 2:
            lines.append(LineString(pts))
    clipped = []
    for line in lines:
        piece = line.intersection(view)
        if piece.is_empty:
            continue
        clipped += list(piece.geoms) if hasattr(piece, "geoms") else [piece]
    clipped = [c for c in clipped if c.geom_type == "LineString" and c.length > 0]
    noded = unary_union(clipped + [view.exterior])
    faces = list(polygonize(noded))
    land = []
    eps = 1e-5
    for face in faces:
        for line in clipped:
            (x1, y1), (x2, y2) = line.coords[0], line.coords[1]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            dx, dy = x2 - x1, y2 - y1
            n = (dx * dx + dy * dy) ** 0.5 or 1.0
            left = Point(mx - dy / n * eps, my + dx / n * eps)
            if face.contains(left):
                land.append(face)
                break
    return unary_union(land).intersection(view)


def rings_of(geom, tolerance):
    polys = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    rings = []
    for poly in polys:
        if not isinstance(poly, Polygon) or poly.area < 2e-7:
            continue
        simple = poly.exterior.simplify(tolerance)
        if len(simple.coords) >= 4:
            rings.append([[round(x, 4), round(y, 4)] for x, y in list(simple.coords)[:-1]])
    return rings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("coast")
    ap.add_argument("map_file")
    ap.add_argument("--id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--west", type=float, required=True)
    ap.add_argument("--south", type=float, required=True)
    ap.add_argument("--east", type=float, required=True)
    ap.add_argument("--north", type=float, required=True)
    ap.add_argument("--center", type=float, nargs=2, required=True, metavar=("LON", "LAT"))
    ap.add_argument("--radius-km", type=float, required=True)
    ap.add_argument("--tolerance", type=float, default=0.0002)
    args = ap.parse_args()

    elements = json.loads(Path(args.coast).read_text(encoding="utf8"))["elements"]
    view = box(args.west, args.south, args.east, args.north)
    rings = rings_of(land_polygons(elements, view), args.tolerance)
    region = {"id": args.id, "title": args.title, "bbox": [args.west, args.south, args.east, args.north],
              "center": list(args.center), "radiusKm": args.radius_km, "credit": CREDIT, "land": rings}
    path = Path(args.map_file)
    data = json.loads(path.read_text(encoding="utf8"))
    data["regions"] = [r for r in data.get("regions", []) if r["id"] != args.id] + [region]
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf8")
    print(f"{args.id}: {len(rings)} land rings, {sum(len(r) for r in rings)} points")


if __name__ == "__main__":
    main()
