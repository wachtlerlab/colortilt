#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import argparse
import sys
import numpy as np
import itertools

from colortilt.io import read_data
from scipy import stats


def chi_squared(a, a_err, b, b_err):
    d2 = (a - b)**2
    e2 = a_err**2 + b_err**2
    r = d2 / e2
    chi2 = sum(r)
    dof = len(a)
    p = 1.0 - stats.chi2.cdf(chi2, dof)
    return {'chi2': np.round(chi2, 3),
            'p': np.round(p, 4),
            'dof': dof}

def chi_squared_sizes(row):
    sizes = row['size'].unique()
    pairs = tuple(itertools.combinations(sizes, 2))

    res = {}
    for p in pairs:
        r_a = row[row['size'] == p[0]]
        r_b = row[row['size'] == p[1]]

        a = np.array(r_a['shift'])
        b = np.array(r_b['shift'])

        a_err = np.array(r_a['err'])
        b_err = np.array(r_b['err'])

        res[str(p[0]) + '_' + str(p[1])] = chi_squared(a, a_err, b, b_err)

    return pd.DataFrame(res).transpose()

def test_significance(chi2, alpha):
    chi2['sig'] = chi2['p'] < alpha
    return chi2


def main():
    parser = argparse.ArgumentParser(description='CT - Analysis]')
    parser.add_argument('data', nargs='?', type=str, default='-')
    parser.add_argument('--alpha', type=float, default=0.01)

    args = parser.parse_args()
    df = read_data([args.data])

    groups = ['bg', 'subject']

    gpd = df.groupby(groups)
    dfg = gpd.apply(chi_squared_sizes)
    dfg = dfg.reset_index()
    dfg.rename(columns={'level_2': 'combination'}, inplace=True)
    test_significance(dfg, args.alpha)
    dfg.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()
