import os
import time
from collections.abc import Callable
from statistics import mean, stdev

import pyautogui
from PIL import Image, ImageGrab

from Card import Card
from Game import Game
from Rank import Rank
from Stack import Stack

CARD_IMAGES = r"res/"


class Board:
    default_delay = 0.1

    square_size = 15
    vertical_spacing_with_square = 15
    horizontal_spacing_with_square = 119

    vertical_spacing = vertical_spacing_with_square + square_size
    horizontal_spacing = horizontal_spacing_with_square + square_size

    left_offset = 369
    top_offset = 465

    card_width = 112
    card_height = 15

    hand_x = 1430
    hand_y = 245

    newgame_x = 1400
    newgame_y = 900

    values = ["H", "0", "9", "8", "7", "6"]
    suits = ["H", "D", "C", "S", "R", "B"]

    def __init__(self):
        self.starting_rows = 4
        self.starting_cols = 9

        self.game = None

        self.bounding_box_list = []
        for c in range(self.starting_cols):
            self.bounding_box_list.append([])
            for r in range(self.starting_rows):
                new_bounding_box = (
                    self.left_offset + self.horizontal_spacing * c,
                    self.top_offset + self.vertical_spacing * r,
                    self.left_offset + self.horizontal_spacing * c + self.square_size,
                    self.top_offset + self.vertical_spacing * r + self.square_size,
                )
                self.bounding_box_list[c].append(new_bounding_box)

    @staticmethod
    def get_card(capture):
        dir = os.listdir(CARD_IMAGES)
        for image_os in dir:
            image_name = os.fsdecode(image_os)
            image = Image.open(CARD_IMAGES + image_os).convert("RGB")
            if list(image.getdata()) == list(capture.getdata()):  # pyright: ignore[reportArgumentType]
                card_value = image_name[0]
                card_suit = image_name[1]
                return Card(card_value, card_suit)
        return Card("?", "?")

    @staticmethod
    def make_game_by_boxes(rank_boxes):
        ranks: list[Rank] = []
        for rank_idx in range(len(rank_boxes)):
            cards: list[Card] = []
            for card_box in rank_boxes[rank_idx]:
                capture = ImageGrab.grab(card_box).convert("RGB")
                card = __class__.get_card(capture)
                cards.append(card)
            ranks.append(Rank(rank_idx, Stack.from_cards(cards)))
        return Game(ranks)

    def execute_move_list(self, move_list):
        self.tab_in()  # Tab into window
        for move in move_list:
            from_position = self.get_back_stack_position(move.from_rank_id)
            dest_position = self.get_front_stack_position(move.dest_rank_id)

            pyautogui.moveTo(
                from_position[0], from_position[1], duration=self.default_delay
            )
            pyautogui.mouseDown(button="left")
            pyautogui.moveTo(
                dest_position[0], dest_position[1], duration=self.default_delay
            )
            pyautogui.mouseUp(button="left")

            self.game.make_move(move)

    def get_rank_x(self, rank_idx):
        return (
            self.left_offset + rank_idx * self.horizontal_spacing + self.card_width / 2
        )

    def get_stack_front_y(self, rank_idx):
        if not self.game:
            return

        rank = self.game.get_rank(rank_idx)
        return (
            self.top_offset
            + (rank.get_total_cards() - 1 + 0.75) * self.vertical_spacing
        )

    def get_stack_back_y(self, rank_idx):
        if not self.game:
            return

        rank = self.game.get_rank(rank_idx)
        rank_stack = rank.get_top_stack()

        return (
            self.top_offset
            + (rank.get_total_cards() - rank_stack.length + 0.75)
            * self.vertical_spacing
        )

    def get_back_stack_position(self, rank_idx):
        if rank_idx == -1:
            return (self.hand_x, self.hand_y)
        else:
            return (self.get_rank_x(rank_idx), self.get_stack_back_y(rank_idx))

    def get_front_stack_position(self, rank_idx):
        if rank_idx == -1:
            return (self.hand_x, self.hand_y)
        else:
            return (self.get_rank_x(rank_idx), self.get_stack_front_y(rank_idx))

    def tab_in(self):
        pyautogui.mouseDown(self.left_offset - 10, self.top_offset - 10, button="left")
        time.sleep(self.default_delay)
        pyautogui.mouseUp()
        time.sleep(self.default_delay)

    def make_game(self):
        return self.make_game_by_boxes(self.bounding_box_list)

    def next_game(
        self, n: int, comp: int, on_complete: Callable[[int], bool] | None
    ) -> bool:
        r = on_complete(comp) if on_complete is not None else False
        if not r and comp < n:
            self.tab_in()
            pyautogui.moveTo(self.newgame_x, self.newgame_y, self.default_delay)
            pyautogui.mouseDown(button="left")
            pyautogui.mouseUp(button="left")
            time.sleep(5)
        return r

    def play_games(
        self,
        n: int,
        game_maker: Callable[[], Game] | None,
        on_complete: Callable[[int], bool] | None,
    ):
        durations = []
        completed_games = 0

        while completed_games < n:
            if game_maker is None:
                self.game = self.make_game()
            else:
                self.game = game_maker()
            start_time = time.time()
            winning_moves = self.game.solve(True)
            end_time = time.time()

            if winning_moves is None:
                if self.next_game(n, completed_games, on_complete):
                    break
                continue

            durations.append(end_time - start_time)
            self.execute_move_list(winning_moves)
            completed_games += 1
            if self.next_game(n, completed_games, on_complete):
                break

        dur_mean = mean(durations) if len(durations) > 0 else 0.0
        dur_std = stdev(durations) if len(durations) > 1 else 0.0
        print(f"{dur_mean:0.3f}s +/- {dur_std}s")

    def play_quick_games(
        self,
        n: int,
        game_maker: Callable[[], Game] | None,
        on_complete: Callable[[int], bool] | None,
    ):
        durations = []
        completed_games = 0

        while completed_games < n:
            if game_maker is None:
                self.game = self.make_game()
            else:
                self.game = game_maker()
            start_time = time.time()
            winning_moves = self.game.solve(False)
            end_time = time.time()

            if winning_moves is None:
                if self.next_game(n, completed_games, on_complete):
                    break
                continue

            durations.append(end_time - start_time)
            self.execute_move_list(winning_moves)
            completed_games += 1
            if self.next_game(n, completed_games, on_complete):
                break

        dur_mean = mean(durations) if len(durations) > 0 else 0.0
        dur_std = stdev(durations) if len(durations) > 1 else 0.0
        print(f"{dur_mean:0.3f}s +/- {dur_std}s")
