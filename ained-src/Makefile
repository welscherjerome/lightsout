VERBOSE=@
COLOR_GREEN="\033[1;32m"
COLOR_RED="\033[1;31m"
COLOR_BLUE="\033[1;34m"
COLOR_YELLOW="\033[1;33m"
COLOR_END="\033[0m"

DEP_PRINT=@echo ${COLOR_BLUE}\(DEP\)${COLOR_END} $@
OBJ_PRINT=@echo ${COLOR_YELLOW}\(OBJ\)${COLOR_END} $@
BUILD_PRINT=@echo ${COLOR_GREEN}\(EXE\)${COLOR_END} $@
CLEAN_PRINT=@echo ${COLOR_RED}Cleaning build files${COLOR_END}
SETCAP_PRINT=@echo ${COLOR_GREEN}\(SETCAP\)${COLOR_END} $@

# Allow optimization level to be overwritten?
SUDO?=sudo
OPT_LEVEL?=2

# include paths
CFLAGS:= -I.

# for debugging 
CFLAGS+= -ggdb -g3

# C version
CFLAGS+= -std=c99
CFLAGS+=-D_POSIX_C_SOURCE=200809L

# Warnings
CFLAGS+= -Wall -Wextra
CFLAGS+= -O$(OPT_LEVEL)

# Linker flags
LDFLAGS:= -lm -ggdb -g3 -lreadline


SOURCES:=$(wildcard *.c)
# Generate list of objects and dependency files.
SOURCES_OBJ+=$(SOURCES:.c=.o)
D_FILES:=$(SOURCES_OBJ:.o=.d)

# Shared library flags
SHARED_CFLAGS := -fPIC
SHARED_LDFLAGS := -shared

all: main ained.so mod_lightsout.so

ained.so: ained.o arm_shared_memory_system.o
	$(BUILD_PRINT)
	$(VERBOSE)${CC} $(SHARED_LDFLAGS) -o $@ $^ $(LDFLAGS)

mod_lightsout.so: arm_shared_memory_system.o mod_lightsout.o ained.o
	$(BUILD_PRINT)
	$(VERBOSE)${CC} $(SHARED_LDFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	$(CLEAN_PRINT)
	$(VERBOSE) rm -f main ${SOURCES_OBJ} ${D_FILES}

-include ${D_FILES}


# Generate dependencies.
%.d: %.c
	$(DEP_PRINT)
	$(VERBOSE)${CC} -c -MT"$*.o" -MM -o $@  $^ ${CFLAGS}

%.o: %.c %.d
	$(OBJ_PRINT)
	$(VERBOSE)${CC} -c -o $@ $< ${CFLAGS}


main: ${SOURCES_OBJ}
	$(BUILD_PRINT)
	$(VERBOSE)${CC} -o $@ ${SOURCES_OBJ}   ${LDFLAGS}
	$(SETCAP_PRINT)
	$(VERBOSE)${SUDO} setcap cap_sys_nice,cap_sys_rawio+ep ./${@}
