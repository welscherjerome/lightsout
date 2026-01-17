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
#include "ained.h"
#include "arm_shared_memory_system.h"
#include <errno.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

/**
 * Hidden structure representing the handle to interact with
 * the AiNed FPGA implementation.
 */
struct ained {
  /** Handle to the register shared memory system. */
  arm_shared device_handle_reg;
  /** Handle to the memory shared memory system. */
  arm_shared device_handle_mem;
  /** Pointer to register memory. */
  uint64_t volatile *registers;
  /** Pointer to memory memory. */
  uint64_t volatile *memory;

  /** Number of detected dipoles. */
  uint32_t num_dipoles;

  /** API fields for handling requests*/
  /** Index of uint64_t word to write. */
  int32_t index;
  /** Write mask. */
  uint64_t mask;
  /** Value to write. */
  uint64_t value;
};

/**
 * Register map
 */
/**
 * Access to 32bit registers.
 */
/** Higher 32bit word of the write mask. */
static const uint32_t AINED_REG_MASK_1 = 0;
/** Lower 32bit word of the write mask. */
static const uint32_t AINED_REG_MASK_2 = 1;
static const uint32_t AINED_REG_COEFF_0 = 2;
static const uint32_t AINED_REG_COEFF_1 = 3;
static const uint32_t AINED_REG_COEFF_2 = 4;
static const uint32_t AINED_REG_COEFF_3 = 5;
static const uint32_t AINED_REG_COEFF_4 = 6;
static const uint32_t AINED_REG_COEFF_5 = 7;
static const uint32_t AINED_REG_COEFF_6 = 8;
static const uint32_t AINED_REG_COEFF_7 = 9;
static const uint32_t AINED_REG_COEFF_8 = 10;
static const uint32_t AINED_REG_COEFF_9 = 11;
static const uint32_t AINED_REG_COEFF_10 = 12;
static const uint32_t AINED_REG_COEFF_11 = 13;
/** Bypass register. */
static const uint32_t AINED_REG_BYPASS = 14;
/** The number of (32bit) registers. */
static const uint32_t AINED_NUM_REGS = 15;
/**
 * Access to 64bit registers.
 */
/** Write mask. */
static const uint32_t AINED_REG_MASK_64BIT = 0;
static const uint32_t AINED_REG_DIPOLE_OFFSET = 0x400;
static const uint32_t AINED_REG_DIPOLE_NUM_REG_PD = 4;

static const uint32_t bsize = 8;
static const uint32_t num_words = 128;

/**
 * Memory map.
 */
static const uint32_t register_addr = 0x43c00000;
static const uint32_t register_addr_len = 1 << 13;
static const uint32_t memory_addr = 0x43c10000;
static const uint32_t memory_addr_len = 1 << 12;

ained_t *ained_init(void) {
  ained_t *handle = calloc(1, sizeof(struct ained));
  handle->registers = arm_shared_init(&(handle->device_handle_reg),
                                      register_addr, register_addr_len);
  if (handle->registers == NULL) {
    fprintf(
        stderr,
        "Failed to open direct access to FPGA region. Check permissions.\n");
    free(handle);
    return NULL;
  }
  handle->memory = arm_shared_init(&(handle->device_handle_mem), memory_addr,
                                   memory_addr_len);
  if (handle->memory == NULL) {
    arm_shared_close(&(handle->device_handle_reg));
    fprintf(
        stderr,
        "Failed to open direct access to FPGA region. Check permissions.\n");
    free(handle);
    return NULL;
  }

  handle->num_dipoles = 0;
  while (((uint32_t *)(handle->registers))[AINED_REG_DIPOLE_OFFSET +
                                           AINED_REG_DIPOLE_NUM_REG_PD *
                                               handle->num_dipoles] != 0) {
    handle->num_dipoles++;
  }
  printf("Found: %u dipoles.\n", handle->num_dipoles);

  handle->mask = handle->value = 0;
  handle->index = -1;
  return handle;
}

void ained_destroy(ained_t *handle) {
  if (handle == NULL) {
    return;
  }
  arm_shared_close(&(handle->device_handle_reg));
  arm_shared_close(&(handle->device_handle_mem));
  free(handle);
}

static uint32_t ained_get_index(const uint32_t rows, const uint32_t columns) {
  const uint32_t y = rows / bsize;
  const uint32_t x = columns / bsize;

  return y * 8 + x;
}
static uint32_t ained_get_word_index(const uint32_t rows,
                                     const uint32_t columns) {
  const uint32_t r = rows % bsize;
  const uint32_t c = columns % bsize;
  return r * 8 + c;
}

