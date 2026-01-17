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
import math
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
    def __init__(self, ained: AiNed, pos: tuple[int, int], N: int):
        self.N = N
        self.pos = pos
        self.ained = ained
    
    @abstractmethod
    def solve(self) -> bool:
        pass
    
    @abstractmethod
    def __str__(self):
        pass


class StochasticStrategy(Strategy):
    """
    A very simple stochastic strategy that simply chooses a random light to flip.
    """
    def __init__(self, ained: AiNed, pos: tuple[int, int], N: int):
        super().__init__(ained, pos, N)
    
    def solve(self) -> bool:
        row = int(random.randint(0, self.N))
        column = int(random.randint(0, self.N))
        self.ained.flip_lights(row, column)
        return True

    def __str__(self):
        return "Stochastic"


class GreedyStrategy(Strategy):
    """
    A greedy strategy that chooses the light that is the most likely to turn off as many lights as possible while minimising the amount of lights that turn on.
    """
    def __init__(self, ained: AiNed, pos: tuple[int, int], N: int):
        super().__init__(ained, pos, N)

    def solve(self) -> bool:
        min_delta_coords = (0, 0)
        min_delta = float("inf")
        current_board = self.ained.get_board(self.pos[0], self.pos[1], self.N, self.N)
        current_coefficients = self.ained.get_coefficients()
        for i in range(len(current_board)):
            current_row = i // self.N
            current_col = i % self.N
            temp_delta = 0
            for j in range(len(current_board)):
                if j == i:
                    if current_board[i] == 0:
                        temp_delta += self.greedy_eval(current_board[i], current_coefficients[0])
                    continue
                respective_row = j // self.N
                respective_col = j % self.N

                row_diff = abs(respective_row - current_row)
                col_diff = abs(respective_col - current_col)
                if row_diff < 5 and col_diff < 5:
                    temp_delta += self.greedy_eval(current_board[j], current_coefficients[row_diff * 5 + col_diff])
            if temp_delta < min_delta:
                min_delta_coords = (current_row, current_col)
                min_delta = min(min_delta, temp_delta)
        self.ained.flip_lights(self.pos[0], self.pos[1], self.N, self.N, min_delta_coords[0], min_delta_coords[1])
        return True

    def greedy_eval(self, light_value: int, probability: float) -> float:
        """ Greedy formula """
        return probability * (1 - 2 * light_value)
    
    def __str__(self):
        return "Greedy"


class SimAnnStrategy(Strategy):
    """ A simulated annealing strategy that is based on MCMC with a decreasing temperature. """
    def __init__(self, ained: AiNed, pos: tuple[int, int], N: int):
        super().__init__(ained, pos, N)
        self.ained = ained
        self.curr_step = 1
        self.start_T = 2.0
        self.min_T = 0.5
        self.T = self.start_T
        self.cool = 0.99
        self.acceptance_window = 1000
        self.recent_accepts = list()

    def solve(self) -> bool:
        board = self.ained.get_board(self.pos[0], self.pos[1], self.N, self.N)
        curr_energy = energy(board)
        row, col = np.random.randint(0, self.N, size=2)
        proposed_energy = self.estimate_energy(board, row, col)
        delta_energy = proposed_energy - curr_energy
        if delta_energy < 0 or np.random.rand() < np.exp(-delta_energy / self.T):
            self.ained.flip_lights(self.pos[0], self.pos[1], self.N, self.N, row, col)
            newer_board = self.ained.get_board(self.pos[0], self.pos[0], self.N, self.N)
            self.cool_down()
            #self.show_temp()
            return True
        else:
            self.cool_down()
            return False
        
    def __str__(self):
        return "SimAnn"

    def cool_down(self):
        self.T *= self.cool
        self.T = max(self.min_T, self.T)

    def show_temp(self):
        """ Print the current temperature and acceptance ratio """
        A = sum(self.recent_accepts) / len(self.recent_accepts)
        print(self.T, A)

    def estimate_energy(self, board: list[int], row: int, col: int, num_estimations=10):
        """ Estimate the likely energy of a given board state after flipping a light """
        estimated_energies = list()
        coeff = self.ained.get_coefficients()
        for i in range(num_estimations):
            temp_board = board[:]
            for index in range(len(temp_board)):
                respective_row = index // self.N
                respective_col = index % self.N

                row_diff = abs(respective_row - row)
                col_diff = abs(respective_col - col)

                if row_diff < 5 and col_diff < 5:
                    curr_coeff = coeff[row_diff * 5 + col_diff]
                    if random.random() < curr_coeff:
                        temp_board[index] = 1 - temp_board[index]
            estimated_energies.append(energy(temp_board))

        return np.mean(estimated_energies)


def energy(board: list) -> int:
    return sum(board)


class SimAnnAdaptStrategy(Strategy):
    """ A simulated annealing strategy that is based on MCMC with a adapting temperature. """
    def __init__(self, ained: AiNed, pos: tuple[int, int], N: int):
        super().__init__(ained, pos, N)
        self.ained = ained
        self.curr_step = 1
        self.start_T = 2.0
        self.best_accept = 0.15
        self.T = self.start_T
        self.cool = 0.99
        self.heat = 1.01
        self.acceptance_window = 1000
        self.recent_accepts = list()

    def solve(self) -> bool:
        board = self.ained.get_board(self.pos[0], self.pos[1], self.N, self.N)
        curr_energy = energy(board)
        row, col = np.random.randint(0, self.N, size=2)
        proposed_energy = self.estimate_energy(board, row, col)
        delta_energy = proposed_energy - curr_energy
        if delta_energy < 0 or np.random.rand() < np.exp(-delta_energy / self.T):
            self.ained.flip_lights(self.pos[0], self.pos[1], self.N, self.N, row, col)
            newer_board = self.ained.get_board(self.pos[0], self.pos[0], self.N, self.N)
            self.recent_accepts.append(1)
            if np.mean(self.recent_accepts) >= self.best_accept:
                self.cool_down()
            else:
                self.heat_up()
            #self.show_temp()
            return True
        else:
            self.recent_accepts.append(0)
            if np.mean(self.recent_accepts) >= self.best_accept:
                self.cool_down()
            else:
                self.heat_up()
            return False
        
    def __str__(self):
        return "SimAnnAdapt"

    def cool_down(self):
        self.T *= self.cool
            
    def heat_up(self):
        self.T *= self.heat
        
    def show_temp(self):
        """ Print the current temperature and acceptance ratio """
        A = sum(self.recent_accepts) / len(self.recent_accepts)
        print(self.T, A)

    def estimate_energy(self, board: list[int], row: int, col: int, num_estimations=10):
        """ Estimate the likely energy of a given board state after flipping a light """
        estimated_energies = list()
        coeff = self.ained.get_coefficients()
        for i in range(num_estimations):
            temp_board = board[:]
            for index in range(len(temp_board)):
                respective_row = index // self.N
                respective_col = index % self.N

                row_diff = abs(respective_row - row)
                col_diff = abs(respective_col - col)

                if row_diff < 5 and col_diff < 5:
                    curr_coeff = coeff[row_diff * 5 + col_diff]
                    if random.random() < curr_coeff:
                        temp_board[index] = 1 - temp_board[index]
            estimated_energies.append(energy(temp_board))

        return np.mean(estimated_energies)

