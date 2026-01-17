/*
 * Copyright (c) 2024 Radboud Universiteit
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
#pragma once

#include "arm_shared_memory_system.h"
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/**
 * @defgroup AINED AiNed
 *
 * @brief High level API for access to AiNed in FPGA fabric.
 *
 * This library gives high level access to the AiNed implementation in the FPGA
 * fabric. Providing both raw memory access for reading/writing and an high
 * level API. It also provides several helper functions for testing and
 * reproducability.
 *
 * Example code
 * @code
 * int main ( int argc, char **argv )
 * {
 *   ained_t *handle = ained_init();
 *   if ( handle == NULL ) {
 *      return EXIT_FAILURE;
 *   }
 *
 *   // Clear the memory, set it all to 0.
 *   ained_clear_memory(handle);
 *
 *   // Print the memory in human readable format.
 *   ained_print_memory(handle);
 *
 *   // Force bit on column 8 and row 8 to 1.
 *   ained_set_bit(handle, 7, 7, 1);
 *   // Force bit on column 7 and row 7 to 0.
 *   ained_set_bit(handle, 6,6, 0);
 *   // Commit the requested change.
 *   ained_commit(handle);
 *
 *   // Print the memory in human readable format.
 *   ained_print_memory(handle);
 *
 *   // Destroy and cleanup the interface.
 *   ained_destroy(handle);
 *   return EXIT_SUCCESS;
 * }
 * @endcode
 *
 * @{
 */

/**
 * Handle used for access to the FPGA implementation.
 * Member of this structure are annonymous as they should not be accessed
 * directly.
 */
typedef struct ained ained_t;

/**
 * Indicate high/low probability coefficient.
 */
typedef enum {
  /** The High coefficient */
  AINED_COEFF_HIGH = 0,
  /** The Low coefficient */
  AINED_COEFF_LOW = 1,
} ained_coeff_t;

/**
 * Opens access to the AiNed FPGA implementation and creates a handle.
 * The handle needs to be free'ed with #ained_destroy.
 *
 * A normal structure looks like:
 * @code
 *
 * ained_t *handle = ained_init();
 * if ( handle != NULL ) {
 *    // Handle error.
 * }
 *
 * ained_destroy(handle);
 *
 * @endcode
 *
 * @returns a newly allocated #ained_t handle or NULL on failure.
 *
 * @warning Only one handle should be active at the same time. Data integratie
 * cannot be guaranteed if multiple are used simultanious for interaction.
 */
ained_t *ained_init(void);

/**
 * @param handle The handle to the AiNed module.
 *
 * Release the FPGA region and free all allocated memory.
 * It is safe to pass \p handle a NULL pointer.
 */
void ained_destroy(ained_t *handle);

/**
 * @}
 */

/**
 * @defgroup INTERFACE Interaction methods
 *
 * @brief Methods for interaction with the memory.
 *
 * Interfacing methods.
 *
 * Allows interacting with the memory region, either via direct access or via an
 * API.
 *
 *
 * @ingroup AINED
 * @{
 */

/**
 * @param handle The handle to the AiNed module.
 *
 * Commit changes to the memory previously set by #ained_set_bit.
 *
 * \warning If neither #ained_set_word or #ained_set_bit, this method does
 * nothing and prints an error message.
 */
void ained_commit(ained_t *handle);

/**
 * @param handle The handle to the AiNed module.
 * @param row The row to set the bit on.
 * @param column The column to set the bit.
 * @param value The value to set the bit.
#include "ained.h"
 *
 * Change a bit in the memory.
 *
 * \warning
 * If an aditional bit is set that falls outside of the 64bit word, this method
 * will throw and error and exit the program: Cannot set bit in more then one
 * word in a single commit.
 *
 * Example usage:
 *
 * @code
 * ained_set_bit(handle, 6 ,6, 1);
 * ained_set_bit(handle, 7 ,7, 1);
 * ained_commit(handle);
 * @endcode
 */
void ained_set_bit(ained_t *handle, const uint32_t row, const uint32_t column,
                   const uint32_t value);

/**
 * @param handle The handle to the AiNed module.
 * @param enable Enable bypass handling.
 *
 * Enable bypass, allowing to direct write values to the memory.
 *
 * \warning By enabling the bypass, the memory region will act as a traditional
 * memory.
 */
void ained_set_bypass(ained_t *handle, bool enable);

/**
 * @param handle The handle to the AiNed module.
 * @param[out] length The size of the memory in 64bit words.
 *
 * Get access to the memory.
 * You can read this memory like normal memory, when writing make sure you
 * always write a full 64bit word that is 64bit aligned. Do not cast this to a
 * smaller data type and do partial writes.
 *
 * You can use #ained_set_mask to set a write mask, this specifies what bits to
 * set in the 64bit word.
 *
 * An example:
 *
 * @code
 * size_t length = 0;
 * uint64_t volatile *mem = ained_get_memory(handle, &length);
 * ained_set_mask(handle, 0x8000800080008000);
 * mem[1] = 0xFFFFFFFFFFFFFFFF;
 * @endcode
 *
 * \warning This pointer gives low-level access to the FPGA region, writing out
 * side of the memory or with invalid alignment/word size can result in
 * unexpected behaviour or even full-system lockups.
 *
 * @returns A uint64_t volatile pointer to the memory.
 */
