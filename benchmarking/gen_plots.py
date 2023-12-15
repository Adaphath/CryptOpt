#!/usr/bin/env python3
import json
import argparse
import os
import datetime
import glob
import matplotlib.pyplot as plt

# Load the JSON data
# with open('scripts/example_data.json') as f:
#     data = json.load(f)


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

convergence_data = []
numEvals_data = []
worseSolutionStatistics_data = []
worseSolutionEvaluations_data = []
evaluations_data = []

for data in inputData:
  # Extract the 'convergence' and 'numEvals' fields
  convergence = [float(i) for i in data['convergence']]
  numEvals = data['numEvals']

  worseSolutionStatistics = [float(i) for i in data['worseSolutionStatistics']]
  worseSolutionEvaluations = list(range(0, numEvals - (numEvals//100), numEvals//100))

  # Create a list for evaluations that increments by 20 for each convergence value
  evaluations = list(range(0, numEvals, 20))

  # Ensure that the lengths of 'evaluations' and 'convergence' are the same
  if len(evaluations) > len(convergence):
    evaluations = evaluations[:len(convergence)]
  elif len(convergence) > len(evaluations):
    convergence = convergence[:len(evaluations)]

  # Ensure that the lengths of 'evaluations' and 'worseSolutionStatistics' are the same
  if len(worseSolutionEvaluations) > len(worseSolutionStatistics):
    evaluations = evaluations[:len(worseSolutionEvaluations)]
  elif len(worseSolutionStatistics) > len(worseSolutionEvaluations):
    worseSolutionStatistics = worseSolutionStatistics[:len(worseSolutionEvaluations)]

  convergence_data.append(convergence)
  numEvals_data.append(numEvals)
  worseSolutionStatistics_data.append(worseSolutionStatistics)
  worseSolutionEvaluations_data.append(worseSolutionEvaluations)
  evaluations_data.append(evaluations)


# Use the data arrays for further processing or plotting
for i in range(len(inputData)):
  convergence = convergence_data[i]
  numEvals = numEvals_data[i]
  worseSolutionStatistics = worseSolutionStatistics_data[i]
  worseSolutionEvaluations = worseSolutionEvaluations_data[i]
  evaluations = evaluations_data[i]

  # Perform operations with the data arrays


fig, ax1 = plt.subplots(3)
fig.suptitle('Convergence and worse solution statistics')
# if only a single file was given, plot the data
if len(inputData) == 1:
  
  # Scatter plot of convergence
  ax1[0].scatter(evaluations_data[0], convergence_data[0], label=inputData[0]['ratio'], alpha=0.3, edgecolors='none')
  ax1[0].set_xlabel('Evaluation')
  ax1[0].set_ylabel('Ratio')
  ax1[0].set_title('Convergence')
  ax1[0].legend()

  # Box plot of convergence
  ax1[1].boxplot(convergence_data[0])
  ax1[1].set_xlabel('Evaluation')
  ax1[1].set_ylabel('Ratio')
  ax1[1].set_title('Convergence')

  # Line plot of worse solution statistics
  ax1[2].plot(worseSolutionEvaluations_data[0], worseSolutionStatistics_data[0])
  ax1[2].set_xlabel('Evaluation')
  ax1[2].set_ylabel('Probability')
  ax1[2].set_title('Worse solution statistics')

# if multiple files were given, plot the data within subplots. In the scatter plot every file is plotted in a different color.
else:
  # Scatter plot of convergence
  for i in range(len(inputData)):
    ax1[0].scatter(evaluations_data[i], convergence_data[i], label=inputData[i]['ratio'], alpha=0.3, edgecolors='none')
  ax1[0].set_xlabel('Evaluation')
  ax1[0].set_ylabel('Ratio')
  ax1[0].set_title('Convergence')
  ax1[0].legend()
  
  # Box plot of convergence for each file in subplots
  for i in range(len(inputData)):
    ax1[1].boxplot(convergence_data[i], positions=[i+1])
  ax1[1].set_xlabel('Evaluation')
  ax1[1].set_ylabel('Ratio')
  ax1[1].set_title('Convergence')
  ax1[1].set_xticks(list(range(1, len(inputData)+1)))
  ax1[1].set_xticklabels([inputData[i]['seed'] for i in range(len(inputData))])
  
  # Line plot of worse solution statistics for each file in subplots in different colors
  for i in range(len(inputData)):
    ax1[2].plot(worseSolutionEvaluations_data[i], worseSolutionStatistics_data[i], label=inputData[i]['seed'])
  ax1[2].set_xlabel('Evaluation')
  ax1[2].set_ylabel('Probability')
  ax1[2].set_title('Worse solution statistics')
  ax1[2].legend()
  
  # fig.subplots_adjust(hspace=2)

  

# get current timestamp
now = datetime.datetime.now()
fig.set_size_inches(10, 5)
fig.savefig('scripts/' + now.isoformat() + '.svg')
    
# fig, ax1 = plt.subplots(3)
# fig.suptitle('Convergence and worse solution statistics')
# # Scatter plot of convergence
# ax1[0].scatter(evaluations_data[0], convergence_data[0])
# ax1[0].set_xlabel('Evaluation')
# ax1[0].set_ylabel('Ratio')
# ax1[0].set_title('Convergence')

# # Box plot of convergence
# ax1[1].boxplot(convergence_data[0])
# ax1[1].set_xlabel('Evaluation')
# ax1[1].set_ylabel('Ratio')
# ax1[1].set_title('Convergence')

# # Line plot of worse solution statistics
# ax1[2].plot(worseSolutionEvaluations_data[0], worseSolutionStatistics_data[0])
# ax1[2].set_xlabel('Evaluation')
# ax1[2].set_ylabel('Probability')
# ax1[2].set_title('Worse solution statistics')

# fig.subplots_adjust(hspace=1)

# fig.savefig('scripts/example_plot.svg')