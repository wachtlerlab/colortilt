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
        '10': u'½°',
        '40': u'2°',
        '160': u'8°'
    }
    return size_map[str(size)]


class Plotter(object):

    def __init__(self, cargs, m, n):
        self.m = m
        self.n = n
        self.cargs = cargs
        self.figures = [None] * (self.m * self.n)
        self.single = self.cargs.single
        self.mapper = lambda x: x
        self.__ax_cache = {}

    def __getitem__(self, item):
        item -= 1
        if self.figures[item] is None:
            fig = plt.figure()
            plt.hold(True)
            self.figures[item] = fig

        return self.figures[item]

    def subplot(self, k, polar=False):
        idx = self.mapper(k)
        if self.single:
            fig = self[idx]
            plt.figure(fig.number)
            ax = plt.subplot(1, 1, 1, polar=polar)
        else:
            fig = self[1]
            ax = plt.subplot(self.m, self.n, idx, polar=polar)

        if (ax, fig) not in self.__ax_cache:
            self.setup_subplot(ax, fig, k, idx)
        return ax, fig

    def setup_subplot(self, ax, fig, k, idx):
        ax.axhline(y=0, color='#777777')
        ax.axvline(x=0, color='#777777')

class ShiftPlotter(Plotter):
    bg2idx_map = make_idx2pos()

    def __init__(self, df, cargs):
        self.is_vertical = hasattr(cargs, 'vertical') and cargs.vertical

        m, n = 3, 3
        idx_map = ShiftPlotter.bg2idx_map

        if self.is_vertical:
            m, n = 9, 1
            idx_map = { i*45 : i+2 for i in range(8) }
            idx_map[-1] = 1

        super(ShiftPlotter, self).__init__(cargs, m, n)
        self.mapper = lambda x: idx_map[x]
        self.gd = GroupedData(df, ['size', 'bg', 'subject'])
        self.ylim = cargs.ylim or np.max(np.abs(df['shift'])) * 1.05
        self.is_absolute = any(np.unique(df.fg) > 180.0)

    @staticmethod
    def make(df, cargs):
        return ShiftPlotter(df, cargs)

    def setup_subplot(self, ax, fig, bg, idx):
        super(ShiftPlotter, self).setup_subplot(ax, fig, bg, idx)
        plt.xlim([-180, 180] if not self.is_absolute else [0, 360])
        plt.ylim([-1*self.ylim, self.ylim])
        ax.annotate(u"%4d°" % int(bg), xy=(.05, .95),  xycoords='axes fraction',
                    horizontalalignment='left', verticalalignment='top',
                    fontsize=18, family='Input Mono', color=angles_to_color([bg])[0])

        subjects = make_subject_string(self.subjects)
        if not hasattr(fig, 'name'):
            name = subjects
            if self.single:
                name +=  " " + str(bg)

            plt.suptitle(name)
            setattr(fig, 'name', name)

    def __call__(self, func, *args, **kwargs):
        gd = self.gd

        subjects = gd.unique('subject')
        pos_idx = make_idx2pos()

        for data, context in gd.data:
            data = data.sort('fg')
            _, bg = context['bg']
            si, s = context['size']
            cs, subject = context['subject']
            group = context.group

            ax, fig = self.subplot(bg)

            plot_style = style_for_size_and_subject(s, cs, len(subjects), self.cargs)
            sstr = size_to_label(s)
            lbl = sstr if len(subjects) == 1 else sstr + ' ' + subject[:2]
            plot_style['label'] = lbl

            func(data, group, ax, plot_style, *args, **kwargs)

            if pos_idx[bg] == 6:
                plt.legend(loc=4, fontsize=12)

        return self.figures

    @property
    def subjects(self):
        return self.gd.unique('subject')


def plot_shifts(df, cargs):
    plotter = ShiftPlotter.make(df, cargs)

    def plot_shift(df, grp, ax, style):
        plt.errorbar(df['fg'], df['shift'], yerr=df['err'], **style)

    return plotter(plot_shift)


def plot_shifts_cmpold(df, cargs):
    plotter = ShiftPlotter.make(df, cargs)
    def plot_shift(df, grp, ax, style):
        x = df[np.isfinite(df['shift'])]
        lbl = style['label']
        plt.errorbar(x['fg'], x['shift'], yerr=x['err'], label=lbl, color='r')
        plt.errorbar(df['fg'], df['oshift'], yerr=df['oerr'], label=lbl + '-old', color='k')

    return plotter(plot_shift)


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

    plot = Plotter(cargs, 1, 2)

    bgs = sorted(df['bg'].unique())
    x_stop = df['40'].max() * 1.05
    colors = angles_to_color(bgs)
    raw = True
    slope = []

    ax, fig = plot.subplot(1)
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
        plt.plot(px, py, color=colors[idx])
        lbl = str(bg)
        plt.scatter(x, y, color=colors[idx], marker='o', label=lbl, s=40)

    plt.xlabel(u'2°')
    plt.ylabel(u'0.5° - 8°')
    plt.xlim([np.min(px), np.max(px)])
    #plt.legend(loc=2)

    ax, fig = plot.subplot(2, polar=True)
    setattr(fig, 'name', 'scat-polar')

    plt.hold()
    plt.scatter(map(lambda x: x/180.0*np.pi, bgs), np.abs(slope), c=colors, s=40, marker='o')
    ax.set_rmax(np.max(np.abs(slope))*1.05)

    return plot.figures


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
    parser.add_argument('--vertical', default=False, action='store_true')
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