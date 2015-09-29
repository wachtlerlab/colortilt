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


def color_for_size(size, style='seq_bmr', in_hsv=False):
    import  colortilt.styles as cts
    func = getattr(cts, 'size_colors_' + style)
    return func(size)

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


def size_to_label(size):
    size_map = {
        '10': u'0.5°',
        '40': u'2°',
        '160': u'8°'
    }
    return size_map[str(size)]


class Plotter(object):

    def __init__(self, cargs, m, n):
        self.m = m
        self.n = n
        self.cargs = cargs
        self.single = self.cargs.single
        self.figures = [None] * (self.m * self.n if self.single else 1)
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
            self.__ax_cache[(ax, fig)] = k
        return ax, fig

    def setup_subplot(self, ax, fig, k, idx):
        if ax.axes.name == 'polar':
            return
        ax.axhline(y=0, color='#777777')
        ax.axvline(x=0, color='#777777')


class ShiftPlotter(Plotter):
    bg2idx_map = make_idx2pos()

    def __init__(self, df, column, cargs):
        self.is_vertical = hasattr(cargs, 'vertical') and cargs.vertical
        self.column = column

        m, n = 3, 3
        idx_map = ShiftPlotter.bg2idx_map

        if self.is_vertical or cargs.single:
            bgs = np.unique(df.bg)
            n, m = 1, len(bgs)
            idx_map = {fg: idx+1 for idx, fg in enumerate(bgs)}

        super(ShiftPlotter, self).__init__(cargs, m, n)
        self.mapper = lambda x: idx_map[x]
        group = ['size', 'bg', 'subject']
        if 'size' not in df.columns:
            del group[0]
        self.gd = GroupedData(df, group)
        self.ylim = cargs.ylim or np.max(np.abs(df[column])) * 1.05
        self.is_absolute = any(np.unique(df.fg) > 180.0)
        self.have_negative = any(np.unique(df[self.column]) < 0)
        self.legend = cargs.legend

    @staticmethod
    def make(df, cargs, column='shift'):
        return ShiftPlotter(df, column, cargs)

    def setup_subplot(self, ax, fig, bg, idx):
        super(ShiftPlotter, self).setup_subplot(ax, fig, bg, idx)
        is_abs = self.is_absolute
        plt.xticks(np.arange(45, 360, 45) if is_abs else np.arange(-135, 180, 45))
        plt.xlim([-180, 180] if not is_abs else [0, 360])
        plt.ylim([-1*self.ylim if self.have_negative else 0, self.ylim])
        color = angles_to_color([bg])[0]
        bgstr = u"%d°" % int(bg) if bg != -1 else "control"
        ax.annotate(bgstr, xy=(.05, .935),  xycoords='axes fraction',
                    horizontalalignment='left', verticalalignment='top',
                    fontsize=14, family='Input Mono', color=color)
        ax.tick_params(labelsize=8)

        if is_abs:
             ax.axvline(x=bg, color=color)

        subjects = make_subject_string(self.subjects)
        if not hasattr(fig, 'name'):
            qal = "_abs" if self.is_absolute else ""
            name = self.column + qal + ": " + subjects
            if self.single:
                name +=  " " + str(bg)

            setattr(fig, 'name', name)
            if not self.cargs.no_title:
                plt.suptitle(name)

            if not self.single:
                fig.text(0.5, 0.01, 'Stimulus hue relative to surround [deg]', ha='center')
                fig.text(0.01, 0.5, 'Induced hue shift [deg]', va='center', rotation='vertical')
                fig.subplots_adjust(top=.95)
                fig.subplots_adjust(bottom=.06)
                fig.subplots_adjust(left=.05)
                fig.subplots_adjust(right=.97)


    def __call__(self):

        for data, context in self.gd.data:
            data = data.sort('fg')
            _, bg = context['bg']

            ax, fig = self.subplot(bg)
            style = self.get_style(data, context)
            self.plot_data(data, context.group, ax, style)

            if self.legend and bg == 0:
                location = 1 if self.is_vertical else 4
                plt.legend(loc=location, fontsize=10, fancybox=True, framealpha=0.5)

        return self.figures

    def get_style(self, data, context):
        if 'size' not in context:
            return {'color': 'black', 'label': self.column}
        si, s = context['size']
        cs, subject = context['subject']
        style = self.style_for_size_and_subject(s, subject)
        return style

    @property
    def subjects(self):
        return self.gd.unique('subject')

    def style_for_size_and_subject(self, size, subject):
        n_subjects = len(self.subjects)
        color = color_for_size(size, style=self.cargs.color)
        cur_subject = self.subjects.index(subject)
        label = str(size) if cur_subject == 0 else "_" + subject

        if n_subjects > 1:
            hsv = rgb_to_hsv(color[:3])
            idx_subject = (cur_subject/n_subjects)
            hsv[1] = (1.0-idx_subject)*0.6+0.2
            color = hsv_to_rgb(hsv)

        style = {'color': color, 'label': label}
        return style

    def plot_data(self, df, grp, ax, style):
        if 'err' in df.columns:
            plt.errorbar(df['fg'], df[self.column], yerr=df['err'], **style)
        else:
            plt.plot(df['fg'], df[self.column], **style)
        if self.cargs.single:
            plt.xlabel("Stimulus hue relative to surround [deg]", fontsize=10)
            plt.ylabel("Induced hue changes [deg]", fontsize=10)

