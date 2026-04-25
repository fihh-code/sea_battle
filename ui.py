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
    Screen,
    TOP_MARGIN,
    WHITE,
    TEXT_TITLE,
    TEXT_MAIN,
    TEXT_SUBTLE,
    TEXT_SHADOW,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    YELLOW,
    Dir,
    Board,
    Ship,
    Cell,
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

        if self.state == Screen.MENU:
            self.draw_menu()
        elif self.state == Screen.SETUP:
            self.draw_setup()
        elif self.state == Screen.BATTLE:
            self.draw_battle()
        elif self.state == Screen.PASS:
            self.draw_under_per()
            self.draw_per()
        elif self.state == Screen.PAUSE:
            self.draw_under_pause()
            self.draw_pause()
        elif self.state == Screen.GAME_OVER:
            self.draw_battle()
            self.draw_over()

    def draw_under_per(self) -> None:
        if self.next_st == Screen.SETUP:
            self.draw_setup()
        elif self.next_st == Screen.BATTLE:
            self.draw_battle()
        else:
            self.draw_menu()


    def draw_under_pause(self) -> None:
        if self.prev_st == Screen.SETUP:
            self.draw_setup()
        elif self.prev_st == Screen.BATTLE:
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
            active = btn.key == self.uroven
            self.assets.draw_button(self.screen, btn.rect, btn.style, btn.text, self.font_btn, active=active)

    def draw_setup(self) -> None:
        title_txt = f"РАССТАНОВКА ФЛОТА — ИГРОК {self.set_player}" if self.mode == "pvp" else "РАССТАНОВКА КОРАБЛЕЙ"
        title = self.font_h2.render(title_txt, True, TEXT_TITLE)
        shadow = self.font_h2.render(title_txt, True, TEXT_SHADOW)
        tx = WINDOW_WIDTH // 2 - title.get_width() // 2
        self.screen.blit(shadow, (tx + 2, 24))
        self.screen.blit(title, (tx, 22))

        self.draw_board(self.tek_pole(), self.left_board_pos, show_ship=True, hide_live=False, preview=True)

        rules_panel = pygame.Rect(LEFT_MARGIN + BOARD_SIZE + 28, TOP_MARGIN, 360, 240)
        rules_cont = self.assets.draw_headered_panel(
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
            self.screen.blit(surf, (rules_cont.x + 6, rules_cont.y + 4 + i * 21))

        st_y = rules_cont.y + 102
        if self.err:
            surf = self.font_small.render(self.err, True, (224, 174, 108))
        elif self.ost_kor:
            size = self.ost_kor[self.vib_kor]
            direction = "ГОРИЗОНТАЛЬНО" if self.napr == Dir.HORIZONTAL else "ВЕРТИКАЛЬНО"
            surf = self.font_small.render(f"ВЫБРАН: {size} КЛ., {direction}", True, TEXT_MAIN)
        else:
            surf = self.font_small.render("ФЛОТ ГОТОВ — МОЖНО НАЧИНАТЬ", True, TEXT_MAIN)
        self.screen.blit(surf, (rules_cont.x + 6, st_y))

        res_panel = pygame.Rect(LEFT_MARGIN, TOP_MARGIN + BOARD_SIZE + 12, BOARD_SIZE + 96, 120)
        res_content = self.assets.draw_headered_panel(
            self.screen, res_panel, "РЕЗЕРВ", self.font_text, TEXT_TITLE, TEXT_SHADOW
        )

        positions = self.get_sel_pos(res_content)
        for i, size in enumerate(self.ost_kor):
            ix, iy = positions[i]
            icon = self.assets.scaled(f"setup_remain_{size}", self.assets.ship_h[size], (size * 16, 14))
            self.screen.blit(icon, (ix, iy))
            if i == self.vib_kor:
                sel = pygame.Rect(ix - 4, iy - 3, icon.get_width() + 8, icon.get_height() + 6)
                pygame.draw.rect(self.screen, YELLOW, sel, 2)

        for btn in self.setup_buttons():
            active = btn.key == "start" and not self.ost_kor
            self.assets.draw_button(self.screen, btn.rect, btn.style, btn.text, self.font_btn, active=active)

    def draw_battle(self) -> None:
        if self.mode == "pve":
            title_txt = "ВАШ ХОД" if self.ochered == 1 else "ХОД КОМПЬЮТЕРА"
            l_board = self.board_p1
            r_board = self.board_p2
        else:
            title_txt = f"ХОД ИГРОКА {self.ochered}"
            l_board = self.board_for(self.ochered)
            r_board = self.pole_vraga(self.ochered)

        self.draw_head(title_txt, self.mode == "pve" and self.ochered != 1)

        self.draw_board(l_board, self.left_board_pos, show_ship=True, hide_live=False, preview=False)
        self.draw_board(r_board, self.right_board_pos, show_ship=True, hide_live=True, preview=False)

        l_label = self.font_text.render("Ваше поле", True, TEXT_MAIN)
        r_label = self.font_text.render("Поле противника", True, TEXT_MAIN)
        l_shadow = self.font_text.render("Ваше поле", True, TEXT_SHADOW)
        r_shadow = self.font_text.render("Поле противника", True, TEXT_SHADOW)

        left_x = self.left_board_pos[0]
        left_y = self.left_board_pos[1] - 30
        right_x = self.right_board_pos[0]
        right_y = self.right_board_pos[1] - 30
        self.screen.blit(l_shadow, (left_x + 2, left_y + 2))
        self.screen.blit(r_shadow, (right_x + 2, right_y + 2))
        self.screen.blit(l_label, (left_x, left_y))
        self.screen.blit(r_label, (right_x, right_y))

        l_live = [ship for ship in l_board.ships if not ship.dead]
        r_live = [ship for ship in r_board.ships if not ship.dead]

        stat_panel = pygame.Rect(LEFT_MARGIN, TOP_MARGIN + BOARD_SIZE + 16, WINDOW_WIDTH - LEFT_MARGIN * 2, 166)
        self.assets.draw_panel(self.screen, stat_panel)

        l_box = pygame.Rect(self.left_board_pos[0], stat_panel.y + 8, 370, 150)
        r_box = pygame.Rect(self.right_board_pos[0], stat_panel.y + 8, 370, 150)

        l_cont = self.assets.draw_headered_panel(
            self.screen, l_box, "РЕЗЕРВ", self.font_text, TEXT_TITLE, TEXT_SHADOW
        )
        r_cont = self.assets.draw_headered_panel(
            self.screen, r_box, "РЕЗЕРВ ПРОТИВНИКА", self.font_text, TEXT_TITLE, TEXT_SHADOW
        )

        self.draw_icons(l_cont, l_live, "reserve_left")
        self.draw_icons(r_cont, r_live, "reserve_right")

    def draw_icons(self, content_rect: pygame.Rect, live_ships, cache_pref: str) -> None:
        x = content_rect.x + 8
        y = content_rect.y + 8
        row_h = 30
        cur_row = 0

        for ship in sorted(live_ships, key=lambda s: (-s.size, s.positions[0][1], s.positions[0][0])):
            icon = self.assets.scaled(
                f"{cache_pref}_{ship.size}",
                self.assets.ship_h[ship.size],
                (ship.size * 17, 15),
            )
            if x + icon.get_width() > content_rect.right - 8:
                cur_row += 1
                x = content_rect.x + 8
                y = content_rect.y + 8 + cur_row * row_h
            if cur_row > 1:
                break
            self.screen.blit(icon, (x, y))
            x += icon.get_width() + 14


    def draw_head(self, title_txt: str, show_hour: bool) -> None:
        text = self.font_h2.render(title_txt, True, TEXT_TITLE)
        shadow = self.font_h2.render(title_txt, True, TEXT_SHADOW)

        icon_w = 0
        gap = 10
        if show_hour:
            icon_w = 18

        total_w = text.get_width() + (icon_w + gap if show_hour else 0)
        start_x = WINDOW_WIDTH // 2 - total_w // 2
        y = 28

        if show_hour:
            self.draw_hour(start_x, y + 4)
            start_x += icon_w + gap

        self.screen.blit(shadow, (start_x + 2, y + 2))
        self.screen.blit(text, (start_x, y))

    def draw_hour(self, x: int, y: int) -> None:
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

    def draw_board(self, board: Board, origin: Tuple[int, int], show_ship: bool,
                   hide_live: bool, preview: bool) -> None:
        ox, oy = origin
        b_rect = pygame.Rect(ox - 4, oy - 4, BOARD_SIZE + 8, BOARD_SIZE + 8)
        self.assets.draw_panel(self.screen, b_rect)

        water_tile = self.assets.scaled("water_cell", self.assets.water, (CELL_SIZE, CELL_SIZE))
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                self.screen.blit(water_tile, rect)

        if show_ship:
            for ship in board.ships:
                if hide_live and not ship.dead:
                    continue
                self.draw_ship(ship, ox, oy)

        hit_fx = self.assets.effect_surface("hit")
        miss_fx = self.assets.effect_surface("miss")
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                state = board.grid[y][x]
                if state == Cell.MISS:
                    self.screen.blit(miss_fx, rect)
                elif state in (Cell.HIT, Cell.DESTROYED):
                    self.screen.blit(hit_fx, rect)
                    if state == Cell.DESTROYED:
                        shade = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                        shade.fill((0, 0, 0, 70))
                        self.screen.blit(shade, rect)

                pygame.draw.rect(self.screen, GRID_BLUE, rect, 1)

        if preview and self.state == Screen.SETUP and self.ost_kor:
            mx, my = pygame.mouse.get_pos()
            if ox <= mx < ox + BOARD_SIZE and oy <= my < oy + BOARD_SIZE:
                gx = (mx - ox) // CELL_SIZE
                gy = (my - oy) // CELL_SIZE
                size = self.ost_kor[self.vib_kor]
                cells = [(gx + i, gy) if self.napr == Dir.HORIZONTAL else (gx, gy + i) for i in range(size)]
                valid = all(0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE for x, y in cells) and board.can_place(cells)
                color = GREEN if valid else RED
                for x, y in cells:
                    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                        rect = pygame.Rect(ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                        pygame.draw.rect(self.screen, color, rect, 3)

    def draw_ship(self, ship: Ship, ox: int, oy: int) -> None:
        direction = Dir.HORIZONTAL
        if len(ship.positions) > 1 and ship.positions[0][0] == ship.positions[1][0]:
            direction = Dir.VERTICAL
        surf = self.assets.ship_surface(ship.size, direction)
        x0, y0 = ship.positions[0]
        self.screen.blit(surf, (ox + x0 * CELL_SIZE + 1, oy + y0 * CELL_SIZE + 1))

    def draw_per(self) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY)
        self.screen.blit(overlay, (0, 0))
        panel = pygame.Rect(WINDOW_WIDTH // 2 - 250, WINDOW_HEIGHT // 2 - 90, 500, 180)
        self.assets.draw_panel(self.screen, panel)
        text = self.font_h2.render(self.per_mes, True, TEXT_TITLE)
        hint = self.font_text.render("Нажмите любую клавишу", True, TEXT_MAIN)
        self.screen.blit(text, (panel.centerx - text.get_width() // 2, panel.y + 42))
        self.screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.y + 94))


    def draw_pause(self) -> None:
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

    def draw_over(self) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY)
        self.screen.blit(overlay, (0, 0))
        panel = pygame.Rect(WINDOW_WIDTH // 2 - 260, WINDOW_HEIGHT // 2 - 100, 520, 200)
        self.assets.draw_panel(self.screen, panel)

        if self.mode == "pve":
            message = "Вы победили!" if self.win == 1 else "Компьютер победил!"
        else:
            message = f"Победил игрок {self.win}!"

        title = self.font_title.render(message, True, YELLOW)
        hint = self.font_text.render("ESC — вернуться в меню", True, TEXT_MAIN)
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 44))
        self.screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.y + 112))
