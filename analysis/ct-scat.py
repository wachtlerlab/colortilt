#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import argparse
import sys

def read_data(file_list):
    if len(file_list) == 1 and file_list[0] == '-':
        file_list[0] = sys.stdin

    df = pd.read_csv(file_list[0], skipinitialspace=True)
    if len(file_list) > 1:
        for data in file_list[1:]:
            to_append = pd.read_csv(data, skipinitialspace=True)
            df = df.append(to_append, ignore_index=True)
    return df

def calc_delta(a):
    x_10 = a.loc[a['size'] == 10.0]['shift'].values[0]
    x_40 = a.loc[a['size'] == 40.0]['shift'].values[0]
    x_160 = a.loc[a['size'] == 160.0]['shift'].values[0]
    fg = a['fg'].unique()
    assert(len(fg) == 1)
    sign = -1 if fg < 0 else 1
    return pd.Series({'40': sign * x_40,
                      'delta': sign * (x_10 - x_160),
                      'sign': sign})

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', nargs='+', type=str, default=['-'])
    args = parser.parse_args()

    df = read_data(args.data)
    df = df[df.bg != -1]
    dfg = df.groupby(['bg', 'fg'])
    x = dfg.apply(calc_delta)
    x = x.reset_index()
    x.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()

