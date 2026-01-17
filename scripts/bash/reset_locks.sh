#!/bin/bash
echo "Forcing removal of all Ained locks..."
rm /dev/shm/sem_sem_* 2>/dev/null
echo "Done. You can run your program now."
