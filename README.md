# lightsout

Bachelor Thesis project about analysing a stochastic _Lights Out_ game 

\- _specifically designed for the PYNQ-Z2 single board computer with the AiNed emulator installed in the FPGA region_

### Version 1.1.0

## Description

This repository contains all the most important code that was implemented and used for the Bachelor Thesis project 

###### "Learning about Probabilistic Memory by Playing Whack-a-Bit: A Lights Out Game Analysis on Probabilistic Hardware"

This repository implements a complete interface to run custom or pre-composed solving and sampling strategies. 
A Genetic Algorithm is also available separately from the interface.

The neural network implementation from the thesis, a visualize helper script and several bash scripts are also available in addition to the interface and genetic algorithm.

This README provides a comprehensive guide to executing the associated code and guides the reader through the implementation of custom strategies.

## Installation

To install this repository on the AiNed board, you have two options:

- You can either download it on the board's connected device and copy the repository over via the "scp -r <path_to_repo_folder>" command
- Or you can establish an internet connection between the board and the connected device to directly clone the repository onto the board
## Additional Setup

It is recommended to first get accustomed to the AiNed board before running the interface and implementing new strategies. It is advised to first run and understand the unmodified AiNed repository. This is especially important when making adjustments to the C code.

An internet connection from the board to the connected device might be crucial for the installation of Python packages.

## User Manual

##### Foreword on _Concurrency_
Before explaining the use of the interface, it must be noted that boards can only run inside the by AiNed predefined 8x8 words due to the usage of the **clear_word()** pyained method
(see scripts/pyained/README.md file for documentation)

In case that boards larger than 8x8 are intended to be used, this method must be replaced by the **clear()** method which clears the entire memory instead. This however prevents concurrency due to interference with other boards on the shared memory. Thus changes to the C files must be made to account for larger boards.

To run multiple processes concurrently via the command-line, simply set up multiple command-line SSH connections and run commands in each command-line individually.

**Important notes:**
- **The factor between all concurrently running processes _must_ be the _same_. Violation of this rule leads to corrupted and false data.**

- **Boards _must_ be separated by a fixed margin due to the interference of the stochastic effect. By default the range of the stochastic spread is 4 cells in each direction around the flipped bit. Therefore each board must be separated by _at least_ a whole 8x8 word.**

- **It is recommended to run the boards on the top left corner of a word as they extend to the right and to the bottom. Example positions for board include:**

	**- row: 0, column: 0**
  
	**- row: 16, column: 16**
  
	**- row: 0, column: 16**
  
	**- row: 16, column: 0**
  
	**- row: 32, column: 16**
  
	**- etc...**

**Simply run the boards at positions that follow the 16 space pattern.**

##### The main.py file - _running simulations intuitively_

Let's get started with the core of the interface.
The main.py file uses the _argparse_ library to allow direct parameterised execution from the command-line.
Here, bash scripts can be used to automate the execution of pre-defined parameter setting batches.

_argparse_ uses flags to let the user adjust parameters.
Some parameters are mandatory and some are optional and have a default value.
Use the command  ```sudo python main.py -h``` to print an simple and straight forward documentation on all the flags and the values that they can take. Here you also see which flags are mandatory and which are optional.

Here is an example command to run the _Greedy_ strategy on a _5x5_ board a _thousand_ times, each time taking steps _until the game is solved_ at a stochastic factor of _0.05_ 
at position _(row: 0, column: 0)_ in the AiNed shared memory and saving the collected data in a CSV file named _greedy_05_

```
sudo python main.py -m greedy -N 5 -i 1000 -t -1 -c 0.05 -p 0 0 -f "greedy_05"
```

See the available bash scripts on inspiration on how to run parameterised batches.

Finally, here is an example command to run the _MCMC_ sampling algorithm on a _5x5_ board over _3_ chains, each chain taking _50000_ steps at a stochastic factor of _0.25_ at position (row: 16, col: 16) in the AiNed shared memory and saving the collected data in the MCMC folder.
**The files are automatically named in an incrementing fashion. No custom names are necessary.**

