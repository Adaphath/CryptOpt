#!/usr/bin/env python3
import json
import argparse
import os
import datetime
import glob

# evaluate file path argument and load data
parser = argparse.ArgumentParser(description='Plot data from json files.')
parser.add_argument('files', metavar='file', type=str, nargs='+',
      help='file paths to json files or directory')
args = parser.parse_args()

inputData = []
for file in args.files:
  if os.path.isdir(file):
    for root, dirs, files in os.walk(file):
      for filename in files:
        if filename.endswith('.json') and '_details' in filename:
          filepath = os.path.join(root, filename)
          with open(filepath) as f:
            inputData.append(json.load(f))
  else:
    # Check if the file path contains a wildcard
    if '*' in file:
      matching_files = glob.glob(file)
      for matching_file in matching_files:
        with open(matching_file) as f:
          inputData.append(json.load(f))
    else:
      with open(file) as f:
        inputData.append(json.load(f))
      
print(inputData)

# iterate through the data and create a ranking of each algorithm based on the ratio

rankings = []

for data in inputData:
  ratio = data['ratio']
  timeTaken = data['elapsed']
  
  rankings.append((ratio, timeTaken, data))
  
# sort the rankings by the ratio
rankings.sort(key=lambda x: x[0])

# print the rankings
### "optimizer":"SA","initialTemperature":532.6979178908545,"alpha":0.97,"threshholdOfAcceptedSolutions":100,"temperatureLengthType":"TL1","temperatureLengthEvals":25
for ranking in rankings:
  print(ranking[0], ranking[1], ranking[2]['optimizer'], ranking[2]['initialTemperature'], ranking[2]['alpha'], ranking[2]['threshholdOfAcceptedSolutions'], ranking[2]['temperatureLengthType'], ranking[2]['temperatureLengthEvals'])