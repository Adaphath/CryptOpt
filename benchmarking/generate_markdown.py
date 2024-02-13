#!/usr/bin/env python3
import json
import os
import mdutils


# Structure:
# Heading 1: Curve Name
# Heading 2: Method Name
# Comparison Plot
# Heading 2: Statistical Tests (Mann-Whitney U Test (with Link to Wikipedia), Cohen's d (with Link to Wikipedia))
# Table with p-values and effect sizes (for LS_SA_FIXED and LS_SA_THRESHOLD)

fileName = "results.md"
mdFile = mdutils.MdUtils(file_name='benchmarking/{}'.format(fileName), title='Results')

curves = ["curve25519", "p256", "p384"]
methods = ["mul", "square"]
evaluations = ["10k", "20k", "50k", "100k", "200k"]

for curve in curves:
  mdFile.new_header(level=1, title=curve)
  for method in methods:
    mdFile.new_header(level=2, title=method)
    mdFile.new_header(level=2, title=f"{method} (all runs)")
    image_path = f"./plots/comparison_{curve}_{method}.svg"
    image_path_allRuns = f"./plots/comparison_{curve}_{method}_allRuns.svg"
      
    # mdFile.new_line(mdFile.new_inline_image(text=f"Comparison Plot for {curve} {method}", path=image_path))
    # mdFile.new_line(mdFile.new_inline_image(text=f"Comparison Plot for {curve} {method} (all runs)", path=image_path_allRuns))

    mdFile.new_header(level=2, title="[Mann-Whitney U Test](https://en.wikipedia.org/wiki/Mann%E2%80%93Whitney_U_test) and [Cohen's d](https://en.wikipedia.org/wiki/Effect_size#Cohen's_d)")
    for evaluation in evaluations:
      # load data from json file
      effectSizeInputData = []
      effectSizeFileName = f"effectsize_{curve}_{method}.json"
      effectSizeAllRunsFileName = f"effectsize_{curve}_{method}_allRuns.json"
        
      effectSizeFilePath = os.path.join(os.path.dirname(__file__), 'statisticalTests', effectSizeFileName)
      effectSizeAllRunsFilePath = os.path.join(os.path.dirname(__file__), 'statisticalTests', effectSizeAllRunsFileName)
      with open(effectSizeFilePath) as f:
        effectSizeInputData = json.load(f)
        
      with open(effectSizeAllRunsFilePath) as f:
        effectSizeInputDataAllRuns = json.load(f)

      mannWhitneyInputData = []
      mannWhitneyFileName = f"mannwhitneyu_{curve}_{method}.json"
      mannWhitneyAllRunsFileName = f"mannwhitneyu_{curve}_{method}_allRuns.json"
        
      mannWhitneyFilePath = os.path.join(os.path.dirname(__file__), 'statisticalTests', mannWhitneyFileName)
      mannWhitneyAllRunsFilePath = os.path.join(os.path.dirname(__file__), 'statisticalTests', mannWhitneyAllRunsFileName)
      with open(mannWhitneyFilePath) as f:
        mannWhitneyInputData = json.load(f)
        
      with open(mannWhitneyAllRunsFilePath) as f:
        mannWhitneyInputDataAllRuns = json.load(f)

      print("evaluation: ", evaluation)
      print("effectSizeInputData: ", effectSizeInputData[evaluation])

      # check if d value is None
      if effectSizeInputData[evaluation]["LS_SA_FIXED"]["d"] is None:
        effectSizeInputData[evaluation]["LS_SA_FIXED"]["d"] = 0

      if effectSizeInputData[evaluation]["LS_SA_THRESHOLD"]["d"] is None:
        effectSizeInputData[evaluation]["LS_SA_THRESHOLD"]["d"] = 0

      if mannWhitneyInputData[evaluation]["LS_SA_FIXED"]["pValue"] is None:
        mannWhitneyInputData[evaluation]["LS_SA_FIXED"]["pValue"] = 0
      
      if mannWhitneyInputData[evaluation]["LS_SA_THRESHOLD"]["pValue"] is None:
        mannWhitneyInputData[evaluation]["LS_SA_THRESHOLD"]["pValue"] = 0
        
      if effectSizeInputDataAllRuns[evaluation]["LS_SA_FIXED"]["d"] is None:
        effectSizeInputDataAllRuns[evaluation]["LS_SA_FIXED"]["d"] = 0
      
      if effectSizeInputDataAllRuns[evaluation]["LS_SA_THRESHOLD"]["d"] is None:
        effectSizeInputDataAllRuns[evaluation]["LS_SA_THRESHOLD"]["d"] = 0
        
      if mannWhitneyInputDataAllRuns[evaluation]["LS_SA_FIXED"]["pValue"] is None:
        mannWhitneyInputDataAllRuns[evaluation]["LS_SA_FIXED"]["pValue"] = 0
        
      if mannWhitneyInputDataAllRuns[evaluation]["LS_SA_THRESHOLD"]["pValue"] is None:
        mannWhitneyInputDataAllRuns[evaluation]["LS_SA_THRESHOLD"]["pValue"] = 0

      mdFile.new_header(level=3, title=f"{evaluation}")
      # create table with p-values and effect sizes
      list_of_strings = ["Configuration", "p-value", "Effect Size"]
      list_of_strings.extend(["LS_SA_FIXED", round(mannWhitneyInputData[evaluation]["LS_SA_FIXED"]["pValue"], 3), round(effectSizeInputData[evaluation]["LS_SA_FIXED"]["d"], 3)])
      list_of_strings.extend(["LS_SA_THRESHOLD", round(mannWhitneyInputData[evaluation]["LS_SA_THRESHOLD"]["pValue"], 3), round(effectSizeInputData[evaluation]["LS_SA_THRESHOLD"]["d"], 3)])
      mdFile.new_line()
      mdFile.new_table(columns=3, rows=3, text=list_of_strings, text_align='center')
      
      mdFile.new_header(level=3, title=f"{evaluation} (all runs)")
      # create table with p-values and effect sizes
      list_of_strings = ["Configuration", "p-value", "Effect Size"]
      list_of_strings.extend(["LS_SA_FIXED", round(mannWhitneyInputDataAllRuns[evaluation]["LS_SA_FIXED"]["pValue"], 3), round(effectSizeInputDataAllRuns[evaluation]["LS_SA_FIXED"]["d"], 3)])
      list_of_strings.extend(["LS_SA_THRESHOLD", round(mannWhitneyInputDataAllRuns[evaluation]["LS_SA_THRESHOLD"]["pValue"], 3), round(effectSizeInputDataAllRuns[evaluation]["LS_SA_THRESHOLD"]["d"], 3)])
      mdFile.new_line()
      mdFile.new_table(columns=3, rows=3, text=list_of_strings, text_align='center')
      
# Create a table of contents
mdFile.new_table_of_contents(table_title='Contents', depth=1)
mdFile.create_md_file()