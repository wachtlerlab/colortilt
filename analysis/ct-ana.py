#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import argparse
import sys, os


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
    if len(file_list) == 1 and file_list[0] == '-':
        file_list[0] = sys.stdin

    df = pd.read_csv(file_list[0], skipinitialspace=True)
    if len(file_list) > 1:
        for data in file_list[1:]:
            to_append = pd.read_csv(data, skipinitialspace=True)
            df = df.append(to_append, ignore_index=True)
    return df


def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', type=str)
    parser.add_argument('--combine', action='store_true', default=False)
    args = parser.parse_args()

    df = read_data([args.data])

    df['shift'] = df['phi'].combine(df['fg'], calc_angle_shift)
    df['fg_rel'] = df['fg'].combine(df['bg'], calc_angle_shift)

    if args.combine:
        groups = ['bg', 'size', 'fg_rel']
        columns = ['bg', 'size', 'fg', 'shift', 'err', 'N']
    else:
        groups = ['bg', 'size', 'fg_rel', 'subject']
        columns = ['bg', 'size', 'fg', 'subject', 'shift', 'err', 'N']

    gpd = df[['bg', 'fg_rel', 'size', 'shift', 'subject']].groupby(groups, as_index=False)
    dfg = gpd.agg([np.mean, stdnerr, len])
    x = dfg.reset_index()
    x.columns = columns

    if args.combine:
        all_subjects = df['subject'].unique()
        subjects = '_'.join(map(lambda x: x[:2],  all_subjects))
        x['subject'] = subjects

    x.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()