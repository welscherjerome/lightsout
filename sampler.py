"""
/*
 * Copyright (c) 2025 Jérôme Welscher
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
 """

from pyained.ained import AiNed
import os
import csv
import numpy as np


class MCMC:
    """ The MCMC algorithm"""
    def __init__(self, ained: AiNed):
        self.ained = ained
        os.makedirs("data/MCMC", exist_ok=True)
        columns = ["board_size", "curr_step", "curr_energy", "proposed_step", "proposed_energy", "accepted_board", "accepted_bool"]
        
        # Name file
        self.i = 1
        self.file_name = "MCMC_simulation_"
        while os.path.exists(f"data/MCMC/{self.file_name}{self.i}.csv"):
            self.i += 1

        # Add columns if file is new
        with open(f"data/MCMC/{self.file_name}{self.i}.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)  

        self.curr_step = 1
        self.T = 13.0

    def sample(self, N: int, pos: tuple[int, int]) -> bool:
        board = self.ained.get_board(pos[0], pos[1], N, N)
        curr_energy = energy(board)
        row, col = np.random.randint(0, N, size=2)
        self.ained.flip_lights(pos[0], pos[1], N, N, row, col)
        new_board = self.ained.get_board(pos[0], pos[1], N, N)
        proposed_energy = energy(new_board)
        delta_energy = proposed_energy - curr_energy
        if delta_energy < 0 or np.random.rand() < np.exp(-delta_energy / self.T):
            self.save_step(N, curr_energy, (row, col), proposed_energy, new_board, accepted=True)
        else:
            self.ained.reconstruct_board(board, pos[0], pos[1], N, N)
            self.save_step(N, curr_energy, (row, col), proposed_energy, board, accepted=False)
        return True

    def save_step(self, N: int, curr_energy: int, proposed_step: tuple[int, int], new_energy: int, accepted_board: list[int], accepted: bool):
        """ Keep track of steps and energy throughout the chain """
        new_row = [N, self.curr_step, curr_energy, proposed_step, new_energy, accepted_board, accepted]
        with open(f"data/MCMC/{self.file_name}{self.i}.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(new_row)
        self.curr_step += 1

    def __str__(self):
        return "MCMC"

def energy(board: list) -> int:
    sum_energy = 0
    for i in range(len(board)):
        sum_energy += int(board[i])
    return sum_energy
