#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import argparse
import sys
from scipy import stats

from colortilt.io import read_data

# wanted to use functools.partial,
# ran into python issue 3445
def make_calc_stats(key):
    def calc_stats(col):
        data = col[key]
        clean = filter(lambda x: np.isfinite(x), data)
        shift = np.mean(clean)
        err = stats.sem(clean, ddof=0)

        return pd.Series({key: shift,
                          'err': err,
                          'N': len(clean)})
    return calc_stats

def mk_subjects(df):
    subs = df['subject'].unique()
    return '_'.join(map(lambda x: x[:2],  subs)) if len(subs) > 1 else subs[0]

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', nargs='?', type=str, default='-')
    parser.add_argument('--combine', action='store_true', default=False)
    parser.add_argument('--col', type=str, default='shift')
    parser.add_argument('--mean', action='store_true', default=False)
    args = parser.parse_args()

    df = read_data([args.data])

    groups = ['bg', 'size', 'fg', 'subject']

    if args.combine:
        groups.remove('subject')

    if args.mean:
        groups.remove('size')

    gpd = df.groupby(groups, as_index=False)
    dfg = gpd.apply(make_calc_stats(args.col))
    x = dfg.reset_index()

    if args.combine:
        subs = df['subject'].unique()
        x['subject'] = '_'.join(map(lambda x: x[:2],  subs)) if len(subs) > 1 else subs[0]

    x.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()