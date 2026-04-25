import sys
from typing import List, Optional, Tuple

import pygame

from core import (
    AI,
    Assets,
    BOARD_GAP,
    BOARD_SIZE,
    Button,
    CELL_SIZE,
    Dir,
    FPS,
    LEFT_MARGIN,
    SHIP_SIZES,
    Screen,
    TOP_MARGIN,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    Board,
)
from ui import GameUI


class Game:
    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        def choose_font(cands: list[str], size: int, bold: bool = False) -> pygame.font.Font:
            for name in cands:
                path = pygame.font.match_font(name, bold=bold)
                if path:
                    return pygame.font.Font(path, size)
            return pygame.font.Font(None, size)

        self.font_title = choose_font(
            ["tahoma", "arial", "dejavusans"],
            42,
            bold=True,
        )
        self.font_h2 = choose_font(
            ["tahoma", "arial", "dejavusans"],
            31,
            bold=True,
        )
        self.font_btn = choose_font(
            ["trebuchetms", "tahoma", "arial", "dejavusans"],
            24,
            bold=True,
        )
        self.font_text = choose_font(
            ["trebuchetms", "tahoma", "arial", "dejavusans"],
            21,
            bold=True,
        )
        self.font_small = choose_font(
            ["trebuchetms", "tahoma", "arial", "dejavusans"],
            18,
            bold=True,
        )

        self.assets = Assets()
        self.ui = GameUI(self)

        self.left_board_pos = (LEFT_MARGIN, TOP_MARGIN)
        self.right_board_pos = (LEFT_MARGIN + BOARD_SIZE + BOARD_GAP, TOP_MARGIN)

        self.board_p1 = Board()
        self.board_p2 = Board()
        self.ai: Optional[AI] = None

        self.mode: Optional[str] = None
        self.uroven = "medium"
        self.state = Screen.MENU
        self.next_st = Screen.MENU
        self.prev_st = Screen.MENU
        self.per_mes = ""

        self.ochered = 1
        self.set_player = 1
        self.ost_kor: List[int] = []
        self.vib_kor = 0
        self.napr = Dir.HORIZONTAL
        self.err = ""
        self.win: Optional[int] = None

        self.ai_delay = 450
        self.ai_vrem = 0

    def to_menu(self) -> None:
        self.board_p1.clear()
        self.board_p2.clear()
        self.ai = None
        self.mode = None
        self.state = Screen.MENU
        self.next_st = Screen.MENU
        self.prev_st = Screen.MENU
        self.per_mes = ""
        self.ochered = 1
        self.set_player = 1
        self.ost_kor = []
        self.vib_kor = 0
        self.napr = Dir.HORIZONTAL
        self.err = ""
        self.win = None
    def start_game(self, mode: str) -> None:
        self.mode = mode
        self.board_p1.clear()
        self.board_p2.clear()
        self.set_player = 1
        self.ost_kor = SHIP_SIZES.copy()
        self.vib_kor = 0
        self.napr = Dir.HORIZONTAL
        self.err = ""
        self.ochered = 1
        self.win = None
        self.state = Screen.SETUP
        self.ai = AI(self.uroven) if mode == "pve" else None
        if mode == "pve":
            self.board_p2.rand_fleet()
    def tek_pole(self) -> Board:
        return self.board_p1 if self.set_player == 1 else self.board_p2
    def board_for(self, player: int) -> Board:
        return self.board_p1 if player == 1 else self.board_p2
    def pole_vraga(self, player: int) -> Board:
        return self.board_p2 if player == 1 else self.board_p1
    def show_per(self, text: str, next_st: Screen) -> None:
        self.per_mes = text
        self.next_st = next_st
        self.state = Screen.PASS

    # -------------------------
    # Buttons
    # -------------------------
    def menu_buttons(self) -> List[Button]:
        cx = WINDOW_WIDTH // 2
        return [
            Button("pvp", pygame.Rect(cx - 150, 210, 300, 56), "Два игрока", "green"),
            Button("pve", pygame.Rect(cx - 150, 284, 300, 56), "Против компьютера", "orange"),
            Button("easy", pygame.Rect(cx - 180, 392, 110, 48), "Легко", "green"),
            Button("medium", pygame.Rect(cx - 55, 392, 110, 48), "Средне", "yellow"),
            Button("hard", pygame.Rect(cx + 70, 392, 110, 48), "Сложно", "red"),
        ]
    def setup_buttons(self) -> List[Button]:
        panel_x = LEFT_MARGIN + BOARD_SIZE + 28
        panel_w = 360
        base_y = TOP_MARGIN + 280
        return [
            Button("start", pygame.Rect(panel_x, base_y, panel_w, 56), "Начать игру", "green"),
            Button("random", pygame.Rect(panel_x, base_y + 72, 172, 52), "Случайно", "orange"),
            Button("clear", pygame.Rect(panel_x + panel_w - 172, base_y + 72, 172, 52), "Очистить", "purple"),
        ]


    def pause_buttons(self) -> List[Button]:
        cx = WINDOW_WIDTH // 2
        return [
            Button("resume", pygame.Rect(cx - 130, 330, 260, 56), "Продолжить", "green"),
            Button("menu", pygame.Rect(cx - 130, 402, 260, 56), "В главное меню", "orange"),
        ]

    def get_sel_pos(self, remain_panel: pygame.Rect) -> List[Tuple[int, int]]:
        positions: List[Tuple[int, int]] = []
        ix = remain_panel.x + 6
        iy = remain_panel.y + 6
        row_h = 26

        for size in self.ost_kor:
            icon = self.assets.scaled(f"setup_remain_{size}", self.assets.ship_h[size], (size * 16, 14))
            if ix + icon.get_width() > remain_panel.right - 6:
                ix = remain_panel.x + 6
                iy += row_h
            positions.append((ix, iy))
            ix += icon.get_width() + 10
        return positions

    # -------------------------
    # Main loop
    # -------------------------
    def run(self) -> None:
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    self.key_down(event.key)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.click(event.pos)

            self.update()
            self.ui.draw()
            pygame.display.flip()
    def key_down(self, key: int) -> None:
        if self.state == Screen.PASS:
            self.state = self.next_st
            return

        if self.state == Screen.PAUSE:
            if key == pygame.K_ESCAPE:
                self.state = self.prev_st
            return

        if key == pygame.K_ESCAPE:
            if self.state in (Screen.SETUP, Screen.BATTLE):
                self.prev_st = self.state
                self.state = Screen.PAUSE
            elif self.state == Screen.GAME_OVER:
                self.to_menu()
            else:
                self.to_menu()
            return

        if self.state == Screen.GAME_OVER and key == pygame.K_r:
            self.to_menu()
            return

        if self.state == Screen.SETUP and key == pygame.K_r:
            self.napr = Dir.VERTICAL if self.napr == Dir.HORIZONTAL else Dir.HORIZONTAL

    def click(self, pos: Tuple[int, int]) -> None:
        if self.state == Screen.MENU:
            self.menu_click(pos)
        elif self.state == Screen.SETUP:
            self.setup_click(pos)
        elif self.state == Screen.BATTLE:
            self.battle_click(pos)
        elif self.state == Screen.PAUSE:
            self.pause_click(pos)

    def pause_click(self, pos: Tuple[int, int]) -> None:
        for btn in self.pause_buttons():
            if not btn.rect.collidepoint(pos):
                continue
            if btn.key == "resume":
                self.state = self.prev_st
            elif btn.key == "menu":
                self.to_menu()
            return

    def menu_click(self, pos: Tuple[int, int]) -> None:
        for btn in self.menu_buttons():
            if not btn.rect.collidepoint(pos):
                continue
            if btn.key in ("pvp", "pve"):
                self.start_game(btn.key)
            else:
                self.uroven = btn.key
    def setup_click(self, pos: Tuple[int, int]) -> None:
        board = self.tek_pole()

        for btn in self.setup_buttons():
            if not btn.rect.collidepoint(pos):
                continue
            if btn.key == "random":
                board.rand_fleet()
                self.ost_kor = []
                self.vib_kor = 0
                self.err = ""
                return
            if btn.key == "clear":
                board.clear()
                self.ost_kor = SHIP_SIZES.copy()
                self.vib_kor = 0
                self.napr = Dir.HORIZONTAL
                self.err = ""
                return
            if btn.key == "start" and not self.ost_kor:
                if self.mode == "pvp" and self.set_player == 1:
                    self.set_player = 2
                    self.ost_kor = SHIP_SIZES.copy()
                    self.vib_kor = 0
                    self.napr = Dir.HORIZONTAL
                    self.err = ""
                    self.show_per("Передайте экран Игроку 2 для расстановки", Screen.SETUP)
                    return
                self.ochered = 1
                if self.mode == "pvp":
                    self.show_per("Передайте экран Игроку 1", Screen.BATTLE)
                else:
                    self.state = Screen.BATTLE
                return

        if self.ost_kor:
            res_panel = pygame.Rect(LEFT_MARGIN, TOP_MARGIN + BOARD_SIZE + 12, BOARD_SIZE + 96, 120)
            res_content = pygame.Rect(res_panel.x + 20, res_panel.y + 60, res_panel.w - 40, res_panel.h - 72)
            positions = self.get_sel_pos(res_content)
            for i, size in enumerate(self.ost_kor):
                icon = self.assets.scaled(f"setup_remain_{size}", self.assets.ship_h[size], (size * 16, 14))
                rect = pygame.Rect(positions[i][0] - 4, positions[i][1] - 3, icon.get_width() + 8, icon.get_height() + 6)
                if rect.collidepoint(pos):
                    self.vib_kor = i
                    return

        bx, by = self.left_board_pos
        if bx <= pos[0] < bx + BOARD_SIZE and by <= pos[1] < by + BOARD_SIZE:
            gx = (pos[0] - bx) // CELL_SIZE
            gy = (pos[1] - by) // CELL_SIZE
            self.try_put_ship(gx, gy)
    def try_put_ship(self, gx: int, gy: int) -> None:
        if not self.ost_kor:
            self.err = "Все корабли уже расставлены."
            return
        board = self.tek_pole()
        size = self.ost_kor[self.vib_kor]
        if board.place_ship(size, gx, gy, self.napr):
            self.ost_kor.pop(self.vib_kor)
            self.vib_kor = min(self.vib_kor, max(0, len(self.ost_kor) - 1))
            self.err = ""
        else:
            self.err = "Нельзя поставить корабль здесь."
    def battle_click(self, pos: Tuple[int, int]) -> None:
        if self.mode == "pve" and self.ochered != 1:
            return

        enemy = self.pole_vraga(self.ochered)
        bx, by = self.right_board_pos
        if not (bx <= pos[0] < bx + BOARD_SIZE and by <= pos[1] < by + BOARD_SIZE):
            return

        gx = (pos[0] - bx) // CELL_SIZE
        gy = (pos[1] - by) // CELL_SIZE
        if enemy.shots[gy][gx]:
            return

        hit, _ = enemy.shot(gx, gy)
        if enemy.all_dead():
            self.win = self.ochered
            self.state = Screen.GAME_OVER
            return

        if self.mode == "pvp":
            if not hit:
                self.ochered = 2 if self.ochered == 1 else 1
                self.show_per(f"Передайте экран Игроку {self.ochered}", Screen.BATTLE)
        else:
            if not hit:
                self.ochered = 2
                self.ai_vrem = pygame.time.get_ticks()
    def update(self) -> None:
        if self.mode != "pve" or self.state != Screen.BATTLE or self.ochered != 2 or self.ai is None:
            return
        now = pygame.time.get_ticks()
        if now - self.ai_vrem < self.ai_delay:
            return

        x, y = self.ai.choose_shot(self.board_p1)
        if (x, y) == (-1, -1):
            self.win = 1
            self.state = Screen.GAME_OVER
            return

        hit, dead = self.board_p1.shot(x, y)
        self.ai.proc_res((x, y), hit, dead, self.board_p1)

        if self.board_p1.all_dead():
            self.win = 2
            self.state = Screen.GAME_OVER
            return

        if not hit:
            self.ochered = 1
        self.ai_vrem = now

if __name__ == "__main__":
    Game().run()
