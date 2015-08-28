#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
from __future__ import division

import pandas as pd
import argparse
import sys
from collections import defaultdict
from functools import partial
import numpy as np

#global flags
do_debug = False


def NestedDefaultDict(levels, baseFn):
    def NDD(lvl):
        return partial(defaultdict, NDD(lvl-1)) if lvl > 0 else baseFn
    return defaultdict(NDD(levels-1))


def read_data(file_list):
    if len(file_list) == 1 and file_list[0] == '-':
        file_list[0] = sys.stdin

    df = pd.read_csv(file_list[0], skipinitialspace=True)
    if len(file_list) > 1:
        for data in file_list[1:]:
            to_append = pd.read_csv(data, skipinitialspace=True)
            df = df.append(to_append, ignore_index=True)
    return df


def on_or_off(value):
    on = [0, 90, 180, 270]
    value = abs(value)
    if value in on:
        return 1
    else:
        return 0


def debug(*args, **kwargs):
    if do_debug:
        print(*args, **kwargs)


def make_stats(df):
    dfg = df.groupby(['subject', 'size', 'bg', 'fg'])
    stats = NestedDefaultDict(4, list)
    debug(dfg.groups, file)
    for k, v in dfg.groups.iteritems():
        bg = on_or_off(k[2])
        fg = on_or_off(k[3])
        sz = k[1]
        sb = k[0]

        if bg == -1 or fg == -1:
            print('Warning: %s no off or on' % str(k))
            continue
        data = int(dfg.get_group(k)['N'].iloc[0])
        stats[bg][fg][sz][sb].append(data)
    debug(stats)
    return stats


def show_summary(stats, df):

    sizes = df['size'].unique()
    om = ['off', 'on ']
    sm = {10: '0.5', 40: '2  ', 160: '8  '}
    for sb in df['subject'].unique():
        print(sb)
        for sz in sizes:
            print('  ' + sm[sz])
            for bg in [0, 1]:
                for fg in [0, 1]:
                    data = stats[bg][fg][sz][sb]
                    if len(data) == 0:
                        continue
                    d_medi = np.median(data)
                    d_mean = np.mean(data)
                    indicator = ' ! ' if d_mean != d_medi else ''
                    print('    %s %s %3.2f [%2.1f] %s' % (om[bg], om[fg], d_mean, d_medi, indicator))


def show_detail(df, stats=None, missing_only=True):
    dfg = df.groupby(['subject', 'size', 'bg', 'fg'])

    for k, v in sorted(dfg.groups.iteritems()):
        sb = k[0]
        sz = k[1]
        bg = k[2]
        fg = k[3]

        bg_b = on_or_off(bg)
        fg_b = on_or_off(fg)

        N = int(dfg.get_group(k)['N'].iloc[0])
        indicator = ''
        m = 0.0
        om = [u'⦿', u'●']

        if stats is not None:
            data = stats[bg_b][fg_b][sz][sb]
            m = np.median(data)
            missing = N < m
            if missing:
                indicator = ' ! '
            elif missing_only:
                continue

        s = u"%10s  %3d %8.2f %s %8.2f %d [%2.1f] %s\n" % (sb, sz, bg, om[bg_b], fg, N, m, indicator)
        sys.stdout.write(s.encode('utf-8'))


def main():
    global do_debug
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', nargs='+', type=str, default=['-'])
    parser.add_argument('--debug', action="store_true", default=False)
    parser.add_argument('--full', action="store_true", default=False)
    args = parser.parse_args()

    do_debug = args.debug

    df = read_data(args.data)
    df = df[df.bg != -1]

    stats = make_stats(df)

    show_detail(df, stats=stats, missing_only=not args.full)
    show_summary(stats, df)

if __name__ == "__main__":
    main()

