#!/usr/bin/env python
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


def main():
    global do_debug
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', nargs='+', type=str, default=['-'])
    parser.add_argument('--debug', action="store_true", default=False)
    args = parser.parse_args()

    do_debug = args.debug

    df = read_data(args.data)
    df = df[df.bg != -1]
    dfg = df.groupby(['bg', 'fg', 'size', 'subject'])

    stats = NestedDefaultDict(4, list)
    debug(dfg.groups, file)
    for k, v in dfg.groups.iteritems():
        bg = on_or_off(k[0])
        fg = on_or_off(k[1])
        sz = k[2]
        sb = k[3]

        if bg == -1 or fg == -1:
            print('Warning: %s no off or on' % str(k))
            continue
        data = int(dfg.get_group(k)['N'].iloc[0])
        stats[bg][fg][sz][sb].append(data)
    debug(stats)

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
                    print('    %s %s %1.2f' % (om[bg], om[fg], np.mean(data)))


if __name__ == "__main__":
    main()

