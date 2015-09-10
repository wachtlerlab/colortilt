#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import argparse
import sys
from scipy import stats

from colortilt.io import read_data

def make_calc_size_diff(dbm=False):
    def calc_size_diff(col):
        data = col['shift']
        clean = filter(lambda x: np.isfinite(x), data)
        shift = np.mean(clean)
        var = np.std(clean)
        #err = stats.sem(clean, ddof=0)
        szdiff = var / (shift if dbm else 1.0)

        return pd.Series({'szdiff': szdiff,
                          'err': 0, # FIXME
                          'N': len(clean)})
    return calc_size_diff

def mk_subjects(df):
    subs = df['subject'].unique()
    return '_'.join(map(lambda x: x[:2],  subs)) if len(subs) > 1 else subs[0]

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', type=str)
    parser.add_argument('--combine', action='store_true', default=False)
    parser.add_argument('--dbm', action='store_true', default=False)

    args = parser.parse_args()

    df = read_data([args.data])

    groups = ['bg', 'fg', 'subject']

    if args.combine:
        groups.remove('subject')

    gpd = df[['bg', 'fg', 'size', 'shift', 'subject']].groupby(groups, as_index=False)
    dfg = gpd.apply(make_calc_size_diff(args.dbm))
    x = dfg.reset_index()

    if args.combine:
        subs = df['subject'].unique()
        x['subject'] = '_'.join(map(lambda x: x[:2],  subs)) if len(subs) > 1 else subs[0]

    x['size'] = 40 # FIXME
    x.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()