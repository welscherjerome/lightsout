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
#include "mod_lightsout.h"
#include <err.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <readline/history.h>
#include <readline/readline.h>
#include <strings.h>

static char **character_name_completion(const char *, int, int);
static char *character_name_generator(const char *, int);
static char *escape(const char *);
static int quote_detector(char *, int);

/**
 * print memory.
 */
static void print_memory(ained_t *handle,
                         const char *memory __attribute__((unused))) {
  printf("Print memory\n");
  ained_print_memory(handle);
}
static void print_info(ained_t *handle,
                       const char *memory __attribute__((unused))) {
  printf("Print info\n");
  ained_print_info(handle);
}
static void print_coeffs(ained_t *handle,
                         const char *memory __attribute__((unused))) {
  printf("Print coefficients\n");
  ained_print_coefficients(handle);
}
static void update_coeffs_euclidian(ained_t *handle, const char *memory
                                    __attribute__((unused))) {
  const char *value = memory + strlen("update_coeffs_euclidian") + 1;
  ained_coeff_t index = AINED_COEFF_HIGH;
  if (strncmp(value, "high", 4) == 0) {
    value += 5;
  } else if (strncmp(value, "low", 3) == 0) {
    value += 4;
    index = AINED_COEFF_LOW;
  }

  double factor = 0.7;
  if ((*value) != 0) {
    factor = strtod(value, NULL);
  }
  printf("Update coefficients %s euclidian with factor: %0.2f\n",
         index == AINED_COEFF_HIGH ? "high" : "low", factor);
  ained_set_coefficients_euclidean(handle, factor, index);
}
static void update_coeffs_manhattan(ained_t *handle, const char *memory
                                    __attribute__((unused))) {
  const char *value = memory + strlen("update_coeffs_manhattan") + 1;
  ained_coeff_t index = AINED_COEFF_HIGH;
  if (strncmp(value, "high", 4) == 0) {
    value += 5;
  } else if (strncmp(value, "low", 3) == 0) {
    value += 4;
    index = AINED_COEFF_LOW;
  }
  double factor = 0.7;
  if ((*value) != 0) {
    factor = strtod(value, NULL);
  }
  printf("Update coefficients %s manhattan with factor: %0.2f\n",
         index == AINED_COEFF_HIGH ? "high" : "low", factor);
  ained_set_coefficients_manhattan(handle, factor, index);
}
/**
 * Clear memory.
 */
static void clear_memory(ained_t *handle,
                         const char *memory __attribute__((unused))) {
  printf("Clear memory to 0\n");
  ained_clear_memory(handle);
}
/**
 * Commit to memory.
 */
static void commit_memory(ained_t *handle,
                          const char *memory __attribute__((unused))) {
  printf("Commit memory\n");
  ained_commit(handle);
}

/**
 * Store memory to file.
 */
static void store_memory(ained_t *handle, const char *memory) {
  const char *filename = memory + strlen("store") + 1;
  if (*filename != 0) {
    printf("Write memory content to file: '%s'\n", filename);
    ained_store_memory(handle, filename);
  }
}
static void test_memory(ained_t *handle,
                        const char *memory __attribute__((unused()))) {
  ained_set_mask(handle, 0xAAAAAAAAAAAAAAAA);
  ained_set_word(handle, 13, 0xFFFFFFFFFFFFFFFF);
  ained_commit(handle);

  uint64_t volatile *mem = ained_get_memory(handle, NULL);
  ained_set_mask(handle, 0x8000800080008000);
  mem[1] = 0xFFFFFFFFFFFFFFFF;
}

/**
 * Restore memory from file.
 */
static void restore_memory(ained_t *handle, const char *memory) {
  const char *filename = memory + strlen("restore") + 1;
  if (*filename != 0) {
    printf("Restore memory content from file: '%s'\n", filename);
    ained_restore_memory(handle, filename);
  }
}

/**
 * Set bit in memory.
 *
 * @TODO move this into lib more.
 */
