from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

import pygame

from core import (
    BOARD_SIZE,
    CELL_SIZE,
    GREEN,
    GRID_BLUE,
    GRID_SIZE,
    LEFT_MARGIN,
    OVERLAY,
    RED,
    ScreenState,
    TOP_MARGIN,
    WHITE,
    TEXT_TITLE,
    TEXT_MAIN,
    TEXT_SUBTLE,
    TEXT_SHADOW,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    YELLOW,
    Direction,
    Board,
    Ship,
    CellState,
)

if TYPE_CHECKING:
    from control import Game


class GameUI:
    def __init__(self, game: "Game") -> None:
        self.game = game

    def __getattr__(self, name):
        return getattr(self.game, name)

    def draw(self) -> None:
        self.assets.tile(self.screen, self.assets.background, self.screen.get_rect())

        if self.state == ScreenState.MENU:
            self.draw_menu()
        elif self.state == ScreenState.SETUP:
            self.draw_setup()
        elif self.state == ScreenState.BATTLE:
            self.draw_battle()
        elif self.state == ScreenState.PASS:
            self.draw_under_pass()
            self.draw_pass_overlay()
        elif self.state == ScreenState.PAUSE:
            self.draw_under_pause()
            self.draw_pause_overlay()
        elif self.state == ScreenState.GAME_OVER:
            self.draw_battle()
            self.draw_game_over()

    def draw_under_pass(self) -> None:
        if self.pending_state == ScreenState.SETUP:
            self.draw_setup()
        elif self.pending_state == ScreenState.BATTLE:
            self.draw_battle()
        else:
            self.draw_menu()


    def draw_under_pause(self) -> None:
        if self.previous_state == ScreenState.SETUP:
            self.draw_setup()
        elif self.previous_state == ScreenState.BATTLE:
            self.draw_battle()
        else:
            self.draw_menu()

    def draw_menu(self) -> None:
        title = self.font_title.render("МОРСКОЙ БOЙ", True, TEXT_TITLE)
        help1 = self.font_small.render("ESC — в меню. В расстановке R поворачивает корабль.", True, TEXT_SUBTLE)

        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 50))
        self.screen.blit(help1, (WINDOW_WIDTH // 2 - help1.get_width() // 2, 132))

        panel = pygame.Rect(WINDOW_WIDTH // 2 - 250, 180, 500, 300)
        self.assets.draw_panel(self.screen, panel)

        label = self.font_text.render("Сложность для игры против компьютера", True, TEXT_MAIN)
        self.screen.blit(label, (WINDOW_WIDTH // 2 - label.get_width() // 2, 354))

        for btn in self.menu_buttons():
            active = btn.key == self.difficulty
            self.assets.draw_button(self.screen, btn.rect, btn.style, btn.text, self.font_btn, active=active)

    def draw_setup(self) -> None:
        title_text = f"РАССТАНОВКА ФЛОТА — ИГРОК {self.setup_player}" if self.mode == "pvp" else "РАССТАНОВКА КОРАБЛЕЙ"
        title = self.font_h2.render(title_text, True, TEXT_TITLE)
        shadow = self.font_h2.render(title_text, True, TEXT_SHADOW)
        tx = WINDOW_WIDTH // 2 - title.get_width() // 2
        self.screen.blit(shadow, (tx + 2, 24))
        self.screen.blit(title, (tx, 22))

        self.draw_board(self.current_setup_board(), self.left_board_pos, show_ships=True, hide_live_ships=False, preview=True)

        rules_panel = pygame.Rect(LEFT_MARGIN + BOARD_SIZE + 28, TOP_MARGIN, 360, 240)
        rules_content = self.assets.draw_headered_panel(
            self.screen, rules_panel, "ПРАВИЛА", self.font_text, TEXT_TITLE, TEXT_SHADOW
        )

        rules = [
            "R — повернуть корабль",
            "ЛКМ — поставить корабль",
            "Клик по резерву — выбрать",
            "Случайно — авторасстановка",
        ]
        for i, line in enumerate(rules):
            surf = self.font_small.render(line, True, TEXT_MAIN)
            self.screen.blit(surf, (rules_content.x + 6, rules_content.y + 4 + i * 21))

        state_y = rules_content.y + 102
        if self.error_text:
            surf = self.font_small.render(self.error_text, True, (224, 174, 108))
        elif self.remaining_ships:
            size = self.remaining_ships[self.selected_ship_index]
            direction = "ГОРИЗОНТАЛЬНО" if self.ship_direction == Direction.HORIZONTAL else "ВЕРТИКАЛЬНО"
            surf = self.font_small.render(f"ВЫБРАН: {size} КЛ., {direction}", True, TEXT_MAIN)
        else:
            surf = self.font_small.render("ФЛОТ ГОТОВ — МОЖНО НАЧИНАТЬ", True, TEXT_MAIN)
        self.screen.blit(surf, (rules_content.x + 6, state_y))

        reserve_panel = pygame.Rect(LEFT_MARGIN, TOP_MARGIN + BOARD_SIZE + 12, BOARD_SIZE + 96, 120)
        reserve_content = self.assets.draw_headered_panel(
            self.screen, reserve_panel, "РЕЗЕРВ", self.font_text, TEXT_TITLE, TEXT_SHADOW
        )

        positions = self.get_setup_selector_positions(reserve_content)
        for i, size in enumerate(self.remaining_ships):
            icon_x, icon_y = positions[i]
            icon = self.assets.scaled(f"setup_remain_{size}", self.assets.ship_h[size], (size * 16, 14))
            self.screen.blit(icon, (icon_x, icon_y))
            if i == self.selected_ship_index:
                sel = pygame.Rect(icon_x - 4, icon_y - 3, icon.get_width() + 8, icon.get_height() + 6)
                pygame.draw.rect(self.screen, YELLOW, sel, 2)

        for btn in self.setup_buttons():
            active = btn.key == "start" and not self.remaining_ships
            self.assets.draw_button(self.screen, btn.rect, btn.style, btn.text, self.font_btn, active=active)

    def draw_battle(self) -> None:
        if self.mode == "pve":
            title_text = "ВАШ ХОД" if self.turn_owner == 1 else "ХОД КОМПЬЮТЕРА"
            left_board = self.board_p1
            right_board = self.board_p2
        else:
            title_text = f"ХОД ИГРОКА {self.turn_owner}"
            left_board = self.board_for(self.turn_owner)
            right_board = self.enemy_board_for(self.turn_owner)

        self.draw_turn_header(title_text, self.mode == "pve" and self.turn_owner != 1)

        self.draw_board(left_board, self.left_board_pos, show_ships=True, hide_live_ships=False, preview=False)
        self.draw_board(right_board, self.right_board_pos, show_ships=True, hide_live_ships=True, preview=False)

        left_label = self.font_text.render("Ваше поле", True, TEXT_MAIN)
        right_label = self.font_text.render("Поле противника", True, TEXT_MAIN)
        left_shadow = self.font_text.render("Ваше поле", True, TEXT_SHADOW)
        right_shadow = self.font_text.render("Поле противника", True, TEXT_SHADOW)

        left_x = self.left_board_pos[0]
        left_y = self.left_board_pos[1] - 30
        right_x = self.right_board_pos[0]
        right_y = self.right_board_pos[1] - 30
        self.screen.blit(left_shadow, (left_x + 2, left_y + 2))
        self.screen.blit(right_shadow, (right_x + 2, right_y + 2))
        self.screen.blit(left_label, (left_x, left_y))
        self.screen.blit(right_label, (right_x, right_y))

        left_alive = [ship for ship in left_board.ships if not ship.destroyed]
        right_alive = [ship for ship in right_board.ships if not ship.destroyed]

        stats_panel = pygame.Rect(LEFT_MARGIN, TOP_MARGIN + BOARD_SIZE + 16, WINDOW_WIDTH - LEFT_MARGIN * 2, 166)
        self.assets.draw_panel(self.screen, stats_panel)

        left_box = pygame.Rect(self.left_board_pos[0], stats_panel.y + 8, 370, 150)
        right_box = pygame.Rect(self.right_board_pos[0], stats_panel.y + 8, 370, 150)

        left_content = self.assets.draw_headered_panel(
            self.screen, left_box, "РЕЗЕРВ", self.font_text, TEXT_TITLE, TEXT_SHADOW
        )
        right_content = self.assets.draw_headered_panel(
            self.screen, right_box, "РЕЗЕРВ ПРОТИВНИКА", self.font_text, TEXT_TITLE, TEXT_SHADOW
        )

        self.draw_reserve_icons(left_content, left_alive, "reserve_left")
        self.draw_reserve_icons(right_content, right_alive, "reserve_right")

    def draw_reserve_icons(self, content_rect: pygame.Rect, alive_ships, cache_prefix: str) -> None:
        x = content_rect.x + 8
        y = content_rect.y + 8
        row_height = 30
        current_row = 0

        for ship in sorted(alive_ships, key=lambda s: (-s.size, s.positions[0][1], s.positions[0][0])):
            icon = self.assets.scaled(
                f"{cache_prefix}_{ship.size}",
                self.assets.ship_h[ship.size],
                (ship.size * 17, 15),
            )
            if x + icon.get_width() > content_rect.right - 8:
                current_row += 1
                x = content_rect.x + 8
                y = content_rect.y + 8 + current_row * row_height
            if current_row > 1:
                break
            self.screen.blit(icon, (x, y))
            x += icon.get_width() + 14


    def draw_turn_header(self, title_text: str, show_hourglass: bool) -> None:
        text = self.font_h2.render(title_text, True, TEXT_TITLE)
        shadow = self.font_h2.render(title_text, True, TEXT_SHADOW)

        icon_w = 0
        gap = 10
        if show_hourglass:
            icon_w = 18

        total_w = text.get_width() + (icon_w + gap if show_hourglass else 0)
        start_x = WINDOW_WIDTH // 2 - total_w // 2
        y = 28

        if show_hourglass:
            self.draw_hourglass_icon(start_x, y + 4)
            start_x += icon_w + gap

        self.screen.blit(shadow, (start_x + 2, y + 2))
        self.screen.blit(text, (start_x, y))

    def draw_hourglass_icon(self, x: int, y: int) -> None:
        c1 = (214, 224, 236)
        c2 = (150, 164, 182)
        c3 = (68, 78, 96)
        pygame.draw.line(self.screen, c1, (x + 2, y), (x + 14, y), 2)
        pygame.draw.line(self.screen, c1, (x + 2, y + 14), (x + 14, y + 14), 2)
        pygame.draw.line(self.screen, c2, (x + 3, y + 1), (x + 8, y + 7), 1)
        pygame.draw.line(self.screen, c2, (x + 13, y + 1), (x + 8, y + 7), 1)
        pygame.draw.line(self.screen, c2, (x + 3, y + 13), (x + 8, y + 7), 1)
        pygame.draw.line(self.screen, c2, (x + 13, y + 13), (x + 8, y + 7), 1)
        pygame.draw.line(self.screen, c3, (x + 8, y + 2), (x + 8, y + 12), 1)

    def draw_board(self, board: Board, origin: Tuple[int, int], show_ships: bool,
                   hide_live_ships: bool, preview: bool) -> None:
        ox, oy = origin
        board_rect = pygame.Rect(ox - 4, oy - 4, BOARD_SIZE + 8, BOARD_SIZE + 8)
        self.assets.draw_panel(self.screen, board_rect)

        water_tile = self.assets.scaled("water_cell", self.assets.water, (CELL_SIZE, CELL_SIZE))
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                self.screen.blit(water_tile, rect)

        if show_ships:
            for ship in board.ships:
                if hide_live_ships and not ship.destroyed:
                    continue
                self.draw_ship(ship, ox, oy)

        hit_fx = self.assets.effect_surface("hit")
        miss_fx = self.assets.effect_surface("miss")
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                state = board.grid[y][x]
                if state == CellState.MISS:
                    self.screen.blit(miss_fx, rect)
                elif state in (CellState.HIT, CellState.DESTROYED):
                    self.screen.blit(hit_fx, rect)
                    if state == CellState.DESTROYED:
                        shade = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                        shade.fill((0, 0, 0, 70))
                        self.screen.blit(shade, rect)

                pygame.draw.rect(self.screen, GRID_BLUE, rect, 1)

        if preview and self.state == ScreenState.SETUP and self.remaining_ships:
            mx, my = pygame.mouse.get_pos()
            if ox <= mx < ox + BOARD_SIZE and oy <= my < oy + BOARD_SIZE:
                gx = (mx - ox) // CELL_SIZE
                gy = (my - oy) // CELL_SIZE
                size = self.remaining_ships[self.selected_ship_index]
                cells = [(gx + i, gy) if self.ship_direction == Direction.HORIZONTAL else (gx, gy + i) for i in range(size)]
                valid = all(0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE for x, y in cells) and board.can_place(cells)
                color = GREEN if valid else RED
                for x, y in cells:
                    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                        rect = pygame.Rect(ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                        pygame.draw.rect(self.screen, color, rect, 3)

    def draw_ship(self, ship: Ship, ox: int, oy: int) -> None:
        direction = Direction.HORIZONTAL
        if len(ship.positions) > 1 and ship.positions[0][0] == ship.positions[1][0]:
            direction = Direction.VERTICAL
        surf = self.assets.ship_surface(ship.size, direction)
        x0, y0 = ship.positions[0]
        self.screen.blit(surf, (ox + x0 * CELL_SIZE + 1, oy + y0 * CELL_SIZE + 1))

    def draw_pass_overlay(self) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY)
        self.screen.blit(overlay, (0, 0))
        panel = pygame.Rect(WINDOW_WIDTH // 2 - 250, WINDOW_HEIGHT // 2 - 90, 500, 180)
        self.assets.draw_panel(self.screen, panel)
        text = self.font_h2.render(self.pass_message, True, TEXT_TITLE)
        hint = self.font_text.render("Нажмите любую клавишу", True, TEXT_MAIN)
        self.screen.blit(text, (panel.centerx - text.get_width() // 2, panel.y + 42))
        self.screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.y + 94))


    def draw_pause_overlay(self) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY)
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(WINDOW_WIDTH // 2 - 230, WINDOW_HEIGHT // 2 - 120, 460, 220)
        self.assets.draw_panel(self.screen, panel)

        title = self.font_title.render("Пауза", True, TEXT_TITLE)
        hint = self.font_small.render("ESC — продолжить игру", True, TEXT_MAIN)
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y +5))
        self.screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.y + 82))

        for btn in self.pause_buttons():
            active = False
            self.assets.draw_button(self.screen, btn.rect, btn.style, btn.text, self.font_btn, active=active)

    def draw_game_over(self) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY)
        self.screen.blit(overlay, (0, 0))
        panel = pygame.Rect(WINDOW_WIDTH // 2 - 260, WINDOW_HEIGHT // 2 - 100, 520, 200)
        self.assets.draw_panel(self.screen, panel)

        if self.mode == "pve":
            message = "Вы победили!" if self.winner == 1 else "Компьютер победил!"
        else:
            message = f"Победил игрок {self.winner}!"

        title = self.font_title.render(message, True, YELLOW)
        hint = self.font_text.render("ESC — вернуться в меню", True, TEXT_MAIN)
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 44))
        self.screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.y + 112))
