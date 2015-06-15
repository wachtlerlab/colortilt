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

def calc_angle_shift(phi, baseline, input_is_radiants=False):
    if input_is_radiants:
        phi = phi/np.pi*180.0
        baseline = baseline/np.pi*180.0
    shift = float(phi - baseline)
    shift += (shift >  180.0) * -360
    shift += (shift < -180.0) *  360
    return shift


def stdnerr(x):
    return np.std(x)/np.sqrt(len(x))


def read_data(file_list):
    df = pd.read_csv(file_list[0], skipinitialspace=True)
    if len(file_list) > 1:
        for data in file_list[1:]:
            to_append = pd.read_csv(data, skipinitialspace=True)
            df = df.append(to_append, ignore_index=True)
    return df


def is_experiment_file(path):
    try:
        fd = open(path)
        l = open.readline()
        fd.close()
        return l.startswith('colortilt')
    except:
        return False

def check_args(args):
    ok = True
    if args.experiment is None and args.data is None:
        sys.stderr.write('Need --data or experiment argument\n')
        ok = False
    elif args.experiment is not None and args.data is not None:
        sys.stderr.write('Cannot have --data AND experiment argument\n')
        ok = False
    return True

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('--data', nargs='+', type=str)
    parser.add_argument('experiment', nargs='?', type=str, default=None)
    parser.add_argument('subject', nargs='?', type=str, default=None)
    args = parser.parse_args()

    args_ok = check_args(args)
    if not args_ok:
        parser.print_help(sys.stderr)
        sys.exit(-1)

    if args.experiment:
        path = os.path.expanduser(args.experiment)
        sys.stderr.write("[I] loading exp: %s\n" % path)
        f = open(path)
        exp = yaml.safe_load(f)
        f.close()
        data_dir = os.path.expanduser(exp['colortilt']['data-path'])
        data_path = os.path.join(os.path.dirname(path), data_dir, args.subject)
        if not os.path.exists(data_path):
            sys.stderr.write('Could not load data from %s\n' % data_path)
            sys.exit(-2)

        filelist = map(lambda x: os.path.join(data_path, x),
                       filter(lambda x: fnmatch.fnmatch(x, "*.dat"),
                              os.listdir(data_path)))
        print(filelist)
        df = read_data(filelist)
        flen = len(filelist)
        subject = args.subject
    else:
        df = read_data(args.data)
        flen = len(args.data)
        subject = 'data'

    df['shift'] = df['phi'].combine(df['fg'], calc_angle_shift)
    df['fg_rel'] = df['fg'].combine(df['bg'], calc_angle_shift)

    gpd = df[['bg', 'fg_rel', 'size', 'shift']].groupby(['bg', 'size', 'fg_rel'])
    dfg = gpd.agg([np.mean, stdnerr])

    print(gpd.agg(len))

    gl = [g for g, n in gpd]
    ad = np.concatenate((np.array(gl), dfg.as_matrix()), axis=1)
    dfc = pd.DataFrame({'bg': ad[:, 0], 'size': ad[:, 1], 'fg': ad[:, 2], 'shift': ad[:, 3], 'err': ad[:,  4]})

    dfc_group = dfc.groupby(['size', 'bg'])

    plt.figure()
    bgs = dfc['bg'].unique()

    pos_map = {-1: (1, 1), 0: (1, 2), 45: (0, 2), 90: (0, 1), 135: (0, 0), 180: (1, 0), 225: (2, 0), 270: (2, 1), 315: (2, 2)}
    pos_idx = {k: pos_map[k][0]*3+pos_map[k][1]+1 for k in pos_map}

    max_shift = np.max(np.abs(ad[:, 3])) * 1.05

    for idx, bg in enumerate(bgs):
        for s in dfc['size'].unique():
            plt.subplot(3, 3, pos_idx[bg])
            try:
                arr = dfc_group.get_group((s, bg))
                plt.axhline(y=0, color='#777777')
                plt.axvline(x=0, color='#777777')
                plt.errorbar(arr['fg'], arr['shift'], yerr=arr['err'], label=str(s))
                plt.xlim([-180, 180])
                plt.ylim([-1*max_shift, max_shift])
                if idx == 0:
                    plt.legend(loc=2)
            except KeyError:
                sys.stderr.write('[W] %.2f %.2f not present\n' % (s, bg))

        plt.xlabel(str(bg))

    plt.suptitle('%s [%d]' % (subject, flen), fontsize=12)
    plt.show()

if __name__ == "__main__":
    main()