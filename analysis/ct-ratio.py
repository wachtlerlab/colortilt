#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import yaml
import sys, os
import fnmatch

def read_data(file_list):
    if len(file_list) == 1 and file_list[0] == '-':
        file_list[0] = sys.stdin

    df = pd.read_csv(file_list[0], skipinitialspace=True)
    if len(file_list) > 1:
        for data in file_list[1:]:
            to_append = pd.read_csv(data, skipinitialspace=True)
            df = df.append(to_append, ignore_index=True)
    return df

def calc_ratio(a):
    print(a, file=sys.stderr)
    if len(a) != 2:
        return 0
    return a.iloc[0] / a.iloc[1]

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', nargs='+', type=str, default=['-'])
    args = parser.parse_args()

    df = read_data(args.data)
    dff = df[(df.size == 10.0) | (df.size == 160.0)]
    dff = dff[(df.fg > -100.0) & (df.fg < 100.0)]
    gpd = dff.groupby(['bg', 'fg', 'subject'])
    print(gpd, file=sys.stderr)
    dfg = gpd['shift'].agg({'ratio': calc_ratio})
    print(dfg, file=sys.stderr)
    x = dfg.reset_index()
    x.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
