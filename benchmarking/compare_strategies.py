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
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

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
  
def generateSingleRunComparisonPlot(bestResults, curve, method, evaluations):  
  # get the data for LS
  LSResult = bestResults[curve][method][evaluations]["LS"]
  LSData = getAverageAndConfidenceFromConfiguration(LSResult["path"], LSResult)
  
  # get the data for SA_FIXED
  if bestResults[curve][method][evaluations]["SA"] is None:
    return
  SA_FIXEDResult = bestResults[curve][method][evaluations]["SA"]["FIXED"]
  SA_FIXEDData = getAverageAndConfidenceFromConfiguration(SA_FIXEDResult["path"], SA_FIXEDResult)
  
  # get the data for SA_THRESHOLD
  SA_THRESHOLDResult = bestResults[curve][method][evaluations]["SA"]["THRESHOLD"]
  SA_THRESHOLDData = getAverageAndConfidenceFromConfiguration(SA_THRESHOLDResult["path"], SA_THRESHOLDResult)
  
  # write the data to a file
  outputFilename = f"comparison_{curve}_{method}_{evaluations}.json"
  outputFilePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), outputFilename)
  # with open(outputFilePath, "w") as f:
  #   json.dump({
  #     "LS": LSData,
  #     "SA_FIXED": SA_FIXEDData,
  #     "SA_THRESHOLD": SA_THRESHOLDData
  #   }, f)
    
  
  # disable grid lines
  sns.set_style("whitegrid")
  
  # set the font size
  sns.set(font_scale=1.5)
  
  # create a new figure
  fig, ax = plt.subplots(figsize=(12, 8))
  
  # plot the data
  # x axis: number of evaluations (logarithmic)
  # y axis: ratio
  # hue: strategy (LS, SA_FIXED, SA_THRESHOLD)
  max_length = max(len(LSData["averageConvergence"]), len(SA_FIXEDData["averageConvergence"]), len(SA_THRESHOLDData["averageConvergence"]))
  # create arrays with our first value of LSData["averageConvergence"] as padding
  paddingArray = np.full(max_length - len(LSData["averageConvergence"]), LSData["averageConvergence"][0])
  
  LSData["averageConvergence"] = np.concatenate((paddingArray, LSData["averageConvergence"]))
  
  sns.lineplot(data=LSData["averageConvergence"], label=f"LS (95%: {np.round(LSResult['confidence_interval'][0], 3)} - {np.round(LSResult['confidence_interval'][1], 3)})", ax=ax, alpha=0.5, color="blue")
  
  upperConfidence = []
  lowerConfidence = []
  
  for i in range(0, len(LSData["confidence"])):
    upperConfidence.append(LSData["confidence"][i][1])
    lowerConfidence.append(LSData["confidence"][i][0])
  
  # add padding to the confidence interval
  upperConfidencePadding = np.full(max_length - len(upperConfidence), upperConfidence[0])
  
  upperConfidence = np.concatenate((upperConfidencePadding, upperConfidence))
  lowerConfidence = np.concatenate((upperConfidencePadding, lowerConfidence))
    
  # plot the confidence interval
  ax.fill_between(range(0, len(upperConfidence)), upperConfidence, lowerConfidence, alpha=0.1, color="blue")
  
  sns.lineplot(data=SA_FIXEDData["averageConvergence"], label=f"SA_FIXED (95%: {np.round(SA_FIXEDResult['confidence_interval'][0], 3)} - {np.round(SA_FIXEDResult['confidence_interval'][1], 3)})", ax=ax, alpha=0.5, color="orange")
  
  upperConfidence = []
  lowerConfidence = []
  
  for i in range(0, len(SA_FIXEDData["confidence"])):
    upperConfidence.append(SA_FIXEDData["confidence"][i][1])
    lowerConfidence.append(SA_FIXEDData["confidence"][i][0])
    
  # add padding to the confidence interval
  upperConfidencePadding = np.full(max_length - len(upperConfidence), upperConfidence[0])
  
  upperConfidence = np.concatenate((upperConfidencePadding, upperConfidence))
  lowerConfidence = np.concatenate((upperConfidencePadding, lowerConfidence))
  
  # plot the confidence interval
  ax.fill_between(range(0, len(upperConfidence)), upperConfidence, lowerConfidence, alpha=0.1, color="orange")
  
  sns.lineplot(data=SA_THRESHOLDData["averageConvergence"], label=f"SA_THRESHOLD (95%: {np.round(SA_THRESHOLDResult['confidence_interval'][0], 3)} - {np.round(SA_THRESHOLDResult['confidence_interval'][1], 3)})", ax=ax, alpha=0.5, color="green")
  
  upperConfidence = []
  lowerConfidence = []
  
  for i in range(0, len(SA_THRESHOLDData["confidence"])):
    upperConfidence.append(SA_THRESHOLDData["confidence"][i][1])
    lowerConfidence.append(SA_THRESHOLDData["confidence"][i][0])
    
  # add padding to the confidence interval
  upperConfidencePadding = np.full(max_length - len(upperConfidence), upperConfidence[0])

  upperConfidence = np.concatenate((upperConfidencePadding, upperConfidence))
  lowerConfidence = np.concatenate((upperConfidencePadding, lowerConfidence))
  
  # plot the confidence interval
  ax.fill_between(range(0, len(upperConfidence)), upperConfidence, lowerConfidence, alpha=0.1, color="green")
  
  # set the x axis to logarithmic
  # ax.set_xscale("log")
  
  # disable grid lines
  ax.grid(False)
  
  # set the x axis label
  ax.set_xlabel("Number of evaluations")
  
  # set the y axis label
  ax.set_ylabel("Ratio")
  
  # set the title
  ax.set_title(f"Comparison of LS, SA_FIXED and SA_THRESHOLD for {curve}_{method}_{evaluations}")
  
  # save the figure
  fig.savefig(f"comparison_{curve}_{method}_{evaluations}.png")
  
