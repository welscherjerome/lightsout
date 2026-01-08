#!/bin/bash

c_values=(0.05 0.1 0.2 0.3 0.4 0.5)

for c in "${c_values[@]}"; do
    echo "Running MCMC simulation: $c"      
    sudo python main.py -N 5 -t 50000 -i 3 -f "MCMC" -c "$c" -m MCMC -p 0 0
done

