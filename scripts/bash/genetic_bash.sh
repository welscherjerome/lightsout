#!/bin/bash

# List of crossover probabilities provided
# Note: 0.01 is included twice as requested
c_values=(0.005 0.01 0.02 0.03 0.04 0.05)

# Loop through each c value
for c in "${c_values[@]}"; do
    echo "Processing crossover value: $c"
    
    # Run 50 times for the current c value
    for i in {1..10}; do
        for j in {1..25}; do
            echo "  - Run $i/10, $j/25 for c=$c"
            sudo python genetic.py -f "big_genetic_scramble" -g 55 -p 150 -c "$c" -l "$j"
        done
    done
done
