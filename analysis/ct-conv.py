#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import argparse
import sys
import numpy as np
import pandas as pd

from colortilt.io import read_data
from colortilt.core import GroupedData

def rename_fg(df, fg_in, fg_out):
    out = df.loc[df.fg == fg_in].reset_index()
    out.fg = fg_out
    return out

def rel2abs(df, args):
    df.fg = (df.fg + df.bg) % 360.0

    if args.extend:
        fgs = np.unique(df.fg)

        start, stop = np.min(fgs), np.max(fgs)
        delta = (start - stop) % 360.0
        left, right = start - delta, stop + delta

        upper = rename_fg(df, start, right)
        lower = rename_fg(df, stop, left)

        df = pd.concat([df, upper, lower], ignore_index=True)
    return df


def main():
    parser = argparse.ArgumentParser(description='CT analysis - Filter')
    parser.add_argument('--data', nargs='+', type=str, default=['-'])
    subparsers = parser.add_subparsers(help='sub-command help')

    sp_r2a = subparsers.add_parser('rel2abs', help='a help')
    sp_r2a.add_argument('--no-extend', action='store_false', default=True, dest='extend')
    sp_r2a.set_defaults(dispatch=rel2abs)
    args = parser.parse_args()

    df = read_data(args.data)
    df = args.dispatch(df, args)
    df.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
