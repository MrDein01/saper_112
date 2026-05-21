import pygame
import random
import sys
import json
import os
from enum import Enum

# Инициализация Pygame
pygame.init()


# Константы для разных уровней сложности
class Difficulty(Enum):
    EASY = ("Легкий", 8, 8, 10)
    MEDIUM = ("Средний", 12, 12, 25)
    HARD = ("Сложный", 16, 16, 40)
    EXPERT = ("Эксперт", 20, 20, 60)


class Modifier(Enum):
    NONE = ("Без модификатора", "Обычная игра", None, True)
    SHUFFLE = ("Перемешивание", "Каждые 30с мины меняются местами, флажки остаются", "shuffle", False)
    CHAIN_REACTION = ("Цепная реакция", "Открытие пустой клетки открывает все соседние пустые клетки", "chain_reaction",
                      False)
    TIMER_BOMB = ("Сапёр-сапёр", "Раз в 40с можно обезвредить мину, указав её расположение", "timer_bomb", False)
    MEGA_MINE = ("Мега-мина", "Одна мина занимает 2x2 клетки", "mega_mine", False)
    FREEZE = ("Заморозка", "Каждые 20с нельзя ставить флаги 5с", "freeze", False)
    MIRROR = ("Искажение", "Поле поворачивается на 90° каждые 25 секунд", "mirror", False)
    DARKNESS = ("Темнота", "Видно только клетки вокруг открытых", "darkness", False)


# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (150, 150, 150)
LIGHT_GRAY = (220, 220, 220)
MEDIUM_GRAY = (180, 180, 180)
VERY_LIGHT_GRAY = (235, 235, 235)
WARM_GRAY = (210, 205, 200)
COOL_GRAY = (200, 205, 210)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 200, 0)
LIGHT_GREEN = (144, 238, 144)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
MAROON = (128, 0, 0)
TEAL = (0, 128, 128)
NAVY = (0, 0, 128)
LIGHT_BLUE = (173, 216, 230)
LIGHT_YELLOW = (255, 255, 224)
LIGHT_ORANGE = (255, 200, 150)
LIGHT_RED = (255, 150, 150)
INFO_BLUE = (100, 150, 255)
GOLD = (255, 215, 0)
DARK_BLUE = (0, 0, 50)
DEFUSE_COLOR = (0, 255, 255)
CHAIN_COLOR = (255, 100, 0)
SHUFFLE_COLOR = (255, 255, 0)

# Новые оттенки серого для открытых клеток
REVEALED_LIGHT = (240, 240, 240)
REVEALED_MEDIUM = (225, 225, 225)
REVEALED_DARK = (210, 210, 210)
CELL_BORDER_LIGHT = (250, 250, 250)
CELL_BORDER_DARK = (160, 160, 160)


