#!/usr/bin/env python3

# define directories
# and plot the results

# we will compare three strategies: LS, SA (fixed interval) and SA (acceptance threshold)
# we will get a list of directories
# in a first step we will print out the best results for every strategy

import argparse
import json
import os
import numpy as np

from scipy import stats

MAX_RUNS = 10

def convertFilenameToIdentifier(filename):
  # example: best_results_LS_10k_curve25519_mul.json
  # other example: best_results_SA_FIXED_10k_1_curve25519_mul.json
  parts = filename.split("_")
  configuration_parts = parts[2:-2]  # Exclude "best_results" and the number of evaluations
  configuration = "_".join(configuration_parts)
  curve = parts[-2]
  method = parts[-1].split(".")[0]
  
  # find the evaluations. they are 10k, 20k, 50k, 100k or 200k
  for part in configuration_parts:
    if part.endswith("k"):
      evaluations = part
      break
  
  if configuration.startswith("results_"):
    configuration = configuration[8:]
  return {
    "configuration": configuration,
    "curve": curve,
    "method": method,
    "evaluations": evaluations
  }

def getAverageAndConfidenceFromConfiguration(directory, identifier):
  print("directory: ", directory)
  print("identifier: ", identifier)
  resultDir = directory
  
  curve = identifier["curve"]
  method = identifier["method"]
  
  print("result_dir: ", resultDir)
  
  # read all json files in the directory
  # load the every json file in the run directory
  inputData = []
  
  # iterate through all runs
  for run in range(0, MAX_RUNS):
    runData = []
    runDirectory = os.path.join(resultDir, f"run{run}", "fiat", f"fiat_{curve}_{method}")
    
    # check if the directory exists
    if not os.path.isdir(runDirectory):
      runDirectory = os.path.join(resultDir, f"run{run}", "fiat", f"fiat_{curve}_carry_{method}")
      
    print("run_directory: ", runDirectory)
    # iterate through all files
    for filename in os.listdir(runDirectory):
      if filename.endswith('.json') and '_details' in filename:
        seed = filename.split("_")[0]
        # check if there is a file with the same name but only with the seed in the beginning "seed_"
        # if there is not, skip this file
        if not os.path.isfile(os.path.join(runDirectory, f"{seed}.dat")): continue
        filepath = os.path.join(runDirectory, filename)
        with open(filepath) as f:
          runData.append(json.load(f))
          
    # sort the data by the ratio
    runData.sort(key=lambda x: x['ratio'])
    # print first and last element
    
    # only append the best result to the inputData
    inputData.append(runData[-1])
        
  print("inputData: ", len(inputData))
  # for every run, calculate the average for every data point and the confidence interval
  outputData = {
    "confidence": [],
    "averageConvergence": [],
    # identifier: {
    #   "configuration": identifier["configuration"],
    #   "curve": identifier["curve"],
    #   "method": identifier["method"]
    # }
  }
  
  for i in range(0, len(inputData[0]["convergence"])):
    # calculate the average for every data point
    dataPoint = []
    for run in inputData:
      dataPoint.append(run["convergence"][i])
    dataPointFloats = [float(i) for i in dataPoint]
    average = np.mean(dataPointFloats, dtype=np.float64)
    confidenceInterval = stats.t.interval(0.95, len(dataPointFloats)-1, loc=average, scale=stats.sem(dataPointFloats))
    outputData["confidence"].append(confidenceInterval)
    outputData["averageConvergence"].append(average)
    
  # save the outputData to a file next to the script
  # outputFilename = f"{identifier['configuration']}_{identifier['curve']}_{identifier['method']}.json"
  # outputFilePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), outputFilename)
  # with open(outputFilePath, "w") as f:
  #   json.dump(outputData, f)
  
  return outputData
  
