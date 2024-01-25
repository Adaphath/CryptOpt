#!/usr/bin/env python3
from effectsize import cohen_d
from statistics import stdev, mean
from math import sqrt

# source: https://stackoverflow.com/questions/21532471/how-to-calculate-cohens-d-in-python
def cohen_quick(c0, c1):
  return (mean(c0) - mean(c1)) / (sqrt((stdev(c0) ** 2 + stdev(c1) ** 2) / 2))


values1 = [1,2,3,4,5,6]
values2 = [100, 200, 300, 400, 500, 600]

cohen = cohen_d(values2, values1)

print('Stdev: ', stdev(values2))
print('Our cohen: ', cohen)
cohensQuick = cohen_quick(values2, values1)
print('Quick cohen from stackoverflow: ', cohensQuick)

print('========================')
print('for same group')
print('Our cohen: ', cohen_d(values2, values2))
print('Quick cohen from stackoverflow: ', cohen_quick(values2, values2))