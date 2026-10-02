"""Rasterize a rough South Sea (Yeosu~Busan) coastline into a 48x24 Unciv flat-top hex grid.

Writes campaign/maps/ch1-south-sea.txt (one char per tile, line 0 = north; odd columns sit half a
row further north, as in Unciv's rectangular maps) and a preview PNG next to it, and prints where
the named places landed. Run from the repo root:  python campaign/tools/mapgen/south_sea.py

Legend: ~ Ocean, . Coast, g Grassland, p Plains, f Grassland+Forest, h Grassland+Hill, m Mountain"""
import pathlib
OUT = pathlib.Path(__file__).resolve().parents[2] / "maps" / "ch1-south-sea.txt"
W, H = 48, 24
LON0, LON1 = 127.40, 129.10
LAT0, LAT1 = 34.60, 35.30
DX = (LON1 - LON0) / W
DY = (LAT1 - LAT0) / H

mainland = [
    (127.40, 34.90), (127.52, 34.88), (127.58, 34.82), (127.60, 34.72), (127.63, 34.68),
    (127.72, 34.70), (127.76, 34.76), (127.72, 34.86), (127.70, 34.93), (127.80, 34.95),
    (127.85, 35.00), (127.88, 34.94), (127.95, 34.95), (128.02, 34.93), (128.04, 35.05),
    (128.06, 35.08), (128.10, 35.02), (128.12, 34.93), (128.20, 34.92), (128.28, 34.93),
    (128.30, 34.85), (128.35, 34.79), (128.42, 34.82), (128.44, 34.88), (128.40, 34.95),
    (128.42, 35.00), (128.38, 35.04), (128.45, 35.06), (128.50, 35.09), (128.54, 35.13),
    (128.55, 35.22), (128.60, 35.15), (128.65, 35.09), (128.72, 35.09), (128.80, 35.11),
    (128.88, 35.09), (128.93, 35.05), (128.97, 35.07), (129.00, 35.05), (129.05, 35.09),
    (129.10, 35.10), (129.10, 35.45), (127.40, 35.45),
]
islands = {
    "namhae": [(127.84, 34.92), (127.95, 34.90), (128.05, 34.85), (128.06, 34.75), (127.98, 34.70),
               (127.88, 34.72), (127.83, 34.80)],
    "geoje": [(128.48, 35.02), (128.60, 35.03), (128.70, 34.98), (128.74, 34.88), (128.70, 34.78),
              (128.62, 34.72), (128.55, 34.75), (128.50, 34.82), (128.47, 34.92)],
    "hansan": [(128.47, 34.79), (128.53, 34.80), (128.53, 34.75), (128.47, 34.75)],
    "gadeok": [(128.79, 35.06), (128.86, 35.06), (128.87, 34.99), (128.80, 34.98)],
}


def inside(pt, poly):
    x, y = pt
    res = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            res = not res
        j = i
    return res


def center(c, line):
    lon = LON0 + (c + 0.5) * DX
    lat = LAT1 - (line + 0.5) * DY + (0.5 * DY if c % 2 == 1 else 0)
    return lon, lat


def hexcoord(c, line):
    column = c - W // 2
    row = (H - 1) // 2 - line
    two_rows = row * 2 + (1 if abs(column) % 2 == 1 else 0)
    return (two_rows - column) // 2, (two_rows + column) // 2


def dist(a, b):
    dx, dy = a[0] - b[0], a[1] - b[1]
    if (dx >= 0) == (dy >= 0):
        return max(abs(dx), abs(dy))
    return abs(dx) + abs(dy)


land = [[False] * W for _ in range(H)]
for line in range(H):
    for c in range(W):
        p = center(c, line)
        land[line][c] = inside(p, mainland) or any(inside(p, poly) for poly in islands.values())

coords = {(c, l): hexcoord(c, l) for l in range(H) for c in range(W)}
land_tiles = [coords[(c, l)] for l in range(H) for c in range(W) if land[l][c]]
water_tiles = [coords[(c, l)] for l in range(H) for c in range(W) if not land[l][c]]


def dist_to(tile, tiles):
    return min(dist(tile, t) for t in tiles)


def h(c, l):  # deterministic hash 0..99
    return (c * 7919 + l * 104729 + 31) % 101


out = []
for l in range(H):
    row = []
    for c in range(W):
        t = coords[(c, l)]
        if land[l][c]:
            d = dist_to(t, water_tiles)
            r = h(c, l)
            if d == 1:
                ch = "g" if r < 55 else "p" if r < 85 else "f"
            elif d == 2:
                ch = "g" if r < 35 else "p" if r < 60 else "f" if r < 85 else "h"
            else:
                ch = "h" if r < 45 else "f" if r < 75 else "m" if r < 87 else "p"
        else:
            ch = "." if dist_to(t, land_tiles) <= 2 else "~"
        row.append(ch)
    out.append("".join(row))

places = {
    "Yeosu": (127.72, 34.76), "Suncheon": (127.49, 34.95), "Jinju": (128.08, 35.18),
    "Sacheon": (128.07, 35.00), "Goseong": (128.32, 34.97), "Busan": (129.03, 35.10),
    "Gimhae": (128.88, 35.23), "Okpo": (128.69, 34.89), "Dangpo": (128.38, 34.80),
    "Danghangpo": (128.40, 35.05), "Jeokjinpo": (128.43, 34.97), "Happo": (128.57, 35.18),
    "Noryang": (127.87, 34.94),
}
OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"wrote {OUT}")
for name, (lon, lat) in places.items():
    c = round((lon - LON0) / DX - 0.5)
    line = round((LAT1 - lat) / DY - 0.5)
    print(f"{name:11s} col={c:2d} line={line:2d} char={out[line][c]}")

# --- preview render: flat-top hexes, odd columns raised half a row ---
from PIL import Image, ImageDraw
import math
S = 14  # hex radius px
colors = {"~": (20, 50, 120), ".": (70, 130, 200), "g": (110, 170, 70), "p": (190, 180, 100),
          "f": (40, 110, 40), "h": (150, 120, 70), "m": (110, 100, 100)}
img = Image.new("RGB", (int(W * 1.5 * S + S), int((H + 1) * math.sqrt(3) * S)), (0, 0, 0))
d = ImageDraw.Draw(img)
for l in range(H):
    for c in range(W):
        cx = S + c * 1.5 * S
        cy = (l + 0.5) * math.sqrt(3) * S + (math.sqrt(3) / 2 * S if c % 2 == 0 else 0)
        pts = [(cx + S * math.cos(math.radians(a)), cy + S * math.sin(math.radians(a))) for a in range(0, 360, 60)]
        d.polygon(pts, fill=colors[out[l][c]], outline=(0, 0, 0))
for name, (lon, lat) in places.items():
    c = round((lon - LON0) / DX - 0.5)
    l = round((LAT1 - lat) / DY - 0.5)
    cx = S + c * 1.5 * S
    cy = (l + 0.5) * math.sqrt(3) * S + (math.sqrt(3) / 2 * S if c % 2 == 0 else 0)
    d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(255, 0, 0))
    d.text((cx + 5, cy - 6), name, fill=(255, 255, 255))
img.save(OUT.with_name("ch1-south-sea-preview.png"))
