#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import colortilt as ct
from colortilt.io import read_data

import pandas as pd
import numpy as np
import argparse
import sys


def calc_angle_shift(phi, baseline, input_is_radiants=False):
    if input_is_radiants:
        phi = phi/np.pi*180.0
        baseline = baseline/np.pi*180.0
    shift = float(phi - baseline)
    shift += (shift >  180.0) * -360
    shift += (shift < -180.0) *  360
    return shift


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
    parser.add_argument('subjects', nargs='*', type=str, default=None)
    args = parser.parse_args()

    args_ok = check_args(args)
    if not args_ok:
        parser.print_help(sys.stderr)
        sys.exit(-1)

    if args.experiment:
        exp = ct.Experiment.load_from_path(args.experiment)
        subjects = args.subjects or exp.subjects
        print('[i] subjects: ' + ' '.join(subjects), file=sys.stderr)
        dfs = map(lambda subject: exp.load_result_data(subject, args.fnfilter), subjects)
        df = pd.concat(dfs, ignore_index=True)
    else:
        df = read_data(args.data)
        df['subject'] = 'data'

    df.rename(columns={'fg': 'fg_abs'}, inplace=True)
    df['shift'] = df['phi'].combine(df['fg_abs'], calc_angle_shift)
    df['fg'] = df['fg_abs'].combine(df['bg'], calc_angle_shift)

    df.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
