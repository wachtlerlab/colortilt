#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import argparse
import sys
import numpy as np

def read_data(file_list):
    if len(file_list) == 1 and file_list[0] == '-':
        file_list[0] = sys.stdin

    df = pd.read_csv(file_list[0], skipinitialspace=True)
    if len(file_list) > 1:
        for data in file_list[1:]:
            to_append = pd.read_csv(data, skipinitialspace=True)
            df = df.append(to_append, ignore_index=True)
    return df

def mean_angle(df, sign, use_mean=False):
    x = df[df.fg == sign*22.5].append(df[df.fg == sign*67.5], ignore_index=True)
    grouped = x.groupby(['bg', 'size'])

    if use_mean:
        fn = np.mean
    else:
        fn = np.max if sign > 0 else np.min

    df_mean = grouped['shift'].agg({'m_plus' if sign > 0 else 'm_minus': fn})
    return df_mean

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', nargs='+', type=str, default=['-'])
    parser.add_argument('--mean', type=bool, default=False)
    args = parser.parse_args()

    df = read_data(args.data)
    df = df[df.bg != -1]
    m_plus = mean_angle(df, 1, use_mean=args.mean)
    print(m_plus, file=sys.stderr)
    m_minus = mean_angle(df, -1, use_mean=args.mean)
    print(m_minus, file=sys.stderr)

    x = pd.concat([m_plus, m_minus], axis=1)
    x = x.reset_index()
    x.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()