# create a comparison plot for a single curve and method with every evaluation
def prepareDataForComparisonPlot(bestResults, curve, method):
  print("bestResults: ", bestResults)
  
  # get the data for LS for every evaluation
  LSAverageData = {}
  LSConfidenceData = {}
  # get the data for SA_FIXED for every evaluation
  SA_FIXEDAverageData = {}
  SA_FIXEDConfidenceData = {}
  # get the data for SA_THRESHOLD for every evaluation
  SA_THRESHOLDAverageData = {}
  SA_THRESHOLDConfidenceData = {}
  for evaluations in bestResults[curve][method]:
    if bestResults[curve][method][evaluations]["SA"] is None:
      continue
    
    LSResult = bestResults[curve][method][evaluations]["LS"]
    # calculate average
    LSAverageData[evaluations] = np.mean(LSResult["best_results"])
    # add confidence interval to the data
    LSConfidenceData[evaluations] = LSResult["confidence_interval"]
    
    SA_FIXEDResult = bestResults[curve][method][evaluations]["SA"]["FIXED"]
    # calculate average
    SA_FIXEDAverageData[evaluations] = np.mean(SA_FIXEDResult["best_results"])
    # add confidence interval to the data
    SA_FIXEDConfidenceData[evaluations] = SA_FIXEDResult["confidence_interval"]
    
    SA_THRESHOLDResult = bestResults[curve][method][evaluations]["SA"]["THRESHOLD"]
    # calculate average
    SA_THRESHOLDAverageData[evaluations] = np.mean(SA_THRESHOLDResult["best_results"])
    # add confidence interval to the data
    SA_THRESHOLDConfidenceData[evaluations] = SA_THRESHOLDResult["confidence_interval"]
    
  
  dfAverage = pd.DataFrame({
    "LS": LSAverageData,
    "SA_FIXED": SA_FIXEDAverageData,
    "SA_THRESHOLD": SA_THRESHOLDAverageData
  })
  
  dfConfidence = pd.DataFrame({
    "LS": LSConfidenceData,
    "SA_FIXED": SA_FIXEDConfidenceData,
    "SA_THRESHOLD": SA_THRESHOLDConfidenceData
  })
  
    
  
  return dfAverage, dfConfidence

def generateCurveComparisonPlot(dfAverage, dfConfidence, curve, method):
  # set the font size
  sns.set(font_scale=1.5)
  
  # create a new figure
  fig, ax = plt.subplots(figsize=(12, 8))
  
  # disable grid lines
  ax.grid(False)
  
  # set the x axis label
  ax.set_xlabel("Number of evaluations")
  
  # set the y axis label
  ax.set_ylabel("Ratio")
  
  # set the title
  ax.set_title(f"Comparison of LS, SA_FIXED and SA_THRESHOLD for {curve}_{method}")
  
  # sort dfAverage by index in the desired order
  dfAverage = dfAverage.reindex(["10k", "20k", "50k", "100k", "200k"])
  
  print("dfAverage: ", dfAverage)
  
  # plot the data
  # x axis: number of evaluations (logarithmic)
  # y axis: ratio
  # hue: strategy (LS, SA_FIXED, SA_THRESHOLD)
  
  sns.lineplot(data=dfAverage, ax=ax, alpha=0.5)
  
  fig.savefig(f"comparison2_{curve}_{method}.png")

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
        # get the data for this identifier
        data = []
        with open(os.path.join(directory, file)) as f:
          data = json.load(f)
          
        identifier["confidence_interval"] = data["confidence_interval"]
        identifier["best_results"] = data["best_results"]
        identifiers.append(identifier)

  for identifier in identifiers:
    SAResults = findBestSAConfiguration(args.directories, identifier["curve"], identifier["method"], identifier["evaluations"])
    
    bestResults[identifier["curve"]][identifier["method"]][identifier["evaluations"]] = {
      "LS": {
        "configuration": identifier["configuration"],
        "path": identifier["path"],
        "curve": identifier["curve"],
        "method": identifier["method"],
        "evaluations": identifier["evaluations"],
        "confidence_interval": identifier["confidence_interval"],
        "best_results": identifier["best_results"]
      },
      "SA": SAResults
    }

  # print(bestResults)
  
  dfAverage, dfConfidence = prepareDataForComparisonPlot(bestResults, "curve25519", "mul")
  
  print("dfAverage: ", dfAverage)
  print("dfConfidence: ", dfConfidence)
  
  # generate a plot for every curve and method
  for curve in bestResults:
    for method in bestResults[curve]:
      dfAverage, dfConfidence = prepareDataForComparisonPlot(bestResults, curve, method)
      generateCurveComparisonPlot(dfAverage, dfConfidence, curve, method)
  
  
  
  # generate a plot for every curve and method and evaluation
  # for curve in bestResults:
  #   for method in bestResults[curve]:
  #     for evaluations in bestResults[curve][method]:
  #       generateComparisonPlot(bestResults, curve, method, evaluations)



if __name__ == "__main__":
  main()