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

import ctypes
import os

here = os.path.dirname(os.path.abspath(__file__))
ained_path = os.path.join(here, "ained_c.so")
lightsout_path = os.path.join(here, "mod_lightsout.so")

lib = ctypes.CDLL(ained_path)
lib_lo = ctypes.CDLL(lightsout_path)

# This is defining the types for each function from ained.c that we want to use

lib.ained_init.restype = ctypes.c_void_p
lib.ained_set_bit.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
lib.ained_get_bit.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]
lib.ained_get_bit.restype = ctypes.c_uint32
lib.ained_commit.argtypes = [ctypes.c_void_p]
lib.ained_clear_memory.argtypes = [ctypes.c_void_p]
lib.ained_print_coefficients.argtypes = [ctypes.c_void_p]
lib.ained_print_coefficients.restype = None
lib.ained_set_coefficients_euclidean.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_int]
lib.ained_set_coefficients_euclidean.restype = None
lib.ained_set_coefficients_manhattan.argtypes = [ctypes.c_void_p, ctypes.c_float, ctypes.c_int]
lib.ained_set_coefficients_manhattan.restype = None
lib.ained_flip_isolated_bit.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
lib.ained_print_memory.argtypes = [ctypes.c_void_p]
lib.ained_get_coefficient_array.argtypes = [ctypes.c_void_p]
lib.ained_get_coefficient_array.restype = ctypes.POINTER(ctypes.c_float)
lib.ained_set_bypass.argtypes = [ctypes.c_void_p, ctypes.c_bool]

lib_lo.ained_game_not_over.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
lib_lo.ained_game_not_over.restype = ctypes.c_bool
lib_lo.ained_print_board.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
lib_lo.ained_get_board.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
lib_lo.ained_get_board.restype = ctypes.POINTER(ctypes.c_uint32)
lib_lo.ained_free_pointer.argtypes = [ctypes.c_void_p]
lib_lo.ained_flip_lights.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]

class AiNed:
    def __init__(self):
        # This is also done in the C code - initialization
        self.handle = lib.ained_init()
        self.length = ctypes.c_size_t()
        self.memory_ptr = lib.ained_get_memory(self.handle, ctypes.byref(self.length))

    def get_bit(self, row, col):
        """Gets bit from memory given a row and a column"""
        return lib_lo.ained_get_bit(self.handle, row, col)

    def commit(self):
        """Commits chhanges to memory. This function must be called after setting bits"""
        lib.ained_commit(self.handle)

    def set_bit(self, row, col, value):
        """Sets bit in memory to the specified value given a row and a column"""
        lib.ained_set_bit(self.handle, row, col, value)
    
    def flip_isolated_bit(self, row, col):
        """This function flips a bit in the memory without affecting neighbours given a row and a column"""
        current_bit = self.get_bit(row, col)
        lib.ained_set_bypass(self.handle, True)
        lib.ained_flip_isolated_bit(self.handle, row, col, 1 - current_bit)
        lib.ained_set_bypass(self.handle, False)

    def flip_lights(self, start_row, start_col, num_row, num_col, row, col):
        """Flips a light given start of board, size of board and coordinates within board"""
        lib_lo.ained_flip_lights(self.handle, start_row, start_col, num_row, num_col, row, col)

    def clear(self):
        """Sets all bits in memory to 0"""
        lib.ained_clear_memory(self.handle)

    def set_coefficients_euclidean(self, factor: float):
        """Sets the low coefficients of the coefficient matrix to certain values by using the Euclidean distance formula"""
        assert (0 <= factor <= 1), "factor must be in range [0, 1]"
        lib.ained_set_coefficients_euclidean(self.handle, ctypes.c_float(factor), ctypes.c_int(1))

    def set_coefficients_manhattan(self, factor: float):
        """Sets the low coefficients of the coefficient matrix to certain values by using the Manhattan distance formula"""
        assert (0 <= factor <= 1), "factor must be in range [0, 1]"
        lib.ained_set_coefficients_manhattan(self.handle, ctypes.c_float(factor), ctypes.c_int(1))

    def print_coefficients(self):
        """Prints the coefficients in a human-readable manner"""
        lib.ained_print_coefficients(self.handle)

    def get_coefficients(self):
        """Returns a 1D array of size 25, containing the low coefficients from the coefficient matrix"""
        pointer = lib.ained_get_coefficient_array(self.handle)
        coeffs = [pointer[i] for i in range(25)]
        lib_lo.ained_free_pointer(pointer)
        return coeffs

    def print_board(self, start_row, start_col, num_row, num_col):
        """Prints a board of given starting position and size in a human-readable manner"""
        lib_lo.ained_print_board(self.handle, start_row, start_col, num_row, num_col)

    def game_not_over(self, start_row, start_col, num_row, num_col):
        """Returns 'False' if all bits on the specified board are zero. Returns 'True' otherwise"""
        return lib_lo.ained_game_not_over(self.handle, start_row, start_col, num_row, num_col)

    def get_board(self, start_row, start_col, num_row, num_col):
        """Returns a 1D array of the bits of size num_row * num_col of the specified board"""
        pointer = lib_lo.ained_get_board(self.handle, start_row, start_col, num_row, num_col)
        board = [pointer[i] for i in range(num_row * num_col)]
        lib_lo.ained_free_pointer(pointer)
        return board

    def reconstruct_board(self, board, start_row, start_col, num_row, num_col):
        """Reconstructs a board according to a 1D array of size num_row * num_col in the memory at the specified coordinates"""
        assert (len(board) == num_row * num_col), "Specified board size must be equal to the length of the 1D board array that is to be reconstructed"
        lib_lo.ained_reconstruct_board.argtypes = [ctypes.c_void_p, ctypes.c_uint32*len(board), ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
        lib_lo.ained_reconstruct_board(self.handle, (ctypes.c_uint32 * len(board))(*board), start_row, start_col, num_row, num_col)