def findBestSAConfiguration(directories, curve, method, evaluations):
  # there are two types: FIXED and THRESHOLD
  # summary files are named: "best_results_SA_FIXED_10k_1_curve25519_mul.json" for example
  # iterate through all files in the directories and find the best one for FIXED and THRESHOLD
  data = {
    "FIXED": {},
    "THRESHOLD": {}
  }
  
  highestConfidenceRatioFixed = 0
  highestConfidenceRatioThreshold = 0
  for directory in directories:
    for file in os.listdir(directory):
      if file.startswith("best_results_SA_FIXED") or file.startswith("MARKED_best_results_SA_FIXED") or file.startswith("best_results_SA_THRESHOLD") or file.startswith("MARKED_best_results_SA_THRESHOLD"):
        # get the curve and method from the filename
        identifier = convertFilenameToIdentifier(file)
        if identifier["curve"] == curve and identifier["method"] == method and str(evaluations) in identifier["configuration"]:
          # load the file and return the best result
          with open(os.path.join(directory, file)) as f:
            fileData = json.load(f)
          
          if "SA_FIXED" in identifier["configuration"]:
            confidenceLow = fileData["confidence_interval"][0]
            confidenceHigh = fileData["confidence_interval"][1]
            
            if confidenceHigh > highestConfidenceRatioFixed:
              highestConfidenceRatioFixed = confidenceHigh
              data["FIXED"] = {
                "configuration": identifier["configuration"],
                "path": os.path.join(directory, identifier["configuration"]),
                "curve": identifier["curve"],
                "method": identifier["method"],
                "evaluations": identifier["evaluations"],
                "confidence_interval": fileData["confidence_interval"],
                "best_results": fileData["best_results"]
              }
              
          if "SA_THRESHOLD" in identifier["configuration"]:
            confidenceLow = fileData["confidence_interval"][0]
            confidenceHigh = fileData["confidence_interval"][1]
            
            if confidenceHigh > highestConfidenceRatioThreshold:
              highestConfidenceRatioThreshold = confidenceHigh
              data["THRESHOLD"] = {
                "configuration": identifier["configuration"],
                "path": os.path.join(directory, identifier["configuration"]),
                "curve": identifier["curve"],
                "method": identifier["method"],
                "evaluations": identifier["evaluations"],
                "confidence_interval": fileData["confidence_interval"],
                "best_results": fileData["best_results"]
              }
  # if both FIXED and THRESHOLD are not empty objects return the data. otherwise return None
  if data["FIXED"] and data["THRESHOLD"]:
    return data
  else:
    return None
  
def generateComparisonPlot(bestResults, curve, method, evaluations):
  # generate a plot with the best results for LS, SA_FIXED and SA_THRESHOLD
  # x axis: number of evaluations (logarithmic)
  # y axis: ratio
  
  # get the data for LS
  LSResult = bestResults[curve][method][evaluations]["LS"]
  LSData = getAverageAndConfidenceFromConfiguration(LSResult["path"], LSResult)
  
  # get the data for SA_FIXED
  SA_FIXEDResult = bestResults[curve][method][evaluations]["SA"]["FIXED"]
  SA_FIXEDData = getAverageAndConfidenceFromConfiguration(SA_FIXEDResult["path"], SA_FIXEDResult)
  
  # get the data for SA_THRESHOLD
  SA_THRESHOLDResult = bestResults[curve][method][evaluations]["SA"]["THRESHOLD"]
  SA_THRESHOLDData = getAverageAndConfidenceFromConfiguration(SA_THRESHOLDResult["path"], SA_THRESHOLDResult)
  
  # write the data to a file
  outputFilename = f"comparison_{curve}_{method}_{evaluations}.json"
  outputFilePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), outputFilename)
  with open(outputFilePath, "w") as f:
    json.dump({
      "LS": LSData,
      "SA_FIXED": SA_FIXEDData,
      "SA_THRESHOLD": SA_THRESHOLDData
    }, f)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--directories", nargs='+', help="Specify the directories to compare")

  args = parser.parse_args()
  identifiers = []
  
  bestResults = {
    "curve25519": {
      "mul": {},
      "square": {},
    },
    "p256": {
      "mul": {},
      "square": {},
    },
    "p384": {
      "mul": {},
      "square": {},
    },
  }
  
  # first find the reference LS directory and collect the identifiers
  for directory in args.directories:
    for file in os.listdir(directory):
      if file.startswith("best_results_LS"):
        identifier = convertFilenameToIdentifier(file)
        identifier["path"] = os.path.join(directory, identifier["configuration"])
        print(identifier)
        identifiers.append(identifier)

  for identifier in identifiers:
    SAResults = findBestSAConfiguration(args.directories, identifier["curve"], identifier["method"], identifier["evaluations"])
    
    bestResults[identifier["curve"]][identifier["method"]][identifier["evaluations"]] = {
      "LS": {
        "configuration": identifier["configuration"],
        "path": identifier["path"],
        "curve": identifier["curve"],
        "method": identifier["method"],
        "evaluations": identifier["evaluations"]
      },
      "SA": SAResults
    }

  print(bestResults)
  generateComparisonPlot(bestResults, "curve25519", "mul", "10k")

# get the data
# every configuration has a directory with 10 runs in it and the curve with method as a subdirectory
# in every run are four independant runs with the same configuration. only the best is used and counts as a run
# calculate an average over the 10 runs


# plotting
# use seaborn
# disable grid lines


if __name__ == "__main__":
  main()