static void set_memory(ained_t *handle, const char *memory) {
  char *saveptr = NULL;
  char *amemory = strdup(memory + 4);
  char *s = amemory;
  if (*s == '\0') {
    printf("Usage:  set {row} {column} {value}\n");
    free(amemory);
    return;
  }
  uint32_t column = 0, row = 0, value = 0;
  uint32_t count = 0;
  for (char *str = strtok_r(s, " ", &saveptr); str != NULL;
       str = strtok_r(NULL, " ", &saveptr)) {
    uint32_t v = strtoul(str, NULL, 0);
    switch (count) {
    case 0:
      if (v > 127) {
        fprintf(stderr, "Rows should between 0 and 127\n");
        break;
      }
      row = v;
      break;
    case 1:
      if (v > 63) {
        fprintf(stderr, "Column should between 0 and 63\n");
        break;
      }
      column = v;
      break;
    case 2:
      if (!(v == 0 || v == 1)) {
        fprintf(stderr, "Value should be 0 or 1\n");
        break;
      }
      value = v;
      break;
    default:
      break;
    }
    count++;
  }
  if (count != 3) {
    printf("Usage:  set {row} {column} {value} %u\n", count);
    free(amemory);
    return;
  }
  ained_set_bit(handle, row, column, value);
  free(amemory);
}


// Jérôme's functions

// print board
static void print_board(ained_t *handle, const char *memory){
  char *saveptr = NULL;
  char *amemory = strdup(memory + 11);
  char *s = amemory;
  if (*s == '\0') {
    printf("Usage:  lights_out {rows} {cols}\n");
    free(amemory);
    return;
  }
  uint32_t cols = 0, rows = 0;
  uint32_t count = 0;
  for (char *str = strtok_r(s, " ", &saveptr); str != NULL;
    str = strtok_r(NULL, " ", &saveptr)) {
        uint32_t v = strtoul(str, NULL, 0);
        switch (count) {
            case 0:
                if (v > 127) {
                    fprintf(stderr, "Row size should between 0 and 127\n");
                    break;
                }
                rows = v;
                break;
            case 1:
                if (v > 63) {
                    fprintf(stderr, "Column size should between 0 and 63\n");
                    break;
                }
                cols = v;
                break;
            default:
                break;
        }
        count++;
  }
  if (count != 2) {
    printf("Usage:  lights_out {rows} {columns} %u\n", count);
    free(amemory);
    return;
  }
  ained_print_board(handle, 0, 0, rows, cols);
  free(amemory);
}

// check if game is over

static void game_not_over(ained_t *handle, const char *memory) {
  char *saveptr = NULL;
  char *amemory = strdup(memory + 8);
  char *s = amemory;
  if (*s == '\0') {
    printf("Usage:  is_over {max_rows} {max_cols}\n");
    free(amemory);
    return;
  }
  uint32_t max_cols = 0, max_rows = 0;
  uint32_t count = 0;
  for (char *str = strtok_r(s, " ", &saveptr); str != NULL;
    str = strtok_r(NULL, " ", &saveptr)) {
        uint32_t v = strtoul(str, NULL, 0);
        switch (count) {
            case 0:
                if (v > 127) {
                    fprintf(stderr, "Max row size should between 0 and 127\n");
                    break;
                }
                max_rows = v;
                break;
            case 1:
                if (v > 63) {
                    fprintf(stderr, "Max column size should between 0 and 63\n");
                    break;
                }
                max_cols = v;
                break;
            default:
                break;
        }
        count++;
  }
  if (count != 2) {
    printf("Usage:  is_over {max_rows} {max_columns} %u\n", count);
    free(amemory);
    return;
  }
  printf("Game %s over\n", ained_game_not_over(handle, 0, 0, max_rows, max_cols) ? "is not" : "is");
  free(amemory);
}

// END Jérôme's functions


/**
 * Structure for user commands.
 */
typedef struct {
  /** The command name */
  const char *command;
  /** Pointer to function to handle the command */
  void (*exec)(ained_t *, const char *arg);
  /** Help message */
  const char *help;

} Commands;

