#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import argparse
import sys
import numpy as np

from colortilt.io import read_data


def mean_angle(df, sign, use_mean=False):
    x = df[df.fg == sign*22.5].append(df[df.fg == sign*67.5], ignore_index=True)
    grouped = x.groupby(['bg', 'size'])

    if use_mean:
        fn = np.mean
    else:
        fn = np.max if sign > 0 else np.min

    df_mean = grouped['shift'].agg({'m_plus' if sign > 0 else 'm_minus': fn})
    return df_mean

def calc_sizerel_avg(df, cargs):
    m_plus = mean_angle(df, 1, use_mean=cargs.mean)
    print(m_plus, file=sys.stderr)
    m_minus = mean_angle(df, -1, use_mean=cargs.mean)
    print(m_minus, file=sys.stderr)

    x = pd.concat([m_plus, m_minus], axis=1)
    x = x.reset_index()

    abs_mean = lambda x, y: np.mean([np.abs(x), np.abs(y)])
    x['m_mean'] = x['m_plus'].combine(x['m_minus'], abs_mean)
    return x

def make_m_mean(x):
    idx = x['shift'].abs().idxmax()
    data = [x.loc[idx]]
    fg = data[0].fg
    xk = x[x.fg == fg]
    m_mean = xk['shift'].abs().mean()
    m_merr = xk['shift'].abs().sem()
    return pd.Series({'m_mean': m_mean, 'm_merr': m_merr})


def calc_sizerel(df, cargs):
    grouped = df.groupby(['bg', 'size'])
    x = grouped.apply(make_m_mean)
    x.reset_index()
    return x

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis [SizeRel]')
    parser.add_argument('--data', type=str, default=['-'])
    parser.add_argument('--mean', action='store_true', default=False)
    args = parser.parse_args()

    df = read_data(args.data)
    df = df[df.bg != -1]

    subjects = df['subject'].unique()
    have_avg = len(subjects) == 1 and '_' in subjects[0]

    if have_avg:
        print('[I] sizerel: using average method!', file=sys.stderr)
        x = calc_sizerel_avg(df, args)
    else:
        x = calc_sizerel(df, args)

    x.to_csv(sys.stdout, ignore_index=have_avg)

if __name__ == "__main__":
    main()

