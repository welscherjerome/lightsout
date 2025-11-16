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


import random
import csv
import os
import numpy as np
from pyained.ained import AiNed
from abc import ABC, abstractmethod


class Strategy(ABC):
    """
    This Strategy interface declares operations common to all supported strategy versions.
    Concrete Strategies inherit from this interface.

    The Solver then uses this interface to call the algorithm defined by Concrete Strategies.

    Each strategy is supposed to calculate which cell to flip and also flip it. After flipping a cell, it should return a boolean.
    The purpose of the boolean is for debugging purposes if any logging is to be implemented or to keep track whether a step was taken or not.
    """
    def __init__(self, ained: AiNed):
        self.ained = ained
    
    @abstractmethod
    def solve(self, N: int, pos: tuple[int, int]) -> bool:
        pass
    
    @abstractmethod
    def __str__(self):
        pass


class StochasticStrategy(Strategy):
    """
    A very simple stochastic strategy that simply chooses a random light to flip.
    """
    def __init__(self, ained: AiNed):
        super().__init__(ained)
    
    def solve(self, N: int, pos: tuple[int, int]) -> bool:
        row = int(random.randint(0, N))
        column = int(random.randint(0, N))
        self.ained.flip_lights(pos[0], pos[1], N, N, row, column)
        return True

    def __str__(self):
        return "Stochastic"


class GreedyStrategy(Strategy):
    """
    A greedy strategy that chooses the light that is the most likely to turn off as many lights as possible while minimising the amount of lights that turn on.
    """
    def __init__(self, ained: AiNed):
        super().__init__(ained)

    def solve(self, N: int, pos: tuple[int, int]) -> bool:
        min_delta_coords = (0, 0)
        min_delta = float("inf")
        current_board = self.ained.get_board(pos[0], pos[1], N, N)
        current_coefficients = self.ained.get_coefficients()
        for i in range(len(current_board)):
            current_row = i // N
            current_col = i % N
            temp_delta = 0
            for j in range(len(current_board)):
                if j == i:
                    if current_board[i] == 0:
                        temp_delta += self.greedy_eval(current_board[i], current_coefficients[0])
                    continue
                respective_row = j // N
                respective_col = j % N

                row_diff = abs(respective_row - current_row)
                col_diff = abs(respective_col - current_col)
                if row_diff < 5 and col_diff < 5:
                    temp_delta += self.greedy_eval(current_board[j], current_coefficients[row_diff * 5 + col_diff])
            if temp_delta < min_delta:
                min_delta_coords = (current_row, current_col)
                min_delta = min(min_delta, temp_delta)
        self.ained.flip_lights(pos[0], pos[1], N, N, min_delta_coords[0], min_delta_coords[1])
        return True

    def greedy_eval(self, light_value: int, probability: float) -> float:
        """ Greedy formula """
        return probability * (1 - 2 * light_value)
    
    def __str__(self):
        return "Greedy"


class SimAnnStrategy(Strategy):
    """ A simulated annealing strategy that is based on MCMC with a decreasing temperature. """
    def __init__(self, ained: AiNed):
        super().__init__(ained)
        self.ained = ained
        os.makedirs("data/SimAnnRuns", exist_ok=True)
        columns = ["curr_step", "curr_energy", "proposed_step", "proposed_energy", "accepted_board", "accepted_bool"]
        
        # Name file
        self.i = 1
        self.file_name = "SimAnn_simulation_"
        while os.path.exists(f"data/SimAnnRuns/{self.file_name}{self.i}.csv"):
            self.i += 1

        # Add columns if file is new
        with open(f"data/SimAnnRuns/{self.file_name}{self.i}.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(columns)  

        self.curr_step = 1
        self.start_T = 10.0
        self.min_T = 1
        self.T = self.start_T
        self.cool = 0.95
        self.acceptance_window = 1000
        self.recent_accepts = list()

    def solve(self, N: int, pos: tuple[int, int]) -> bool:
        board = self.ained.get_board(pos[0], pos[1], N, N)
        curr_energy = energy(board)
        row, col = np.random.randint(0, N, size=2)
        proposed_energy = self.estimate_energy(board, N, row, col)
        delta_energy = proposed_energy - curr_energy
        if delta_energy < 0 or np.random.rand() < np.exp(-delta_energy / self.T):
            self.ained.flip_lights(pos[0], pos[1], N, N, row, col)
            newer_board = self.ained.get_board(pos[0], pos[0], N, N)
            self.save_step(curr_energy, (row, col), proposed_energy, newer_board, accepted=True)
            self.cool_down()
            self.show_temp()
            return True
        else:
            self.save_step(curr_energy, (row, col), proposed_energy, board, accepted=False)
            self.cool_down()
            return False
        

    def save_step(self, curr_energy: int, proposed_step: tuple[int, int], new_energy: int, accepted_board: list[int], accepted: bool):
        """
        Special function that logs and keeps track of energy and board states throughout Simulated Annealing.
        It also keeps track of the acceptance ratio via the recently accepted steps.
        """

        self.recent_accepts.append(1 if accepted else 0)
        if len(self.recent_accepts) > self.acceptance_window:
            self.recent_accepts.pop(0)

        new_row = [self.curr_step, curr_energy, proposed_step, new_energy, accepted_board, accepted]
        with open(f"data/SimAnnRuns/{self.file_name}{self.i}.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(new_row)
        if accepted:
            self.curr_step += 1

    def __str__(self):
        return "SimAnn"

    def cool_down(self):
        self.T *= self.cool
        self.T = max(self.min_T, self.T)

    def show_temp(self):
        """ Print the current temperature and acceptance ratio """
        A = sum(self.recent_accepts) / len(self.recent_accepts)
        print(f"Current Accept Rate: {A:0.2f}, Current Heat: {self.T:0.2f}")

    def estimate_energy(self, board: list[int], N: int, row: int, col: int, num_estimations=10):
        """ Estimate the likely energy of a given board state after flipping a light """
        estimated_energies = list()
        for i in range(num_estimations):
            coeff = self.ained.get_coefficients()
            for index in range(len(board)):
                respective_row = index // N
                respective_col = index % N

                row_diff = abs(respective_row - row)
                col_diff = abs(respective_col - col)

                if row_diff < 5 and col_diff < 5:
                    curr_coeff = coeff[row_diff * 5 + col_diff]
                    if random.random() < curr_coeff:
                        board[index] = 1 - board[index]
            estimated_energies.append(energy(board))

        return np.mean(estimated_energies)


def energy(board: list) -> int:
    sum_energy = 0
    for i in range(len(board)):
        sum_energy += int(board[i])
    return sum_energy