// Defines to convert a define to string.
#define VAL(str) #str
#define TOSTRING(str) VAL(str)

void ained_print_info(const ained_t *handle) {
  if (handle == NULL) {
    return;
  }
  uint32_t *reg = (uint32_t *)handle->registers;
  printf("Registers:\n");
  printf(" %s: %08llX\n", TOSTRING(AINED_REG_MASK_1),
         handle->registers[AINED_REG_MASK_64BIT]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_0), reg[AINED_REG_COEFF_0]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_1), reg[AINED_REG_COEFF_1]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_2), reg[AINED_REG_COEFF_2]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_3), reg[AINED_REG_COEFF_3]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_4), reg[AINED_REG_COEFF_4]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_5), reg[AINED_REG_COEFF_5]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_6), reg[AINED_REG_COEFF_6]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_7), reg[AINED_REG_COEFF_7]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_8), reg[AINED_REG_COEFF_8]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_9), reg[AINED_REG_COEFF_9]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_10), reg[AINED_REG_COEFF_10]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_COEFF_11), reg[AINED_REG_COEFF_11]);
  printf(" %s: %08X\n", TOSTRING(AINED_REG_BYPASS), reg[AINED_REG_BYPASS]);
  printf("Dipoles (%u)\n", handle->num_dipoles);
  printf(" ID  Rand       S1         S2         S3\n");
  for (uint32_t i = 0; i < handle->num_dipoles; i++) {
    printf(" %02u: %08X - %08X - %08X - %08X\n", i,
           reg[AINED_REG_DIPOLE_OFFSET + i * AINED_REG_DIPOLE_NUM_REG_PD + 0],
           reg[AINED_REG_DIPOLE_OFFSET + i * AINED_REG_DIPOLE_NUM_REG_PD + 1],
           reg[AINED_REG_DIPOLE_OFFSET + i * AINED_REG_DIPOLE_NUM_REG_PD + 2],
           reg[AINED_REG_DIPOLE_OFFSET + i * AINED_REG_DIPOLE_NUM_REG_PD + 3]);
  }
  printf("Memory:\n");

  for (uint32_t i = 0; i < num_words; i++) {
    printf(" %03u: %016llX\n", i, handle->memory[i]);
  }
}

void ained_print_memory(const ained_t *handle) {
  if (handle == NULL) {
    return;
  }

  printf("     | ");
  for (uint32_t column = 0; column < bsize * 8; column++) {
    printf("%02u ", 63 - column);
    if ((column % 8) == 7) {
      printf(" ");
    }
  }
  printf("\n\n");
  for (uint32_t row = 0; row < num_words; row++) {
    printf("%5u| ", row * bsize * bsize);
    for (uint32_t column = 0; column < bsize * 8; column++) {
      uint32_t of = ained_get_index(row, 63 - column);
      uint32_t id = ained_get_word_index(row, 63 - column);
      const uint64_t value = handle->memory[of];
      const uint32_t v = ((value & (((uint64_t)1) << id)) != 0) ? 1 : 0;
      printf(" %u ", v);

      if ((column % 8) == 7) {
        printf(" ");
      }
    }
    printf("\n");
    if ((row % 8) == 7) {
      printf("\n");
    }
  }
}

void ained_set_bit(ained_t *handle, const uint32_t row, const uint32_t column,
                   const uint32_t value) {
  if (handle == NULL) {
    return;
  }
  uint32_t index = ained_get_index(row, column);
  uint32_t id = ained_get_word_index(row, column);

  if (handle->index >= 0 && index != (uint32_t)handle->index) {
    fprintf(stderr,
            "Cannot set bit in more then one word in a single commit.\n");
    return;
  }
  handle->index = index;
  if (value) {
    handle->value |= (((uint64_t)1) << id);
    handle->mask |= (((uint64_t)1) << id);
  } else {
    handle->value &= ~(((uint64_t)1) << id);
    handle->mask |= (((uint64_t)1) << id);
  }
}

void ained_commit(ained_t *handle) {
  if (handle == NULL) {
    return;
  }
  if (handle->index < 0) {
    fprintf(stderr, "Nothing to commit.\n");
    return;
  }
  handle->registers[AINED_REG_MASK_64BIT] = handle->mask;
  handle->memory[handle->index] = handle->value;

  handle->mask = handle->value = 0;
  handle->index = -1;
}

