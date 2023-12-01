#!/bin/bash

# read config filenames into an array, exclude files with disabled in the name
configs=($(ls config/* | grep -v disabled))

# generate results directory name based on date
result_dir="results/$(date +%Y-%m-%d_%H-%M-%S)"

curves=("curve25519")

methods=("square" "mul")

iterations=1

# run the optimizer for each curve
for curve in "${curves[@]}"
do
  # run the optimizer for each method
  for method in "${methods[@]}"
  do
    # run the optimizer for each config
    for config in "${configs[@]}"
    do
      # run the optimizer for each config
      for ((i=1;i<=iterations;i++));
      do
        # run the optimizer
        ./CryptOpt --optimizerConfigPath $config --curve $curve --method $method --resultDir $result_dir
      done
    done
  done
done

# Loop over the configuration files
# for config in "${configs[@]}"
# do
#   # Run your program with the current configuration file
#   node dist/CryptOpt.js --optimizerConfigPath $config
# done