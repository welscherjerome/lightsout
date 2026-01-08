#include <stdint.h>

void ained_print_board(ained_t *handle, uint32_t start_row, uint32_t start_col, uint32_t num_row, uint32_t num_col);
// prints a lights out game board of the given size


uint32_t* ained_get_board(ained_t *handle, uint32_t start_row, uint32_t start_col, uint32_t num_row, uint32_t num_col);
// provides array of bits from board

void ained_free_board(uint32_t* board);
// frees memory of the board array

bool ained_game_not_over(ained_t *handle, uint32_t start_row, uint32_t start_col, uint32_t num_row, uint32_t num_col);
// checks if the game is over