class CompareShiftPlotter(ShiftPlotter):
    def __init__(self, df, cargs):
        super(CompareShiftPlotter, self).__init__(df, 'shift', cargs)

    def setup_subplot(self, ax, fig, bg, idx):
        name = "compare: " + self.gd.unique('subject')[0]
        if self.single:
            name +=  " " + str(bg)

        if not self.cargs.no_title:
            plt.suptitle(name)
        setattr(fig, 'name', name)
        super(CompareShiftPlotter, self).setup_subplot(ax, fig, bg, idx)
        plt.xlabel("Stimulus hue relative to surround [deg]", fontsize=11)
        plt.ylabel("Induced hue changes [deg]", fontsize=11)

    def plot_data(self, df, grp, ax, style):
        x = df[np.isfinite(df['shift'])]
        style['linewidht'] = 1.5
        color = color_for_size(40)
        plt.errorbar(x['fg'], x['shift'], yerr=x['err'], label='Kellner & Wachtler 2016', color=color)
        plt.errorbar(df['fg'], df['oshift'], yerr=df['oerr'], label='Klauke & Wachtler 2015', color='k')


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
        x = data.sort(['fg'])
        plt.plot(x['fg'], x['shift'], label="%s %s" % (date, side))
        plt.xlim([-180, 180])
        plt.ylim([-1*max_shift, max_shift])
        if pos_idx[bg] in [3, 6]:
            plt.legend(loc=4, fontsize=6)

        ax.annotate(u"%4d°" % int(bg), xy=(.05, .95),  xycoords='axes fraction',
                    horizontalalignment='left', verticalalignment='top',
                    fontsize=18, family='Input Mono', color=angles_to_color([bg])[0])
    return [fig]

def plot_shifts_bgavg(df, args):
    plotter = Plotter(args, 1, 1)
    ax, fig = plotter.subplot(1)

    ylim = args.ylim or np.max(np.abs(df['shift'])) * 1.05
    is_absolute = any(np.unique(df.fg) > 180.0)

    gd = GroupedData(df, ['size', 'subject'])
    for data, context in gd.data:
        si, size = context['size']
        color = color_for_size(size, style=args.color)
        plt.errorbar(x=data['fg'], y=data['shift'], yerr=data['err'], color=color, label=size_to_label(size))
        plt.ylim([-1*ylim, ylim])

    plt.legend(loc=4, fontsize=12)
    name = 'shift_avg'
    if is_absolute:
        name += '_abs'
    name += ": " + make_subject_string(df.subject.unique())
    plt.suptitle(name)
    setattr(fig, 'name', name)

    return plotter.figures

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
        plt.scatter(x, arr['m_mean'], color=colors[idx], marker='.', s=140, label=u'%s°' % str(int(bg)))
        plt.xlabel('Stimulus size [deg]', fontsize=10)

    labels = [size_to_label(s) for s in sorted(df['size'].unique())]
    plt.xticks(x, labels)
    plt.ylabel('Induced hue shift [deg]', fontsize=10)
    #plt.ylim([0, y_max])
    legend = plt.legend(fontsize=10, fancybox=True, framealpha=0.5, scatterpoints=1)

    setattr(fig, 'name', 'sizerel')

    return [fig]

def cart2pol(x, y):
    theta = np.arctan2(y, x)
    rho = np.hypot(x, y)
    return theta, rho


def pol2cart(theta, rho):
    x = rho * np.cos(theta)
    y = rho * np.sin(theta)
    return x, y