void help_list(ained_t *handle, const char *memory);
Commands character_names[] = {
    {.command = "quit", .exec = NULL, .help = "quit"},
    {.command = "print", .exec = print_memory, .help = "print"},
    {.command = "info", .exec = print_info, .help = "info"},
    {.command = "coeffs", .exec = print_coeffs, .help = "coeffs"},
    {.command = "update_coeffs_euclidian",
     .exec = update_coeffs_euclidian,
     .help = "update_coeffs_euclidian <high|low> <factor>"},
    {.command = "update_coeffs_manhattan",
     .exec = update_coeffs_manhattan,
     .help = "update_coeffs_manhattan <high|low> <factor>"},
    {.command = "commit", .exec = commit_memory, .help = "commit"},
    {.command = "set",
     .exec = set_memory,
     .help = "set <row> <column> <value>"},
    {.command = "clear", .exec = clear_memory, .help = "clear"},
    {.command = "store", .exec = store_memory, .help = "store <filename>"},
    {.command = "restore",
     .exec = restore_memory,
     .help = "restore <filename>"},
    {.command = "test", .exec = test_memory, .help = "test method"},
    {.command = "help", .exec = help_list, .help = "this help message"},
    {.command = "lights_out", .exec = print_board, .help = "lights_out <rows> <cols>"},
    {.command = "is_over", .exec = game_not_over, .help = "is_over"},
    {NULL}};
static char **character_name_completion(const char *text,
                                        int start __attribute__((unused)),
                                        int end __attribute__((unused))) {
  rl_attempted_completion_over = 1;
  return rl_completion_matches(text, character_name_generator);
}

void help_list(ained_t *handle __attribute__((unused())),
               const char *memory __attribute__((unused()))) {
  printf("Commands:\n");
  for (int i = 0; character_names[i].command != NULL; i++) {
    printf(" * %s\n", character_names[i].help);
  }
  printf("\n");
}

static char *character_name_generator(const char *text, int state) {
  static int list_index, len;
  char *name;
  const char *iter;

  if (!state) {
    list_index = 0;
    len = strlen(text);
  }

  while ((iter = character_names[list_index++].command)) {
    if (rl_completion_quote_character) {
      name = strdup(iter);
    } else {
      name = escape(iter);
    }

    if (strncmp(name, text, len) == 0) {
      return name;
    } else {
      free(name);
    }
  }

  return NULL;
}

static char *escape(const char *original) {
  size_t original_len;
  size_t j = 0;
  char *escaped, *resized_escaped;

  original_len = strlen(original);

  if (original_len > SIZE_MAX / 2) {
    errx(1, "string too long to escape");
  }

  if ((escaped = malloc(2 * original_len + 1)) == NULL) {
    err(1, NULL);
  }

  for (size_t i = 0; i < original_len; ++i, ++j) {
    if (original[i] == ' ') {
      escaped[j++] = '\\';
    }
    escaped[j] = original[i];
  }
  escaped[j] = '\0';

  if ((resized_escaped = realloc(escaped, j)) == NULL) {
    free(escaped);
    resized_escaped = NULL;
    err(1, NULL);
  }

  return resized_escaped;
}

static int quote_detector(char *line, int index) {
  return (index > 0 && line[index - 1] == '\\' &&
          !quote_detector(line, index - 1));
}

static size_t mins(const size_t a, const size_t b) {
  if (a < b) {
    return a;
  }
  return b;
}


/**
 * main application.
 */
int main(__attribute__((unused)) int argc,
         __attribute__((unused)) char **argv) {
  ained_t *handle;

  rl_attempted_completion_function = character_name_completion;
  rl_completer_quote_characters = "'\"";
  rl_completer_word_break_characters = " ";
  rl_char_is_quoted_p = &quote_detector;

  // Create handle to FPGA.
  handle = ained_init();
  if (handle == NULL) {
    fprintf(stderr, "Failed to open memory.\n");
    return EXIT_FAILURE;
  }

  bool quit = true;
  while (quit) {
    char *inp = readline("Command: ");
    if (inp == NULL) {
      break;
    }
    printf("Got command: '%s'\n", inp);
    for (uint32_t i = 0; character_names[i].command != NULL; i++) {
      if (strncasecmp(inp, character_names[i].command,
                      mins(strlen(character_names[i].command), strlen(inp))) ==
          0) {
        Commands *c = &(character_names[i]);
        if (c->exec == NULL) {
          quit = false;
          break;
        } else {
          c->exec(handle, inp);
          add_history(inp);
        }
      }
    }
  }

  // Cleanup
  ained_destroy(handle);
  return EXIT_SUCCESS;
}
