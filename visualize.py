from pyained.ained import AiNed
import time
import sys


def clean_print(ained_interface, N, start_row, start_col):
    """
    Print the current state of the board using ANSI escape codes.
    """

    board = ained_interface.get_board(start_row, start_col, N, N)
    print("     ", end="")
    l = "\u2588"
    o = "\u2591"
    for i in range(N):
        print(f" {i:2d}", end="")
    print("\n-" + "---" * (N+2))
    for i in range(N):
        print(f"{i:3d}", end=" |")
        for j in range(N):
            print(f" {(l if board[i*N + j] == 1 else o):>2}", end="")
        print()


if __name__ == "__main__":
    ained = AiNed()
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"
    try:
        sys.stdout.write(HIDE_CURSOR)
        sys.stdout.flush()

        start_r = int(input("Start row of board: "))
        start_c = int(input("Start col of board: "))
        N = int(input("Size of board: "))
        clean_print(ained, N, start_r, start_c)
        while True:
            print("\n")
            sys.stdout.write(f"\033[{N + 4}A") # This moves the cursor up by N + 4 lines!
            sys.stdout.flush()
            clean_print(ained, N, start_r, start_c)
            time.sleep(0.15)
    finally:
        sys.stdout.write(SHOW_CURSOR)
        sys.stdout.flush()
        ained.close()

