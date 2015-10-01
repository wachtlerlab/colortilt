#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import argparse
import sys
import itertools

import numpy as np
import pandas as pd

from colortilt.io import read_data

index = {x: idx for idx, x in enumerate(itertools.permutations([160, 40, 10]))}

def find_oder(df):
    key = 'shift' if 'shift' in df.columns else 'm_mean'
    k = np.array(df[key]).argsort()
    idx = tuple(int(df.iloc[l]['size']) for l in k)
    x = index[idx]
    #print(df, k, x, idx)

    return pd.Series({'order': x})


def stats_order(df):
    groups = ['bg', 'fg', 'subject']

    gpd = df.groupby(groups)
    dfg = gpd.apply(find_oder)
    x = dfg.reset_index()
    x.to_csv(sys.stdout, index=False)

    print(index, file=sys.stderr)

    gpd = x.groupby(['subject', 'order'])
    cnt = gpd.count()
    s = cnt.reset_index()
    s['percent'] = s['bg'] / len(x)
    s['percent'] *= 100
    s['percent'] = s['percent'].round(1)
    s.to_csv(sys.stdout, index=False)

def find_max(row):
    upper = np.max(row['shift'])
    lower = np.min(row['shift'])
    idx_upper = row['shift'].idxmax()
    idx_lower = row['shift'].idxmin()
    size_upper = row.ix[idx_upper]['size']
    size_lower = row.ix[idx_lower]['size']
    delta = upper - lower
    return pd.Series({'spread': delta,
                      'size_upper': size_upper,
                      'size_lower': size_lower,
                      'upper': upper,
                      'lower': lower})

def max_spread(df):
    gx = df.groupby(['bg', 'subject'])
    smax = df.ix[gx.spread.idxmax()]
    return smax

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', nargs='?', type=str, default='-')
    args = parser.parse_args()

    df = read_data([args.data])

    gpd = df.groupby(['fg', 'bg', 'subject'])
    x = gpd.apply(find_max)
    x.reset_index(inplace=True)

    foo = max_spread(x)
    foo.to_csv(sys.stdout, index=False)

    gx = x.groupby(['bg', 'subject'])
    imax = x.ix[gx.upper.idxmax()]
    imax.to_csv(sys.stdout, index=False)

    foo.set_index(['bg', 'subject'])
    imax.set_index(['bg', 'subject'])

    foo['dfg'] = foo['fg'] - imax['fg']
    foo.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()