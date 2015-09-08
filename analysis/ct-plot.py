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
from utils import ggsave

from colortilt.io import read_data
from colortilt.plot import (angles_to_color, mk_rgb)
from colortilt.core import GroupedData


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

    #cs_map = {
    #    '10':  mk_rgb('#ffeda0'),
    #    '40': mk_rgb('#feb24c'),
    #    '160':  mk_rgb('#f03b20')
    #}

    c = cs_map[str(size)]
    if in_hsv:
        c = rgb_to_hsv(c[:3])
    return c

def get_figure(figures, cargs):
    if cargs.single or len(figures) == 0:
        fig = plt.figure()
        figures.append(fig)
    else:
        fig = figures[0]
    return fig

def make_subject_string(subjects):
    if len(subjects) == 1:
        title = subjects[0]
    else:
        title = '+'.join(map(lambda x: x[:2], subjects))
    return title


def style_for_size_and_subject(size, subject, n_subjects, cargs):
    if not cargs.gray:
        hsv = color_for_size(size, in_hsv=True)
        hsv[1] = (1.0-(subject/n_subjects))*0.6+0.2
        color = hsv_to_rgb(hsv)
        return {'color': color}
    else:
        cs_map = {
            '10':  [0.60, 0.60, 0.60, 1.0],
            '40': [0.35, 0.35, 0.35, 1.0],
            '160':  [0.1, 0.1, 0.1, 1.0]
        }
        c = cs_map[str(size)]
        line_styles = ['-', '--', ':']
        if n_subjects > len(line_styles):
            raise ValueError('More subjects then available line styles')
        return {'color': c, 'linestyle': line_styles[subject], 'linewidth': 1.5}

def size_to_label(size):
    size_map = {
        '10': u'0.5°',
        '40': u'  2°',
        '160': u'  8°'
    }
    return size_map[str(size)]


class ShiftPlotter(object):

    bg2idx_map = make_idx2pos()

    def __init__(self, cargs):
        self.m = 3
        self.n = 3
        self.__cargs = cargs
        self.figures = [None] * (self.m * self.n)
        self.single = self.__cargs.single
        self.mapper = lambda x: self.bg2idx_map[x]

    def __getitem__(self, item):
        item -= 1
        if self.figures[item] is None:
            fig = plt.figure()
            plt.hold(True)
            self.figures[item] = fig

        return self.figures[item]

    def subplot(self, k):
        idx = self.mapper(k)
        if self.single:
            fig = self[idx]
            plt.figure(fig.number)
            ax = plt.subplot(1, 1, 1)
        else:
            fig = self[1]
            ax = plt.subplot(self.m, self.n, idx)
        return ax, fig


def plot_shift_like(df, cargs, func, *args, **kwargs):
    gd = GroupedData(df, ['size', 'bg', 'subject'])
    subjects = gd.unique('subject')
    pos_idx = make_idx2pos()

    ylim = cargs.ylim or np.max(np.abs(df['shift'])) * 1.05
    subject_str = make_subject_string(subjects)

    layout = ShiftPlotter(cargs)

    for data, context in gd.data:
        _, bg = context['bg']
        si, s = context['size']
        cs, subject = context['subject']
        group = context.group

        ax, fig = layout.subplot(bg)
        if cargs.single:
            if not cargs.no_title:
                plt.suptitle(subject_str + " " + str(bg))
            setattr(fig, 'name', subject_str + " " + str(bg))

        plot_style = style_for_size_and_subject(s, cs, len(subjects), cargs)
        sstr = size_to_label(s)
        lbl = sstr if len(subjects) == 1 else sstr + ' ' + subject[:2]
        plot_style['label'] = lbl
        plt.axhline(y=0, color='#777777')
        plt.axvline(x=0, color='#777777')

        func(data, group, ax, plot_style, *args, **kwargs)

        plt.xlim([-180, 180])
        plt.ylim([-1*ylim, ylim])
        if pos_idx[bg] == 6:
            plt.legend(loc=4, fontsize=12)

        ax.annotate(u"%4d°" % int(bg), xy=(.05, .95),  xycoords='axes fraction',
                    horizontalalignment='left', verticalalignment='top',
                    fontsize=18, family='Input Mono', color=angles_to_color([bg])[0])


def plot_shifts(df, cargs):
    def plot_shift(df, grp, ax, style):
        plt.errorbar(df['fg'], df['shift'], yerr=df['err'], **style)
    return plot_shift_like(df, cargs, plot_shift)


def plot_shifts_cmpold(df, cargs):
    def plot_shift(df, grp, ax, style):
        x = df[np.isfinite(df['shift'])]
        lbl = style['label']
        plt.errorbar(x['fg'], x['shift'], yerr=x['err'], label=lbl, color='r')
        plt.errorbar(df['fg'], df['oshift'], yerr=df['oerr'], label=lbl + '-old', color='k')

    return plot_shift_like(df, cargs, plot_shift)


def plot_shifts_individual(df, cargs):
    gd = GroupedData(df, ['subject', 'size', 'date', 'side', 'bg'])

    fig = plt.figure()
    pos_idx = make_idx2pos()
    max_shift = np.max(np.abs(df['shift'])) * 1.05

    for data, context in gd.data:
        subject, size, date, side, bg = context.group
        if len(data) != 8:
            print('skipping %s' % (str(date)), file=sys.stderr)
            continue

        ax = plt.subplot(3, 3, pos_idx[bg])

        plt.axhline(y=0, color='#777777')
        plt.axvline(x=0, color='#777777')
        date = str(np.unique(data['date']))
        side = str(np.unique(data['side']))
        x = data.sort(['fg_rel'])
        plt.plot(x['fg_rel'], x['shift'], label="%s %s" % (date, side))
        plt.xlim([-180, 180])
        plt.ylim([-1*max_shift, max_shift])
        if pos_idx[bg] in [3, 6]:
            plt.legend(loc=4, fontsize=6)

        ax.annotate(u"%4d°" % int(bg), xy=(.05, .95),  xycoords='axes fraction',
                    horizontalalignment='left', verticalalignment='top',
                    fontsize=18, family='Input Mono', color=angles_to_color([bg])[0])
    return [fig]


