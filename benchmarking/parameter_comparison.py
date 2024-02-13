#!/usr/bin/env python3

# configuration file with TL1: {
#     "option": "SA",
#     "evals": 10000,
#     "acceptanceRate": 0.7,
#     "coolingRateAlpha": 0.97,
#     "temperatureLengthType": "TL1",
#     "lengthConstant": 0.006
# }
# acceptanceRate, coolingRateAlpha and lengthConstant are the parameters to be compared

# results file: {"best_results": [1.9703026841804683, 2.147848317000426], "confidence_interval": [0.9311099202555564, 3.187041080925338]}

# comparison in 3d scatter plot and the average of the best results as color for 4th dimension

import os
import json
import argparse
import datetime
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.cm as cm
import matplotlib.colors as colors

OUTPUT_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "plots")


def generateParameterComparisonGraph(
  data,
  params
):
  # extract the parameters and results from data
  # data = [
  #  {
  #   "acceptanceRate": 0.6,
  #   "coolingRateAlpha": 0.95,
  #   "lengthParam": 0.004,
  #   "best_results": [1.9703026841804683, 2.147848317000426],
  #   "confidence_interval": [0.9311099202555564, 3.187041080925338]
  #  },
  # ...]

  # generate all combinations of the parameters
  combinations = []
  results = {}
  for comb in data:
    acceptanceRate = comb["acceptanceRate"]
    coolingRateAlpha = comb["coolingRateAlpha"]
    lengthParam = comb["lengthParam"]
    best_results = comb["best_results"]
    confidence_interval = comb["confidence_interval"]

    combinations.append((acceptanceRate, coolingRateAlpha, lengthParam))
    results[(acceptanceRate, coolingRateAlpha, lengthParam)] = np.mean(best_results)

  # plot the results
  fig = plt.figure()
  ax = fig.add_subplot(111, projection='3d')

  # x: acceptanceRate
  # y: coolingRateAlpha
  # z: lengthParam
  # c: average of the best results

  # plot the 3d scatter plot
  x = [comb[0] for comb in combinations]
  y = [comb[1] for comb in combinations]
  z = [comb[2] for comb in combinations]
  c = [results[comb] for comb in combinations]

  sc = ax.scatter(x, y, z, c=c, cmap=cm.coolwarm, vmin=min(c), vmax=max(c))

  # add color bar
  cbar = fig.colorbar(sc, ticks=[min(c), 5, max(c)], pad=0.15)

  # set labels
  cbar.set_label('Average of Best Results')

  # set labels
  ax.set_xlabel('Acceptance Rate')
  ax.set_ylabel('Cooling Rate Alpha')
  ax.set_zlabel('Length Param (Constant or Threshold)')

  outputFilePath = os.path.join(OUTPUT_DIRECTORY, f"parameter_comparison_{params.get('curve')}_{params.get('method')}_{params.get('temperatureLength')}_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.svg")
  fig.savefig(outputFilePath)

  # print out best result with corresponding parameters
  best = max(results, key=results.get)
  print(f"Best result: {results[best]} with parameters: {best}")


# generate example plots
# acceptanceRate, coolingRateAlpha and lengthConstant are the parameters to be compared
acceptanceRate = [0.6, 0.7, 0.8]
coolingRateAlpha = [0.95, 0.97, 0.99]
lengthConstant = [0.004, 0.006, 0.008]
result = [[1.9703026841804683, 2.747848317000426], [1.2703026841804683, 2.147848317000426], [1.4703026841804683, 2.147848317000426]]

data = []

# for i in range(len(acceptanceRate)):
#   data.append({
#     "acceptanceRate": acceptanceRate[i],
#     "coolingRateAlpha": coolingRateAlpha[i],
#     "lengthConstant": lengthConstant[i],
#     "best_results": result[i],
#     "confidence_interval": [0.9311099202555564, 3.187041080925338]
#   })

# generateParameterComparisonGraph(data)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--directory", help="Specify directory to read configurations from", required=True)
  parser.add_argument("--curve")
  parser.add_argument("--method")
  parser.add_argument("--temperatureLength", choices=["TL1", "TL6"], help="Specify the temperature length type")
  parser.add_argument("--evals", help="Specify the number of evaluations")
  args = parser.parse_args()
  # arg parameters: result directories, curve, method, temperature length type
  curve = "p384"
  method = "square"
  # TL1: FIXED, TL6: THRESHOLD
  temperatureLengthType = "TL1"
  evals = '10k'
  
  # if directory is not given, abort with error message
  if not args.directory:
    print("Please specify a directory to read configurations from")
    return
  
  curve = args.curve if args.curve else curve
  method = args.method if args.method else method
  temperatureLengthType = args.temperatureLength if args.temperatureLength else temperatureLengthType
  evals = args.evals if args.evals else evals
  
  temperatureLengthType = "FIXED" if temperatureLengthType == "TL1" else "THRESHOLD"
  
  # print parameters
  print(f"curve: {curve}, method: {method}, temperatureLengthType: {temperatureLengthType}, evals: {evals}")
  
  # type: {
#      "configName": configName,
#     "acceptanceRate": acceptanceRate[i],
#     "coolingRateAlpha": coolingRateAlpha[i],
#     "lengthConstant": lengthConstant[i],
#     "best_results": result[i],
#     "confidence_interval": [0.9311099202555564, 3.187041080925338]
#   }
  configurationData = []
  
  # load configurations from directory
  # example file name: SA_THRESHOLD_10k_config_10.json
  # name format: {optimizer}_{temperatureLength}_{evals}k_config_{configNumber}.json
  # it contains the configuration parameters
  for file in os.listdir(args.directory):
    print(file)
    # skip if file is not a json file
    if not file.endswith('.json'):
      continue
    # check if file name contains the given parameters and starts with SA_
    if temperatureLengthType in file and evals in file and file.startswith("SA"):
      with open(os.path.join(args.directory, file), "r") as f:
        data = json.load(f)
        print(data)
        if temperatureLengthType == "FIXED":
          configurationData.append({
            "configName": file.split(".")[0],
            "acceptanceRate": data["acceptanceRate"],
            "coolingRateAlpha": data["coolingRateAlpha"],
            "lengthParam": data["lengthConstant"],
          })
        else:
          configurationData.append({
            "configName": file.split(".")[0],
            "acceptanceRate": data["acceptanceRate"],
            "coolingRateAlpha": data["coolingRateAlpha"],
            "lengthParam": data["threshholdOfAcceptedSolutions"],
          })
  
  # load results and add to configuration data
  # example file name: best_results_SA_THRESHOLD_10k_config_10_p384_square.json
  # name format: best_results_{optimizer}_{temperatureLength}_{evals}k_config_{configNumber}_{curve}_{method}.json
  # it contains the best results and the confidence interval
  for file in os.listdir(args.directory):
    if not file.endswith('.json'):
      continue
    print(file)
    # check if file name contains the given parameters
    if curve in file and method in file and temperatureLengthType in file and evals in file:
      with open(os.path.join(args.directory, file), "r") as f:
        data = json.load(f)
        print(data)
        for config in configurationData:
          if config["configName"] in file:
            config["best_results"] = data["best_results"]
            config["confidence_interval"] = data["confidence_interval"]
            
  print(configurationData)
  
  generateParameterComparisonGraph(configurationData, {
    "curve": curve,
    "method": method,
    "temperatureLength": temperatureLengthType
  })

if __name__ == "__main__":
  main()