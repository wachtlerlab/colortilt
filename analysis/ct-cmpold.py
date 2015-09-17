#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import argparse
import sys
import numpy as np

from colortilt.io import read_data
from scipy import stats


def chi_squared_two_curves(row):
    d2 = (row['shift'] - row['oshift'])**2
    e2 = row['err']**2 + row['oerr']**2
    r = d2 / e2
    chi2 = sum(r)
    dof = len(row)
    p = 1.0 - stats.chi2.cdf(chi2, dof)
    return pd.Series({'chi2': np.round(chi2, 3),
                      'p': np.round(p, 3),
                      'dof': dof})

def test_significance(df, alpha=0.01):
    gd = df.groupby(['size', 'bg'])
    chi2 = gd.apply(chi_squared_two_curves)
    chi2.reset_index(inplace=True)
    del chi2['size']
    chi2['sig'] = chi2['p'] < alpha
    chi2.to_csv(sys.stdout, index=False)

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('subject', type=str)
    parser.add_argument('olddata', type=str)
    parser.add_argument('data', nargs='?', type=str, default='-')
    parser.add_argument('--inner', action='store_true', default=False)
    parser.add_argument('--chi2', action='store_true', default=False)
    parser.add_argument('--alpha', type=float, default=0.01)

    args = parser.parse_args()
    df = read_data([args.data])

    if args.subject not in df.subject.unique():
        print('Subject not in new data!', file=sys.stderr)
        sys.exit(-1)

    df = df[df.subject == args.subject]
    df = df[df.size == 40]

    old_df = pd.read_csv(args.olddata)
    old_df['size'] = 40

    old_df.columns = ['bg', 'fg', 'oshift', 'oerr', 'size']
    dfi = df.set_index(['size', 'bg', 'fg'])
    dfo = old_df.set_index(['size', 'bg', 'fg'])

    kwargs = {}
    if args.chi2 or args.inner:
        kwargs['join'] = 'inner'

    dfa = pd.concat([dfi, dfo], axis=1, **kwargs)
    x = dfa.reset_index()
    x.subject = args.subject

    if args.chi2:
        test_significance(x, alpha=args.alpha)
    else:
        x.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
