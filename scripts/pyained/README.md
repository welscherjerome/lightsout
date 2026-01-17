# PyAiNed: a Lights Out game AiNed modification wrapped in Python

### Version 1.2.0

## Description

This package is a Python wrapper around a modified version of the AiNed repository code.
This package mainly allows for the implementation of the stochastic Lights Out game.
It does not provide all ained.c functions for use and instead only provides the necessary and most useful function for the Lights Out game.
This package contains both C and Python code.

## Installation

Installing this package is possible in two ways. 
Either pip install this pyained directory on the board (requires Internet connection)
or move the ained\_c.so, the mod\_lightsout.so and the ained.py file in your target project directory and import the python file.

## Additional Setup

No additional setup is required. 
This package only provides easy access to the memory to support an implementation of the Lights Out game and does not provide a full Lights Out game implementation by itself.
Most methods in the AiNed class are geared towards specific use in the Lights Out game.

## Documentation

### Classes 

- **AiNed**

This class contains all the functions and initialises the handle that allows for interaction with the memory for ained.
Instantiate one or multiple AiNed objects to gain access to the shared memory.

### AiNed class methods

- **close()**

This function severs the connection to the shared memory and frees memory usage.

_- Connection is automatically severed if the process is killed_

_- This function is usually only necessary in programs that run multiple processes concurrently_

- **get\_bit(row, col)**

This function simply allows retrieving a bit (0 or 1) from the current state of the shared memory given the row and column in the memory.

- **set\_bit(row, col, value)**

This function prepares the memory to change a bit on the specified coordinates to 0 or 1.
Allows for multiple bits to be set at once.

_- Requires commit() to be called afterwards._

- **commit()**

This function commits the staged changes to the memory and executes the stochastic effect according to the coefficients.

- **flip\_isolated\_bit(row, col)**

This function allows the flipping of a bit given a row and column coordinate without affecting neighbour bits.

_- This function uses locks and may slow down processes that run concurrently._

- **flip\_lights(start\_row, start\_col, num\_row, num\_col, row, col)**

This function flips a light given the row and column coordinates within a board. Additionally, the starting row, starting column, height and width of the board must be specified.
This function affects neighbour bits.

_- This function uses locks and may slow down processes that run concurrently._

- **clear()**

This function sets all bits in the ained shared memory to 0.

_- This function prevents the program from running concurrently with other processes that use the shared memory_

- **clear_word(row, col)**

This function sets all bits in the word that contains the bit (row, col) in the ained shared memory to 0.

_- This function allows the program to run concurrently with other processes using shared memory, provided they do not access the same word simultaneously._

- **set\_coefficients\_euclidean(factor: float)**

This function adjusts the _low_ coefficients using the euclidean distance formula. The factor argument must be in between 0 and 1.

_- To resolve unexpected behaviour, consider modifying the function to target high coefficients by setting the hardcoded argument to 0._

_- For this implementation, generally only the low coefficients matter (Probabilities of flipping from 0 to 1)_

- **set\_coefficients\_manhattan(factor: float)**

This function adjusts the _low_ coefficients using the manhattan distance formula. The factor argument must be in between 0 and 1.

_- To resolve unexpected behaviour, consider modifying the function to target high coefficients by setting the hardcoded argument to 0._

_- For this implementation, generally only the low coefficients matter (Probabilities of flipping from 0 to 1)_

- **print\_coefficients()**

This function prints the low coefficients in a human-readable manner. 

_- For this implementation, generally only the low coefficients matter (Probabilities of flipping from 0 to 1)_

- **get\_coefficients()**

This function returns a python list of length 25 of all the bottom-right low coefficients in a 1D shape.

_- For this implementation, generally only the low coefficients matter (Probabilities of flipping from 0 to 1)_

- **print\_board(start\_row, start\_col, num\_row, num\_col)**

This function prints the current board given start row, start column, height and width in a human-readable manner.

- **game\_not\_over(start\row, start\_col, num\_row, num\_col)**

This function evaluates a board on the given coordinates if it has been solved.

- **get\_board(start\_row, start\_col, num\_row, num\_col)**

This function returns a 1D shaped list of size _num\_row * num\_col_ of the bits in the shared memory given a board's initial coordinates and its dimensions.

- **reconstruct\_board(board, start\_row, start\_col, num\_row, num\_col)**

This function allows reconstructing a given 1D board list on the given coordinates given the board dimensions.

_- This function uses locks and may slow down processes that run concurrently._

- **def construct_random_board(start_row, start_col, num_row, num_col)**

This function constructs a random board of a given dimension on the given coordinates.
Once finished, the constructed board is returned for further use.

_- This function uses locks and may slow down processes that run concurrently._

## Recommended Use

When planning on running multiple processes concurrently, it is recommended to work with the clear_word() method and to reduce the use of functions that lock the shared memory to a minimum. 

When planning the distance between boards, keep in mind the range of the stochastic flip spread.

Concurrency is naturally improved in computationally heavy algorithms where data processing takes longer than taking steps.

## Issues and Questions

If you encounter any issues or have any questions relating to my package, try to reach out to jerome.welscher@ru.nl

I will not be in possession of the board anymore but I might be able to help from a distance given enough context.

## Citations

This code is built on top of the ained repository that provides the base framework for most functions. It uses the _modified_ code files that are available in this project.

The license is provided at the root of this repository.

[Original GitHub repository](https://github.com/AiNedMemory/AiNedMemory)