uint64_t volatile *ained_get_memory(ained_t *handle, size_t *length);

/**
 * @param handle The handle to the AiNed module.
 * @param mask  The write mask to set
 *
 * Set the write mask, only the masked bits are written in the word.
 * Either write by directly write to memory via #ained_get_memory or
 * with #ained_set_mask followed by a #ained_commit.
 */
void ained_set_mask(ained_t *handle, const uint64_t mask);

/**
 * @param handle The device handle
 * @param offset The offset (in 64bit) multiple of the word to write in memory.
 * @param word The value to write
 *
 * To write a word directly run:
 *
 * @code
 * ained_set_mask(handle, 0xAAAAAAAAAAAAAAAA);
 * ained_set_word(handle, 16, 0xFFFFFFFFFFFFFFFF);
 * ained_commit(handle);
 * @endcode
 *
 */
void ained_set_word(ained_t *handle, uint32_t const offset,
                    uint64_t const word);
/**
 * @}
 */
/**
 * @defgroup COEFF Coefficients Methods
 *
 * @brief Interact with the probability coefficients methods.
 *
 * @ingroup AINED
 * @{
 */

/**
 * @param handle The handle to the AiNed module.
 * @param index The coefficient group to update.
 * @param value The new coefficient value.
 *
 * Update the coefficient value. There are 4 values (8 bit) packed in each
 * group, 6 groups in total.
 *
 * This is low level access method to the registers.
 */
void ained_set_coefficients(ained_t *handle, uint32_t index, uint32_t value);

/**
 * @param handle The handle to the AiNed module.
 * @param index The coefficient group to read.
 *
 * There are 4 values (8 bit) packed in each group, 6 groups in
 * total.
 *
 * This is low level access method to the registers.
 * @returns The coefficient value.
 */
uint32_t ained_get_coefficients(ained_t *handle, uint32_t index);

/**
 * @param handle The handle to the AiNed module.
 * @param factor The fall off factor.
 * @param co_index The coefficient set to check.
 *
 * Update the coefficients table based on euclidean distance from the center
 * (0,0) and the target, given the specified `factor`.
 * \f[ distance_{r,c} = \sqrt(r^2 + c^2)\\
 *     value_{r,c} = factor^{distance_{r,c}}
 * \f]
 **/
void ained_set_coefficients_euclidean(ained_t *handle, const float factor,
                                      const ained_coeff_t co_index);

/**
 * @param handle The handle to the AiNed module.
 * @param factor The fall off factor.
 * @param co_index The coefficient set to check.
 *
 * Update the coefficients table based on manhattan distance from the center
 * (0,0) and the target, given the specified `factor`.
 * \f[ distance_{r,c} = r+c\\
 *     value_{r,c} = factor^{distance_{r,c}}
 * \f]
 **/
void ained_set_coefficients_manhattan(ained_t *handle, const float factor,
                                      const ained_coeff_t co_index);

/**
 * @param handle The handle to the AiNed module.
 *
 * Print out the bottom right quadrant coefficients matrix in human readable
 * format to standard out.
 *
 * @code
 * Right bottom quadrant of the coefficient matrix.
 *
 *  1.00  0.70  0.49  0.35  0.24
 *  0.70  0.61  0.45  0.33  0.23
 *  0.49  0.45  0.36  0.28  0.20
 *  0.35  0.33  0.28  0.22  0.17
 *  0.24  0.23  0.20  0.17  0.13
 *
 * @endcode
 */
void ained_print_coefficients(ained_t *handle);

/**
 * @}
 */
/**
 * @defgroup DIPOLE Dipole Method
 *
 * @brief Interact with the individual dipoles methods.
 *
 * @ingroup AINED
 * @{
 */

/**
 * @param handle The handle to the AiNed module.
 *
 * @returns the number of dipoles.
 */
uint32_t ained_get_num_dipoles(ained_t *handle);

/**
 * @param handle The handle to the AiNed module.
 * @param dipole The dipole to target.
 * @param s0  The first 32bit seed for the generator.
 * @param s1  The second 32bit seed for the generator.
 * @param s2  The third 32bit seed for the generator.
 *
 * Set the seeds for the random generator for \p dipole.
 *
 * The generator is based on the tausworthe generator.
 */
void ained_set_dipole_rng(ained_t *handle, uint32_t dipole, uint32_t s0,
                          uint32_t s1, uint32_t s2);

/**
 * @param handle The handle to the AiNed module.
 * @param dipole The dipole to target.
 * @param[out] s0  The first 32bit seed for the generator.
 * @param[out] s1  The second 32bit seed for the generator.
 * @param[out] s2  The third 32bit seed for the generator.
 *
 * Get the seeds for the random generator for \p dipole.
 *
 * The generator is based on the tausworthe generator.
 *
 * @returns the current random value of the generator.
 */
