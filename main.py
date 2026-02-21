from Board import Board


def main():
    board = Board()
    board.play_games(10, None, lambda _: None)


if __name__ == "__main__":
    main()
