#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import yaml
import sys, os
import fnmatch

plt.style.use('ggplot')

def read_data(file_list):
    if len(file_list) == 1 and file_list[0] == '-':
        file_list[0] = sys.stdin

    df = pd.read_csv(file_list[0], skipinitialspace=True)
    if len(file_list) > 1:
        for data in file_list[1:]:
            to_append = pd.read_csv(data, skipinitialspace=True)
            df = df.append(to_append, ignore_index=True)
    return df

def plot_shifts(df):
    dfc_group = df.groupby(['size', 'bg'])

    fig = plt.figure()
    bgs = df['bg'].unique()

    pos_map = {-1: (1, 1), 0: (1, 2), 45: (0, 2), 90: (0, 1), 135: (0, 0), 180: (1, 0), 225: (2, 0), 270: (2, 1), 315: (2, 2)}
    pos_idx = {k: pos_map[k][0]*3+pos_map[k][1]+1 for k in pos_map}

    max_shift = np.max(np.abs(df['shift'])) * 1.05

    df = df.sort(['bg', 'size'])

    for idx, bg in enumerate(bgs):
        for s in df['size'].unique():
            plt.subplot(3, 3, pos_idx[bg])
            try:
                arr = dfc_group.get_group((s, bg))
                plt.axhline(y=0, color='#777777')
                plt.axvline(x=0, color='#777777')
                plt.errorbar(arr['fg'], arr['shift'], yerr=arr['err'], label=str(s))
                plt.xlim([-180, 180])
                plt.ylim([-1*max_shift, max_shift])
                if pos_idx[bg] == 6:
                    plt.legend(loc=2)
            except KeyError:
                sys.stderr.write('[W] %.2f %.2f not present\n' % (s, bg))

        plt.xlabel(str(bg))

    subjects = df['subject'].unique()
    if len(subjects) == 1:
        plt.suptitle('%s' % (subjects[0]), fontsize=12)

    return fig

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', type=str, nargs='+', default='-')
    args = parser.parse_args()

    df = read_data(args.data)
    print(df, file=sys.stderr)

    if 'shift' in df.columns:
        plot_shifts(df)
    else:
        raise ValueError('Unknown data set')

    plt.show()

if __name__ == '__main__':
    main()