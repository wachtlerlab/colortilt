#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import argparse
import sys

from colortilt.io import read_data


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

