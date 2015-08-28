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
    parser = argparse.ArgumentParser(description='CT analysis - Filter')
    parser.add_argument('data', nargs='+', type=str, default=['-'])
    parser.add_argument('--size', default=None)
    args = parser.parse_args()

    df = read_data(args.data)

    if args.size is not None:
        df = df[df.size == int(args.size)]

    df.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
