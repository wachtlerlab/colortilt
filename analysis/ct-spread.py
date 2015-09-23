#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import argparse
import sys

from colortilt.io import read_data


def calc_max_spread(row):
    upper = np.max(row['shift'])
    lower = np.min(row['shift'])
    idx_upper = row['shift'].idxmax()
    idx_lower = row['shift'].idxmin()
    size_upper = row.ix[idx_upper]['size']
    size_lower = row.ix[idx_lower]['size']
    ref = np.mean(row.ix[row['size'] == 40]['shift'].values)
    delta = upper - lower
    return pd.Series({'spread': delta, 'upper': size_upper, 'lower': size_lower, 'ref': ref})


def max_spread(df):
    gx = df.groupby(['bg', 'subject'])
    smax = df.ix[gx.spread.idxmax()]
    return smax


def convert2sizerel(x, df):
    idx = ['bg', 'fg', 'subject']
    dfmax = max_spread(x)
    smax = dfmax[['bg', 'fg', 'subject']]
    smax[['bg', 'fg', 'subject']].to_csv(sys.stderr, index=False)
    df.set_index(idx, inplace=True)
    sizerel = df.ix[[tuple(x) for x in smax.to_records(index=False)]].copy()
    #print(sizerel, file=sys.stderr)
    sizerel.rename(columns={'shift': 'm_mean', 'err': 'm_merr'}, inplace=True)
    #sizerel.to_csv(sys.stdout, ignore_index=True)
    return sizerel


def calc_delta_scat(a):
    x_40 = np.mean(a.loc[a['size'] == 40.0]['m_mean'].values)
    upper = np.max(a['m_mean'])
    return pd.Series({'ref': upper})


def spread_slrel(x, df):
    idx = ['bg', 'fg', 'subject']
    data = convert2sizerel(x, df)
    data.reset_index(inplace=True)
    gd = data.groupby(['bg', 'fg', 'subject'])
    scat = gd.apply(calc_delta_scat)
    data.set_index(idx, inplace=True)
    data['ref'] = scat
    data['m_mean'] = data['m_mean'] / data['ref']
    print(data, file=sys.stderr)
    data.reset_index(inplace=True)
    return data


def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', type=str, nargs='?', default='-')
    parser.add_argument('--sizerel', default=False, action='store_true')
    parser.add_argument('--max-spread', dest='maxspread', default=False, action='store_true')
    parser.add_argument('--sl-rel', dest='slrel', default=False, action='store_true')

    args = parser.parse_args()
    df = read_data([args.data])

    gd = df.groupby(['bg', 'fg', 'subject'])
    x = gd.apply(calc_max_spread)
    x.reset_index(inplace=True)

    if args.sizerel:
        x = convert2sizerel(x, df)
        x.to_csv(sys.stdout, ignore_index=True)
    elif args.maxspread:
        x = max_spread(x)
        x.to_csv(sys.stdout, index=False)
    elif args.slrel:
        x = spread_slrel(x, df)
        x.to_csv(sys.stdout, index=False)
    else:
        x.to_csv(sys.stdout, index=False)

    return 0

if __name__ == '__main__':
    ret = main()
    sys.exit(ret)