#!/bin/bash

# Loop 1: 05 to 40 (increments of 5)
for i in {5..25..5}
do
   VAL=$(printf "%02d" $i)
   # Calculate decimal: 5 becomes 0.05, 10 becomes 0.10
   C_VAL=$(awk "BEGIN {printf \"%.2f\", $i/100}")
   
   echo "Running: simannAdapt_$VAL with -c $C_VAL and -i 1000"
   sudo python main.py -N 5 -t -1 -i 1000 -f "simann_latest_$VAL" -c "$C_VAL" -m simann -p 0 0
done


