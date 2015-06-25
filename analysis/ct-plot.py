#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import sys

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


def angles_to_color(angles):
    def rgb(r, g, b):
        return "#%02x%02x%02x" % (r, g, b)

    bg = list(np.arange(0, 360, 360.0/8))
    cls = [rgb(252, 38, 28),
           rgb(253, 77, 252),
           rgb(13, 66, 251),
           rgb(49, 183, 229),
           rgb(26, 176, 29),
           rgb(181, 248, 50),
           rgb(216, 202, 43),
           rgb(252, 151, 39)]
    return [cls[bg.index(a)] for a in angles]


def plot_delta(df):
    dfc_group = df.groupby('bg')

    fig = plt.figure()
    bgs = sorted(df['bg'].unique())

    x_stop = df['40'].max() * 1.05

    colors = angles_to_color(bgs)
    fig.hold()
    raw = True
    for idx, bg in enumerate(bgs):
        arr = dfc_group.get_group(bg)
        print(arr, file=sys.stderr)
        x = arr['40'] if raw else np.abs(arr['40'])
        y = arr['delta'] if raw else np.abs(arr['delta'])
        p = np.polyfit(x, y, 1)
        px = np.arange(0, x_stop, 0.5)
        py = np.polyval(p, px)
        plt.plot(px, py, color=colors[idx], label=str(bg))
        plt.scatter(x, y, color=colors[idx])

    plt.xlabel('40 degree')
    plt.ylabel('10 - 160 degree')
    plt.legend(loc=2)


def plot_ratio(df):
    fig = plt.figure()

    dfc_group = df.groupby(['subject', 'bg'])
    bgs = df['bg'].unique()
    pos_map = {-1: (1, 1), 0: (1, 2), 45: (0, 2), 90: (0, 1), 135: (0, 0), 180: (1, 0), 225: (2, 0), 270: (2, 1), 315: (2, 2)}
    pos_idx = {k: pos_map[k][0]*3+pos_map[k][1]+1 for k in pos_map}

    max_ratio = np.max(np.abs(df['ratio'])) * 1.05
    df = df.sort(['bg', 'subject'])

    for idx, bg in enumerate(bgs):
        for s in df['subject'].unique():
            plt.subplot(3, 3, pos_idx[bg])
            try:
                arr = dfc_group.get_group((s, bg))
                plt.axhline(y=0, color='#777777')
                plt.axvline(x=0, color='#777777')
                plt.plot(arr['fg'], arr['ratio'], label=str(s))
                plt.xlim([-180, 180])
                #plt.ylim([-1*max_ratio, max_ratio])
                if pos_idx[bg] == 6:
                    plt.legend(loc=2)
            except KeyError:
                sys.stderr.write('[W] %sf %.2f not present\n' % (s, bg))

        plt.xlabel(str(bg))

    subjects = df['subject'].unique()
    if len(subjects) == 1:
        plt.suptitle('%s' % (subjects[0]), fontsize=12)

    return fig

def plot_sizerel(df):
    dfc_group = df.groupby('bg')

    fig = plt.figure()
    bgs = sorted(df['bg'].unique())

    colors = angles_to_color(bgs)
    fig.hold()

    for idx, bg in enumerate(bgs):
        arr = dfc_group.get_group(bg)
        print(arr, file=sys.stderr)
        plt.subplot(1, 2, 1)
        plt.plot(np.log2(arr['size']), arr['m_plus'], color=colors[idx])
        plt.scatter(np.log2(arr['size']), arr['m_plus'], color=colors[idx], marker='.', s=80, label='%s +' % str(bg))
        plt.subplot(1, 2, 2)
        plt.plot(np.log2(arr['size']), -1*arr['m_minus'], color=colors[idx])
        plt.scatter(np.log2(arr['size']), -1*arr['m_minus'], color=colors[idx], marker="1", s=80, label='%s -' % str(bg))
    plt.subplot(1, 2, 1)
    plt.xlabel('size')
    plt.ylabel('induction')
    plt.legend()


def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', type=str, nargs='+', default='-')
    args = parser.parse_args()

    df = read_data(args.data)
    print(df, file=sys.stderr)

    if 'shift' in df.columns:
        plot_shifts(df)
    elif 'ratio' in df.columns:
        plot_ratio(df)
    elif 'delta' in df.columns:
        plot_delta(df)
    elif 'm_plus' in df.columns:
        plot_sizerel(df)
    else:
        raise ValueError('Unknown data set')

    plt.show()

if __name__ == '__main__':
    main()