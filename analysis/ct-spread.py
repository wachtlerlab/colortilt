#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import argparse
import sys
from scipy import stats

from colortilt.io import read_data


def calc_max_spread(row):
    upper = np.max(row['shift'])
    lower = np.min(row['shift'])
    delta = upper - lower
    return pd.Series({'spread': delta})


def convert2sizerel(x, df):
    idx = ['bg', 'fg', 'subject']
    gx = x.groupby(['bg', 'subject'])
    smax = x.ix[gx.spread.idxmax()][['bg', 'fg', 'subject']]
    df.set_index(idx, inplace=True)
    sizerel = df.ix[[tuple(x) for x in smax.to_records(index=False)]].copy()
    #print(sizerel, file=sys.stderr)
    sizerel.rename(columns={'shift': 'm_mean', 'err': 'm_merr'}, inplace=True)
    #sizerel.to_csv(sys.stdout, ignore_index=True)
    return sizerel


def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('--data', type=str, default='-')
    parser.add_argument('--sizerel', default=False, action='store_true')

    args = parser.parse_args()
    df = read_data([args.data])

    gd = df.groupby(['bg', 'fg', 'subject'])
    x = gd.apply(calc_max_spread)
    x.reset_index(inplace=True)

    if args.sizerel:
        x = convert2sizerel(x, df)
        x.to_csv(sys.stdout, ignore_index=True)
    else:
        x['size'] = 40  # FIXME
        x.to_csv(sys.stdout, index=False)

    return 0

if __name__ == '__main__':
    ret = main()
    sys.exit(ret)