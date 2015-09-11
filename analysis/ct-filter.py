#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import argparse
import sys

from colortilt.io import read_data

def filter_control(df):
    return df[df.bg != -1]

def filter_size(df, size):
    df = df[df.size == int(size)]
    return df

def main():
    parser = argparse.ArgumentParser(description='CT analysis - Filter')
    parser.add_argument('data', nargs='+', type=str, default=['-'])
    parser.add_argument('--size', default=None)
    parser.add_argument('--no-control', action='store_true', default=False, dest='ctrl')
    args = parser.parse_args()

    df = read_data(args.data)

    if args.size is not None:
        df = filter_size(df, args.size)

    if args.ctrl:
        df = filter_control(df)

    df.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
