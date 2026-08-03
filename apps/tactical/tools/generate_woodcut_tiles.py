"""Generate original Shaelvien woodcut tile assets.

This script uses only deterministic local drawing routines and the Python
standard library. It does not download or copy any external artwork.
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import zlib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "tiles" / "woodcut"
ATLAS_PATH = ROOT / "assets" / "tiles" / "woodcut_atlas_001.png"
REGISTRY_PATH = ROOT / "data" / "assets" / "tile_asset_registry.json"
MANIFEST_PATH = ROOT / "data" / "tile_manifest.json"
SIZE = 32
ATLAS_COLUMNS = 8


PALETTE = {
    "oak": (173, 122, 68, 255),
    "oak_light": (204, 162, 102, 255),
    "walnut": (93, 56, 34, 255),
    "cedar": (136, 75, 43, 255),
    "ash": (190, 180, 148, 255),
    "charcoal": (42, 34, 28, 255),
    "parchment": (216, 196, 142, 255),
    "moss": (83, 122, 70, 255),
    "moss_dark": (50, 83, 49, 255),
    "blue": (76, 119, 130, 255),
    "blue_dark": (44, 78, 94, 255),
    "stone": (122, 119, 106, 255),
    "stone_dark": (70, 69, 64, 255),
    "sand": (197, 164, 102, 255),
    "snow": (221, 222, 203, 255),
    "swamp": (65, 76, 52, 255),
    "ember": (203, 95, 44, 255),
    "rune": (120, 91, 156, 255),
}


TILES = [
    ("woodcut-terrain-grass-001", "Grass", "terrain", "grass", ["temperate", "grass"]),
    ("woodcut-terrain-forest-001", "Forest", "terrain", "forest", ["forest", "trees"]),
    ("woodcut-terrain-mountain-001", "Mountains", "terrain", "mountain", ["mountain", "relief"]),
    ("woodcut-terrain-coast-001", "Coast", "terrain", "coast", ["coast", "shore"]),
    ("woodcut-terrain-water-001", "Water", "terrain", "water", ["water", "animated_candidate"]),
    ("woodcut-terrain-road-001", "Road", "terrain", "road", ["road", "route"]),
    ("woodcut-terrain-sand-001", "Sand", "terrain", "sand", ["desert", "sand"]),
    ("woodcut-terrain-cliff-001", "Cliff", "terrain", "cliff", ["cliff", "contour"]),
    ("woodcut-terrain-snow-001", "Snow", "terrain", "snow", ["snow", "cold"]),
    ("woodcut-terrain-swamp-001", "Swamp", "terrain", "swamp", ["swamp", "pools"]),
    ("woodcut-terrain-stone-001", "Stone", "terrain", "stone", ["stone", "dungeon"]),
    ("woodcut-terrain-wood-floor-001", "Wood Floor", "terrain", "wood_floor", ["tavern", "floor"]),
    ("woodcut-terrain-stone-wall-001", "Stone Wall", "terrain", "stone_wall", ["wall", "dungeon"]),
    ("woodcut-terrain-dungeon-floor-001", "Dungeon Floor", "terrain", "dungeon_floor", ["dungeon", "stone"]),
    ("woodcut-terrain-castle-stone-001", "Castle Stone", "terrain", "castle_stone", ["castle", "stone"]),
    ("woodcut-terrain-ruins-stone-001", "Ruins Stone", "terrain", "ruins_stone", ["ruins", "stone"]),
    ("woodcut-terrain-magical-001", "Magical Terrain", "terrain", "magical", ["magical", "rune"]),
    ("woodcut-symbol-village-001", "Village Symbol", "symbol", "village", ["village", "map_symbol"]),
    ("woodcut-symbol-town-001", "Town Symbol", "symbol", "town", ["town", "map_symbol"]),
    ("woodcut-symbol-city-001", "City Symbol", "symbol", "city", ["city", "map_symbol"]),
    ("woodcut-symbol-block-001", "Block Symbol", "symbol", "block", ["block", "map_symbol"]),
    ("woodcut-symbol-tavern-001", "Tavern Symbol", "symbol", "tavern", ["tavern", "map_symbol"]),
    ("woodcut-object-tree-001", "Tree", "object", "tree", ["tree", "forest"]),
    ("woodcut-object-bush-001", "Bush", "object", "bush", ["bush", "forest"]),
    ("woodcut-object-flowers-001", "Flowers", "object", "flowers", ["flowers", "temperate"]),
    ("woodcut-object-log-001", "Log", "object", "log", ["log", "forest"]),
    ("woodcut-object-rock-001", "Rock", "object", "rock", ["rock", "stone"]),
    ("woodcut-object-boulder-001", "Boulder", "object", "boulder", ["boulder", "stone"]),
    ("woodcut-object-bridge-001", "Bridge", "object", "bridge", ["bridge", "road"]),
    ("woodcut-object-fence-001", "Fence", "object", "fence", ["fence", "village"]),
    ("woodcut-object-sign-001", "Sign", "object", "sign", ["sign", "village"]),
    ("woodcut-object-crate-001", "Crate", "object", "crate", ["crate", "tavern"]),
    ("woodcut-object-barrel-001", "Barrel", "object", "barrel", ["barrel", "tavern"]),
    ("woodcut-object-chest-001", "Chest", "object", "chest", ["chest", "container"]),
    ("woodcut-object-table-001", "Table", "object", "table", ["table", "tavern"]),
    ("woodcut-object-chair-001", "Chair", "object", "chair", ["chair", "tavern"]),
    ("woodcut-object-shelves-001", "Shelves", "object", "shelves", ["shelves", "interior"]),
    ("woodcut-object-bed-001", "Bed", "object", "bed", ["bed", "interior"]),
    ("woodcut-object-fireplace-001", "Fireplace", "object", "fireplace", ["fireplace", "animated_candidate"]),
    ("woodcut-object-door-001", "Door", "object", "door", ["door", "interior"]),
    ("woodcut-object-window-001", "Window", "object", "window", ["window", "interior"]),
    ("woodcut-object-stairs-001", "Stairs", "object", "stairs", ["stairs", "interior"]),
    ("woodcut-object-bar-001", "Bar", "object", "bar", ["bar", "tavern"]),
    ("woodcut-object-torch-001", "Torch", "object", "torch", ["torch", "animated_candidate"]),
    ("woodcut-object-portal-001", "Portal", "object", "portal", ["portal", "animated_candidate"]),
    ("woodcut-marker-entrance-001", "Entrance Marker", "marker", "entrance", ["entrance", "marker"]),
    ("woodcut-marker-exit-001", "Exit Marker", "marker", "exit", ["exit", "marker"]),
    ("woodcut-marker-trigger-001", "Trigger Marker", "marker", "trigger", ["trigger", "hidden"]),
    ("woodcut-marker-player-start-001", "Player Start", "marker", "player_start", ["player", "start"]),
    ("woodcut-marker-enemy-start-001", "Enemy Start", "marker", "enemy_start", ["enemy", "start"]),
]

AUTOTILE_BASES = ["grass", "road", "water", "forest", "sand", "cliff", "snow", "stone"]
AUTOTILE_EDGES = ["n", "e", "s", "w"]


def stable_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


class Canvas:
    def __init__(self, seed: str):
        self.seed = stable_seed(seed)
        self.pixels = [[(0, 0, 0, 0) for _ in range(SIZE)] for _ in range(SIZE)]

    def noise(self, x: int, y: int, salt: int = 0) -> int:
        value = (self.seed + x * 374761393 + y * 668265263 + salt * 1442695041) & 0xFFFFFFFF
        value ^= value >> 13
        value = (value * 1274126177) & 0xFFFFFFFF
        return value & 0xFF

    def set(self, x: int, y: int, color: tuple[int, int, int, int]) -> None:
        if 0 <= x < SIZE and 0 <= y < SIZE:
            self.pixels[y][x] = color

    def rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int, int]) -> None:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def line(self, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int]) -> None:
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx: int, cy: int, radius: int, color: tuple[int, int, int, int], fill: bool = False) -> None:
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                dist = math.hypot(x - cx, y - cy)
                if (fill and dist <= radius) or (not fill and radius - 0.75 <= dist <= radius + 0.75):
                    self.set(x, y, color)

    def polygon(self, points: list[tuple[int, int]], color: tuple[int, int, int, int]) -> None:
        min_y = max(0, min(y for _, y in points))
        max_y = min(SIZE - 1, max(y for _, y in points))
        for y in range(min_y, max_y + 1):
            nodes = []
            j = len(points) - 1
            for i, (xi, yi) in enumerate(points):
                xj, yj = points[j]
                if (yi < y <= yj) or (yj < y <= yi):
                    nodes.append(int(xi + (y - yi) / ((yj - yi) or 1) * (xj - xi)))
                j = i
            nodes.sort()
            for i in range(0, len(nodes), 2):
                if i + 1 >= len(nodes):
                    break
                for x in range(max(0, nodes[i]), min(SIZE - 1, nodes[i + 1]) + 1):
                    self.set(x, y, color)

    def wood_base(self, base: tuple[int, int, int, int] = PALETTE["oak"], shade: tuple[int, int, int, int] = PALETTE["walnut"]) -> None:
        for y in range(SIZE):
            for x in range(SIZE):
                grain = int(math.sin((x + self.noise(0, y, 1) / 38) / 3.2) * 8)
                jitter = (self.noise(x, y, 2) % 9) - 4
                color = tuple(max(0, min(255, base[i] + grain + jitter)) for i in range(3)) + (255,)
                self.set(x, y, color)
        for y in range(2, SIZE, 5):
            offset = self.noise(y, 0, 3) % 5 - 2
            self.line(0, y, SIZE - 1, max(0, min(SIZE - 1, y + offset)), fade(shade, 0.72))
        for x in range(3, SIZE, 9):
            self.line(x, 0, x + (self.noise(x, 0, 4) % 5 - 2), SIZE - 1, fade(shade, 0.38))

    def border_burn(self) -> None:
        c = fade(PALETTE["charcoal"], 0.72)
        self.line(0, 0, SIZE - 1, 0, c)
        self.line(0, SIZE - 1, SIZE - 1, SIZE - 1, c)
        self.line(0, 0, 0, SIZE - 1, c)
        self.line(SIZE - 1, 0, SIZE - 1, SIZE - 1, c)


def fade(color: tuple[int, int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return color[:3] + (max(0, min(255, int(color[3] * alpha))),)


def blend_under(bg: tuple[int, int, int, int], fg: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    alpha = fg[3] / 255
    return tuple(int(fg[i] * alpha + bg[i] * (1 - alpha)) for i in range(3)) + (255,)


def apply_alpha(canvas: Canvas) -> None:
    for y in range(SIZE):
        for x in range(SIZE):
            color = canvas.pixels[y][x]
            if color[3] != 255:
                canvas.pixels[y][x] = blend_under(canvas.pixels[y][x], color)


def draw_kind(asset_id: str, kind: str) -> Canvas:
    c = Canvas(asset_id)
    c.wood_base()
    burn = PALETTE["charcoal"]
    dark = PALETTE["walnut"]
    moss = PALETTE["moss"]
    blue = PALETTE["blue"]
    stone = PALETTE["stone"]
    parchment = PALETTE["parchment"]

    if kind in {"grass", "temperate"}:
        for i in range(20):
            x = (c.noise(i, 2) % 30) + 1
            y = (c.noise(i, 3) % 28) + 2
            c.line(x, y + 2, x + (i % 3) - 1, y, fade(moss, 0.9))
        c.rect(2, 2, 2, 2, PALETTE["moss"])
        c.rect(24, 23, 2, 2, PALETTE["moss_dark"])
    elif kind == "forest":
        for x, y, r in [(8, 10, 6), (16, 8, 7), (23, 13, 6), (13, 20, 6)]:
            c.circle(x, y, r, fade(PALETTE["moss_dark"], 0.92), fill=True)
            c.circle(x, y, r, burn)
            c.line(x, y + r, x, min(31, y + r + 5), dark)
        for x in (7, 15, 23):
            c.line(x - 3, 22, x, 16, burn)
            c.line(x, 16, x + 3, 22, burn)
    elif kind == "mountain":
        for points in [[(3, 25), (11, 7), (20, 25)], [(12, 27), (23, 5), (31, 27)]]:
            c.polygon(points, PALETTE["ash"])
            for a, b in zip(points, points[1:] + points[:1]):
                c.line(a[0], a[1], b[0], b[1], burn)
        c.line(11, 7, 12, 25, dark)
        c.line(23, 5, 22, 27, dark)
        c.line(16, 16, 24, 15, fade(dark, 0.8))
    elif kind == "water":
        c.wood_base(PALETTE["blue"], PALETTE["blue_dark"])
        for y in range(6, 30, 6):
            c.line(1, y, 8, y - 2, fade(PALETTE["parchment"], 0.55))
            c.line(9, y - 2, 18, y + 1, fade(PALETTE["parchment"], 0.55))
            c.line(19, y + 1, 31, y - 1, fade(PALETTE["parchment"], 0.55))
    elif kind == "coast":
        c.wood_base(PALETTE["sand"], PALETTE["walnut"])
        c.polygon([(0, 0), (32, 0), (32, 16), (21, 18), (14, 15), (8, 20), (0, 18)], fade(PALETTE["blue"], 0.92))
        for y in (7, 12, 17):
            c.line(1, y, 30, y + (c.noise(y, 0) % 5 - 2), fade(PALETTE["parchment"], 0.56))
        c.line(0, 18, 8, 20, burn)
        c.line(8, 20, 14, 15, burn)
        c.line(14, 15, 21, 18, burn)
        c.line(21, 18, 31, 16, burn)
    elif kind == "road":
        c.wood_base(PALETTE["oak_light"], PALETTE["walnut"])
        c.polygon([(0, 19), (7, 16), (13, 17), (20, 15), (31, 12), (31, 20), (22, 23), (14, 22), (7, 24), (0, 27)], PALETTE["ash"])
        for y in (17, 22):
            c.line(0, y + 4, 31, y - 4, fade(burn, 0.5))
    elif kind == "sand":
        c.wood_base(PALETTE["sand"], PALETTE["cedar"])
        for y in range(6, 29, 5):
            c.line(2, y, 12, y - 2, fade(dark, 0.45))
            c.line(16, y - 1, 30, y + 1, fade(dark, 0.45))
    elif kind == "cliff":
        c.wood_base(PALETTE["cedar"], PALETTE["charcoal"])
        for x in (6, 12, 19, 26):
            c.line(x, 1, x - 3, 30, burn)
        for y in (6, 12, 18, 25):
            c.line(2, y, 30, y + (c.noise(y, 0) % 5 - 2), fade(burn, 0.8))
    elif kind == "snow":
        c.wood_base(PALETTE["snow"], PALETTE["ash"])
        for i in range(12):
            x = c.noise(i, 1) % 30
            y = c.noise(i, 2) % 30
            c.line(x, y, min(31, x + 3), max(0, y - 2), fade(PALETTE["stone_dark"], 0.45))
    elif kind == "swamp":
        c.wood_base(PALETTE["swamp"], PALETTE["charcoal"])
        for x, y, r in [(8, 10, 5), (20, 19, 6), (25, 8, 3)]:
            c.circle(x, y, r, fade(PALETTE["blue_dark"], 0.75), fill=True)
            c.circle(x, y, r, fade(burn, 0.7))
        for i in range(10):
            x = c.noise(i, 4) % 31
            c.line(x, 23, x + 1, 18, fade(PALETTE["moss"], 0.75))
    elif kind in {"stone", "dungeon_floor", "castle_stone", "ruins_stone", "stone_wall"}:
        c.wood_base(stone, PALETTE["stone_dark"])
        for y in range(0, 32, 8):
            c.line(0, y, 31, y, fade(burn, 0.65))
        for y in range(4, 32, 8):
            for x in range(-8, 32, 16):
                c.line(x, y, x, min(31, y + 8), fade(burn, 0.55))
        if kind == "stone_wall":
            c.rect(0, 0, 32, 6, fade(burn, 0.45))
            c.rect(0, 22, 32, 10, fade(burn, 0.38))
        if kind == "ruins_stone":
            c.line(4, 4, 28, 26, fade(burn, 0.8))
            c.rect(24, 0, 8, 8, PALETTE["oak"])
    elif kind == "wood_floor":
        c.wood_base(PALETTE["oak"], PALETTE["walnut"])
        for x in (8, 16, 24):
            c.line(x, 0, x, 31, fade(burn, 0.66))
        for y in (10, 21):
            c.line(0, y, 31, y, fade(burn, 0.45))
    elif kind == "magical":
        c.wood_base(PALETTE["walnut"], PALETTE["charcoal"])
        c.circle(16, 16, 10, PALETTE["rune"])
        c.circle(16, 16, 5, fade(PALETTE["parchment"], 0.72))
        c.line(16, 5, 16, 27, fade(PALETTE["rune"], 0.96))
        c.line(5, 16, 27, 16, fade(PALETTE["rune"], 0.96))
    elif kind in {"city", "town", "village", "block", "tavern"}:
        c.wood_base(PALETTE["parchment"], PALETTE["walnut"])
        if kind == "block":
            for y in (8, 16, 24):
                c.line(3, y, 29, y, burn)
            for x in (10, 21):
                c.line(x, 4, x, 28, burn)
        else:
            houses = [(6, 18, 7, 8), (14, 13, 7, 13), (22, 17, 6, 9)]
            for x, y, w, h in houses:
                c.rect(x, y, w, h, PALETTE["ash"])
                c.polygon([(x - 1, y), (x + w // 2, y - 5), (x + w + 1, y)], PALETTE["cedar"])
                c.line(x - 1, y, x + w // 2, y - 5, burn)
                c.line(x + w // 2, y - 5, x + w + 1, y, burn)
            if kind == "tavern":
                c.rect(12, 21, 8, 5, PALETTE["walnut"])
                c.line(7, 9, 25, 9, burn)
            if kind == "city":
                c.line(5, 27, 28, 27, burn)
                c.line(16, 6, 16, 26, burn)
    else:
        draw_object(c, kind)

    c.border_burn()
    apply_alpha(c)
    return c


def draw_object(c: Canvas, kind: str) -> None:
    burn = PALETTE["charcoal"]
    dark = PALETTE["walnut"]
    wood = PALETTE["cedar"]
    moss = PALETTE["moss_dark"]
    stone = PALETTE["stone"]

    if kind == "tree":
        c.circle(16, 12, 9, moss, fill=True)
        c.circle(16, 12, 9, burn)
        c.rect(14, 19, 4, 9, dark)
    elif kind == "bush":
        for x, y in [(10, 17), (16, 14), (22, 18)]:
            c.circle(x, y, 6, moss, fill=True)
            c.circle(x, y, 6, burn)
    elif kind == "flowers":
        for x, y in [(8, 11), (18, 15), (25, 9), (13, 23)]:
            c.line(x, y + 5, x, y, PALETTE["moss"])
            c.rect(x - 1, y, 3, 3, PALETTE["parchment"])
    elif kind == "log":
        c.rect(5, 13, 22, 7, wood)
        c.circle(6, 16, 4, dark)
        c.circle(26, 16, 4, dark)
        c.line(8, 13, 24, 20, burn)
    elif kind == "rock":
        c.polygon([(8, 22), (12, 11), (22, 9), (27, 20), (19, 25)], stone)
        c.line(12, 11, 22, 9, burn)
        c.line(22, 9, 27, 20, burn)
    elif kind == "boulder":
        c.circle(16, 17, 10, stone, fill=True)
        c.circle(16, 17, 10, burn)
        c.line(9, 16, 24, 10, fade(burn, 0.7))
    elif kind == "bridge":
        c.rect(2, 11, 28, 10, PALETTE["ash"])
        for x in range(5, 30, 6):
            c.line(x, 10, x, 22, burn)
        c.line(2, 11, 30, 11, burn)
        c.line(2, 21, 30, 21, burn)
    elif kind == "fence":
        for x in range(4, 31, 6):
            c.rect(x, 9, 2, 17, dark)
        c.rect(2, 14, 28, 3, wood)
        c.rect(2, 21, 28, 3, wood)
    elif kind == "sign":
        c.rect(14, 12, 3, 17, dark)
        c.rect(7, 7, 18, 9, PALETTE["ash"])
        c.line(9, 11, 23, 11, burn)
    elif kind in {"crate", "chest"}:
        c.rect(6, 10, 20, 15, wood)
        c.line(6, 10, 26, 25, burn)
        c.line(26, 10, 6, 25, burn)
        if kind == "chest":
            c.rect(5, 8, 22, 6, PALETTE["cedar"])
            c.rect(15, 9, 3, 16, PALETTE["accent"] if "accent" in PALETTE else PALETTE["parchment"])
    elif kind == "barrel":
        c.rect(9, 7, 14, 20, wood)
        c.circle(16, 8, 7, dark)
        c.circle(16, 26, 7, dark)
        c.line(9, 13, 23, 13, burn)
        c.line(9, 21, 23, 21, burn)
    elif kind == "table":
        c.rect(4, 8, 24, 14, wood)
        c.line(5, 13, 27, 13, burn)
        c.rect(7, 22, 4, 6, dark)
        c.rect(21, 22, 4, 6, dark)
    elif kind == "chair":
        c.rect(9, 7, 14, 6, wood)
        c.rect(10, 13, 12, 9, PALETTE["oak"])
        c.rect(10, 22, 3, 6, dark)
        c.rect(19, 22, 3, 6, dark)
    elif kind == "shelves":
        c.rect(6, 5, 20, 23, dark)
        for y in (11, 17, 23):
            c.rect(7, y, 18, 2, PALETTE["oak"])
        for x in (10, 17, 22):
            c.rect(x, 6, 2, 5, PALETTE["parchment"])
    elif kind == "bed":
        c.rect(6, 7, 20, 20, PALETTE["ash"])
        c.rect(8, 9, 16, 6, PALETTE["parchment"])
        c.rect(8, 16, 16, 9, PALETTE["cedar"])
    elif kind == "fireplace":
        c.rect(6, 6, 20, 21, stone)
        c.rect(10, 12, 12, 11, burn)
        c.polygon([(13, 22), (16, 12), (20, 22)], PALETTE["ember"])
        c.polygon([(15, 21), (17, 15), (19, 21)], PALETTE["parchment"])
    elif kind == "door":
        c.rect(8, 5, 16, 23, wood)
        c.line(16, 5, 16, 28, burn)
        c.circle(21, 17, 1, PALETTE["parchment"], fill=True)
    elif kind == "window":
        c.rect(7, 8, 18, 16, PALETTE["blue"])
        c.line(16, 8, 16, 24, burn)
        c.line(7, 16, 25, 16, burn)
        c.line(7, 8, 25, 8, burn)
        c.line(7, 24, 25, 24, burn)
    elif kind == "stairs":
        for i, y in enumerate(range(8, 25, 5)):
            c.rect(5 + i * 3, y, 21 - i * 3, 3, PALETTE["ash"])
            c.line(5 + i * 3, y, 26, y, burn)
    elif kind == "bar":
        c.rect(2, 10, 28, 10, wood)
        c.rect(2, 20, 28, 5, dark)
        for x in (8, 16, 24):
            c.line(x, 10, x, 25, burn)
    elif kind == "torch":
        c.rect(15, 12, 3, 15, dark)
        c.polygon([(12, 12), (16, 4), (21, 12)], PALETTE["ember"])
        c.polygon([(15, 12), (17, 7), (19, 12)], PALETTE["parchment"])
    elif kind == "portal":
        c.circle(16, 16, 11, PALETTE["rune"])
        c.circle(16, 16, 7, fade(PALETTE["blue"], 0.82), fill=True)
        c.line(16, 5, 16, 27, PALETTE["parchment"])
    elif kind in {"entrance", "exit"}:
        c.circle(16, 16, 11, PALETTE["blue"] if kind == "entrance" else PALETTE["moss"])
        c.line(8, 16, 24, 16, PALETTE["parchment"])
        c.line(18, 10, 24, 16, PALETTE["parchment"])
        c.line(18, 22, 24, 16, PALETTE["parchment"])
    elif kind == "trigger":
        c.circle(16, 16, 10, PALETTE["rune"])
        c.line(16, 7, 23, 23, PALETTE["parchment"])
        c.line(23, 23, 8, 14, PALETTE["parchment"])
    elif kind == "player_start":
        c.circle(16, 16, 10, PALETTE["blue"])
        c.line(16, 7, 16, 25, PALETTE["parchment"])
        c.line(9, 16, 23, 16, PALETTE["parchment"])
    elif kind == "enemy_start":
        c.circle(16, 16, 10, PALETTE["ember"])
        c.line(10, 10, 22, 22, PALETTE["parchment"])
        c.line(22, 10, 10, 22, PALETTE["parchment"])


def make_autotile(asset_id: str, base_kind: str, edge: str) -> Canvas:
    c = draw_kind(asset_id + "-base", base_kind if base_kind != "stone" else "stone")
    burn = PALETTE["charcoal"]
    if edge == "n":
        c.rect(0, 0, SIZE, 4, fade(burn, 0.42))
    elif edge == "s":
        c.rect(0, SIZE - 4, SIZE, 4, fade(burn, 0.42))
    elif edge == "e":
        c.rect(SIZE - 4, 0, 4, SIZE, fade(burn, 0.42))
    elif edge == "w":
        c.rect(0, 0, 4, SIZE, fade(burn, 0.42))
    c.border_burn()
    return c


def png_bytes(pixels: list[list[tuple[int, int, int, int]]]) -> bytes:
    height = len(pixels)
    width = len(pixels[0])
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for pixel in row:
            raw.extend(pixel)
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def write_png(path: Path, canvas: Canvas) -> str:
    data = png_bytes(canvas.pixels)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def atlas_canvas(canvases: list[Canvas]) -> Canvas:
    rows = math.ceil(len(canvases) / ATLAS_COLUMNS)
    atlas = Canvas("woodcut-atlas")
    atlas.pixels = [[(0, 0, 0, 0) for _ in range(ATLAS_COLUMNS * SIZE)] for _ in range(rows * SIZE)]
    for index, canvas in enumerate(canvases):
        col = index % ATLAS_COLUMNS
        row = index // ATLAS_COLUMNS
        for y in range(SIZE):
            for x in range(SIZE):
                atlas.pixels[row * SIZE + y][col * SIZE + x] = canvas.pixels[y][x]
    return atlas


def source_rect_for(index: int) -> dict:
    return {
        "x": (index % ATLAS_COLUMNS) * SIZE,
        "y": (index // ATLAS_COLUMNS) * SIZE,
        "width": SIZE,
        "height": SIZE,
    }


def image_ref(asset_id: str) -> dict:
    return {
        "imageAssetId": asset_id,
        "fitMode": "cover",
        "rotationDeg": 0,
        "flipX": False,
        "flipY": False,
        "opacity": 1.0,
        "tint": None,
    }


def fallback_sprite(base: str = "#b07a44") -> dict:
    return {
        "base": base,
        "rects": [
            {"x": 0, "y": 0, "w": 32, "h": 1, "color": "#2a221c"},
            {"x": 0, "y": 31, "w": 32, "h": 1, "color": "#2a221c"},
            {"x": 5, "y": 9, "w": 22, "h": 1, "color": "#5d3822"},
        ],
    }


def update_manifest(asset_map: dict[str, str]) -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["schemaVersion"] = "shaelvien.tile_manifest.v2"
    manifest["tileSize"] = SIZE
    manifest["visualLanguage"] = "shaelvien_woodcut_v1"
    manifest["defaultAssetSet"] = "shaelvien_woodcut_tileset_1"
    manifest["autotileVisualOnly"] = True

    mappings = {
        "grass": "woodcut-terrain-grass-001",
        "water": "woodcut-terrain-water-001",
        "road": "woodcut-terrain-road-001",
        "wall": "woodcut-terrain-stone-wall-001",
        "floor": "woodcut-terrain-wood-floor-001",
        "door": "woodcut-object-door-001",
        "city": "woodcut-symbol-city-001",
        "block": "woodcut-symbol-block-001",
        "tavern": "woodcut-symbol-tavern-001",
        "stairs": "woodcut-object-stairs-001",
        "table": "woodcut-object-table-001",
        "chair": "woodcut-object-chair-001",
        "bar": "woodcut-object-bar-001",
        "chest": "woodcut-object-chest-001",
        "entrance": "woodcut-marker-entrance-001",
        "exit": "woodcut-marker-exit-001",
        "trigger-marker": "woodcut-marker-trigger-001",
        "player-start": "woodcut-marker-player-start-001",
        "enemy-start": "woodcut-marker-enemy-start-001",
    }

    existing = {definition["id"]: definition for definition in manifest["definitions"]}
    for tile_id, asset_id in mappings.items():
        definition = existing.get(tile_id)
        if definition:
            definition["image"] = image_ref(asset_id)
            definition["visualStyle"] = "shaelvien_woodcut_v1"

    additions = [
        ("forest", "Forest", "forest", False, "woodcut-terrain-forest-001"),
        ("mountain", "Mountain", "mountain", True, "woodcut-terrain-mountain-001"),
        ("coast", "Coast", "coast", False, "woodcut-terrain-coast-001"),
        ("sand", "Sand", "sand", False, "woodcut-terrain-sand-001"),
        ("cliff", "Cliff", "cliff", True, "woodcut-terrain-cliff-001"),
        ("snow", "Snow", "snow", False, "woodcut-terrain-snow-001"),
        ("swamp", "Swamp", "swamp", True, "woodcut-terrain-swamp-001"),
        ("stone", "Stone", "stone", False, "woodcut-terrain-stone-001"),
        ("dungeon-floor", "Dungeon Floor", "dungeon", False, "woodcut-terrain-dungeon-floor-001"),
        ("castle-stone", "Castle Stone", "castle", True, "woodcut-terrain-castle-stone-001"),
        ("ruins-stone", "Ruins Stone", "ruins", False, "woodcut-terrain-ruins-stone-001"),
        ("magical-terrain", "Magical Terrain", "magical terrain", False, "woodcut-terrain-magical-001"),
        ("village", "Village", "village", False, "woodcut-symbol-village-001"),
        ("town", "Town", "town", False, "woodcut-symbol-town-001"),
        ("tree", "Tree", "tree", True, "woodcut-object-tree-001"),
        ("bush", "Bush", "bush", False, "woodcut-object-bush-001"),
        ("flowers", "Flowers", "flowers", False, "woodcut-object-flowers-001"),
        ("log", "Log", "log", True, "woodcut-object-log-001"),
        ("rock", "Rock", "rock", True, "woodcut-object-rock-001"),
        ("boulder", "Boulder", "boulder", True, "woodcut-object-boulder-001"),
        ("bridge", "Bridge", "bridge", False, "woodcut-object-bridge-001"),
        ("fence", "Fence", "fence", True, "woodcut-object-fence-001"),
        ("sign", "Sign", "sign", False, "woodcut-object-sign-001"),
        ("crate", "Crate", "crate", True, "woodcut-object-crate-001"),
        ("barrel", "Barrel", "barrel", True, "woodcut-object-barrel-001"),
        ("shelves", "Shelves", "shelves", True, "woodcut-object-shelves-001"),
        ("bed", "Bed", "bed", True, "woodcut-object-bed-001"),
        ("fireplace", "Fireplace", "fireplace", True, "woodcut-object-fireplace-001"),
        ("window", "Window", "window", True, "woodcut-object-window-001"),
        ("torch", "Torch", "torch", False, "woodcut-object-torch-001"),
        ("portal", "Portal", "portal", False, "woodcut-object-portal-001"),
    ]
    for tile_id, name, category, blocked, asset_id in additions:
        if tile_id in existing:
            continue
        manifest["definitions"].append({
            "id": tile_id,
            "name": name,
            "category": category,
            "defaultWidth": 1,
            "defaultHeight": 1,
            "blocked": blocked,
            "sprite": fallback_sprite(),
            "image": image_ref(asset_id),
            "visualStyle": "shaelvien_woodcut_v1",
        })

    manifest["autotileSets"] = [
        {
            "id": f"woodcut-autotile-{base}-001",
            "terrain": base,
            "visualOnly": True,
            "edges": {edge: f"woodcut-autotile-{base}-{edge}-001" for edge in AUTOTILE_EDGES},
        }
        for base in AUTOTILE_BASES
    ]
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    canvases: list[Canvas] = []
    generated: list[dict] = []

    work = list(TILES)
    for base in AUTOTILE_BASES:
        for edge in AUTOTILE_EDGES:
            work.append((f"woodcut-autotile-{base}-{edge}-001", f"{base.title()} Edge {edge.upper()}", "autotile", f"autotile:{base}:{edge}", ["autotile", base, edge]))

    for index, (asset_id, name, asset_type, kind, tags) in enumerate(work):
        if kind.startswith("autotile:"):
            _, base, edge = kind.split(":")
            canvas = make_autotile(asset_id, base, edge)
        else:
            canvas = draw_kind(asset_id, kind)
        frame_path = ASSET_DIR / f"{asset_id}.png"
        frame_hash = write_png(frame_path, canvas)
        canvases.append(canvas)
        generated.append({
            "assetId": asset_id,
            "name": name,
            "type": "tile_image" if asset_type != "autotile" else "autotile_image",
            "sourcePath": str(frame_path.relative_to(ROOT)).replace("\\", "/"),
            "mimeType": "image/png",
            "widthPx": SIZE,
            "heightPx": SIZE,
            "contentHash": frame_hash,
            "licenseStatus": "original",
            "author": "Shaelvien deterministic local generator",
            "tags": ["shaelvien_woodcut_v1", asset_type] + tags,
            "createdAt": now,
            "updatedAt": now,
            "atlasId": "woodcut-atlas-001",
            "atlasSourcePath": "assets/tiles/woodcut_atlas_001.png",
            "sourceRect": source_rect_for(index),
        })

    atlas = atlas_canvas(canvases)
    atlas_hash = write_png(ATLAS_PATH, atlas)
    atlas_record = {
        "assetId": "woodcut-atlas-001",
        "name": "Shaelvien Woodcut Atlas 001",
        "type": "tile_atlas",
        "sourcePath": "assets/tiles/woodcut_atlas_001.png",
        "mimeType": "image/png",
        "widthPx": ATLAS_COLUMNS * SIZE,
        "heightPx": math.ceil(len(canvases) / ATLAS_COLUMNS) * SIZE,
        "contentHash": atlas_hash,
        "licenseStatus": "original",
        "author": "Shaelvien deterministic local generator",
        "tags": ["shaelvien_woodcut_v1", "atlas", "original"],
        "createdAt": now,
        "updatedAt": now,
        "tileSizePx": SIZE,
        "columns": ATLAS_COLUMNS,
        "frameCount": len(canvases),
    }

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    preserved = [
        asset for asset in registry.get("assets", [])
        if not str(asset.get("assetId", "")).startswith("woodcut-")
    ]
    registry["schemaVersion"] = "shaelvien.tile_asset_registry.v2"
    registry["defaultVisualLanguage"] = "shaelvien_woodcut_v1"
    registry["assets"] = preserved + [atlas_record] + generated
    registry["woodcutPolicy"] = {
        "style": "hand_burned_engraved_cartography",
        "authoritativeTileSizePx": SIZE,
        "originality": "deterministic local drawing; no external source art",
        "commercialAssetUse": "forbidden",
        "atlasRequired": True,
        "animationPolicy": "restrained handcrafted frame deltas only",
    }
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    update_manifest({asset["assetId"]: asset["sourcePath"] for asset in generated})
    print(json.dumps({"generatedFrames": len(generated), "atlas": str(ATLAS_PATH), "atlasHash": atlas_hash}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
