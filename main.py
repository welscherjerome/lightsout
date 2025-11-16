#!/usr/bin/env python3
import argparse
from pyained.ained import AiNed
from simulation import Solver, Sampler

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run stochastic Lights Out simulations."
    )

    # Simulation parameters
    parser.add_argument(
        "-N", "--size", type=int, required=True,
        help="[Required] Size of the board")
    parser.add_argument(
        "-t", "--num_steps", type=int, required=True,
        help="[Required] Maximum number of steps per simulation (-1 for unlimited)"
    )
    parser.add_argument(
        "-i", "--num_iter", type=int, default=1,
        help="[Required] Number of simulations to run"
    )
    parser.add_argument(
        "-f", "--savefile", type=str, default=None,
        help="[Required] Name for the csv file that collects the data"
    )
    parser.add_argument(
        "-c", "--coeff", type=float, required=True,
        help="[Required] Factor for the coefficient matrix distance formula"
    )

    parser.add_argument(
        "-m", "--method", type=str, choices=["greedy", "stochastic", "simann", "MCMC"], default="greedy",
        help="[Optional] Method to use (e.g., greedy, MCMC, etc.) [default is greedy]"
    )
    parser.add_argument(
        "-s", "--show", action="store_true",
        help="[Optional] Show the solver or sampler in the console as it goes through the state space"
    )
    parser.add_argument(
        "-o", "--initial_state", type=str, default=None,
        help="[Optional] Name of initial board state file (example file is provided) [default is None]"
    )
    parser.add_argument(
        "-d", "--distance", type=str, choices=["manhattan", "euclidean"], default = "euclidean",
        help="[Optional] Distance formula for the coefficient calculation [default is euclidean]"
    )

    return parser.parse_args()


def main():
    args = parse_args()
    
    ained = AiNed()

    if args.distance == "manhattan":
        ained.set_coefficients_manhattan(args.coeff)
    else:
        ained.set_coefficients_euclidean(args.coeff)
    
    if args.method == "MCMC": # Use sampler simulation
        pos = 0, 0
        method = Sampler(sampler_name=args.method, ained=ained)

        if args.num_iter > 0:
            method.multiple_sample_chains(
                N=args.size,
                pos=pos,
                num_steps=args.num_steps,
                num_chain=args.num_iter,
                print_boards=args.show
            )

        print("Sampling success!")

    else: # Use solver simulation
        method = Solver(strategy_name=args.method, ained=ained)
        pos = 0, 0

        if args.initial_state is not None:
            with open(args.initial_state, "r") as f:
                initial_state = [int(x) for line in f for x in line.strip().split()]
        else:
            initial_state = None

        if args.num_iter > 0:
            method.multiple_simulations(
                N=args.size,
                pos=pos,
                savefile_name=args.savefile,
                num_sim=args.num_iter,
                num_steps=args.num_steps,
                print_boards=args.show,
                initial_state=initial_state
            )


if __name__ == "__main__":
    main()