def plot_delta(df, cargs):
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
    return [fig]

def plot_delta_combined(df, cargs):
    dfc_group = df.groupby(['bg'])

    fig = plt.figure()
    bgs = sorted(df['bg'].unique())
    x_stop = df['40'].max() * 1.05

    colors = angles_to_color(bgs)
    fig.hold()
    raw = True
    slope = []

    figures = []
    fig = get_figure(figures, cargs)
    setattr(fig, 'name', 'scat')

    for idx, bg in enumerate(bgs):
        arr = dfc_group.get_group(bg)
        print(arr, file=sys.stderr)
        x = arr['40'] if raw else np.abs(arr['40'])
        y = arr['delta'] if raw else np.abs(arr['delta'])
        p = np.polyfit(x, y, 1)
        px = np.arange(-5, x_stop, 0.5)
        py = np.polyval(p, px)
        slope.append(p[0])
        if not cargs.single:
            plt.subplot(1, 2, 1)
        plt.plot(px, py, color=colors[idx])
        lbl = str(bg)
        plt.scatter(x, y, color=colors[idx], marker='o', label=lbl, s=40)

    plt.xlabel(u'2°')
    plt.ylabel(u'0.5° - 8°')
    plt.xlim([np.min(px), np.max(px)])
    #plt.legend(loc=2)

    if not cargs.single:
        ax = plt.subplot(1, 2, 2, polar=True)
    else:
        fig = get_figure(figures, cargs)
        setattr(fig, 'name', 'scat-polar')
        ax = plt.subplot(1, 1, 1, polar=True)
    plt.hold()
    plt.scatter(map(lambda x: x/180.0*np.pi, bgs), np.abs(slope), c=colors, s=40, marker='o')
    ax.set_rmax(np.max(np.abs(slope))*1.05)
    return figures


def plot_ratio(df, cargs):
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
                if pos_idx[bg] == 6:
                    plt.legend(loc=2)
            except KeyError:
                sys.stderr.write('[W] %sf %.2f not present\n' % (s, bg))

        plt.xlabel(str(bg))

    subjects = df['subject'].unique()
    if len(subjects) == 1:
        plt.suptitle('%s' % (subjects[0]), fontsize=12)

    return [fig]

def plot_sizerel(df, cargs):
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
    setattr(fig, 'name', 'sizerel')
    return [fig]

def plot_sizerel_combined(df, cargs):
    #df = df.sort(['size', 'm_mean'], ascending=[1, 1])
    dfc_group = df.groupby('bg')

    fig = plt.figure()
    bgs = sorted(df['bg'].unique())

    colors = angles_to_color(bgs)
    fig.hold()

    y_max = np.max(np.abs(df['m_mean'])) * 1.10

    for idx, bg in enumerate(bgs):
        arr = dfc_group.get_group(bg)
        x = 2*np.arctan2(arr['size'], 2.0*1145.0)/np.pi*180.0
        x = np.log2(x)
        plt.errorbar(x, arr['m_mean'], yerr=arr['m_merr'], color=colors[idx])
        plt.scatter(x, arr['m_mean'], color=colors[idx], marker='.', s=140, label=u'%03s°' % str(int(bg)))
        plt.xlabel('stimulus size [deg]')

    labels = [u'0.5°', u'2°', u'8°']
    plt.xticks(x, labels)
    plt.ylabel('induced hue shift [deg]')
    plt.ylim([0, y_max])
    plt.legend()

    setattr(fig, 'name', 'sizerel')

    return [fig]


def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', type=str, nargs='+', default='-')
    parser.add_argument('--single', action='store_true', default=False)
    parser.add_argument('--style', nargs='*', type=str, default=['ck'])
    parser.add_argument('--gray', default=False, action='store_true')
    parser.add_argument('--save', default=False, action='store_true')
    parser.add_argument('--legend', dest='legend', action='store_true', default=False)
    parser.add_argument('--no-title', dest='no_title', action='store_true', default=False)
    parser.add_argument('--ylim', default=None, type=float)
    parser.add_argument('-H, --height', dest='height', type=float, default=13.7)
    parser.add_argument('-W, --width', dest='width', type=float, default=24.7)
    parser.add_argument('-U, --unit', dest='unit', type=str, default='cm')
    args = parser.parse_args()

    df = read_data(args.data)
    print(df, file=sys.stderr)

    plt.style.use(args.style)

    if 'shift' in df.columns and 'N' not in df.columns:
        fig = plot_shifts_individual(df, args)
    elif 'oshift' in df.columns:
        fig = plot_shifts_cmpold(df, args)
    elif 'shift' in df.columns:
        fig = plot_shifts(df, args)
    elif 'ratio' in df.columns:
        fig = plot_ratio(df, args)
    elif 'delta' in df.columns:
        fig = plot_delta_combined(df, args)
    elif 'm_plus' in df.columns:
        fig = plot_sizerel(df, args)
    elif 'm_mean' in df.columns:
        fig = plot_sizerel_combined(df, args)
    else:
        raise ValueError('Unknown data set')

    if args.save:
        for f in fig:
            ggsave(plot=f, width=args.width, height=args.height, units=args.unit)
    else:
        plt.show()

if __name__ == '__main__':
    main()