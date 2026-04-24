
import os
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

import pygame

pygame.init()

# ----------------------------
# Конфигурация
# ----------------------------
CELL_SIZE = 40
GRID_SIZE = 10
BOARD_SIZE = CELL_SIZE * GRID_SIZE

LEFT_MARGIN = 36
TOP_MARGIN = 96
BOARD_GAP = 56
WINDOW_WIDTH = LEFT_MARGIN * 2 + BOARD_SIZE * 2 + BOARD_GAP
WINDOW_HEIGHT = 760
FPS = 60

SHIP_SIZES = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

WHITE = (240, 245, 250)
TEXT_TITLE = (226, 230, 236)
TEXT_MAIN = (210, 218, 228)
TEXT_SUBTLE = (186, 196, 210)
TEXT_SHADOW = (20, 28, 40)
BLACK = (18, 24, 35)
RED = (220, 70, 70)
GREEN = (70, 180, 100)
YELLOW = (240, 210, 70)
GRID_BLUE = (126, 206, 255)
SEA_A = (20, 79, 145)
SEA_B = (28, 106, 182)
OVERLAY = (0, 0, 0, 160)


class Direction(Enum):
    HORIZONTAL = auto()
    VERTICAL = auto()


class CellState(Enum):
    EMPTY = auto()
    SHIP = auto()
    HIT = auto()
    MISS = auto()
    DESTROYED = auto()


class ScreenState(Enum):
    MENU = auto()
    SETUP = auto()
    BATTLE = auto()
    PASS = auto()
    PAUSE = auto()
    GAME_OVER = auto()


@dataclass
class Ship:
    size: int
    positions: List[Tuple[int, int]]
    hits: List[bool] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.hits:
            self.hits = [False] * self.size

    def hit(self, pos: Tuple[int, int]) -> None:
        for i, p in enumerate(self.positions):
            if p == pos:
                self.hits[i] = True
                return

    @property
    def destroyed(self) -> bool:
        return all(self.hits)


