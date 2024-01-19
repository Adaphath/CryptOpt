#!/usr/bin/env python3
import json
import os
import mdutils

mdFile = mdutils.MdUtils(file_name='benchmarking/results.md', title='Results')

# Structure:
# Heading 1: Curve Name
# Heading 2: Method Name
# Comparison Plot
# Heading 2: Statistical Tests (Mann-Whitney U Test (with Link to Wikipedia), Cohen's d (with Link to Wikipedia))
# Table with p-values and effect sizes (for LS_SA_FIXED and LS_SA_THRESHOLD)

curves = ["curve25519", "p256", "p384"]
methods = ["mul", "square"]
evaluations = ["10k", "20k", "50k", "100k", "200k"]

for curve in curves:
  mdFile.new_header(level=1, title=curve)
  for method in methods:
    mdFile.new_header(level=2, title=method)
    image_path = f"./plots/comparison_{curve}_{method}.png"
    mdFile.new_line(mdFile.new_inline_image(text=f"Comparison Plot for {curve} {method}", path=image_path))

    mdFile.new_header(level=2, title="[Mann-Whitney U Test](https://en.wikipedia.org/wiki/Mann%E2%80%93Whitney_U_test) and [Cohen's d](https://en.wikipedia.org/wiki/Effect_size#Cohen's_d)")
    for evaluation in evaluations:
      # load data from json file
      effectSizeInputData = []
      effectSizeFilePath = os.path.join(os.path.dirname(__file__), f"./statisticalTests/effectsize_{curve}_{method}.json")
      with open(effectSizeFilePath) as f:
        effectSizeInputData = json.load(f)

      mannWhitneyInputData = []
      mannWhitneyFilePath = os.path.join(os.path.dirname(__file__), f"./statisticalTests/mannwhitneyu_{curve}_{method}.json")
      with open(mannWhitneyFilePath) as f:
        mannWhitneyInputData = json.load(f)

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

      mdFile.new_header(level=3, title=f"{evaluation}")
      # create table with p-values and effect sizes
      list_of_strings = ["Configuration", "p-value", "Effect Size"]
      list_of_strings.extend(["LS_SA_FIXED", round(mannWhitneyInputData[evaluation]["LS_SA_FIXED"]["pValue"], 3), round(effectSizeInputData[evaluation]["LS_SA_FIXED"]["d"], 3)])
      list_of_strings.extend(["LS_SA_THRESHOLD", round(mannWhitneyInputData[evaluation]["LS_SA_THRESHOLD"]["pValue"], 3), round(effectSizeInputData[evaluation]["LS_SA_THRESHOLD"]["d"], 3)])
      mdFile.new_line()
      mdFile.new_table(columns=3, rows=3, text=list_of_strings, text_align='center')
      
      
mdFile.create_md_file()