#!/bin/bash

for i in {5..25..5}
do
   VAL=$(printf "%02d" $i)

   C_VAL=$(awk "BEGIN {printf \"%.2f\", $i/100}")
   
   echo "Running: simannAdapt_$VAL with -c $C_VAL and -i 1000"
   sudo python main.py -N 5 -t -1 -i 1000 -f "simann_latest_$VAL" -c "$C_VAL" -m simann -p 0 0
done