def plot_spread_polar(df, args):
    plotter = Plotter(args, 1, 1)
    df = df[df.bg != -1] # filter out control
    df.sort(['bg'], inplace=True)
    ax, fig = plotter.subplot(1, polar=True)
    bgs = df['bg']
    colors = angles_to_color(bgs)
    theta = np.array(map(lambda x: x/180.0*np.pi, bgs))
    rho = np.array(df['spread'])
    x, y = pol2cart(theta, rho)
    plt.hold(True)
    try:
        from colortilt.ellipse import fit_ellipse, get_parameters, create_ellipse
        a = fit_ellipse(x, y)
        rf, xcf, alpha_f = get_parameters(a)
        el = create_ellipse(rf,xcf,alpha_f)
        tl, rl = cart2pol(el[:, 0], el[:, 1])
        alpha_deg = alpha_f/np.pi*180.0
        print(u"α: %f = %f°" % (alpha_f, alpha_deg))
        plt.plot(tl, rl, label=u"fitted ellipse", color='#111111')
    except ImportError:
        rl = 0
        print('No ellipse fitting, code missing', file=sys.stderr)

    plt.scatter(theta, rho, c=colors, s=50, marker='o', label='surround hue')

    ax.set_rmax(args.ylim or np.max([np.max(rl), np.max(rho)])*1.05)
    sstr = make_subject_string(df['subject'].unique())
    setattr(fig, 'name', 'spread_polar_' + sstr)
    ax.legend(framealpha=0.5, scatterpoints=8, bbox_to_anchor=(1.11, 1.11))
    return plotter.figures

def scatter_spread(df, args):
    from scipy import stats

    plotter = Plotter(args, 1, 1)
    df = df[df.bg != -1] # filter out control
    df.sort(['bg'], inplace=True)
    colors = angles_to_color(df['bg'])
    ax, fig = plotter.subplot(1, polar=False)
    x, y = df['ref'], df['spread']

    slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
    print(p_value, r_value)
    p = np.polyfit(x, y, 1)
    px = np.arange(-5, np.max(np.abs(x))*1.2, 0.5)
    py = np.polyval(p, px)
    plt.plot(px, py, label='fit', color="#999999")
    plt.hold(True)
    plt.scatter(x, y, c=colors, s=50, marker='o')
    plt.xlabel('induction @ ' + size_to_label(40))
    plt.ylabel('max spread')
    return plotter.figures


def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', type=str, nargs='?', default='-')
    parser.add_argument('--single', action='store_true', default=False)
    parser.add_argument('--style', nargs='*', type=str, default=['ck'])
    parser.add_argument('--color', default='seq_bmr', type=str)
    parser.add_argument('-S', '--save', dest='save', default=False, action='store_true')
    parser.add_argument('--no-legend', dest='legend', action='store_false', default=True)
    parser.add_argument('--no-title', dest='no_title', action='store_true', default=False)
    parser.add_argument('--ylim', default=None, type=float)
    parser.add_argument('--vertical', default=False, action='store_true')
    parser.add_argument('-H', '--height', dest='height', type=float, default=13.7)
    parser.add_argument('-W', '--width', dest='width', type=float, default=24.7)
    parser.add_argument('-U', '--unit', dest='unit', type=str, default='cm')
    parser.add_argument('-P', '--path', dest='path', type=str, default=None)
    parser.add_argument('-F', '--filename', dest='filename', type=str, default=None)
    parser.add_argument('--scale', default=1, type=float)
    args = parser.parse_args()

    df = read_data([args.data])
    print(df, file=sys.stderr)

    plt.style.use(args.style)

    if 'shift' in df.columns and 'N' not in df.columns:
        fig = plot_shifts_individual(df, args)
    elif 'shift' in df.columns and 'bg' not in df.columns:
        fig = plot_shifts_bgavg(df, args)
    elif 'oshift' in df.columns:
        plotter = CompareShiftPlotter(df, args)
        fig = plotter()
    elif 'shift' in df.columns:
        plotter = ShiftPlotter.make(df, args)
        fig = plotter()
    elif 'delta' in df.columns:
        fig = plot_delta_combined(df, args)
    elif 'm_plus' in df.columns:
        fig = plot_sizerel(df, args)
    elif 'm_mean' in df.columns:
        fig = plot_sizerel_combined(df, args)
    elif 'duration' in df.columns:
        plotter = ShiftPlotter.make(df, args, column='duration')
        fig = plotter()
    elif 'szdiff' in df.columns:
        plotter = ShiftPlotter.make(df, args, column='szdiff')
        fig = plotter()
    elif 'spread' in df.columns and (len(df) != 9):
        plotter = ShiftPlotter.make(df, args, column='spread')
        fig = plotter()
    elif 'spread' in df.columns:
        fig = plot_spread_polar(df, args)
    else:
        raise ValueError('Unknown data set')

    if args.save:
        for f in fig:
            ggsave(plot=f, filename=args.filename, path=args.path,
                   width=args.width, height=args.height, units=args.unit,
                   dpi=600, scale=args.scale)
    else:
        plt.show()

if __name__ == '__main__':
    main()