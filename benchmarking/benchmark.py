#!/usr/bin/env python3
import os
import subprocess
import datetime
import glob
import argparse
import sys
import json
import scipy.stats as stats
import numpy as np
import os
import subprocess
import datetime
import glob
import argparse
import sys
import json
import numpy as np

# read --opt argument. if == LS only read config files with LS in the name to an array. if == SA only read config files with SA in the name to an array.
# parser = argparse.ArgumentParser()
# parser.add_argument("--opt", choices=["LS", "SA"], help="Specify the optimizer type")
# parser.add_argument("--file", help="Specify the config file to run the optimizer for")
# args = parser.parse_args()

# if args.opt == "LS":
#   configs = glob.glob(os.path.join(os.path.dirname(__file__), 'config/*LS*'))
#   configs = [config for config in configs if 'disabled' not in config]
# elif args.opt == "SA":
#   configs = glob.glob(os.path.join(os.path.dirname(__file__), 'config/*SA*'))
#   configs = [config for config in configs if 'disabled' not in config]
# else:
#   configs = glob.glob(os.path.join(os.path.dirname(__file__), 'config/*'))
#   configs = [config for config in configs if 'disabled' not in config]

# if args.file:
#   print("file: ", args.file)
#   configs = glob.glob(os.path.join(os.path.dirname(__file__), 'config/' + args.file))

# print("configs: ", configs)

# # generate results directory name based on date
# result_dir = os.path.join(os.path.dirname(__file__), '../results', datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

# # curves=("bls12_381_p" "bls12_381_q" "curve25519" "curve25519_solinas" "p224" "p256" "p384" "p434" "p448_solinas" "p521" "poly1305" "secp256k1_montgomery" "secp256k1_dettman")
# # methods=("square" "mul")
# curves = ["p256", "curve25519"]
# methods = ["square", "mul"]

# n = 10

# Initialize a dictionary to store the best results for each config
best_results_per_config_curve_method = {}

# run the optimizer for each curve
import scipy.stats as stats
def findBestInRun(result_dir, curve, method):
  # load the every json file in the run directory
  inputData = []
  directory = os.path.join(result_dir, "fiat", f"fiat_{curve}_{method}")
  
  # check if the directory exists
  if not os.path.isdir(directory):
    directory = os.path.join(result_dir, "fiat", f"fiat_{curve}_carry_{method}")
  
  
  for filename in os.listdir(directory):
    if filename.endswith('.json') and '_details' in filename:
      filepath = os.path.join(directory, filename)
      with open(filepath) as f:
        inputData.append(json.load(f))

  # iterate through the data and create a ranking of each algorithm based on the ratio
  rankings = []
  for data in inputData:
    ratio = data['ratio']
    timeTaken = data['elapsed']
    rankings.append((ratio, timeTaken, data))

  # sort the rankings by the ratio
  rankings.sort(key=lambda x: x[0])

  # print last element of rankings
  print(rankings[-1])

  # return the best algorithm
  return rankings[-1]

def runOptimizer(config, curve, method, result_dir, n):
  processes = []

  configFileName = os.path.basename(config).split('.')[0]
  key = (configFileName, curve, method)
  best_results_per_config_curve_method[key] = []

  config_result_dir = os.path.join(result_dir, configFileName)

  for i in range(n):
    run_result_dir = os.path.join(config_result_dir, "run" + str(i))
    for core in range(4):
      process = subprocess.Popen(["taskset", "-c", str(core), "./CryptOpt", "--optimizerConfigPath", config, "--curve", curve, "--method", method, "--resultDir", run_result_dir])
      processes.append(process)

    for process in processes:
      process.wait()

    print("Finished run " + str(i) + " for curve " + curve + " with method " + method + " and config " + configFileName)
    best_in_run = findBestInRun(run_result_dir, curve, method)
    print("Best in run: ", best_in_run)
    best_results_per_config_curve_method[key].append(best_in_run[0])

  best_results = best_results_per_config_curve_method[key]
  confidence_interval = stats.t.interval(0.95, len(best_results)-1, loc=np.mean(best_results), scale=stats.sem(best_results))
  with open(os.path.join(result_dir, f"best_results_{configFileName}_{curve}_{method}.json"), "w") as f:
    json.dump({"best_results": best_results, "confidence_interval": confidence_interval}, f)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--opt", choices=["LS", "SA"], help="Specify the optimizer type")
  parser.add_argument("--file", help="Specify the config file to run the optimizer for")
  args = parser.parse_args()

  if args.opt == "LS":
    configs = glob.glob(os.path.join(os.path.dirname(__file__), 'config/*LS*'))
    configs = [config for config in configs if 'disabled' not in config]
  elif args.opt == "SA":
    configs = glob.glob(os.path.join(os.path.dirname(__file__), 'config/*SA*'))
    configs = [config for config in configs if 'disabled' not in config]
  else:
    configs = glob.glob(os.path.join(os.path.dirname(__file__), 'config/*'))
    configs = [config for config in configs if 'disabled' not in config]

  if args.file:
    print("file: ", args.file)
    configs = glob.glob(os.path.join(os.path.dirname(__file__), 'config/' + args.file))

  print("configs: ", configs)

  result_dir = os.path.join(os.path.dirname(__file__), '../results', datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

  # copy the config files to the results directory
  os.makedirs(result_dir)
  for config in configs:
    configFileName = os.path.basename(config)
    os.system(f"cp {config} {result_dir}/{configFileName}")

  curves = ["curve25519"]
  methods = ["square", "mul"]
  n = 10
  

  for curve in curves:
    for method in methods:
      for config in configs:
        runOptimizer(config, curve, method, result_dir, n)

if __name__ == "__main__":
  main()
