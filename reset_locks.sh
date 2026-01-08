#!/bin/bash

# Use shell script in very rare case of lingering Ained locks

echo "Forcing removal of all Ained locks..."
rm /dev/shm/sem_sem_* 2>/dev/null
echo "Done. You can run your program now."
