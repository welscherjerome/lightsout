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
import strategy
import sampler
import random
import os
import csv


class Solver:
    def __init__(self, strategy_name: str, ained: AiNed):
        """
        Initialises strategy and board for solving simulations.

        :param strategy_name: Strategy name
        :param ained: AiNed object
        """
        self.ained = ained
        self.strategy_name = strategy_name

        # Add new strategies here
        self.strategies = {
                    "greedy": strategy.GreedyStrategy,
                    "stochastic": strategy.StochasticStrategy,
                    "simann": strategy.SimAnnStrategy
                    }

        self.strategy: strategy.Strategy = self.strategies[self.strategy_name](self.ained)

    def save_verdict(self, savefile_name: str, attempt: int, num_steps: int, success: bool, N: int):
        """
        This function writes to the csv file that collects all the important data from simulations.
        It is called at the end of a simulation to save all the important data from that simulation.

        :param savefile_name: The name of the csv file
        :param attempt: The number of the current simulation attempt.
        :param num_steps: The number of steps that the simulation took to solve the game.
        :param success: Whether the game was successfully solved or not.
        :param N: The board size.
        """
        csv_file = savefile_name + ".csv"
        coeff = self.ained.get_coefficients()[1]
        columns =  ["board_size", "strategy", "attempt", "step_count", "factor", "success"]
        os.makedirs("data", exist_ok=True)
        if not os.path.exists("data/" + csv_file):
            with open("data/" + csv_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(columns)       
        new_row = [N, str(self.strategy), attempt, num_steps, round(coeff, 2), success]
        with open("data/" + csv_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(new_row)

    def run_simulation_solve(self, N: int, pos: tuple[int, int], savefile_name: str, num_steps=-1, attempt=1, print_board=False, initial_state: list=None):
        """
        Runs a single simulation until either num_steps is reached or the game is successfully solved.

        :param N: The board size.
        :param pos: The starting position of the board in the AiNed memory.
        :param savefile_name: The name of the csv file
        :param num_steps: The number of steps that the simulation may take to solve the game. (-1 for unlimited).
        :param attempt: The number of the current simulation attempt.
        :param print_board: Whether the board should be printed to the console or not.
        :param initial_state: An optional initial state of the board in the AiNed memory.

        :return: Whether the game was successfully solved or not.
        """
        if initial_state is not None:
            self.ained.reconstruct_board(initial_state, pos[0], pos[1], N, N)
        else:
            # Randomly initialise a board
            for i in range(N):
                self.ained.set_bit(pos[0] + random.randint(0, N), pos[1] + random.randint(0, N), 1)
                self.ained.set_bit(pos[0] + random.randint(0, N), pos[1] + random.randint(0, N), 1)
                self.ained.commit()

        count = 0

        if print_board:
            self.ained.print_board(pos[0], pos[1], N, N)

        while self.ained.game_not_over(pos[0], pos[1], N, N) and count != num_steps - 1:
            step_taken = self.strategy.solve(N, pos)
            if step_taken:
                if print_board:
                    self.visualise(count, pos, N)
                count += 1

        success = not self.ained.game_not_over(pos[0], pos[1], N, N)
        self.save_verdict(savefile_name, attempt, count + 1, success, N)

        return success

    def multiple_simulations(self, N: int, pos: tuple[int, int], savefile_name: str, num_sim=1, num_steps=-1, print_boards=False, initial_state: list=None):
        """
        Run multiple simulations consecutively.

        :param N: The board size.
        :param pos: The starting position of the board in the AiNed memory.
        :param savefile_name: The name of the csv file.
        :param num_sim: The number of simulation that are carried out.
        :param num_steps: The number of steps that the simulation may take to solve the game. (-1 for unlimited).
        :param print_boards: Whether the board should be printed to the console or not.
        :param initial_state: An optional initial state of the board in the AiNed memory for each simulation.
        """
        curr_sim_num = 1
        print(f"Running {num_sim} simulations.\n")

        while curr_sim_num <= num_sim:
            print(f"Running simulation number {curr_sim_num}...")
            self.ained.clear() # wipe *the whole* ained memory clear before each simulation

            self.strategy = self.strategies[self.strategy_name](self.ained) # Reset the strategy to its initial state

            os.makedirs("data/" + str(self.strategy) + "/" + savefile_name, exist_ok=True)
            savefile_name = str(self.strategy) + "/" + savefile_name # Each simulation file is stored in their respective strategy folder

            string = f"Simulation {curr_sim_num} "
            string += "was a success!" if self.run_simulation_solve(N, pos, savefile_name, num_steps, curr_sim_num, print_boards, initial_state) else "has failed!"
            print(string, "\n")

            curr_sim_num += 1
        print("Done!")

    def visualise(self, count: int, pos: tuple[int, int], N: int):
        """Visualises simulation in the console"""
        print(f"Step {count + 1}:")
        self.ained.print_board(pos[0], pos[1], N, N)
        print("\n")


class Sampler:
    def __init__(self, sampler_name: str, ained: AiNed):
        """
        Initialises strategy and board for sampling the state space by walking through.

        :param sampler_name: Sampler name
        :param ained: AiNed object
        """
        self.ained = ained
        self.sampler_name = sampler_name

        # Add samplers here
        self.samplers = {
                    "MCMC": sampler.MCMC
                    }
        self.sampler = self.samplers[self.sampler_name](self.ained)

    def run_simulation_sample(self, N: int, pos: tuple[int, int], num_steps: int, print_board=False):
        """
        Runs a single simulation until num_steps is reached.

        :param N: The board size.
        :param pos: The starting position of the board in the AiNed memory.
        :param num_steps: The number of steps that the simulation may take to solve the game.
        :param print_board: Whether the board should be printed to the console or not.
        """
        # Randomly initialise a board
        for i in range(N):
            self.ained.set_bit(pos[0] + random.randint(0, N), pos[1] + random.randint(0, N), 1)
            self.ained.set_bit(pos[0] + random.randint(0, N), pos[1] + random.randint(0, N), 1)
            self.ained.commit()

        count = 1

        if print_board:
            self.ained.print_board(pos[0], pos[1], N, N)

        while count != num_steps:
            self.sampler.sample(N, pos) # Follow the sampling strategy (samples should be tracked in some csv file)
            if print_board:
                print(f"Step {count}:")
                self.ained.print_board(pos[0], pos[1], N, N)
                print("\n")
            count += 1

    def multiple_sample_chains(self, N: int, pos: tuple[int, int], num_steps: int, num_chain=1, print_boards=False):
        """
        Run multiple chains consecutively in order to analyse convergence.

        :param N: The board size.
        :param pos: The starting position of the board in the AiNed memory.
        :param num_steps: The number of steps that the simulation may take to solve the game.
        :param num_chain: The number of chains that are carried out.
        :param print_boards: Whether the board should be printed to the console during sampling or not.
        """
        curr_iter = 1
        print(f"Running {num_chain} simulations.\n")

        while curr_iter <= num_chain:
            self.sampler = self.samplers[self.sampler_name](self.ained) # Reset sampler to its initial state
            print(f"Running simulation number {curr_iter}...")
            self.ained.clear() # clear the *whole* AiNed module memory
            string = f"Chain {curr_iter} completed"
            self.run_simulation_sample(N, pos, num_steps, print_boards)
            print(string, "\n")

            curr_iter += 1
        print("Done!")

