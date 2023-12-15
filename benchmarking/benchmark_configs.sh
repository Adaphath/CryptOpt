#!/bin/bash



# read config filenames into an array, exclude files with disabled in the name
# configs=($(ls config/* | grep -v disabled))

# read --opt argument. if == LS only read config files with LS in the name to an array. if == SA only read config files with SA in the name to an array.
if [ "$1" == "--opt=LS" ]; then
  configs=($(ls ../config/*LS* | grep -v disabled))
elif [ "$1" == "--opt=SA" ]; then
  configs=($(ls ../config/*SA* | grep -v disabled))
else
  configs=($(ls ../config/* | grep -v disabled))
fi


# if the --file argument is given then only run the optimizer for the given config file
if [ "$1" == "--file" ]; then
  configs=($(ls ../config/$2))
fi

echo "configs: ${configs[@]}"

# generate results directory name based on date
result_dir="../results/$(date +%Y-%m-%d_%H-%M-%S)"

seed=$(date +%s%3N)

# curves=("bls12_381_p" "bls12_381_q" "curve25519" "curve25519_solinas" "p224" "p256" "p384" "p434" "p448_solinas" "p521" "poly1305" "secp256k1_montgomery" "secp256k1_dettman")
curves=("p256")

# methods=("square" "mul")
methods=("square")

n=5
pi=2

# R3 validation
#Algorithm 1: Round-Robin & Rotate (R3-validation) validation protocol
# input:Given a set S of N configurations, and π the number of
# times a permutation is to be repeated within a
# discharge cycle.
# 1 Create a permutation Π based on S.
# 2 repeat N times
# 3 Reboot and recharge the device.
# 4 repeat π times
# 5 Execute permutation Π on the device.
# 6 end
# 7 Rotate Π left by one position.
# 8 end

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
      for ((i=1;i<=n;i++));
      do
        # run the optimizer
        ./CryptOpt --optimizerConfigPath $config --curve $curve --method $method --resultDir $result_dir --seed $seed
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