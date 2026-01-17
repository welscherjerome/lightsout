#include "ained.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void ained_print_board(ained_t *handle, uint32_t start_row, uint32_t start_col, uint32_t num_row, uint32_t num_col){
    if( handle == NULL ){
        return;
    }
    printf("  | ");
    for(uint32_t column = 0; column < num_col; column++){
        printf("%d ", column);
    }
    printf("\n\n");
    for(uint32_t i = 0; i < num_row; i++){
        printf("%d | ", i);
        for(uint32_t j = 0; j < num_col; j++){
            printf("%d ", ained_get_bit(handle, start_row + i, start_col + j));
        }
        printf("\n");
    }
}

bool ained_game_not_over(ained_t *handle, uint32_t start_row, uint32_t start_col, uint32_t num_row, uint32_t num_col){
    for(uint32_t i = 0; i < num_row; i++){
        for(uint32_t j = 0; j < num_col; j++){
            if(ained_get_bit(handle, start_row + i, start_col + j) == 1){
                return true;
            }
        }
    }
    return false;
}

uint32_t* ained_get_board(ained_t *handle, uint32_t start_row, uint32_t start_col, uint32_t num_row, uint32_t num_col){
	uint32_t *board = calloc(num_row * num_col, sizeof(uint32_t));
	for(uint32_t row=0; row < num_row; row++){
		for(uint32_t col=0; col < num_col; col++){
			board[num_col * row + col] = ained_get_bit(handle, start_row + row, start_col + col);
		}
	}
	return board;
}

void ained_free_pointer(uint32_t* pointer){
	free(pointer);
}

void ained_flip_lights(ained_t *handle, uint32_t start_row, uint32_t start_col, uint32_t num_row, uint32_t num_col, uint32_t row, uint32_t col){
	if( row + start_row < start_row || row + start_row > start_row + num_row - 1 || col + start_col < start_col || col + start_col > start_col + num_col - 1 ){
                return;
	}
	uint32_t *old_board = ained_get_board(handle, start_row, start_col, num_row, num_col);
	ained_clear_word(handle, start_row, start_col);
	ained_set_bit(handle, start_row + row, start_col + col, 1);
	ained_commit(handle);
	// Black magic (likely force sync)
	ained_get_bit(handle, start_row, start_col);
	ained_set_bypass(handle, true);
	for (size_t i = 0; i < num_row * num_col; i++) {
		if(old_board[i] == 1){
        		ained_flip_isolated_bit(handle, start_row + (i / num_col), start_col + (i % num_col));	
		}
	}
	ained_set_bypass(handle, false);
	free(old_board);
}

void ained_reconstruct_board(ained_t *handle, uint32_t *board, uint32_t start_row, uint32_t start_col, uint32_t num_row, uint32_t num_col){
	ained_clear_word(handle, start_row, start_col);
	ained_set_bypass(handle, true);
	for (size_t i = 0; i < num_row * num_col; i++) {
                if( board[i] != 0 )
                        ained_flip_isolated_bit(handle, start_row + i / num_col, start_col + i % num_col);
        }
	ained_set_bypass(handle, false);

}