void ained_set_bypass(ained_t *handle, bool enable) {
  if (handle == NULL) {
    return;
  }
  // This is 32bit accessed.
  uint32_t *regs = (uint32_t *)(handle->registers);
  regs[AINED_REG_BYPASS] = enable;
  if (enable) {
    // Set the writemask
    arm_shared_lock(&handle->device_handle_reg); // new code to add lock to avoid other processes to accidentally use deterministic behaviour
    handle->registers[AINED_REG_MASK_64BIT] = (uint64_t)0xFFFFFFFFFFFFFFFF;
  } else {
    // Unset the writemask
    handle->registers[AINED_REG_MASK_64BIT] = (uint64_t)0x0;
    arm_shared_unlock(&handle->device_handle_reg);
  }
}

void ained_clear_memory(ained_t *handle) {
  if (handle == NULL) {
    return;
  }
  ained_set_bypass(handle, true);
  for (uint32_t j = 0; j < num_words; j++) {
    handle->memory[j] = (uint64_t)0ULL;
  }
  ained_set_bypass(handle, false);
}

void ained_store_memory(ained_t *handle, const char *filename) {
  if (handle == NULL) {
    return;
  }
  size_t const length = strlen(filename) + strlen(".state") + 1;
  char mem_fn[length];

  snprintf(mem_fn, length, "%s.mem", filename);

  FILE *fd = fopen(mem_fn, "wb");
  if (fd == NULL) {
    fprintf(stderr, "Failed to store memory to file: %s: '%s'\n", mem_fn,
            strerror(errno));
    return;
  }
  ssize_t written =
      fwrite((void *)(handle->memory), sizeof(uint64_t), num_words, fd);

  if (written != num_words) {
    fprintf(
        stderr,
        "Failed to write full memory image to file: 'Only %zd words written'\n",
        written);
  }

  fclose(fd);

  snprintf(mem_fn, length, "%s.state", filename);
  fd = fopen(mem_fn, "wb");
  if (fd == NULL) {
    fprintf(stderr, "Failed to store state to file: %s: '%s'\n", mem_fn,
            strerror(errno));
    return;
  }
  written =
      fwrite((void *)(handle->registers), sizeof(uint32_t), AINED_NUM_REGS, fd);

  if (written != AINED_NUM_REGS) {
    fprintf(
        stderr,
        "Failed to write full memory image to file: 'Only %zd words written'\n",
        written);
  }

  written = fwrite((void *)&(handle->registers[AINED_REG_DIPOLE_OFFSET / 2]),
                   sizeof(uint32_t),
                   handle->num_dipoles * AINED_REG_DIPOLE_NUM_REG_PD, fd);
  if (written != (ssize_t)(handle->num_dipoles * AINED_REG_DIPOLE_NUM_REG_PD)) {
    fprintf(
        stderr,
        "Failed to write full memory image to file: 'Only %zd words written'\n",
        written);
  }
  fclose(fd);
}
void ained_restore_memory(ained_t *handle, const char *filename) {
  if (handle == NULL) {
    return;
  }

  size_t const length = strlen(filename) + strlen(".state") + 1;
  char mem_fn[length];

  snprintf(mem_fn, length, "%s.mem", filename);
  FILE *fd = fopen(mem_fn, "rb");
  if (fd == NULL) {
    fprintf(stderr, "Failed to store memory to file: %s: '%s'\n", mem_fn,
            strerror(errno));
    return;
  }
  ained_set_bypass(handle, true);
  ssize_t readwords =
      fread((void *)(handle->memory), sizeof(uint64_t), num_words, fd);

  if (readwords != num_words) {
    fprintf(stderr,
            "Failed to read full memory image to memory: 'Only %zd words'\n",
            readwords);
  }
  ained_set_bypass(handle, false);
  fclose(fd);

  snprintf(mem_fn, length, "%s.state", filename);
  fd = fopen(mem_fn, "rb");
  if (fd == NULL) {
    fprintf(stderr, "Failed to store state to file: %s: '%s'\n", mem_fn,
            strerror(errno));
    return;
  }
  readwords =
      fread((void *)(handle->registers), sizeof(uint32_t), AINED_NUM_REGS, fd);

  if (readwords != AINED_NUM_REGS) {
    fprintf(stderr,
            "Failed to read full state image to registers: 'Only %zd words'\n",
            readwords);
  }
  readwords = fread((void *)&(handle->registers[AINED_REG_DIPOLE_OFFSET / 2]),
                    sizeof(uint32_t),
                    handle->num_dipoles * AINED_REG_DIPOLE_NUM_REG_PD, fd);

  if (readwords !=
      (ssize_t)(handle->num_dipoles * AINED_REG_DIPOLE_NUM_REG_PD)) {
    fprintf(stderr,
            "Failed to read full state image to memory: 'Only %zd words'\n",
            readwords);
  }
  fclose(fd);
}

