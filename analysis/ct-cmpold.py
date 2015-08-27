#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import argparse
import sys

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
    parser.add_argument('subject', type=str)
    parser.add_argument('olddata', type=str)
    parser.add_argument('data', nargs='+', type=str, default=['-'])

    args = parser.parse_args()
    df = read_data(args.data)
    df = df[df.subject == args.subject]
    df = df[df.size == 40]

    old_df = pd.read_csv(args.olddata)
    old_df['size'] = 40

    old_df.columns = ['bg', 'fg', 'oshift', 'oerr', 'size']
    dfi = df.set_index(['size', 'bg', 'fg'])
    dfo = old_df.set_index(['size', 'bg', 'fg'])

    dfa = pd.concat([dfi, dfo], axis=1)
    x = dfa.reset_index()
    x.subject = args.subject
    x.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