```
sudo python main.py -m MCMC -N 5 -i 3 -t 50000 -c 0.25 -p 16 16 -f "MCMC"
```
##### The strategy.py file - _implementing custom strategies_

The strategy.py file allows the implementation of custom solving strategies for the user, taking away the responsibility of adjusting the code for each strategy.

For this guide we will take a look at the implementation of the simple stochastic strategy.

```
class StochasticStrategy(Strategy):
    def __init__(self, ained: AiNed, pos: tuple[int, int], N: int):
        super().__init__(ained, pos, N)
    
    def solve(self) -> bool:
        row = int(random.randint(0, self.N))
        column = int(random.randint(0, self.N))
        self.ained.flip_lights(row, column)
        return True

    def __str__(self):
        return "Stochastic"
```

This strategy contains the minimal components that are required for the strategy to run.

\- Class Composition
To begin implementing a strategy, first inherit from the strategy class.

\- the \_\_init\_\_ method
Next define the initialisation method by providing the three core parameters to the parent class via super().

\- the solve method
Then you implement the core solving strategy. This method is called by the simulation.
It is required that some part of this method affects the game board in some way. Yet not every method call is required to end up in a step.
A return statement must be provided to signal to the simulation whether a step was taken or not. 

This is crucial for data collection as only actual steps are recorded for data analysis.

\- the \_\_str\_\_ method
This is the final mandatory method that defines the folder name where the collected data is stored.

More complex examples such as the Greedy strategy and Simulated Annealing strategies are provided in the strategy.py file.

Next, go to the simulation.py file and add your strategy to the strategy dictionary with the command-line call-key as the key:

```
self.strategies = {
                    "greedy": strategy.GreedyStrategy,
                    "stochastic": strategy.StochasticStrategy,
                    "simann": strategy.SimAnnStrategy,
                    "simannAdapt": strategy.SimAnnAdaptStrategy
                    }
```

Finally you need to go to the main.py file and add the call-key to the parser choices:

```
parser.add_argument(
        "-m", "--method", 
        type=str, 
        choices=["greedy", "stochastic", "simann", "simannAdapt", "MCMC"], < here
		default="greedy",
		help="[Optional] Method to use (e.g., greedy, MCMC, etc.) 
		      [default is greedy]"
    )
```

Done!

##### The visualize.py file - _Human-readable concurrency monitoring_

This script was created in case that the user wishes to observe the shared memory in real-time.

This may be useful for debugging or for observation of speed, progress or freezing patterns.

**Note: This file does _not_ affect concurrency directly due to its read-only nature.**
	  **However, the process may take some of the processing power of a core.**
	  **This might affect the solving speed of one of the concurrently running algorithms;**
	  **time readings are false either way, so use at own discretion.**
	  **This script _is_ perfectly safe to use in combination with a single process because of the**
	  **2-core board architecture.**

##### The neural_net.py file - _Advanced Data Modelling_

This is the neural network that was used for the Bachelor Thesis.
This model can be trained on any step_count or runtime data for advanced algorithmic analysis beyond computationally feasible stochastic factors.

It must be noted that the parameters may need adjustment for different strategies and different sizes of training data and that vast amounts of data is required to predict accurate behaviour.

The model for the Bachelor Thesis was trained on factors in the interval \[0.05, 0.5] at a step interval of 0.05. 1000 simulations were used for training for each factor, except for 0.45 and 0.5 where, due to time constraints, only 200 simulations were recorded, leading to a total of 8400 simulations.

## Issues and Questions

If you encounter any issues or have any questions relating to my package, try to reach out to jerome.welscher@ru.nl (preferred) or welscherjerome@gmail.com (in case there is no response)

I will not be in possession of the board anymore but I might be able to help from a distance given enough context.

## Citations

This code is built on top of the ained repository that provides the base framework for most functions. It uses the _modified_ code files that are available in this project.

The license is provided at the root of this repository.

[Original GitHub repository](https://github.com/AiNedMemory/AiNedMemory)
