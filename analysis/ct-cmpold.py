#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import argparse
import sys

from colortilt.io import read_data

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('subject', type=str)
    parser.add_argument('olddata', type=str)
    parser.add_argument('data', nargs='?', type=str, default='-')
    parser.add_argument('--inner', action='store_true', default=False)

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
    if args.inner:
        kwargs['join'] = 'inner'

    dfa = pd.concat([dfi, dfo], axis=1, **kwargs)
    x = dfa.reset_index()
    x.subject = args.subject
    x.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
