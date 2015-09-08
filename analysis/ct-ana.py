#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import argparse
import sys
from scipy import stats

from colortilt.io import read_data


def calc_stats(col):
    shift = np.mean(col['shift'])
    err = stats.sem(col['shift'], ddof=0)

    return pd.Series({'shift': shift,
                      'err': err,
                      'N': len(col)})


def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', type=str)
    parser.add_argument('--combine', action='store_true', default=False)
    args = parser.parse_args()

    df = read_data([args.data])

    groups = ['bg', 'size', 'fg', 'subject']

    if args.combine:
        groups.remove('subject')

    gpd = df[['bg', 'fg', 'size', 'shift', 'subject']].groupby(groups, as_index=False)
    dfg = gpd.apply(calc_stats)
    x = dfg.reset_index()

    if args.combine:
        all_subjects = df['subject'].unique()
        subjects = '_'.join(map(lambda x: x[:2],  all_subjects))
        x['subject'] = subjects

    x.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()