uint64_t volatile *ained_get_memory(ained_t *handle, size_t *length) {
  if (handle == NULL) {
    return NULL;
  }
  if (length != NULL) {
    *length = num_words;
  }
  return handle->memory;
}

void ained_set_mask(ained_t *handle, uint64_t const mask) {
  handle->mask = mask;
  handle->registers[AINED_REG_MASK_64BIT] = handle->mask;
}

void ained_set_word(ained_t *handle, uint32_t const offset,
                    uint64_t const word) {
  handle->index = offset;
  handle->value = word;
}

uint32_t ained_get_num_dipoles(ained_t *handle) {
  if (handle == NULL) {
    return 0;
  }
  return handle->num_dipoles;
}
uint32_t ained_get_dipole_rng(ained_t *handle, uint32_t dipole, uint32_t *s0,
                              uint32_t *s1, uint32_t *s2) {

  if (handle == NULL) {
    return 0;
  }
  if (dipole > handle->num_dipoles) {
    fprintf(stderr, "Only %u dipoles in the system, requested %u.\n",
            handle->num_dipoles, dipole);
    return 0;
  }
  uint32_t *reg = (uint32_t *)handle->registers;
  if (s0 != NULL) {
    *s0 =
        reg[AINED_REG_DIPOLE_OFFSET + dipole * AINED_REG_DIPOLE_NUM_REG_PD + 1];
  }
  if (s1 != NULL) {
    *s1 =
        reg[AINED_REG_DIPOLE_OFFSET + dipole * AINED_REG_DIPOLE_NUM_REG_PD + 2];
  }
  if (s2 != NULL) {
    *s2 =
        reg[AINED_REG_DIPOLE_OFFSET + dipole * AINED_REG_DIPOLE_NUM_REG_PD + 3];
  }

  return reg[AINED_REG_DIPOLE_OFFSET + dipole * AINED_REG_DIPOLE_NUM_REG_PD +
             0];
}
void ained_set_dipole_rng(ained_t *handle, uint32_t dipole, uint32_t s0,
                          uint32_t s1, uint32_t s2) {

  if (handle == NULL) {
    return;
  }
  if (dipole > handle->num_dipoles) {
    fprintf(stderr, "Only %u dipoles in the system, requested %u.\n",
            handle->num_dipoles, dipole);
    return;
  }
  uint32_t *reg = (uint32_t *)handle->registers;
  reg[AINED_REG_DIPOLE_OFFSET + dipole * AINED_REG_DIPOLE_NUM_REG_PD + 1] = s0;
  reg[AINED_REG_DIPOLE_OFFSET + dipole * AINED_REG_DIPOLE_NUM_REG_PD + 2] = s1;
  reg[AINED_REG_DIPOLE_OFFSET + dipole * AINED_REG_DIPOLE_NUM_REG_PD + 3] = s2;

  return;
}

void ained_set_coefficients(ained_t *handle, uint32_t index, uint32_t value) {
  if (handle == NULL) {
    return;
  }
  if (index > 11) {
    fprintf(stderr, "Only 12 coefficients to set.");
    return;
  }
  uint32_t *reg = (uint32_t *)handle->registers;
  reg[AINED_REG_COEFF_0 + index] = value;
  return;
}
uint32_t ained_get_coefficients(ained_t *handle, uint32_t index) {
  if (handle == NULL) {
    return 0;
  }
  if (index > 11) {
    fprintf(stderr, "Only 12 coefficients to set.");
    return 0;
  }
  uint32_t *reg = (uint32_t *)handle->registers;
  return reg[AINED_REG_COEFF_0 + index];
}

typedef struct coeffs {
  uint8_t fields[6 * 4];
} coeffs;

