import multiprocessing
import random
import math
import sys
import os
import csv
import copy
import argparse
import time
import numpy as np
from pyained.ained import AiNed


class GeneticAlgorithm:
    def __init__(self, N):
        self.N = N

    def generate_initial_state(self, num_lights=None):
        if num_lights is None:
            return [0 if 0.5 < random.random() else 1 for i in range(self.N ** 2)]
        else:
            matrix = [0 for i in range(self.N**2)]
            for i in range(num_lights):
                rand = random.randint(0, self.N**2 - 1)
                while matrix[rand] == 1:
                    rand = random.randint(0, self.N**2 - 1)
                matrix[rand] = 1
            return matrix




    def generate_population(self, pop_size: int, estimated_steps: int) -> list[list[int]]:
        population = list()
        for i in range(pop_size):
            population.append([random.randint(0, self.N ** 2) for j in range(estimated_steps)])
        return population
    
    def fitness_evaluate(self, population_chunk, initial_board, assigned_pos, coeff, num_sim):
        ained = AiNed()
        try:    
            results = {}

            ained.set_coefficients_euclidean(coeff)
            
            for chromosome in population_chunk:
                fitness_list = []
        
                for i in range(num_sim):
                    ained.reconstruct_board(initial_board, assigned_pos[0], assigned_pos[1], self.N, self.N)
            
                    solved = False
                    for idx, genome in enumerate(chromosome):
                        row = genome // self.N
                        col = genome % self.N
                
                        ained.flip_lights(assigned_pos[0], assigned_pos[1], self.N, self.N, row, col)
                
                        if not ained.game_not_over(assigned_pos[0], assigned_pos[1], self.N, self.N):
                            solved = True
                            break
            
                    if not solved:
                        fitness_list.append(self.N**2 - self.energy(ained.get_board(assigned_pos[0], assigned_pos[1], self.N, self.N)))
                    else:
                        fitness_list.append(self.N**2 + self.N)
                       
                conservative_fitness = np.mean(fitness_list)
            
                results[tuple(chromosome)] = conservative_fitness
            return results
        finally:
            ained.close()

    
    def evaluate_fitness_parallel(self, population: list[list[int]], initial_board: list[int], 
                                  pos_core_1=(0, 0), pos_core_2=(0, 16), coeff=0.1, num_sim=3) -> dict:
        """
        Splits the population and runs on 2 cores with different memory offsets.
        Note: You must provide a valid 'pos_core_2' that doesn't overlap with 'pos_core_1' in memory.
        """
        
        midpoint = len(population) // 2
        chunk_1 = population[:midpoint]
        chunk_2 = population[midpoint:]

        tasks = [
            (chunk_1, initial_board, pos_core_1, coeff, num_sim),
            (chunk_2, initial_board, pos_core_2, coeff, num_sim)
        ]

        with multiprocessing.Pool(processes=2) as pool:
            results_list = pool.starmap(self.fitness_evaluate, tasks)

        final_fitness_mappings = {**results_list[0], **results_list[1]}
        
        return final_fitness_mappings


    def run_genetic_algorithm(self, save_file_name, pop_size, coeff, num_generations=100, num_sim_per_chrom=100, boltzman=2, initial_mutation_rate=0.05, num_tests=1000, initial_num_lights=None):
        initial_board = self.generate_initial_state(initial_num_lights)
        estimated_steps = sum(initial_board)
        pop = self.generate_population(pop_size, estimated_steps)

        print("Initial board:\n")
        for i in range(self.N):
            for j in range(self.N):
                print(initial_board[i * self.N + j], end = " ")
            print()
        print(f"\nMaximum achievable fitness: {self.N**2 + self.N} (N**2 + N), estimated steps: {estimated_steps}")
        mutation_rate = initial_mutation_rate
        for generation in range(num_generations):
            fitness_mappings = self.evaluate_fitness_parallel(pop, initial_board, coeff=coeff, num_sim=num_sim_per_chrom)
            fitness_average = np.mean(list(fitness_mappings.values()))
            best_chromosome = tuple(self.pick_best_chromosome(fitness_mappings))
            sys.stdout.write(f"\033[{4}A")
            sys.stdout.flush()

            print(
                    f"Generation {generation + 1}:                     " +
                    f"\nBest Fitness = {fitness_mappings[best_chromosome]:0.2f}" +
                    f"\nAverage Fitness: {fitness_average:0.2f}"
                    )
            
            pop = self.create_next_generation(fitness_mappings, boltzman, mutation_rate)
            mutation_rate = max(0.5 * initial_mutation_rate * (1 + math.cos(generation * math.pi / num_generations)), 0.04)
            print("Mutation rate:", mutation_rate)

        print(f"Best chromosome for initial_board ({initial_board}):\n{best_chromosome}\n")
        timings, successes, lights_count = self.test(best_chromosome, initial_board, num_tests)
        print(f"\nChromosome took on average {np.mean(timings):0.2f} seconds to complete with on average {np.mean(lights_count):0.2f} lights left on and a total of {sum(successes)} out of {num_tests} successes.\n\n\n ")
        self.save_verdict(save_file_name, initial_board, coeff, num_generations, pop_size, lights_count, successes, timings, num_tests)
            
    def energy(self, state: list[int]) -> int:
        return sum(state)

    def selection(self, fitness_mappings, boltzman=2, num_parents=2):
        chromosomes = list(fitness_mappings.keys())
        fitness_values = list(fitness_mappings.values())
        max_fitness = max(fitness_values)

        k2 = np.var(fitness_values)
        std_dev = np.sqrt(k2)
        
        if std_dev == 0:
            std_dev = 1e-6

        boltzman_weight = boltzman/std_dev

        weights = list()
        for value in fitness_values:
            weights.append(math.exp(boltzman_weight * (value - max_fitness))) # max_fitness substraction is necessary to avoid overflow

        selected_parents = random.choices(chromosomes, weights=weights, k=num_parents)

        return selected_parents
    
    def mutation(self, chromosome: list, gamma=0.05):
        chromosome = list(chromosome)
        for idx in range(len(chromosome)):
            if random.random() < gamma:
                total_buttons = self.N * self.N 
                new_gene = random.randint(0, total_buttons - 1)
                chromosome[idx] = new_gene
        return chromosome

    def crossover(self, parent1: list, parent2: list) -> tuple[list, list]:
        child1 = []
        child2 = []
        
        for i in range(len(parent1)):
            # 50% chance to swap genes at this specific index
            if random.random() > 0.5:
                child1.append(parent1[i])
                child2.append(parent2[i])
            else:
                child1.append(parent2[i])
                child2.append(parent1[i])
                
        return child1, child2

    def create_next_generation(self, fitness_mappings, boltzman, mutation_rate):
        new_population = list()
        
        current_population = list(fitness_mappings.values())
        best_chromosome = self.pick_best_chromosome(fitness_mappings)
        new_population.append(best_chromosome)

        while len(new_population) < len(current_population):
        
            parent1, parent2 = self.selection(fitness_mappings, boltzman)
        
            child1 = copy.deepcopy(parent1)
            child2 = copy.deepcopy(parent2)

            child1 = self.mutation(child1, mutation_rate)
            child2 = self.mutation(child2, mutation_rate)
            new_population.append(child1)
            
            if len(new_population) < len(current_population):
                new_population.append(child2)
        return new_population

    def pick_best_chromosome(self, fitness_mappings):
        if not fitness_mappings: return None, None    
        return max(fitness_mappings.items(), key=lambda item: item[1])[0]


    def test(self, chromosome, initial_board, test_size=1000):
        ained = AiNed()
        timings = list()
        successes = list()
        final_lights = list()
        for i in range(test_size):
            ained.reconstruct_board(initial_board, 0, 0, self.N, self.N)
            
            solved = False
            step_count = 0
            t0 = time.time()
            for idx, genome in enumerate(chromosome):
                row = genome // self.N
                col = genome % self.N
            
                ained.flip_lights(0, 0, self.N, self.N, row, col)
                step_count += 1

                ained.print_board(0, 0, self.N, self.N)
                if idx != len(chromosome) - 1:
                    sys.stdout.write(f"\033[{self.N + 2}A")
                    sys.stdout.flush()
                               
                if not ained.game_not_over(0, 0, self.N, self.N):
                    solved = True
                    break
            t1 = time.time()
            final_board = ained.get_board(0, 0, self.N, self.N)
            num_lights_on = sum(final_board)
            
            final_lights.append(num_lights_on)
            successes.append(1 if solved else 0)
            timings.append(t1 - t0)
            print()

        return timings, successes, final_lights

    def save_verdict(self, savefile_name: str, initial_config: list[int], coeff: float, num_gen: int, pop_size: int, num_lights_left_on: list[int], successes: list[int], timings: list[float], num_tests=1000):
        """
        This function writes to the csv file that collects all the important data from simulations.
        It is called at the end of a simulation to save all the important data from that simulation.

        :param savefile_name: The name of the csv file
        :param attempt: The number of the current simulation attempt.
        :param num_steps: The number of steps that the simulation took to solve the game.
        :param success: Whether the game was successfully solved or not.
        :param N: The board size.
        """

        for i in range(num_tests):
            csv_file = savefile_name + ".csv"
            columns =  ["board_size", "initial_config", "num_initial_lights", "coeff", "num_generations", "pop_size", "num_lights_left_on", "success", "runtime"]
            os.makedirs("data", exist_ok=True)
            if not os.path.exists("data/Genetic/" + csv_file):
                with open("data/Genetic/" + csv_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
            new_row = [self.N, initial_config, sum(initial_config), round(coeff, 3), num_gen, pop_size, num_lights_left_on[i], successes[i], timings[i]]
            with open("data/Genetic/" + csv_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(new_row)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a Genetic Algorithm solver for Lights Out.")

    # Positional or Optional arguments
    parser.add_argument("-f", "--file_name", type=str, required=True, help="Name of the output file. [Required]")
    parser.add_argument("-N", "--size", type=int, default=5, help="Grid size (N x N). [Default: 5]")
    parser.add_argument("-g", "--generations", type=int, default=50, help="Number of generations. [Default: 50]")
    parser.add_argument("-p", "--pop_size", type=int, default=200, help="Population size. [Default: 200]")
    parser.add_argument("-c", "--coeff", type=float, default=0.02, help="Coefficient factor. [Default: 0.01]")
    parser.add_argument("-b", "--boltzman", type=float, default=3, help="Boltzmann factor. [Default: 3]")
    parser.add_argument("-m", "--mutation", type=float, default=0.5, help="Initial mutation rate.  [Default: 0.3]")
    parser.add_argument("-l", "--lights", type=int, default=None, help="Number of initial lights. [Default: None (random)]")

    args = parser.parse_args()

    print(f"Running GA: Size={args.size}, Gen={args.generations}, Pop={args.pop_size}, "
          f"Coeff={args.coeff}, Boltz={args.boltzman}, Mut={args.mutation}")

    # Pass the arguments to your class and function
    genAlg = GeneticAlgorithm(args.size)
    genAlg.run_genetic_algorithm(
        save_file_name=args.file_name,
        num_generations=args.generations, 
        pop_size=args.pop_size, 
        coeff=args.coeff, 
        boltzman=args.boltzman, 
        initial_mutation_rate=args.mutation,
        initial_num_lights=args.lights
    )
