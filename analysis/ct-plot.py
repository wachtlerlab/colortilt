#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
from __future__ import division
from collections import defaultdict

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import sys
from matplotlib.colors import rgb_to_hsv, hsv_to_rgb

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


def make_idx2pos():
    pos_map = {-1: (1, 1), 0: (1, 2), 45: (0, 2), 90: (0, 1), 135: (0, 0), 180: (1, 0), 225: (2, 0), 270: (2, 1), 315: (2, 2)}
    pos_idx = {k: pos_map[k][0]*3+pos_map[k][1]+1 for k in pos_map}
    return pos_idx

def color_for_size(size, in_hsv=False):
    cs_map = {
        '10':  [0.4910111613133375, 0.77181085558498608, 0.38794311670696036, 1.0],
        '40': [0.65098041296005249, 0.80784314870834351, 0.89019608497619629, 1.0],
        '160':  [0.9020069262560676, 0.1649519457244405, 0.17131872735187115, 1.0]
    }

    c = cs_map[str(size)]
    if in_hsv:
        c = rgb_to_hsv(c[:3])
    return c


def plot_shifts(df):
    dfc_group = df.groupby(['size', 'bg', 'subject'])

    fig = plt.figure()
    bgs = df['bg'].unique()
    subjects = df['subject'].unique()
    sizes = df['size'].unique()
    pos_idx = make_idx2pos()

    max_shift = np.max(np.abs(df['shift'])) * 1.05

    df = df.sort(['bg', 'size'])
    cm = plt.get_cmap('Paired')

    for idx, bg in enumerate(bgs):
        for si, s in enumerate(sizes):
            for cs, subject in enumerate(subjects):
                plt.subplot(3, 3, pos_idx[bg])
                try:
                    hsv = color_for_size(s, in_hsv=True)
                    hsv[1] = (1.0-(cs/len(subjects)))*0.6+0.2
                    color = hsv_to_rgb(hsv)
                    arr = dfc_group.get_group((s, bg, subject))
                    plt.axhline(y=0, color='#777777')
                    plt.axvline(x=0, color='#777777')
                    lbl = str(s) if len(subjects) == 1 else str(s) + ' ' + subject[:2]
                    plt.errorbar(arr['fg'], arr['shift'], yerr=arr['err'], label=lbl, color=color)
                    plt.xlim([-180, 180])
                    plt.ylim([-1*max_shift, max_shift])
                    if pos_idx[bg] == 3:
                        plt.legend(loc=2, fontsize=8)
                except KeyError:
                    sys.stderr.write('[W] %s %.2f %.2f not present\n' % (subject, s, bg))

        plt.xlabel(str(bg))

    if len(subjects) == 1:
        title = subjects[0]
    else:
        title = ', '.join(map(lambda x: x[:2], subjects))

    plt.suptitle(title, fontsize=12)

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
    dfc_group = df.groupby(['bg', 'sign'])

    fig = plt.figure()
    bgs = sorted(df['bg'].unique())
    signs = sorted(df['sign'].unique())
    assert(len(signs) == 2 and all(map(lambda s: s in signs, [-1, 1])))
    x_stop = df['40'].max() * 1.05

    colors = angles_to_color(bgs)
    fig.hold()
    raw = True
    slope = defaultdict(list)

    markers = {-1: 's', 1: 'o'}
    m_size = {-1: 35, 1: 40}

    for si, sign in enumerate(signs):
        for idx, bg in enumerate(bgs):
            arr = dfc_group.get_group((bg, sign))
            print(arr, file=sys.stderr)
            x = arr['40'] if raw else np.abs(arr['40'])
            y = arr['delta'] if raw else np.abs(arr['delta'])
            p = np.polyfit(x, y, 1)
            px = np.arange(-5, x_stop, 0.5)
            py = np.polyval(p, px)
            print(p, file=sys.stderr)
            slope[sign].append(p[0])
            plt.subplot(1, 2, 1)
            plt.plot(px, py, color=colors[idx])
            lbl = str(bg) + ' ' + ('+' if sign > 0 else '-')
            plt.scatter(x, y, color=colors[idx], marker=markers[sign], label=lbl, s=m_size[sign])
    plt.xlabel('40 degree')
    plt.ylabel('10 - 160 degree')
    plt.legend(loc=2)

    plt.subplot(1, 2, 2, polar=True)
    plt.hold()
    print(slope, file=sys.stderr)
    plt.scatter(map(lambda x: (x-10)/180.0*np.pi, bgs), np.abs(slope[-1]), c=colors, s=m_size[-1], marker=markers[-1])
    plt.hold()
    plt.scatter(map(lambda x: (x+10)/180.0*np.pi, bgs), np.abs(slope[+1]), c=colors, s=m_size[+1], marker=markers[+1])


def plot_delta_combined(df):
    dfc_group = df.groupby(['bg'])

    fig = plt.figure()
    bgs = sorted(df['bg'].unique())
    x_stop = df['40'].max() * 1.05

    colors = angles_to_color(bgs)
    fig.hold()
    raw = True
    slope = []

    for idx, bg in enumerate(bgs):
        arr = dfc_group.get_group(bg)
        print(arr, file=sys.stderr)
        x = arr['40'] if raw else np.abs(arr['40'])
        y = arr['delta'] if raw else np.abs(arr['delta'])
        p = np.polyfit(x, y, 1)
        px = np.arange(-5, x_stop, 0.5)
        py = np.polyval(p, px)
        slope.append(p[0])
        plt.subplot(1, 2, 1)
        plt.plot(px, py, color=colors[idx])
        lbl = str(bg)
        plt.scatter(x, y, color=colors[idx], marker='o', label=lbl, s=40)

    plt.xlabel('40 degree')
    plt.ylabel('10 - 160 degree')
    plt.legend(loc=2)

    ax = plt.subplot(1, 2, 2, polar=True)
    plt.hold()
    print(slope, file=sys.stderr)
    plt.scatter(map(lambda x: x/180.0*np.pi, bgs), np.abs(slope), c=colors, s=40, marker='o')
    ax.set_rmax(np.max(np.abs(slope))*1.05)


def plot_ratio(df):
    fig = plt.figure()

    dfc_group = df.groupby(['subject', 'bg'])
    bgs = df['bg'].unique()
    pos_idx = make_idx2pos()

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

    y_max = np.max([df['m_plus'].max(), np.abs(df['m_minus'].min())]) * 1.05

    for idx, bg in enumerate(bgs):
        arr = dfc_group.get_group(bg)
        plt.subplot(1, 2, 1)
        x = np.log2(arr['size'])
        plt.plot(x, arr['m_plus'], color=colors[idx])
        plt.scatter(x, arr['m_plus'], color=colors[idx], marker='.', s=80, label='%s +' % str(bg))
        plt.subplot(1, 2, 2)
        plt.plot(x, -1*arr['m_minus'], color=colors[idx])
        plt.scatter(x, -1*arr['m_minus'], color=colors[idx], marker="1", s=80, label='%s -' % str(bg))
    plt.subplot(1, 2, 1)
    plt.xlabel('size')
    plt.ylabel('induction')
    plt.ylim([0, y_max])
    plt.legend()
    plt.subplot(1, 2, 2)
    plt.xlabel('size')
    plt.ylabel('induction')
    plt.ylim([0, y_max])
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
        plot_delta_combined(df)
    elif 'm_plus' in df.columns:
        plot_sizerel(df)
    else:
        raise ValueError('Unknown data set')

    plt.show()

if __name__ == '__main__':
    main()