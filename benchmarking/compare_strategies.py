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

from utils import convertFilenameToIdentifier, findBestSAConfiguration, getDataFromConfiguration, getFullMeanAndConfidenceFromConfiguration

OUTPUT_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "plots")


def generateSingleRunComparisonPlot(bestResults, curve, method, evaluations):  
  # get the data for LS
  LSResult = bestResults[curve][method][evaluations]["LS"]
  LSData = getDataFromConfiguration(LSResult["path"], LSResult)
  
  # get the data for SA_FIXED
  if bestResults[curve][method][evaluations]["SA"] is None:
    return
  SA_FIXEDResult = bestResults[curve][method][evaluations]["SA"]["FIXED"]
  SA_FIXEDData = getDataFromConfiguration(SA_FIXEDResult["path"], SA_FIXEDResult)
  
  # get the data for SA_THRESHOLD
  SA_THRESHOLDResult = bestResults[curve][method][evaluations]["SA"]["THRESHOLD"]
  SA_THRESHOLDData = getDataFromConfiguration(SA_THRESHOLDResult["path"], SA_THRESHOLDResult)
  
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
  outputFilePath = os.path.join(OUTPUT_DIRECTORY, f"comparison_{curve}_{method}_{evaluations}.png")
  fig.savefig(outputFilePath)
  
# create a comparison plot for a single curve and method with every evaluation
def prepareDataForComparisonPlot(bestResults, curve, method):  
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
    
    print("LSResult: ", LSResult)
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
  
  # sort dfConfidence by index in the desired order
  dfConfidence = dfConfidence.reindex(["10k", "20k", "50k", "100k", "200k"])
  
  # remove indexes with NaN values
  dfAverage = dfAverage.dropna()
  dfConfidence = dfConfidence.dropna()
  
  print("dfAverage: ", dfAverage)
  
  print("dfConfidence: ", dfConfidence)
  
  # plot the data
  # x axis: number of evaluations (logarithmic)
  # y axis: ratio
  # hue: strategy (LS, SA_FIXED, SA_THRESHOLD)
  
  sns.lineplot(data=dfAverage, ax=ax, alpha=0.5)
  

  # Plot confidence intervals for each strategy
  for column in dfConfidence.columns:
    # Extract lower and upper bounds of confidence intervals
    lower_bounds = [interval[0] for interval in dfConfidence[column]]
    upper_bounds = [interval[1] for interval in dfConfidence[column]]

    # Plot confidence intervals with fill_between
    ax.fill_between(dfConfidence.index, lower_bounds, upper_bounds, alpha=0.2, label=column)

    # Annotate averages to data points
    for i, avg in enumerate(dfAverage[column]):
      ax.annotate(f"{avg:.2f}", (dfAverage.index[i], avg), textcoords="offset points", xytext=(0, 0), fontsize=8)
      
    # Annotate confidence intervals to data points
    for i, interval in enumerate(dfConfidence[column]):
      ax.annotate(f"{interval[0]:.2f} - {interval[1]:.2f}", (dfConfidence.index[i], interval[1]), textcoords="offset points", xytext=(0, 0), fontsize=6)
      


  
  outputFilePath = os.path.join(OUTPUT_DIRECTORY, f"comparison_all_{curve}_{method}.png")
  fig.savefig(outputFilePath)

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--allRuns", help="Specify if all runs should be used")
  parser.add_argument("--directories", nargs='+', help="Specify the directories to compare")

  args = parser.parse_args()
  identifiers = []

  # ensure that the output directory exists
  if not os.path.isdir(OUTPUT_DIRECTORY):
    os.mkdir(OUTPUT_DIRECTORY)
  
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
          
        (confidenceAllRuns, averageAllRuns, ratios) = getFullMeanAndConfidenceFromConfiguration(identifier["path"], identifier)
        
        identifier["confidence_interval_allRuns"] = confidenceAllRuns
        identifier["average_allRuns"] = averageAllRuns
        identifier["ratios"] = ratios
          
        identifier["confidence_interval"] = data["confidence_interval"]
        
        # if confidenceHigh is NaN set it to the first value of best_results
        if np.isnan(identifier["confidence_interval"][1]):
          identifier["confidence_interval"][0] = data["best_results"][0]
          identifier["confidence_interval"][1] = data["best_results"][0]
        
        identifier["best_results"] = data["best_results"]
        identifiers.append(identifier)

  for identifier in identifiers:
    SAResults = findBestSAConfiguration(args.directories, identifier["curve"], identifier["method"], identifier["evaluations"])
    
    
    if SAResults is None:
      continue
    
    (SA_FIXEDConfidenceAllRuns, SA_FIXEDAverageAllRuns, SA_FIXEDRatios) = getFullMeanAndConfidenceFromConfiguration(SAResults["FIXED"]["path"], identifier)
    
    (SA_THRESHOLDConfidenceAllRuns, SA_THRESHOLDAverageAllRuns, SA_THRESHOLDRatios) = getFullMeanAndConfidenceFromConfiguration(SAResults["THRESHOLD"]["path"], identifier)
    
    # SAResults["FIXED"]["confidence_interval_allRuns"] = SAFIXED_confidenceAllRuns
    # SAResults["FIXED"]["average_allRuns"] = SAFIXED_averageAllRuns
    
    # SAResults["THRESHOLD"]["confidence_interval_allRuns"] = SATHRESHOLD_confidenceAllRuns
    # SAResults["THRESHOLD"]["average_allRuns"] = SATHRESHOLD_averageAllRuns
    
    
    if args.allRuns:
      identifier["confidence_interval"] = identifier["confidence_interval_allRuns"]
      identifier["best_results"] = identifier["ratios"]
      
      SAResults["FIXED"]["confidence_interval"] = SA_FIXEDConfidenceAllRuns
      SAResults["FIXED"]["best_results"] = SA_FIXEDRatios
      
      SAResults["THRESHOLD"]["confidence_interval"] = SA_THRESHOLDConfidenceAllRuns
      SAResults["THRESHOLD"]["best_results"] = SA_THRESHOLDRatios
      
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
  
  # dfAverage, dfConfidence = prepareDataForComparisonPlot(bestResults, "p384", "mul")
  
  # print("dfAverage: ", dfAverage)
  # print("dfConfidence: ", dfConfidence)
  
  # generateCurveComparisonPlot(dfAverage, dfConfidence, "p384", "mul")
  
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