void ained_print_coefficients(ained_t *handle) {
  if (handle == NULL) {
    return;
  }
  uint32_t *reg = (uint32_t *)handle->registers;
  coeffs cfs = *((coeffs *)&reg[AINED_REG_COEFF_0]);
  printf("Right bottom quadrant of the coefficient high matrix.\n\n");

  printf("  1.00  ");
  for (uint32_t i = 0; i < 4; i++) {
    printf("%.2f  ", cfs.fields[i] / 255.0);
  }
  for (uint32_t j = 0; j < 4; j++) {
    printf("\n  ");
    for (uint32_t i = 4 + j * 5; i < (9 + (j * 5)); i++) {
      printf("%.2f  ", cfs.fields[i] / 255.0);
    }
  }
  printf("\n\n");
  cfs = *((coeffs *)&reg[AINED_REG_COEFF_6]);
  printf("Right bottom quadrant of the coefficient low matrix.\n\n");

  printf("  1.00  ");
  for (uint32_t i = 0; i < 4; i++) {
    printf("%.2f  ", cfs.fields[i] / 255.0);
  }
  for (uint32_t j = 0; j < 4; j++) {
    printf("\n  ");
    for (uint32_t i = 4 + j * 5; i < (9 + (j * 5)); i++) {
      printf("%.2f  ", cfs.fields[i] / 255.0);
    }
  }
  printf("\n\n");
}

void ained_set_coefficients_euclidean(ained_t *handle, const float factor,
                                      const ained_coeff_t co_index) {
  coeffs cfs;
  uint32_t *reg = (uint32_t *)handle->registers;

  for (int r = 0; r < 5; r++) {
    for (int c = 0; c < 5; c++) {
      double distance = sqrt(r * r + c * c);
      int ind = r * 5 + c - 1;
      double f = pow(factor, distance);
      uint8_t v = round(f * 256);
      if (ind >= 0) {
        cfs.fields[ind] = v;
      }
    }
  }
  printf("set %d\n", co_index);
  *((coeffs *)&reg[(co_index == AINED_COEFF_HIGH) ? AINED_REG_COEFF_0
                                                  : AINED_REG_COEFF_6]) = cfs;
}

void ained_set_coefficients_manhattan(ained_t *handle, const float factor,
                                      const ained_coeff_t co_index) {
  coeffs cfs;
  uint32_t *reg = (uint32_t *)handle->registers;

  for (int r = 0; r < 5; r++) {
    for (int c = 0; c < 5; c++) {
      double distance = r + c;
      int ind = r * 5 + c - 1;
      double f = pow(factor, distance);
      uint8_t v = round(f * 256);
      if (ind >= 0) {
        cfs.fields[ind] = v;
      }
    }
  }
  printf("set %d\n", co_index);
  *((coeffs *)&reg[(co_index == AINED_COEFF_HIGH) ? AINED_REG_COEFF_0
                                                  : AINED_REG_COEFF_6]) = cfs;
}

// Jérôme's functions

/*
 * This function simply returns a single bit from the memory given a row and column coordinate
 */

uint32_t ained_get_bit(ained_t *handle, uint32_t row, uint32_t col){
    uint32_t of = ained_get_index(row, col);
    uint32_t id = ained_get_word_index(row, col);
    const uint64_t value = handle->memory[of];
    const uint32_t bit = ((value & ((uint64_t)1 << id)) != 0) ? 1 : 0;
    return bit;
}


/*
 * This function flips a single bit. It assumes that the bypass is set to true. Setting a bit via set_bit function and commit proves to act in unexpected behaviour.
 */
void ained_flip_isolated_bit(ained_t *handle, uint32_t row, uint32_t col){ 
	uint32_t word_index = ained_get_index(row, col);
	uint32_t bit_index = ained_get_word_index(row, col);
	// Flip only the target bit
	handle->memory[word_index] ^= (1ULL << bit_index);
}


/*
 * This function saves the coefficient values in an array on the heap and returns that array. 
 *
 * WARNING: The heap memory must be freed after use
 */
float* ained_get_coefficient_array(ained_t *handle) {
  float *coefficients = calloc(25, sizeof(float));
  if (handle == NULL) {
    return coefficients;
  }
  uint32_t *reg = (uint32_t *)handle->registers;
  coeffs cfs = *((coeffs *)&reg[AINED_REG_COEFF_6]);
  
  coefficients[0] = 1.00;

  for (uint32_t i = 0; i < 4; i++) {
	  coefficients[i + 1] = cfs.fields[i] / 255.0;
  }
  for (uint32_t j = 0; j < 4; j++) {
    for (uint32_t i = 4 + j * 5; i < (9 + (j * 5)); i++) {
      coefficients[i + 1] = cfs.fields[i] / 255.0;
    }
  }
  return coefficients;
}


/*
 * This function clears only a single word given the row and column of any cell that is present in the word.
 */
void ained_clear_word(ained_t *handle, uint32_t row, uint32_t col) {
  if (handle == NULL) {
    return;
  }
  ained_set_bypass(handle, true);
  uint32_t index = ained_get_index(row, col);
  handle->memory[index] = (uint64_t)0ULL;
  ained_set_bypass(handle, false);
}