class RecordsManager:
    def __init__(self):
        self.records_file = "minesweeper_records.json"
        self.records = self.load_records()

    def load_records(self):
        if os.path.exists(self.records_file):
            try:
                with open(self.records_file, "r", encoding="utf-8") as f:
                    records = json.load(f)

                for diff in Difficulty:
                    if diff.name not in records:
                        records[diff.name] = {}

                return records

            except Exception as e:
                print("Ошибка загрузки рекордов:", e)

        return self.get_default_records()

    def get_default_records(self):
        records = {}

        for diff in Difficulty:
            records[diff.name] = {}

        return records

    def save_records(self):
        try:
            with open(self.records_file, "w", encoding="utf-8") as f:
                json.dump(self.records, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print("Ошибка сохранения рекордов:", e)

    def get_record_key(self, modifiers):
        if not modifiers:
            return "NONE"

        return "_".join(sorted([mod.name for mod in modifiers]))

    def update_record(self, difficulty, modifiers, time_value):
        diff_name = difficulty.name
        key = self.get_record_key(modifiers)

        if key not in self.records[diff_name]:
            self.records[diff_name][key] = {
                "time": None,
                "modifiers": [mod.name for mod in modifiers]
            }

        current_record = self.records[diff_name][key]["time"]

        if current_record is None or time_value < current_record:
            self.records[diff_name][key]["time"] = time_value
            self.save_records()
            return True

        return False

    def get_record(self, difficulty, modifiers):
        diff_name = difficulty.name
        key = self.get_record_key(modifiers)

        if key in self.records[diff_name]:
            record_time = self.records[diff_name][key]["time"]

            if record_time is not None:
                return f"{record_time}с"

        return "Нет рекорда"


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.neighbor_mines = 0
        self.is_mega_mine = False
        self.chain_reaction_triggered = False
        self.chain_reaction_glow = 0


class InfoWindow:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.is_visible = False
        self.window_width = 550
        self.window_height = 500
        self.x = (width - self.window_width) // 2
        self.y = (height - self.window_height) // 2

    def toggle(self):
        self.is_visible = not self.is_visible

    def draw(self, screen, font, small_font, tiny_font):
        if not self.is_visible:
            return

        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        window_rect = pygame.Rect(self.x, self.y, self.window_width, self.window_height)
        pygame.draw.rect(screen, WHITE, window_rect)
        pygame.draw.rect(screen, BLACK, window_rect, 3)

        title = font.render("ℹ Горячие клавиши и управление", True, BLACK)
        title_rect = title.get_rect(center=(self.x + self.window_width // 2, self.y + 35))
        screen.blit(title, title_rect)

        pygame.draw.line(screen, BLACK,
                         (self.x + 30, self.y + 65),
                         (self.x + self.window_width - 30, self.y + 65), 2)

        hotkeys = [
            ("Левая кнопка мыши", "Открыть клетку / Обезвредить мину"),
            ("Правая кнопка мыши", "Поставить / убрать флаг"),
            ("Клавиша 1", "Выбрать легкий уровень"),
            ("Клавиша 2", "Выбрать средний уровень"),
            ("Клавиша 3", "Выбрать сложный уровень"),
            ("Клавиша 4", "Выбрать экспертный уровень"),
            ("Клавиша R", "Начать игру заново"),
            ("Клавиша I", "Показать / скрыть это окно"),
            ("Клавиша M", "Открыть меню модификаторов"),
            ("Клавиша Пробел", "Активировать обезвреживание"),
            ("Клавиша ESC", "Закрыть окна / Отменить действие"),
        ]

        y_offset = self.y + 85
        for key, description in hotkeys:
            if (y_offset - self.y - 85) // 32 % 2 == 0:
                row_rect = pygame.Rect(self.x + 20, y_offset - 2, self.window_width - 40, 30)
                pygame.draw.rect(screen, LIGHT_GRAY, row_rect)

            key_text = small_font.render(key, True, INFO_BLUE)
            screen.blit(key_text, (self.x + 40, y_offset))

            dash_text = small_font.render("—", True, BLACK)
            screen.blit(dash_text, (self.x + 280, y_offset))

            desc_text = small_font.render(description, True, BLACK)
            screen.blit(desc_text, (self.x + 310, y_offset))

            y_offset += 36

        pygame.draw.line(screen, BLACK,
                         (self.x + 30, y_offset + 10),
                         (self.x + self.window_width - 30, y_offset + 10), 2)

        y_offset += 25
        info_title = small_font.render("Модификаторы:", True, BLACK)
        screen.blit(info_title, (self.x + 40, y_offset))

        y_offset += 30
        info_texts = [
            "• Цепная реакция: пустые клетки открывают соседние каскадом",
            "• Сапёр-сапёр: обезвреживайте мины вручную",
            "• Искажение: поле поворачивается каждые 25 секунд",
            "• Перемешивание: мины меняются местами, флажки остаются",
        ]

        for info in info_texts:
            info_text = tiny_font.render(info, True, DARK_GRAY)
            screen.blit(info_text, (self.x + 40, y_offset))
            y_offset += 25

        y_offset += 10
        hint_text = small_font.render("Нажмите I, ESC или кликните вне окна чтобы закрыть", True, GRAY)
        hint_rect = hint_text.get_rect(center=(self.x + self.window_width // 2, self.y + self.window_height - 30))
        screen.blit(hint_text, hint_rect)

    def handle_click(self, pos):
        if self.is_visible:
            window_rect = pygame.Rect(self.x, self.y, self.window_width, self.window_height)
            if not window_rect.collidepoint(pos):
                self.is_visible = False


class ModifierMenu:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.is_visible = False
        self.window_width = 650
        self.window_height = 600
        self.x = (width - self.window_width) // 2
        self.y = (height - self.window_height) // 2
        self.selected_modifiers = []

    def toggle(self):
        self.is_visible = not self.is_visible

    def toggle_modifier(self, modifier):
        if modifier == Modifier.NONE:
            self.selected_modifiers = []
        elif modifier in self.selected_modifiers:
            self.selected_modifiers.remove(modifier)
        else:
            if len(self.selected_modifiers) < 3:
                self.selected_modifiers.append(modifier)

    def draw(self, screen, font, small_font, tiny_font, current_modifiers, difficulty):
        if not self.is_visible:
            return

        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        window_rect = pygame.Rect(self.x, self.y, self.window_width, self.window_height)
        pygame.draw.rect(screen, WHITE, window_rect)
        pygame.draw.rect(screen, BLACK, window_rect, 3)

        title = font.render("⚙ Выбор модификаторов (макс. 3)", True, BLACK)
        title_rect = title.get_rect(center=(self.x + self.window_width // 2, self.y + 35))
        screen.blit(title, title_rect)

        if difficulty in [Difficulty.EASY]:
            avail_text = small_font.render("⚠ Модификаторы доступны со среднего уровня!", True, RED)
            avail_rect = avail_text.get_rect(center=(self.x + self.window_width // 2, self.y + 60))
            screen.blit(avail_text, avail_rect)

        pygame.draw.line(screen, BLACK,
                         (self.x + 30, self.y + 75),
                         (self.x + self.window_width - 30, self.y + 75), 2)

        modifiers_list = [
            (Modifier.NONE, "Обычная игра", "Классический сапёр без особенностей"),
            (Modifier.SHUFFLE, "Перемешивание", "Каждые 30с мины меняются местами, флажки сохраняются"),
            (Modifier.CHAIN_REACTION, "Цепная реакция", "Пустые клетки каскадно открывают соседние области"),
            (Modifier.TIMER_BOMB, "Сапёр-сапёр", "Раз в 40с можно обезвредить мину (левый клик по мине)"),
            (Modifier.MEGA_MINE, "Мега-мина", "Одна случайная мина занимает 2x2 клетки"),
            (Modifier.FREEZE, "Заморозка", "Каждые 20 секунд нельзя ставить флаги 5 секунд"),
            (Modifier.MIRROR, "Искажение", "Поле поворачивается на 90° каждые 25 секунд"),
            (Modifier.DARKNESS, "Темнота", "Видно только клетки вокруг открытых"),
        ]

        y_offset = self.y + 90
        button_height = 50
        button_margin = 5

        for mod, name, description in modifiers_list:
            btn_rect = pygame.Rect(self.x + 30, y_offset, self.window_width - 60, button_height)

            is_selected = mod in self.selected_modifiers
            is_current = mod in current_modifiers
            is_disabled = difficulty in [Difficulty.EASY] and mod != Modifier.NONE

            if is_disabled:
                color = LIGHT_RED
                border_color = RED
                border_width = 1
            elif is_selected:
                color = LIGHT_GREEN
                border_color = GREEN
                border_width = 3
            elif is_current and mod == Modifier.NONE and not self.selected_modifiers:
                color = LIGHT_BLUE
                border_color = BLUE
                border_width = 2
            else:
                color = LIGHT_GRAY
                border_color = GRAY
                border_width = 1

            pygame.draw.rect(screen, color, btn_rect)
            pygame.draw.rect(screen, border_color, btn_rect, border_width)

            name_text = small_font.render(name, True, BLACK if not is_disabled else DARK_GRAY)
            screen.blit(name_text, (self.x + 45, y_offset + 5))

            desc_text = tiny_font.render(description, True, DARK_GRAY if not is_disabled else GRAY)
            screen.blit(desc_text, (self.x + 45, y_offset + 28))

            # Чекбокс
            checkbox_x = self.x + self.window_width - 80
            checkbox_y = y_offset + 15
            checkbox_rect = pygame.Rect(checkbox_x, checkbox_y, 20, 20)

            if is_disabled:
                pygame.draw.rect(screen, LIGHT_RED, checkbox_rect)
                pygame.draw.rect(screen, RED, checkbox_rect, 1)
            elif is_selected:
                pygame.draw.rect(screen, GREEN, checkbox_rect)
                pygame.draw.rect(screen, BLACK, checkbox_rect, 2)
                pygame.draw.line(screen, BLACK, (checkbox_x + 4, checkbox_y + 10),
                                 (checkbox_x + 8, checkbox_y + 16), 3)
                pygame.draw.line(screen, BLACK, (checkbox_x + 8, checkbox_y + 16),
                                 (checkbox_x + 16, checkbox_y + 4), 3)
            else:
                pygame.draw.rect(screen, WHITE, checkbox_rect)
                pygame.draw.rect(screen, BLACK, checkbox_rect, 2)

            y_offset += button_height + button_margin

        counter_text = small_font.render(f"Выбрано: {len(self.selected_modifiers)}/3", True, BLACK)
        counter_rect = counter_text.get_rect(center=(self.x + self.window_width // 2, y_offset + 10))
        screen.blit(counter_text, counter_rect)

        button_width = 150
        button_y = self.y + self.window_height - 50

        apply_btn = pygame.Rect(self.x + self.window_width // 2 - button_width - 10, button_y, button_width, 35)
        pygame.draw.rect(screen, GREEN, apply_btn)
        pygame.draw.rect(screen, BLACK, apply_btn, 2)
        apply_text = small_font.render("Применить", True, BLACK)
        apply_text_rect = apply_text.get_rect(center=apply_btn.center)
        screen.blit(apply_text, apply_text_rect)

        cancel_btn = pygame.Rect(self.x + self.window_width // 2 + 10, button_y, button_width, 35)
        pygame.draw.rect(screen, RED, cancel_btn)
        pygame.draw.rect(screen, BLACK, cancel_btn, 2)
        cancel_text = small_font.render("Отмена", True, BLACK)
        cancel_text_rect = cancel_text.get_rect(center=cancel_btn.center)
        screen.blit(cancel_text, cancel_text_rect)

        return apply_btn, cancel_btn


class Minesweeper:
    def __init__(self, difficulty, modifiers, records_manager):
        self.difficulty = difficulty
        self.modifiers = modifiers
        self.records_manager = records_manager
        self.rows = difficulty.value[1]
        self.cols = difficulty.value[2]
        self.mines = difficulty.value[3]
        self.cell_size = 600 // max(self.rows, self.cols)
        self.width = self.cols * self.cell_size
        self.height = self.rows * self.cell_size

        self.grid = [[Cell(row, col) for col in range(self.cols)] for row in range(self.rows)]
        self.game_over = False
        self.win = False
        self.first_click = True
        self.flags_count = self.mines
        self.revealed_count = 0
        self.new_record = False

        # Таймер
        self.start_time = 0
        self.elapsed_time = 0
        self.timer_started = False
        self.final_time = 0

        # Для модификаторов
        self.last_shuffle_time = 0
        self.last_defuse_time = 0
        self.last_freeze_time = 0
        self.last_rotation_time = 0
        self.is_frozen = False
        self.freeze_end_time = 0
        self.mega_mine_cells = []
        self.defuse_available = False
        self.defuse_mode = False
        self.rotation_angle = 0
        self.mines_defused = 0
        self.chain_reaction_cells = []
        self.chain_reaction_timer = 0
        self.shuffle_warning = False  # Предупреждение о перемешивании

    def has_modifier(self, modifier):
        return modifier in self.modifiers

    def place_mines(self, first_row, first_col):
        mines_placed = 0
        mega_mine_pos = None

        if self.has_modifier(Modifier.MEGA_MINE):
            mega_mine_row = random.randint(0, self.rows - 2)
            mega_mine_col = random.randint(0, self.cols - 2)
            mega_mine_pos = (mega_mine_row, mega_mine_col)

            while (mega_mine_row <= first_row <= mega_mine_row + 1 and
                   mega_mine_col <= first_col <= mega_mine_col + 1):
                mega_mine_row = random.randint(0, self.rows - 2)
                mega_mine_col = random.randint(0, self.cols - 2)

            self.mega_mine_cells = []
            for r in range(mega_mine_row, mega_mine_row + 2):
                for c in range(mega_mine_col, mega_mine_col + 2):
                    self.grid[r][c].is_mine = True
                    self.grid[r][c].is_mega_mine = True
                    self.mega_mine_cells.append((r, c))
                    mines_placed += 1

        while mines_placed < self.mines:
            row = random.randint(0, self.rows - 1)
            col = random.randint(0, self.cols - 1)

            if (row == first_row and col == first_col) or \
                    (abs(row - first_row) <= 1 and abs(col - first_col) <= 1):
                continue

            if self.has_modifier(Modifier.MEGA_MINE) and mega_mine_pos:
                if (mega_mine_pos[0] <= row <= mega_mine_pos[0] + 1 and
                        mega_mine_pos[1] <= col <= mega_mine_pos[1] + 1):
                    continue

            if not self.grid[row][col].is_mine:
                self.grid[row][col].is_mine = True
                mines_placed += 1

        self.calculate_numbers()

    def calculate_numbers(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if not self.grid[row][col].is_mine:
                    count = 0
                    for r in range(max(0, row - 1), min(self.rows, row + 2)):
                        for c in range(max(0, col - 1), min(self.cols, col + 2)):
                            if self.grid[r][c].is_mine:
                                count += 1
                    self.grid[row][col].neighbor_mines = count

    def trigger_chain_reaction(self, row, col):
        """Запускает цепную реакцию открытия пустых клеток"""
        if not self.has_modifier(Modifier.CHAIN_REACTION):
            return

        to_reveal = []
        visited = set()
        queue = [(row, col)]

        while queue:
            r, c = queue.pop(0)
            if (r, c) in visited:
                continue

            visited.add((r, c))
            cell = self.grid[r][c]

            if not cell.is_revealed and not cell.is_flagged and not cell.is_mine:
                to_reveal.append((r, c))

                if cell.neighbor_mines == 0:
                    for dr in range(-1, 2):
                        for dc in range(-1, 2):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                if (nr, nc) not in visited:
                                    queue.append((nr, nc))

        self.chain_reaction_cells = to_reveal
        self.chain_reaction_timer = pygame.time.get_ticks()

    def reveal_cell(self, row, col):
        cell = self.grid[row][col]

        if cell.is_revealed or cell.is_flagged or self.game_over:
            return

        if self.is_frozen and self.has_modifier(Modifier.FREEZE):
            return

        if self.defuse_mode and self.has_modifier(Modifier.TIMER_BOMB):
            self.try_defuse_mine(row, col)
            return

        if self.first_click:
            self.place_mines(row, col)
            self.first_click = False
            self.timer_started = True
            self.start_time = pygame.time.get_ticks()
            self.last_shuffle_time = 0
            self.last_defuse_time = 0
            self.last_rotation_time = 0

        cell.is_revealed = True
        self.revealed_count += 1

        if cell.is_mine:
            self.final_time = self.get_time()  # Сначала фиксируем время
            self.game_over = True              # Потом завершаем игру
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.grid[r][c].is_mine:
                        self.grid[r][c].is_revealed = True
            return

        if self.has_modifier(Modifier.CHAIN_REACTION) and cell.neighbor_mines == 0:
            self.trigger_chain_reaction(row, col)
            return

        if cell.neighbor_mines == 0 and not self.has_modifier(Modifier.CHAIN_REACTION):
            for r in range(max(0, row - 1), min(self.rows, row + 2)):
                for c in range(max(0, col - 1), min(self.cols, col + 2)):
                    if not self.grid[r][c].is_revealed:
                        self.reveal_cell(r, c)

    def try_defuse_mine(self, row, col):
        """Попытка обезвредить мину"""
        if not self.defuse_mode or not self.defuse_available:
            return False

        cell = self.grid[row][col]
        if cell.is_mine and not cell.is_revealed:
            cell.is_mine = False
            cell.is_mega_mine = False
            cell.is_revealed = True
            self.revealed_count += 1
            self.mines_defused += 1

            self.calculate_numbers()

            self.defuse_available = False
            self.defuse_mode = False
            self.last_defuse_time = self.get_time()
            return True

        self.defuse_available = False
        self.defuse_mode = False
        self.last_defuse_time = self.get_time()
        return False

    def toggle_flag(self, row, col):
        if self.is_frozen and self.has_modifier(Modifier.FREEZE):
            return

        cell = self.grid[row][col]
        if cell.is_revealed or self.game_over:
            return

        if cell.is_flagged:
            cell.is_flagged = False
            self.flags_count += 1
        else:
            if self.flags_count > 0:
                cell.is_flagged = True
                self.flags_count -= 1

    def check_win(self):
        total_mines = self.mines - self.mines_defused
        if self.revealed_count >= self.rows * self.cols - total_mines and not self.game_over:
            self.win = True
            self.final_time = self.get_time()  # Сначала запоминаем время
            self.game_over = True              # Потом завершаем игру

            if self.records_manager.update_record(self.difficulty, self.modifiers, self.final_time):
                self.new_record = True

            for r in range(self.rows):
                for c in range(self.cols):
                    if self.grid[r][c].is_mine and not self.grid[r][c].is_flagged:
                        self.grid[r][c].is_flagged = True
                        self.flags_count -= 1
            return True
        return False

    def update_chain_reaction(self):
        """Обновление анимации цепной реакции"""
        if not self.chain_reaction_cells:
            return

        current_time = pygame.time.get_ticks()
        cells_per_frame = 3

        for _ in range(min(cells_per_frame, len(self.chain_reaction_cells))):
            if self.chain_reaction_cells:
                r, c = self.chain_reaction_cells.pop(0)
                if not self.grid[r][c].is_revealed:
                    self.grid[r][c].is_revealed = True
                    self.grid[r][c].chain_reaction_triggered = True
                    self.grid[r][c].chain_reaction_glow = 255
                    self.revealed_count += 1

        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col].chain_reaction_glow > 0:
                    self.grid[row][col].chain_reaction_glow = max(0, self.grid[row][col].chain_reaction_glow - 10)

    def shuffle_mines(self):
        """Перемешивание мин с умными флажками"""
        if self.first_click or self.game_over:
            return

        # Запоминаем информацию о флажках:
        # был ли флажок установлен правильно
        flags_data = []

        for row in range(self.rows):
            for col in range(self.cols):
                cell = self.grid[row][col]

                if cell.is_flagged:
                    flags_data.append({
                        "was_on_mine": cell.is_mine
                    })

        # Сохраняем открытые клетки
        revealed_cells = set()

        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col].is_revealed:
                    revealed_cells.add((row, col))

        # Убираем все флажки
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid[row][col].is_flagged = False

        # Удаляем старые мины
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid[row][col].is_mine = False
                self.grid[row][col].is_mega_mine = False

        # Доступные клетки для новых мин
        available_cells = []

        for row in range(self.rows):
            for col in range(self.cols):
                if (row, col) not in revealed_cells:
                    available_cells.append((row, col))

        random.shuffle(available_cells)

        # Ставим новые мины
        new_mines = []

        for i in range(min(self.mines, len(available_cells))):
            row, col = available_cells[i]

            self.grid[row][col].is_mine = True
            new_mines.append((row, col))

        # Пересчитываем числа
        self.calculate_numbers()

        # Список безопасных клеток
        safe_cells = []

        for row in range(self.rows):
            for col in range(self.cols):
                if (
                        not self.grid[row][col].is_mine
                        and not self.grid[row][col].is_revealed
                        and not self.grid[row][col].is_flagged
                ):
                    safe_cells.append((row, col))

        # Копия мин для распределения флажков
        free_mines = new_mines.copy()

        random.shuffle(free_mines)
        random.shuffle(safe_cells)

        # Возвращаем флажки
        for flag_info in flags_data:

            # Если флажок был на мине
            if flag_info["was_on_mine"]:

                if free_mines:
                    row, col = free_mines.pop()

                    self.grid[row][col].is_flagged = True

            # Если флажок был НЕ на мине
            else:

                if safe_cells:
                    row, col = safe_cells.pop()

                    self.grid[row][col].is_flagged = True

        self.last_shuffle_time = self.get_time()
        self.shuffle_warning = False

    def rotate_field(self):
        """Поворот поля на 90 градусов"""
        if not self.has_modifier(Modifier.MIRROR) or self.first_click or self.game_over:
            return

        self.rotation_angle = (self.rotation_angle + 90) % 360

        new_grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]

        for row in range(self.rows):
            for col in range(self.cols):
                if self.rotation_angle == 90:
                    new_row = col
                    new_col = self.rows - 1 - row
                elif self.rotation_angle == 180:
                    new_row = self.rows - 1 - row
                    new_col = self.cols - 1 - col
                elif self.rotation_angle == 270:
                    new_row = self.cols - 1 - col
                    new_col = row
                else:
                    new_row = row
                    new_col = col

                new_grid[new_row][new_col] = self.grid[row][col]
                new_grid[new_row][new_col].row = new_row
                new_grid[new_row][new_col].col = new_col

        self.grid = new_grid
        self.last_rotation_time = self.get_time()

    def get_time(self):
        if self.timer_started:
            if self.game_over:
                return self.final_time
            else:
                self.elapsed_time = (pygame.time.get_ticks() - self.start_time) // 1000
                return self.elapsed_time
        return 0

    def update(self):
        if self.game_over or not self.timer_started:
            return

        current_time = self.get_time()

        self.update_chain_reaction()

        # Модификатор перемешивания
        if self.has_modifier(Modifier.SHUFFLE):
            time_since_shuffle = current_time - self.last_shuffle_time
            if time_since_shuffle >= 30:
                self.shuffle_mines()
            elif time_since_shuffle >= 27:  # Предупреждение за 3 секунды
                self.shuffle_warning = True

        # Модификатор сапёра-сапёра
        if self.has_modifier(Modifier.TIMER_BOMB):
            if not self.defuse_available and current_time - self.last_defuse_time >= 40:
                self.defuse_available = True

        # Модификатор заморозки
        if self.has_modifier(Modifier.FREEZE):
            if not self.is_frozen and current_time - self.last_freeze_time >= 20:
                self.is_frozen = True
                self.freeze_end_time = current_time + 5
                self.last_freeze_time = current_time

            if self.is_frozen and current_time >= self.freeze_end_time:
                self.is_frozen = False

        # Модификатор искажения
        if self.has_modifier(Modifier.MIRROR):
            if current_time - self.last_rotation_time >= 25:
                self.rotate_field()

    def should_show_cell(self, row, col):
        if not self.timer_started or self.game_over:
            return True

        cell = self.grid[row][col]
        if cell.is_revealed:
            return True

        if self.has_modifier(Modifier.DARKNESS):
            for r in range(max(0, row - 1), min(self.rows, row + 2)):
                for c in range(max(0, col - 1), min(self.cols, col + 2)):
                    if self.grid[r][c].is_revealed:
                        return True
            return False

        return True

    def draw(self, screen, font, small_font):
        screen.fill(LIGHT_GRAY)

        for row in range(self.rows):
            for col in range(self.cols):
                cell = self.grid[row][col]

                x = col * self.cell_size
                y = row * self.cell_size

                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

                show_cell = self.should_show_cell(row, col)

                if cell.is_revealed:
                    if cell.is_mine:
                        color = PURPLE if cell.is_mega_mine else RED
                        pygame.draw.rect(screen, color, rect)
                        center_x = x + self.cell_size // 2
                        center_y = y + self.cell_size // 2
                        radius = self.cell_size // 4

                        pygame.draw.circle(screen, BLACK, (center_x, center_y), radius)
                        pygame.draw.line(screen, BLACK, (center_x, y + self.cell_size // 5),
                                         (center_x, y + self.cell_size // 5 * 4), 2)
                        pygame.draw.line(screen, BLACK, (x + self.cell_size // 5, center_y),
                                         (x + self.cell_size // 5 * 4, center_y), 2)
                    else:
                        if cell.chain_reaction_glow > 0:
                            glow_intensity = cell.chain_reaction_glow
                            glow_color = (
                                min(255, 255 - glow_intensity),
                                min(255, 200 + glow_intensity // 5),
                                min(255, 100 + glow_intensity)
                            )
                            pygame.draw.rect(screen, glow_color, rect)
                        else:
                            if (row + col) % 2 == 0:
                                color = REVEALED_LIGHT
                            else:
                                color = REVEALED_MEDIUM
                            pygame.draw.rect(screen, color, rect)

                        if cell.neighbor_mines > 0:
                            colors = {
                                1: BLUE, 2: GREEN, 3: RED, 4: NAVY,
                                5: MAROON, 6: TEAL, 7: BLACK, 8: GRAY
                            }
                            text_color = colors.get(cell.neighbor_mines, BLACK)
                            font_size = max(20, self.cell_size // 2)
                            cell_font = pygame.font.Font(None, font_size)
                            text = cell_font.render(str(cell.neighbor_mines), True, text_color)
                            text_rect = text.get_rect(center=(x + self.cell_size // 2, y + self.cell_size // 2))
                            screen.blit(text, text_rect)
                elif show_cell:
                    pygame.draw.rect(screen, GRAY, rect)
                    pygame.draw.line(screen, CELL_BORDER_LIGHT, (x, y), (x + self.cell_size - 1, y), 2)
                    pygame.draw.line(screen, CELL_BORDER_LIGHT, (x, y), (x, y + self.cell_size - 1), 2)
                    pygame.draw.line(screen, CELL_BORDER_DARK, (x + self.cell_size - 1, y),
                                     (x + self.cell_size - 1, y + self.cell_size - 1), 2)
                    pygame.draw.line(screen, CELL_BORDER_DARK, (x, y + self.cell_size - 1),
                                     (x + self.cell_size - 1, y + self.cell_size - 1), 2)

                    # Показываем предупреждение о перемешивании
                    if self.shuffle_warning and self.has_modifier(Modifier.SHUFFLE):
                        warning_surface = pygame.Surface((self.cell_size, self.cell_size))
                        warning_surface.set_alpha(50)
                        warning_surface.fill(SHUFFLE_COLOR)
                        screen.blit(warning_surface, (x, y))

                    if cell.is_flagged and not (self.is_frozen and self.has_modifier(Modifier.FREEZE)):
                        flag_x = x + self.cell_size // 4
                        flag_y = y + self.cell_size // 4
                        flag_size = self.cell_size // 2

                        pygame.draw.line(screen, BLACK,
                                         (flag_x + flag_size // 2, flag_y),
                                         (flag_x + flag_size // 2, flag_y + flag_size), 2)
                        pygame.draw.polygon(screen, RED, [
                            (flag_x + flag_size // 2, flag_y),
                            (flag_x + flag_size, flag_y + flag_size // 3),
                            (flag_x + flag_size // 2, flag_y + flag_size // 3 * 2)
                        ])
                else:
                    pygame.draw.rect(screen, DARK_GRAY, rect)
                    if cell.is_flagged:
                        flag_x = x + self.cell_size // 4
                        flag_y = y + self.cell_size // 4
                        flag_size = self.cell_size // 2
                        pygame.draw.line(screen, DARK_GRAY,
                                         (flag_x + flag_size // 2, flag_y),
                                         (flag_x + flag_size // 2, flag_y + flag_size), 2)

    def draw_ui(self, screen, font, small_font, tiny_font):
        top_panel_height = 60
        pygame.draw.rect(screen, DARK_GRAY, (0, 0, self.width, top_panel_height))

        # Кнопка информации
        info_button_size = 30
        info_button_x = 15
        info_button_y = 15
        info_button_rect = pygame.Rect(info_button_x, info_button_y, info_button_size, info_button_size)

        pygame.draw.circle(screen, INFO_BLUE, (info_button_x + info_button_size // 2,
                                               info_button_y + info_button_size // 2),
                           info_button_size // 2)
        pygame.draw.circle(screen, WHITE, (info_button_x + info_button_size // 2,
                                           info_button_y + info_button_size // 2),
                           info_button_size // 2, 2)

        info_text = font.render("i", True, WHITE)
        info_text_rect = info_text.get_rect(center=(info_button_x + info_button_size // 2,
                                                    info_button_y + info_button_size // 2))
        screen.blit(info_text, info_text_rect)

        # Кнопка модификаторов
        mod_button_x = info_button_x + info_button_size + 10
        mod_button_y = info_button_y
        mod_button_rect = pygame.Rect(mod_button_x, mod_button_y, info_button_size, info_button_size)

        mod_button_color = PURPLE if self.modifiers else DARK_GRAY
        pygame.draw.circle(screen, mod_button_color, (mod_button_x + info_button_size // 2,
                                                      mod_button_y + info_button_size // 2),
                           info_button_size // 2)
        pygame.draw.circle(screen, WHITE, (mod_button_x + info_button_size // 2,
                                           mod_button_y + info_button_size // 2),
                           info_button_size // 2, 2)

        mod_text = font.render("⚙", True, WHITE)
        mod_text_rect = mod_text.get_rect(center=(mod_button_x + info_button_size // 2,
                                                  mod_button_y + info_button_size // 2))
        screen.blit(mod_text, mod_text_rect)

        # Счетчик мин
        mines_text = font.render(f"💣 {self.flags_count}", True, WHITE)
        mines_text_rect = mines_text.get_rect(midleft=(mod_button_x + info_button_size + 15, 30))
        screen.blit(mines_text, mines_text_rect)

        # Таймер
        current_time = self.get_time()
        time_color = GOLD if self.new_record else WHITE

        if self.has_modifier(Modifier.TIMER_BOMB) and self.defuse_available:
            time_text = font.render(f"⏱ {current_time}с [ОБЕЗВРЕЖИВАНИЕ]", True, DEFUSE_COLOR)
        elif self.has_modifier(Modifier.MIRROR):
            time_text = font.render(f"⏱ {current_time}с [Поворот: {self.rotation_angle}°]", True, ORANGE)
        elif self.has_modifier(Modifier.CHAIN_REACTION) and self.chain_reaction_cells:
            time_text = font.render(f"⏱ {current_time}с [ЦЕПНАЯ РЕАКЦИЯ]", True, CHAIN_COLOR)
        elif self.has_modifier(Modifier.SHUFFLE) and self.shuffle_warning:
            time_text = font.render(f"⏱ {current_time}с [ПЕРЕМЕШИВАНИЕ]", True, SHUFFLE_COLOR)
        else:
            time_text = font.render(f"⏱ {current_time}с", True, time_color)

        time_rect = time_text.get_rect(center=(self.width // 2, 30))
        screen.blit(time_text, time_rect)

        # Рекорд и модификаторы справа
        record = self.records_manager.get_record(self.difficulty, self.modifiers)

        if self.modifiers:
            mod_names = ", ".join([mod.value[0] for mod in self.modifiers])
            mod_text = tiny_font.render(f"Моды: {mod_names}", True, LIGHT_BLUE)
        else:
            mod_text = tiny_font.render("Без модификаторов", True, LIGHT_BLUE)
        mod_rect = mod_text.get_rect(midright=(self.width - 20, 20))
        screen.blit(mod_text, mod_rect)

        info_y = 42
        if self.has_modifier(Modifier.TIMER_BOMB):
            if self.defuse_available:
                defuse_text = tiny_font.render("🔧 Можно обезвредить мину!", True, DEFUSE_COLOR)
                defuse_rect = defuse_text.get_rect(midright=(self.width - 20, info_y))
                screen.blit(defuse_text, defuse_rect)
            else:
                time_left = 40 - (current_time - self.last_defuse_time)
                defuse_text = tiny_font.render(f"Обезвреживание через: {max(0, time_left)}с", True, WHITE)
                defuse_rect = defuse_text.get_rect(midright=(self.width - 20, info_y))
                screen.blit(defuse_text, defuse_rect)
            info_y += 15

        record_text = tiny_font.render(f"Рекорд: {record}", True, GOLD)
        record_rect = record_text.get_rect(midright=(self.width - 20, info_y))
        screen.blit(record_text, record_rect)

        # Статус игры
        if self.is_frozen:
            status_text = small_font.render("❄ ЗАМОРОЗКА! ❄", True, BLUE)
            status_rect = status_text.get_rect(center=(self.width // 2, 50))
            screen.blit(status_text, status_rect)
        elif self.defuse_mode:
            status_text = small_font.render("🎯 ВЫБЕРИТЕ МИНУ ДЛЯ ОБЕЗВРЕЖИВАНИЯ", True, DEFUSE_COLOR)
            status_rect = status_text.get_rect(center=(self.width // 2, 50))
            screen.blit(status_text, status_rect)
        elif self.chain_reaction_cells:
            status_text = small_font.render("⚡ ЦЕПНАЯ РЕАКЦИЯ! ⚡", True, CHAIN_COLOR)
            status_rect = status_text.get_rect(center=(self.width // 2, 50))
            screen.blit(status_text, status_rect)
        elif self.shuffle_warning:
            status_text = small_font.render("🔄 СКОРО ПЕРЕМЕШИВАНИЕ! 🔄", True, SHUFFLE_COLOR)
            status_rect = status_text.get_rect(center=(self.width // 2, 50))
            screen.blit(status_text, status_rect)
        elif self.game_over:
            if self.win:
                if self.new_record:
                    status_text = small_font.render("🏆 НОВЫЙ РЕКОРД! 🏆", True, GOLD)
                else:
                    status_text = small_font.render("ПОБЕДА!", True, GREEN)
            else:
                status_text = small_font.render("ПРОИГРЫШ", True, RED)
            status_rect = status_text.get_rect(center=(self.width // 2, 50))
            screen.blit(status_text, status_rect)

        # Нижняя панель с кнопками сложности
        bottom_panel_height = 60
        bottom_y = self.height + top_panel_height

        difficulties = [
            (Difficulty.EASY, "Легкий", LIGHT_BLUE),
            (Difficulty.MEDIUM, "Средний", LIGHT_YELLOW),
            (Difficulty.HARD, "Сложный", LIGHT_ORANGE),
            (Difficulty.EXPERT, "Эксперт", LIGHT_RED)
        ]

        button_width = 100
        button_height = 35
        total_width = len(difficulties) * (button_width + 10) - 10
        start_x = (self.width - total_width) // 2

        for i, (diff, text, color) in enumerate(difficulties):
            btn_x = start_x + i * (button_width + 10)
            btn_y = bottom_y + 12

            btn_color = color if diff == self.difficulty else DARK_GRAY
            pygame.draw.rect(screen, btn_color, (btn_x, btn_y, button_width, button_height))

            if diff == self.difficulty:
                pygame.draw.rect(screen, BLACK, (btn_x, btn_y, button_width, button_height), 3)
            else:
                pygame.draw.rect(screen, DARK_GRAY, (btn_x, btn_y, button_width, button_height), 2)

            btn_text = small_font.render(text, True, BLACK)
            btn_rect = btn_text.get_rect(center=(btn_x + button_width // 2, btn_y + button_height // 2))
            screen.blit(btn_text, btn_rect)

        return top_panel_height, bottom_panel_height, info_button_rect, mod_button_rect


class Game:
    def __init__(self):
        self.records_manager = RecordsManager()
        self.current_difficulty = Difficulty.MEDIUM
        self.current_modifiers = []
        self.game = Minesweeper(self.current_difficulty, self.current_modifiers, self.records_manager)
        self.setup_display()
        self.info_window = InfoWindow(self.game.width, self.game.height + 120)
        self.modifier_menu = ModifierMenu(self.game.width, self.game.height + 120)

    def setup_display(self):
        top_panel = 60
        bottom_panel = 60
        total_height = self.game.height + top_panel + bottom_panel
        self.screen = pygame.display.set_mode((self.game.width, total_height))

        mod_text = ", ".join([m.value[0] for m in self.current_modifiers]) if self.current_modifiers else "Без модов"
        pygame.display.set_caption(f"Сапёр - {self.current_difficulty.value[0]} [{mod_text}]")
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 22)
        self.tiny_font = pygame.font.Font(None, 18)

    def change_difficulty(self, difficulty):
        self.current_difficulty = difficulty

        if difficulty == Difficulty.EASY:
            self.current_modifiers = []

        self.game = Minesweeper(difficulty, self.current_modifiers, self.records_manager)
        self.setup_display()
        self.info_window = InfoWindow(self.game.width, self.game.height + 120)
        self.modifier_menu = ModifierMenu(self.game.width, self.game.height + 120)

    def apply_modifiers(self, modifiers):
        self.current_modifiers = modifiers
        self.game = Minesweeper(self.current_difficulty, modifiers, self.records_manager)
        self.setup_display()
        self.info_window = InfoWindow(self.game.width, self.game.height + 120)
        self.modifier_menu = ModifierMenu(self.game.width, self.game.height + 120)

    def handle_click(self, pos, button):
        if self.info_window.is_visible:
            self.info_window.handle_click(pos)
            return

        if self.modifier_menu.is_visible:
            apply_btn, cancel_btn = self.modifier_menu.draw(
                self.screen, self.font, self.small_font, self.tiny_font,
                self.current_modifiers, self.current_difficulty
            )

            x, y = pos

            if apply_btn and apply_btn.collidepoint(x, y) and button == 1:
                if self.current_difficulty != Difficulty.EASY:
                    self.apply_modifiers(self.modifier_menu.selected_modifiers)
                self.modifier_menu.is_visible = False
                return

            if cancel_btn and cancel_btn.collidepoint(x, y) and button == 1:
                self.modifier_menu.is_visible = False
                return

            modifiers_list = list(Modifier)
            button_height = 50
            button_margin = 5
            y_offset = self.modifier_menu.y + 90

            for mod in modifiers_list:
                if self.current_difficulty == Difficulty.EASY and mod != Modifier.NONE:
                    y_offset += button_height + button_margin
                    continue

                btn_rect = pygame.Rect(
                    self.modifier_menu.x + 30,
                    y_offset,
                    self.modifier_menu.window_width - 60,
                    button_height
                )

                if btn_rect.collidepoint(x, y) and button == 1:
                    self.modifier_menu.toggle_modifier(mod)
                    return

                y_offset += button_height + button_margin

            window_rect = pygame.Rect(
                self.modifier_menu.x,
                self.modifier_menu.y,
                self.modifier_menu.window_width,
                self.modifier_menu.window_height
            )
            if not window_rect.collidepoint(x, y):
                self.modifier_menu.is_visible = False
            return

        x, y = pos
        top_panel = 60
        game_y_start = top_panel
        game_y_end = game_y_start + self.game.height

        # Кнопка информации
        info_button_size = 30
        info_button_x = 15
        info_button_y = 15
        info_button_rect = pygame.Rect(info_button_x, info_button_y, info_button_size, info_button_size)

        if info_button_rect.collidepoint(x, y) and button == 1:
            self.info_window.toggle()
            return

        # Кнопка модификаторов
        mod_button_x = info_button_x + info_button_size + 10
        mod_button_y = info_button_y
        mod_button_rect = pygame.Rect(mod_button_x, mod_button_y, info_button_size, info_button_size)

        if mod_button_rect.collidepoint(x, y) and button == 1:
            if self.current_difficulty != Difficulty.EASY:
                self.modifier_menu.toggle()
                self.modifier_menu.selected_modifiers = self.current_modifiers.copy()
            return

        # Активация режима обезвреживания
        if self.game.has_modifier(Modifier.TIMER_BOMB) and self.game.defuse_available and not self.game.defuse_mode:
            if button == 1 and game_y_start <= y < game_y_end:
                self.game.defuse_mode = True
                return

        # Игровое поле
        if game_y_start <= y < game_y_end and x < self.game.width:
            col = x // self.game.cell_size
            row = (y - game_y_start) // self.game.cell_size

            if 0 <= row < self.game.rows and 0 <= col < self.game.cols:
                if button == 1:
                    self.game.reveal_cell(row, col)
                    self.game.check_win()
                elif button == 3:
                    self.game.toggle_flag(row, col)

        # Кнопки сложности
        bottom_y = game_y_end + 22
        difficulties = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD, Difficulty.EXPERT]
        button_width = 100
        button_height = 35
        total_width = len(difficulties) * (button_width + 10) - 10
        start_x = (self.game.width - total_width) // 2

        for i, diff in enumerate(difficulties):
            btn_x = start_x + i * (button_width + 10)
            btn_y = bottom_y
            btn_rect = pygame.Rect(btn_x, btn_y, button_width, button_height)

            if btn_rect.collidepoint(x, y) and button == 1:
                self.change_difficulty(diff)
                return

    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos, event.button)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_i:
                        self.info_window.toggle()
                    elif event.key == pygame.K_m:
                        if self.current_difficulty != Difficulty.EASY:
                            self.modifier_menu.toggle()
                            self.modifier_menu.selected_modifiers = self.current_modifiers.copy()
                    elif event.key == pygame.K_ESCAPE:
                        if self.info_window.is_visible:
                            self.info_window.is_visible = False
                        elif self.modifier_menu.is_visible:
                            self.modifier_menu.is_visible = False
                        elif self.game.defuse_mode:
                            self.game.defuse_mode = False
                            self.game.defuse_available = True
                    elif event.key == pygame.K_SPACE:
                        if self.game.has_modifier(Modifier.TIMER_BOMB) and self.game.defuse_available:
                            self.game.defuse_mode = not self.game.defuse_mode
                    elif not self.info_window.is_visible and not self.modifier_menu.is_visible and not self.game.defuse_mode:
                        if event.key == pygame.K_1:
                            self.change_difficulty(Difficulty.EASY)
                        elif event.key == pygame.K_2:
                            self.change_difficulty(Difficulty.MEDIUM)
                        elif event.key == pygame.K_3:
                            self.change_difficulty(Difficulty.HARD)
                        elif event.key == pygame.K_4:
                            self.change_difficulty(Difficulty.EXPERT)
                        elif event.key == pygame.K_r:
                            self.change_difficulty(self.current_difficulty)

            # Обновление игры
            self.game.update()

            # Отрисовка
            self.screen.fill(DARK_GRAY)

            top_panel = 60
            game_surface = pygame.Surface((self.game.width, self.game.height))
            self.game.draw(game_surface, self.font, self.small_font)
            self.screen.blit(game_surface, (0, top_panel))

            self.game.draw_ui(self.screen, self.font, self.small_font, self.tiny_font)

            if self.modifier_menu.is_visible:
                self.modifier_menu.draw(self.screen, self.font, self.small_font, self.tiny_font,
                                        self.current_modifiers, self.current_difficulty)
            else:
                self.info_window.draw(self.screen, self.font, self.small_font, self.tiny_font)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()