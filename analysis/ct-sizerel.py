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

def mean_angle(df, sign):
    x = df[df.fg == sign*22.5].append(df[df.fg == sign*67.5], ignore_index=True)
    grouped = x.groupby(['bg', 'size'])
    df_mean = grouped['shift'].agg({'m_plus' if sign > 0 else 'm_minus': np.max})
    return df_mean

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', nargs='+', type=str, default=['-'])
    args = parser.parse_args()

    df = read_data(args.data)
    df = df[df.bg != -1]
    m_plus = mean_angle(df, 1)
    print(m_plus, file=sys.stderr)
    m_minus = mean_angle(df, -1)
    print(m_minus, file=sys.stderr)

    x = pd.concat([m_plus, m_minus], axis=1)
    x = x.reset_index()
    x.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()

