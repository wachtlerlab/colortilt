#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import argparse
import sys

from scipy import stats
from colortilt.io import read_data

def calc_mean_over_surrounds(row):
    key = 'm_mean'
    data = row[key]
    clean = filter(lambda x: np.isfinite(x), data)
    shift = np.mean(clean)
    err = stats.sem(clean, ddof=1)

    return pd.Series({'bg': -2,
                      key: shift,
                      'm_merr': err,
                      'N': len(clean)})


def calc_slope(a, b):
    assert(len(a['size'].values) == 1)
    assert(len(a['m_mean'].values) == 1)
    space = np.log
    dx = space(a['size'].values[0]) - space(b['size'].values[0])
    dy = a['m_mean'].values[0] - b['m_mean'].values[0]
    slope = dy / dx
    return slope


def slope_avg_surrounds(df, args):

    if args.nos:
        df = df[df.bg != 270]
        df = df[df.bg != 90]

    dfg = df.groupby(['size', 'subject'])
    md = dfg.apply(calc_mean_over_surrounds)
    md = md.reset_index()
    md.to_csv(sys.stdout, index=False)

    x10 = md[md.size == 10]
    x40 = md[md.size == 40]
    x160 = md[md.size == 160]

    print('Slope, 40, 10', calc_slope(x40, x10), file=sys.stderr)
    print('Slope, 160, 40', calc_slope(x160, x40), file=sys.stderr)

def get_val(row, key):
    vals = row[key].values
    assert(len(vals) == 1)
    return vals[0]

def slope_avg_sizes(df, args):
    def mean_slope(row):
        x10 = row[row.size == 10]
        x40 = row[row.size == 40]
        x160 = row[row.size == 160]

        s1 = calc_slope(x40, x10)
        s2 = calc_slope(x160, x40)
        s3 = calc_slope(x10, x160)
        sm = np.mean([s1, s2])

        return pd.Series({'slope_10_40': s1,
                          'slope_40_160': s2,
                          'slope_10_160': s3,
                          'slope_mean':sm,
                          'slope_mean_abs': -1*s2})

    def slope_last(row):
        x40 = row[row.size == 40]
        x160 = row[row.size == 160]

        s2 = calc_slope(x160, x40)

        return pd.Series({'slope_40_160': s2,
                          'slope_mean_abs': -1*s2})

    def slope_regress(row):
        x10 = row[row.size == 10]
        x40 = row[row.size == 40]
        x160 = row[row.size == 160]

        x = np.log([get_val(k, 'size') for k in [x160, x40]])
        y = [get_val(k, 'm_mean') for k in [x160, x40]]

        slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)

        return pd.Series({ 'slope_mean_abs': -1*slope, 'err': std_err, 'p': p_value })


    dfg = df.groupby(['bg', 'subject'])
    mm = {'regress': slope_regress, 'last': slope_last, 'mean': mean_slope}
    method=mm[args.method]
    md = dfg.apply(method)
    md = md.reset_index()
    md.to_csv(sys.stdout, index=False)

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', type=str, nargs='?', default='-')
    parser.add_argument('over', choices=['surrounds', 'size'])
    parser.add_argument('--method', choices=['mean', 'regress', 'last'], default='regress')
    parser.add_argument('--no-s', dest='nos', action='store_true', default=False)

    args = parser.parse_args()
    df = read_data([args.data])

    if args.over == 'surrounds':
        slope_avg_surrounds(df, args)
    else:
        slope_avg_sizes(df, args)


if __name__ == '__main__':
    ret = main()
    sys.exit(ret)