uint32_t ained_get_dipole_rng(ained_t *handle, uint32_t dipole, uint32_t *s0,
                              uint32_t *s1, uint32_t *s2);
/**
 * @}
 */
/**
 * @defgroup Helper Helper methods
 *
 * @brief High level helper methods.
 *
 * @ingroup AINED
 * @{
 */

/**
 * @param handle The handle to the AiNed module.
 * @param filename Path to file.
 *
 * Stores the current content of the memory and the random generators into file
 * \p filename with prefix .mem and the state in \p filename .state
 */
void ained_store_memory(ained_t *handle, const char *filename);

/**
 * @param handle The handle to the AiNed module.
 * @param filename Path to file.
 *
 * Restores the current content of the memory and the random generators from
 * \p filename with prefix .mem and restores the state in \p filename .state
 */
void ained_restore_memory(ained_t *handle, const char *filename);

/**
 * @param handle The device handle
 *
 * Print the state of the device.
 * It prints the registers, the random generator state
 * and the memory content in hexadecimal format.
 */
void ained_print_info(const ained_t *handle);

/**
 * @param handle The device handle
 *
 * Print the memory layout in a human readable format.
 *
 * Each 64bit word is printed as block from right to left, top to bottom.
 *
 * @code
 *
 *     | 63 62 61 60 59 58 57 56   55 54 53 52   ...   07 06 05 04 03 02 01 00
 *
 *    0|  0  0  0  0  0  0  0  0    0  0  0  0   ...    0  0  0  0  0  0  0  0
 *   64|  0  0  0  0  0  0  0  0    0  0  0  0   ...    0  0  0  0  0  0  0  0
 *  128|  0  0  0  0  0  0  0  0    0  0  0  0   ...    0  1  1  0  1  1  0  0
 *  192|  0  0  0  0  0  0  0  0    0  0  0  0   ...    1  1  1  1  0  1  0  0
 *  256|  0  0  0  0  0  0  0  0    0  0  0  0   ...    1  1  1  1  0  1  0  0
 *  320|  0  0  0  0  0  0  0  0    0  0  0  0   ...    1  1  1  1  0  0  0  0
 *  384|  0  0  0  0  0  0  0  0    0  0  0  0   ...    1  1  0  1  1  0  0  0
 *  448|  0  0  0  0  0  0  0  0    0  0  0  0   ...    1  1  1  1  1  0  0  0
 *
 *     .  .  .  .  .  .  .  .  .    .  .  .  .          .  .  .  .  .  .  .  .
 *     .  .  .  .  .  .  .  .  .    .  .  .  .          .  .  .  .  .  .  .  .
 *     .  .  .  .  .  .  .  .  .    .  .  .  .          .  .  .  .  .  .  .  .
 *
 * 7680|  0  0  0  0  0  0  0  0    0  0  0  0   ...    0  0  0  0  0  0  0  0
 * 7744|  0  0  0  0  0  0  0  0    0  0  0  0   ...    0  0  0  0  0  0  0  0
 * 7808|  0  0  0  0  0  0  0  0    0  0  0  0   ...    0  0  0  0  0  0  0  0
 * 7872|  0  0  0  0  0  0  0  0    0  0  0  0   ...    0  0  0  0  0  0  0  0
 * 7936|  0  0  0  0  0  0  0  0    0  0  0  0   ...    0  0  0  0  0  0  0  0
 * 8000|  0  0  0  0  0  0  0  0    0  0  0  0   ...    0  0  0  0  0  0  0  0
 * 8064|  0  0  0  0  0  0  0  0    0  0  0  0   ...    0  0  0  0  0  0  0  0
 * 8128|  0  0  0  0  0  0  0  0    0  0  0  0   ...    0  0  0  0  0  0  0  0
 * @endcode
 */
void ained_print_memory(const ained_t *handle);

/**
 * @param handle The handle to the AiNed module.
 *
 * Clears the memory by setting the whole memory to 0.
 *
 * \warning This method enables and disables the bypass bit. If set before
 * calling this method, it will be disabled afterwards.
 */
void ained_clear_memory(ained_t *handle);

/**
 * @}
 */


// Jérôme's functions

uint32_t ained_get_bit(ained_t *handle, uint32_t row, uint32_t col);

/**
 * @param handle The handle to the AiNed module.
 * @param row The row of the bit that you want to be retrieved
 * @param col The column of the bit that you want to be retrieved
 *
 * Retrieves a bit on position (row, col) from the memory.
 */

void ained_flip_isolated_bit(ained_t *handle, uint32_t row, uint32_t col);

/**
 * @param handle The handle to the AiNed module.
 * @param row The row of the bit that you want to isolate
 * @param col The column of the bit that you want to isolate
 * 
 * Set bit to a value according to regular memory rules.
 */

void ained_clear_word(ained_t *handle, uint32_t row, uint32_t col);

/**
 * @param handle The handle to the AiNed module.
 * @param row The row of the bit that you want to be retrieved
 * @param col The column of the bit that you want to be retrieved
 *
 * Clears a word given (row, col) from the memory.
 */

