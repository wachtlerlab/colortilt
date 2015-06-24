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
    parser.add_argument('--exclude-files', dest='fnfilter', type=str)
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
        print(filelist, file=sys.stderr)
        if args.fnfilter is not None:
            filelist = filter(lambda x: not fnmatch.fnmatch(x, args.fnfilter), filelist)
            print(filelist, file=sys.stderr)
        df = read_data(filelist)
        flen = len(filelist)
        subject = args.subject
    else:
        df = read_data(args.data)
        flen = len(args.data)
        subject = 'data'

    df['shift'] = df['phi'].combine(df['fg'], calc_angle_shift)
    df['fg_rel'] = df['fg'].combine(df['bg'], calc_angle_shift)

    df['subject'] = subject
    gpd = df[['bg', 'fg_rel', 'size', 'shift', 'subject']].groupby(['bg', 'size', 'fg_rel', 'subject'], as_index=False)
    dfg = gpd.agg([np.mean, stdnerr, len])

    x = dfg.reset_index()
    x.columns = ['bg','size','fg', 'subject', 'shift','err','N']
    x.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()