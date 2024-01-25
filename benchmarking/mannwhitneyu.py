#!/usr/bin/env python3
# mann-whitney u test (rank sum test)

# steps:
# 1. load all runs from best configuration / LS = every run
# 2. use data from all runs to calculate mann-whitney u test

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

from utils import convertFilenameToIdentifier, findBestSAConfiguration, getDataFromConfiguration, getFullMeanAndConfidenceFromConfiguration

OUTPUT_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "statisticalTests")

def calculateMannWhitneyU(bestResults, curve, method, evaluations, includeAllRuns=False):
  if not includeAllRuns:
    LSData = bestResults[curve][method][evaluations]["LS"]["best_results"]
  else:
    LSData = getDataFromConfiguration(bestResults[curve][method][evaluations]["LS"]["path"], bestResults[curve][method][evaluations]["LS"])["convergence"]
  
  if bestResults[curve][method][evaluations]["SA"] is None:
    return {
      "LS_SA_FIXED": {
        "uStatistic": None,
        "pValue": None
      },
      "LS_SA_THRESHOLD": {
        "uStatistic": None,
        "pValue": None
      }
    }
  
  if not includeAllRuns:
    SA_FIXEDData = bestResults[curve][method][evaluations]["SA"]["FIXED"]["best_results"]
    SA_THRESHOLDData = bestResults[curve][method][evaluations]["SA"]["THRESHOLD"]["best_results"]
  else:
    (SA_FIXEDConfidenceAllRuns, SA_FIXEDAverageAllRuns, SA_FIXEDData) = getFullMeanAndConfidenceFromConfiguration(bestResults[curve][method][evaluations]["SA"]["FIXED"]["path"], bestResults[curve][method][evaluations]["SA"]["FIXED"]["identifier"])
    (SA_THRESHOLDConfidenceAllRuns, SA_THRESHOLDAverageAllRuns, SA_THRESHOLDData) = getFullMeanAndConfidenceFromConfiguration(bestResults[curve][method][evaluations]["SA"]["THRESHOLD"]["path"], bestResults[curve][method][evaluations]["SA"]["THRESHOLD"]["identifier"])
  
  LS_SA_FIXED_uStatistic, LS_SA_FIXED_pValue = stats.mannwhitneyu(LSData, SA_FIXEDData, alternative="two-sided")
  
  
  LS_SA_THRESHOLD_uStatistic, LS_SA_THRESHOLD_pValue = stats.mannwhitneyu(LSData, SA_THRESHOLDData, alternative="two-sided")
  
  
  return {
    "LS_SA_FIXED": {
      "uStatistic": LS_SA_FIXED_uStatistic,
      "pValue": LS_SA_FIXED_pValue
    },
    "LS_SA_THRESHOLD": {
      "uStatistic": LS_SA_THRESHOLD_uStatistic,
      "pValue": LS_SA_THRESHOLD_pValue
    }
  
  }
  

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--allRuns", help="Specify if all runs should be used")
  parser.add_argument("--directories", nargs='+', help="Specify the directories to compare")

  args = parser.parse_args()
  identifiers = []

  # ensure that the output directory exists
  if not os.path.exists(OUTPUT_DIRECTORY):
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
          
        identifier["confidence_interval"] = data["confidence_interval"]
        
        # if confidenceHigh is NaN set it to the first value of best_results
        if np.isnan(identifier["confidence_interval"][1]):
          identifier["confidence_interval"][0] = data["best_results"][0]
          identifier["confidence_interval"][1] = data["best_results"][0]
        
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
  
  # calculate mann-whitney u test for every curve and method
  for curve in bestResults:
    for method in bestResults[curve]:
      mannWhitneyResult = {
        "10k": {},
        "20k": {},
        "50k": {},
        "100k": {},
        "200k": {},
      }
      for evaluations in bestResults[curve][method]:
        mannWhitneyResult[evaluations] = calculateMannWhitneyU(bestResults, curve, method, evaluations, args.allRuns)
        
      # save to json file (curve and method) append evaluations
      outputFilePath = os.path.join(OUTPUT_DIRECTORY, "mannwhitneyu_{}_{}.json".format(curve, method))
      with open(outputFilePath, "w") as f:
        json.dump(mannWhitneyResult, f, indent=2)



if __name__ == "__main__":
  main()