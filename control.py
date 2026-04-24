import sys
from typing import List, Optional, Tuple

import pygame

from core import (
    AIPlayer,
    Assets,
    BOARD_GAP,
    BOARD_SIZE,
    Button,
    CELL_SIZE,
    Direction,
    FPS,
    LEFT_MARGIN,
    SHIP_SIZES,
    ScreenState,
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
        def choose_font(candidates: list[str], size: int, bold: bool = False) -> pygame.font.Font:
            for name in candidates:
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
        self.ai: Optional[AIPlayer] = None

        self.mode: Optional[str] = None
        self.difficulty = "medium"
        self.state = ScreenState.MENU
        self.pending_state = ScreenState.MENU
        self.previous_state = ScreenState.MENU
        self.pass_message = ""

        self.turn_owner = 1
        self.setup_player = 1
        self.remaining_ships: List[int] = []
        self.selected_ship_index = 0
        self.ship_direction = Direction.HORIZONTAL
        self.error_text = ""
        self.winner: Optional[int] = None

        self.ai_delay = 450
        self.last_ai_tick = 0

    # -------------------------
    # Flow
    # -------------------------
    def reset_to_menu(self) -> None:
        self.board_p1.clear()
        self.board_p2.clear()
        self.ai = None
        self.mode = None
        self.state = ScreenState.MENU
        self.pending_state = ScreenState.MENU
        self.previous_state = ScreenState.MENU
        self.pass_message = ""
        self.turn_owner = 1
        self.setup_player = 1
        self.remaining_ships = []
        self.selected_ship_index = 0
        self.ship_direction = Direction.HORIZONTAL
        self.error_text = ""
        self.winner = None
    def start_mode(self, mode: str) -> None:
        self.mode = mode
        self.board_p1.clear()
        self.board_p2.clear()
        self.setup_player = 1
        self.remaining_ships = SHIP_SIZES.copy()
        self.selected_ship_index = 0
        self.ship_direction = Direction.HORIZONTAL
        self.error_text = ""
        self.turn_owner = 1
        self.winner = None
        self.state = ScreenState.SETUP
        self.ai = AIPlayer(self.difficulty) if mode == "pve" else None
        if mode == "pve":
            self.board_p2.place_random_fleet()
    def current_setup_board(self) -> Board:
        return self.board_p1 if self.setup_player == 1 else self.board_p2
    def board_for(self, player: int) -> Board:
        return self.board_p1 if player == 1 else self.board_p2
    def enemy_board_for(self, player: int) -> Board:
        return self.board_p2 if player == 1 else self.board_p1
    def show_pass_screen(self, text: str, next_state: ScreenState) -> None:
        self.pass_message = text
        self.pending_state = next_state
        self.state = ScreenState.PASS

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

    def get_setup_selector_positions(self, remain_panel: pygame.Rect) -> List[Tuple[int, int]]:
        positions: List[Tuple[int, int]] = []
        icon_x = remain_panel.x + 6
        icon_y = remain_panel.y + 6
        row_height = 26

        for size in self.remaining_ships:
            icon = self.assets.scaled(f"setup_remain_{size}", self.assets.ship_h[size], (size * 16, 14))
            if icon_x + icon.get_width() > remain_panel.right - 6:
                icon_x = remain_panel.x + 6
                icon_y += row_height
            positions.append((icon_x, icon_y))
            icon_x += icon.get_width() + 10
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
                    self.handle_keydown(event.key)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)

            self.update()
            self.ui.draw()
            pygame.display.flip()
    def handle_keydown(self, key: int) -> None:
        if self.state == ScreenState.PASS:
            self.state = self.pending_state
            return

        if self.state == ScreenState.PAUSE:
            if key == pygame.K_ESCAPE:
                self.state = self.previous_state
            return

        if key == pygame.K_ESCAPE:
            if self.state in (ScreenState.SETUP, ScreenState.BATTLE):
                self.previous_state = self.state
                self.state = ScreenState.PAUSE
            elif self.state == ScreenState.GAME_OVER:
                self.reset_to_menu()
            else:
                self.reset_to_menu()
            return

        if self.state == ScreenState.GAME_OVER and key == pygame.K_r:
            self.reset_to_menu()
            return

        if self.state == ScreenState.SETUP and key == pygame.K_r:
            self.ship_direction = Direction.VERTICAL if self.ship_direction == Direction.HORIZONTAL else Direction.HORIZONTAL

    def handle_click(self, pos: Tuple[int, int]) -> None:
        if self.state == ScreenState.MENU:
            self.handle_menu_click(pos)
        elif self.state == ScreenState.SETUP:
            self.handle_setup_click(pos)
        elif self.state == ScreenState.BATTLE:
            self.handle_battle_click(pos)
        elif self.state == ScreenState.PAUSE:
            self.handle_pause_click(pos)

    def handle_pause_click(self, pos: Tuple[int, int]) -> None:
        for btn in self.pause_buttons():
            if not btn.rect.collidepoint(pos):
                continue
            if btn.key == "resume":
                self.state = self.previous_state
            elif btn.key == "menu":
                self.reset_to_menu()
            return

    def handle_menu_click(self, pos: Tuple[int, int]) -> None:
        for btn in self.menu_buttons():
            if not btn.rect.collidepoint(pos):
                continue
            if btn.key in ("pvp", "pve"):
                self.start_mode(btn.key)
            else:
                self.difficulty = btn.key
    def handle_setup_click(self, pos: Tuple[int, int]) -> None:
        board = self.current_setup_board()

        for btn in self.setup_buttons():
            if not btn.rect.collidepoint(pos):
                continue
            if btn.key == "random":
                board.place_random_fleet()
                self.remaining_ships = []
                self.selected_ship_index = 0
                self.error_text = ""
                return
            if btn.key == "clear":
                board.clear()
                self.remaining_ships = SHIP_SIZES.copy()
                self.selected_ship_index = 0
                self.ship_direction = Direction.HORIZONTAL
                self.error_text = ""
                return
            if btn.key == "start" and not self.remaining_ships:
                if self.mode == "pvp" and self.setup_player == 1:
                    self.setup_player = 2
                    self.remaining_ships = SHIP_SIZES.copy()
                    self.selected_ship_index = 0
                    self.ship_direction = Direction.HORIZONTAL
                    self.error_text = ""
                    self.show_pass_screen("Передайте экран Игроку 2 для расстановки", ScreenState.SETUP)
                    return
                self.turn_owner = 1
                if self.mode == "pvp":
                    self.show_pass_screen("Передайте экран Игроку 1", ScreenState.BATTLE)
                else:
                    self.state = ScreenState.BATTLE
                return

        if self.remaining_ships:
            reserve_panel = pygame.Rect(LEFT_MARGIN, TOP_MARGIN + BOARD_SIZE + 12, BOARD_SIZE + 96, 120)
            reserve_content = pygame.Rect(reserve_panel.x + 20, reserve_panel.y + 60, reserve_panel.w - 40, reserve_panel.h - 72)
            positions = self.get_setup_selector_positions(reserve_content)
            for i, size in enumerate(self.remaining_ships):
                icon = self.assets.scaled(f"setup_remain_{size}", self.assets.ship_h[size], (size * 16, 14))
                rect = pygame.Rect(positions[i][0] - 4, positions[i][1] - 3, icon.get_width() + 8, icon.get_height() + 6)
                if rect.collidepoint(pos):
                    self.selected_ship_index = i
                    return

        bx, by = self.left_board_pos
        if bx <= pos[0] < bx + BOARD_SIZE and by <= pos[1] < by + BOARD_SIZE:
            gx = (pos[0] - bx) // CELL_SIZE
            gy = (pos[1] - by) // CELL_SIZE
            self.try_place_ship(gx, gy)
    def try_place_ship(self, gx: int, gy: int) -> None:
        if not self.remaining_ships:
            self.error_text = "Все корабли уже расставлены."
            return
        board = self.current_setup_board()
        size = self.remaining_ships[self.selected_ship_index]
        if board.place_ship(size, gx, gy, self.ship_direction):
            self.remaining_ships.pop(self.selected_ship_index)
            self.selected_ship_index = min(self.selected_ship_index, max(0, len(self.remaining_ships) - 1))
            self.error_text = ""
        else:
            self.error_text = "Нельзя поставить корабль здесь."
    def handle_battle_click(self, pos: Tuple[int, int]) -> None:
        if self.mode == "pve" and self.turn_owner != 1:
            return

        enemy = self.enemy_board_for(self.turn_owner)
        bx, by = self.right_board_pos
        if not (bx <= pos[0] < bx + BOARD_SIZE and by <= pos[1] < by + BOARD_SIZE):
            return

        gx = (pos[0] - bx) // CELL_SIZE
        gy = (pos[1] - by) // CELL_SIZE
        if enemy.shots[gy][gx]:
            return

        hit, _ = enemy.receive_shot(gx, gy)
        if enemy.all_destroyed():
            self.winner = self.turn_owner
            self.state = ScreenState.GAME_OVER
            return

        if self.mode == "pvp":
            if not hit:
                self.turn_owner = 2 if self.turn_owner == 1 else 1
                self.show_pass_screen(f"Передайте экран Игроку {self.turn_owner}", ScreenState.BATTLE)
        else:
            if not hit:
                self.turn_owner = 2
                self.last_ai_tick = pygame.time.get_ticks()
    def update(self) -> None:
        if self.mode != "pve" or self.state != ScreenState.BATTLE or self.turn_owner != 2 or self.ai is None:
            return
        now = pygame.time.get_ticks()
        if now - self.last_ai_tick < self.ai_delay:
            return

        x, y = self.ai.choose_shot(self.board_p1)
        if (x, y) == (-1, -1):
            self.winner = 1
            self.state = ScreenState.GAME_OVER
            return

        hit, destroyed = self.board_p1.receive_shot(x, y)
        self.ai.process_result((x, y), hit, destroyed, self.board_p1)

        if self.board_p1.all_destroyed():
            self.winner = 2
            self.state = ScreenState.GAME_OVER
            return

        if not hit:
            self.turn_owner = 1
        self.last_ai_tick = now

    # -------------------------
    # Drawing
    # -------------------------


if __name__ == "__main__":
    Game().run()
