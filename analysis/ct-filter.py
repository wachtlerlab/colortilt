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


def filter_fg_range(df, fg):
    return df[(-fg <= df.fg) & (df.fg <= +fg)]


def filter_fg_sign(df, sign):
    if sign not in ['+', '-']:
        raise ValueError("Sign must be + or -")
    return df[(df.fg > 0 if sign == '+' else df.fg < 0)]


def filter_bg(df, bg):
    return df[df.bg == float(bg)]


def main():
    parser = argparse.ArgumentParser(description='CT analysis - Filter')
    parser.add_argument('data', nargs='?', type=str, default='-')
    parser.add_argument('--size', default=None)
    parser.add_argument('--no-control', action='store_true', default=False, dest='ctrl')
    parser.add_argument('--fg', dest='fg', type=float, default=None)
    parser.add_argument('-B', '--bg', dest='bg', type=float, default=None)
    parser.add_argument('--fg-sign', dest='fg_sign', default=None)
    args = parser.parse_args()

    df = read_data([args.data])

    if args.size is not None:
        df = filter_size(df, args.size)

    if args.ctrl:
        df = filter_control(df)

    if args.fg:
        df = filter_fg_range(df, args.fg)

    if args.fg_sign:
        df = filter_fg_sign(df, args.fg_sign)

    if args.bg is not None:
        df = filter_bg(df, args.bg)


    df.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