class Board:
    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self.grid = [[CellState.EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.shots = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.ships: List[Ship] = []

    @staticmethod
    def in_bounds(x: int, y: int) -> bool:
        return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE

    def around(self, x: int, y: int) -> List[Tuple[int, int]]:
        out = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if self.in_bounds(nx, ny):
                    out.append((nx, ny))
        return out

    def can_place(self, positions: List[Tuple[int, int]]) -> bool:
        for x, y in positions:
            if not self.in_bounds(x, y):
                return False
            if self.grid[y][x] != CellState.EMPTY:
                return False
            for nx, ny in self.around(x, y):
                if self.grid[ny][nx] == CellState.SHIP:
                    return False
        return True

    def place_ship(self, size: int, x: int, y: int, direction: Direction) -> bool:
        positions = []
        for i in range(size):
            positions.append((x + i, y) if direction == Direction.HORIZONTAL else (x, y + i))
        if not self.can_place(positions):
            return False
        ship = Ship(size, positions)
        self.ships.append(ship)
        for sx, sy in positions:
            self.grid[sy][sx] = CellState.SHIP
        return True

    def place_random_fleet(self) -> bool:
        self.clear()
        for size in SHIP_SIZES:
            placed = False
            for _ in range(3000):
                x = random.randint(0, GRID_SIZE - 1)
                y = random.randint(0, GRID_SIZE - 1)
                direction = random.choice([Direction.HORIZONTAL, Direction.VERTICAL])
                if self.place_ship(size, x, y, direction):
                    placed = True
                    break
            if not placed:
                return False
        return True

    def ship_at(self, x: int, y: int) -> Optional[Ship]:
        for ship in self.ships:
            if (x, y) in ship.positions:
                return ship
        return None

    def receive_shot(self, x: int, y: int) -> Tuple[bool, bool]:
        if self.shots[y][x]:
            return False, False

        self.shots[y][x] = True
        if self.grid[y][x] != CellState.SHIP:
            self.grid[y][x] = CellState.MISS
            return False, False

        ship = self.ship_at(x, y)
        if ship is None:
            self.grid[y][x] = CellState.HIT
            return True, False

        ship.hit((x, y))
        if ship.destroyed:
            for sx, sy in ship.positions:
                self.grid[sy][sx] = CellState.DESTROYED
            self.mark_around_sunk(ship)
            return True, True

        self.grid[y][x] = CellState.HIT
        return True, False

    def mark_around_sunk(self, ship: Ship) -> None:
        for x, y in ship.positions:
            for nx, ny in self.around(x, y):
                if self.grid[ny][nx] == CellState.EMPTY and not self.shots[ny][nx]:
                    self.shots[ny][nx] = True
                    self.grid[ny][nx] = CellState.MISS

    def all_destroyed(self) -> bool:
        return all(ship.destroyed for ship in self.ships)

    def available_shots(self) -> List[Tuple[int, int]]:
        return [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE) if not self.shots[y][x]]


class AIPlayer:
    def __init__(self, difficulty: str = "medium") -> None:
        self.difficulty = difficulty
        self.queue: List[Tuple[int, int]] = []
        self.hit_memory: List[Tuple[int, int]] = []

    def reset(self) -> None:
        self.queue.clear()
        self.hit_memory.clear()

    def choose_shot(self, board: Board) -> Tuple[int, int]:
        available = set(board.available_shots())
        while self.queue:
            target = self.queue.pop(0)
            if target in available:
                return target
        if not available:
            return -1, -1

        if self.difficulty == "easy":
            return random.choice(list(available))

        if self.difficulty == "medium":
            return random.choice(list(available))

        parity = [p for p in available if (p[0] + p[1]) % 2 == 0]
        return random.choice(parity or list(available))

    def process_result(self, pos: Tuple[int, int], hit: bool, destroyed: bool, board: Board) -> None:
        if self.difficulty == "easy":
            return

        if destroyed:
            self.queue.clear()
            self.hit_memory.clear()
            return

        if not hit:
            return

        self.hit_memory.append(pos)
        x, y = pos

        candidates: List[Tuple[int, int]] = []
        if self.difficulty == "hard" and len(self.hit_memory) >= 2:
            xs = {hx for hx, _ in self.hit_memory}
            ys = {hy for _, hy in self.hit_memory}
            if len(xs) == 1:
                candidates = [(x, y - 1), (x, y + 1)]
            elif len(ys) == 1:
                candidates = [(x - 1, y), (x + 1, y)]

        if not candidates:
            candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

        seen = set(self.queue)
        for nx, ny in candidates:
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and not board.shots[ny][nx]:
                if (nx, ny) not in seen:
                    self.queue.append((nx, ny))
                    seen.add((nx, ny))


@dataclass
class Button:
    key: str
    rect: pygame.Rect
    text: str
    style: str


class Assets:
    def __init__(self) -> None:
        base = os.path.join(os.path.dirname(__file__), "assets")
        self.base = base
        self.cache: Dict[Tuple[str, Tuple[int, int]], pygame.Surface] = {}
        self.raw: Dict[str, pygame.Surface] = {}

        self.background = self.load("background_tile.png")
        self.water = self.load("water_tile.png")
        self.panel = self.load("panel_tile.png")
        self.parchment = self.load("parchment_panel.png")
        self.metal_label = self.load("metal_label.png")
        self.selector = self.load("selector.png")
        self.hit = self.load("hit.png", alpha=True)
        self.miss = self.load("miss.png", alpha=True)

        self.buttons = {
            "green": self.load("button_green.png"),
            "orange": self.load("button_orange.png"),
            "purple": self.load("button_purple.png"),
            "gray": self.load("button_gray.png"),
            "red": self.load("button_red.png"),
            "yellow": self.load("button_yellow.png"),
        }

        self.ship_h = {s: self.load(f"ship_{s}_h.png", alpha=True) for s in (1, 2, 3, 4)}
        self.ship_v = {s: self.load(f"ship_{s}_v.png", alpha=True) for s in (1, 2, 3, 4)}

    def load(self, filename: str, alpha: bool = False) -> pygame.Surface:
        path = os.path.join(self.base, filename)
        img = pygame.image.load(path)
        return img.convert_alpha() if alpha else img.convert()

    def scaled(self, name: str, surf: pygame.Surface, size: Tuple[int, int]) -> pygame.Surface:
        key = (name, size)
        if key not in self.cache:
            self.cache[key] = pygame.transform.scale(surf, size)
        return self.cache[key]

    def tile(self, dst: pygame.Surface, tile_surf: pygame.Surface, rect: pygame.Rect) -> None:
        tw, th = tile_surf.get_size()
        for y in range(rect.top, rect.bottom, th):
            for x in range(rect.left, rect.right, tw):
                dst.blit(tile_surf, (x, y))


    def draw_scaled_panel(self, dst: pygame.Surface, rect: pygame.Rect, surf: pygame.Surface) -> None:
        panel = self.scaled(f"panel_{id(surf)}_{rect.w}_{rect.h}", surf, (rect.w, rect.h))
        dst.blit(panel, rect)

    def _draw_symmetric_panel(
        self,
        dst: pygame.Surface,
        rect: pygame.Rect,
        fill_top: tuple[int, int, int],
        fill_bottom: tuple[int, int, int],
        border_light: tuple[int, int, int],
        border_dark: tuple[int, int, int],
        accent: tuple[int, int, int],
    ) -> None:
        panel = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        for y in range(rect.h):
            t = y / max(1, rect.h - 1)
            col = (
                int(fill_top[0] * (1 - t) + fill_bottom[0] * t),
                int(fill_top[1] * (1 - t) + fill_bottom[1] * t),
                int(fill_top[2] * (1 - t) + fill_bottom[2] * t),
            )
            pygame.draw.line(panel, col, (0, y), (rect.w - 1, y))

        pygame.draw.rect(panel, border_dark, panel.get_rect(), 2)
        pygame.draw.line(panel, border_light, (2, 2), (rect.w - 3, 2), 1)
        pygame.draw.line(panel, border_light, (2, 2), (2, rect.h - 3), 1)
        pygame.draw.line(panel, border_dark, (2, rect.h - 3), (rect.w - 3, rect.h - 3), 1)
        pygame.draw.line(panel, border_dark, (rect.w - 3, 2), (rect.w - 3, rect.h - 3), 1)

        inner = pygame.Rect(8, 8, max(0, rect.w - 16), max(0, rect.h - 16))
        if inner.w > 0 and inner.h > 0:
            pygame.draw.rect(panel, accent, inner, 1)
            deco_w = min(18, max(8, rect.w // 18))
            deco_h = 5
            deco_y = 10
            pygame.draw.rect(panel, border_light, pygame.Rect(14, deco_y, deco_w, deco_h))
            pygame.draw.rect(panel, border_light, pygame.Rect(rect.w - 14 - deco_w, deco_y, deco_w, deco_h))
            pygame.draw.rect(panel, border_light, pygame.Rect(14, rect.h - deco_y - deco_h, deco_w, deco_h))
            pygame.draw.rect(panel, border_light, pygame.Rect(rect.w - 14 - deco_w, rect.h - deco_y - deco_h, deco_w, deco_h))

        dst.blit(panel, rect.topleft)

    def draw_panel(self, dst: pygame.Surface, rect: pygame.Rect) -> None:
        self._draw_symmetric_panel(
            dst, rect,
            fill_top=(46, 54, 70),
            fill_bottom=(28, 34, 46),
            border_light=(118, 128, 148),
            border_dark=(8, 12, 18),
            accent=(84, 92, 108),
        )

    def draw_parchment_panel(self, dst: pygame.Surface, rect: pygame.Rect) -> None:
        self._draw_symmetric_panel(
            dst, rect,
            fill_top=(198, 178, 136),
            fill_bottom=(166, 144, 102),
            border_light=(230, 214, 180),
            border_dark=(92, 70, 44),
            accent=(150, 126, 88),
        )

    def draw_label_panel(self, dst: pygame.Surface, rect: pygame.Rect) -> None:
        self._draw_symmetric_panel(
            dst, rect,
            fill_top=(62, 70, 86),
            fill_bottom=(42, 48, 60),
            border_light=(132, 142, 160),
            border_dark=(10, 14, 20),
            accent=(92, 102, 118),
        )


    def draw_headered_panel(
        self,
        dst: pygame.Surface,
        rect: pygame.Rect,
        title: str,
        title_font: pygame.font.Font,
        title_color,
        shadow_color,
    ) -> pygame.Rect:
        # external steel frame
        self._draw_symmetric_panel(
            dst, rect,
            fill_top=(34, 42, 58),
            fill_bottom=(20, 26, 38),
            border_light=(120, 132, 154),
            border_dark=(6, 10, 16),
            accent=(70, 82, 98),
        )

        inner = pygame.Rect(rect.x + 10, rect.y + 10, rect.w - 20, rect.h - 20)
        self._draw_symmetric_panel(
            dst, inner,
            fill_top=(40, 48, 64),
            fill_bottom=(24, 30, 42),
            border_light=(134, 146, 168),
            border_dark=(10, 14, 20),
            accent=(86, 96, 112),
        )

        header = pygame.Rect(inner.x + 8, inner.y + 8, inner.w - 16, 32)
        self._draw_symmetric_panel(
            dst, header,
            fill_top=(56, 66, 86),
            fill_bottom=(38, 46, 60),
            border_light=(146, 156, 176),
            border_dark=(12, 16, 24),
            accent=(98, 108, 126),
        )

        title_surf = title_font.render(title, True, title_color)
        title_shadow = title_font.render(title, True, shadow_color)
        tx = header.centerx - title_surf.get_width() // 2
        ty = header.centery - title_surf.get_height() // 2 - 1

        line_y = header.centery
        left_start = header.x + 18
        left_end = tx - 16
        right_start = tx + title_surf.get_width() + 16
        right_end = header.right - 18
        if left_end - left_start > 20:
            pygame.draw.line(dst, (154, 164, 182), (left_start, line_y), (left_end, line_y), 1)
            pygame.draw.line(dst, (74, 84, 98), (left_start + 10, line_y + 2), (left_end - 10, line_y + 2), 1)
        if right_end - right_start > 20:
            pygame.draw.line(dst, (154, 164, 182), (right_start, line_y), (right_end, line_y), 1)
            pygame.draw.line(dst, (74, 84, 98), (right_start + 10, line_y + 2), (right_end - 10, line_y + 2), 1)

        dst.blit(title_shadow, (tx + 2, ty + 2))
        dst.blit(title_surf, (tx, ty))

        return pygame.Rect(inner.x + 10, header.bottom + 10, inner.w - 20, inner.h - 52)

    def draw_button(self, dst: pygame.Surface, rect: pygame.Rect, style: str, text: str,
                    font: pygame.font.Font, active: bool = False) -> None:
        base = self.scaled(f"btn_{style}_{rect.w}_{rect.h}", self.buttons[style], (rect.w, rect.h))
        dst.blit(base, rect)
        if active:
            glow = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            pygame.draw.rect(glow, (236, 204, 90, 70), glow.get_rect(), 2)
            dst.blit(glow, rect)
        shadow = font.render(text, True, (230, 235, 240))
        surf = font.render(text, True, (10, 16, 22))
        tx = rect.centerx - surf.get_width() // 2
        ty = rect.centery - surf.get_height() // 2 - 1
        dst.blit(shadow, (tx, ty + 1))
        dst.blit(surf, (tx, ty))

    def ship_surface(self, size: int, direction: Direction) -> pygame.Surface:
        if direction == Direction.HORIZONTAL:
            return self.scaled(
                f"ship_h_{size}",
                self.ship_h[size],
                (size * CELL_SIZE - 2, CELL_SIZE - 2),
            )
        return self.scaled(
            f"ship_v_{size}",
            self.ship_v[size],
            (CELL_SIZE - 2, size * CELL_SIZE - 2),
        )

    def effect_surface(self, kind: str) -> pygame.Surface:
        surf = self.hit if kind == "hit" else self.miss
        return self.scaled(kind, surf, (CELL_SIZE, CELL_SIZE))


