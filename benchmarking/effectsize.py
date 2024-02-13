#!/usr/bin/env python3

import argparse
import json
import os
import numpy as np

from scipy import stats

from utils import convertFilenameToIdentifier, findBestSAConfiguration, getDataFromConfiguration, getFullMeanAndConfidenceFromConfiguration

OUTPUT_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "statisticalTests")

# inspired from: https://machinelearningmastery.com/effect-size-measures-in-python/
def cohen_d(group1, group2):
    # Calculate the means and standard deviations
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)

    # Calculate the pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * std1 ** 2 + (n2 - 1) * std2 ** 2) / (n1 + n2 - 2))

    # Calculate Cohen's d
    d = (mean1 - mean2) / pooled_std
    return d

def calculateEffectSize(bestResults, curve, method, evaluations, includeAllRuns=False):
  if not includeAllRuns:
    LSData = bestResults[curve][method][evaluations]["LS"]["best_results"]
  else:
    (LSConfidenceAllRuns, LSAverageAllRuns, LSData) = getFullMeanAndConfidenceFromConfiguration(bestResults[curve][method][evaluations]["LS"]["path"], bestResults[curve][method][evaluations]["LS"]["identifier"])
  
  if bestResults[curve][method][evaluations]["SA"] is None:
    print("no sa data for: {} {} {}".format(curve, method, evaluations))
    return {
      "LS_SA_FIXED": {
        "d": None,
      },
      "LS_SA_THRESHOLD": {
        "d": None,
      }
    }
  
  if not includeAllRuns:
    SA_FIXEDData = bestResults[curve][method][evaluations]["SA"]["FIXED"]["best_results"]
    SA_THRESHOLDData = bestResults[curve][method][evaluations]["SA"]["THRESHOLD"]["best_results"]
  else:
    (SA_FIXEDConfidenceAllRuns, SA_FIXEDAverageAllRuns, SA_FIXEDData) = getFullMeanAndConfidenceFromConfiguration(bestResults[curve][method][evaluations]["SA"]["FIXED"]["path"], bestResults[curve][method][evaluations]["SA"]["FIXED"]["identifier"])
    (SA_THRESHOLDConfidenceAllRuns, SA_THRESHOLDAverageAllRuns, SA_THRESHOLDData) = getFullMeanAndConfidenceFromConfiguration(bestResults[curve][method][evaluations]["SA"]["THRESHOLD"]["path"], bestResults[curve][method][evaluations]["SA"]["THRESHOLD"]["identifier"])
    
  # if len(LSData) != len(SA_FIXEDData) or len(LSData) != len(SA_THRESHOLDData):
  #   print("lengths do not match for: {} {} {}".format(curve, method, evaluations))
  #   print("LS: {}".format(len(LSData)))
  #   print("SA_FIXED: {}".format(len(SA_FIXEDData)))
  #   print("SA_THRESHOLD: {}".format(len(SA_THRESHOLDData)))
  #   return {
  #     "LS_SA_FIXED": {
  #       "d": None,
  #     },
  #     "LS_SA_THRESHOLD": {
  #       "d": None,
  #     }
  #   }
    
  if len(LSData) < 2 or len(SA_FIXEDData) < 2 or len(SA_THRESHOLDData) < 2:
    return {
      "LS_SA_FIXED": {
        "d": None,
      },
      "LS_SA_THRESHOLD": {
        "d": None,
      }
    }
  
  LS_SA_FIXED_d = cohen_d(SA_FIXEDData, LSData)
  
  LS_SA_THRESHOLD_d = cohen_d(SA_THRESHOLDData, LSData)
  
  
  return {
    "LS_SA_FIXED": {
      "d": LS_SA_FIXED_d,
    },
    "LS_SA_THRESHOLD": {
      "d": LS_SA_THRESHOLD_d,
    }
  }
  

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--allRuns", help="Specify if all runs should be used", action="store_true")
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
        "identifier": identifier,
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
  
  # calculate the effect size for every curve and method
  for curve in bestResults:
    for method in bestResults[curve]:
      effectSizeResult = {
        "10k": {},
        "20k": {},
        "50k": {},
        "100k": {},
        "200k": {},
      }
      for evaluations in bestResults[curve][method]:
        effectSizeResult[evaluations] = calculateEffectSize(bestResults, curve, method, evaluations, args.allRuns)
        
      fileName = "effectsize_{}_{}.json".format(curve, method)
      
      if args.allRuns:
        fileName = "effectsize_{}_{}_allRuns.json".format(curve, method)
        
      # save to json file (curve and method) append evaluations
      outputFilePath = os.path.join(OUTPUT_DIRECTORY, fileName)
      with open(outputFilePath, "w") as f:
        json.dump(effectSizeResult, f, indent=2)



if __name__ == "__main__":
  main()