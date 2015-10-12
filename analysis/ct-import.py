#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import sys, os
import fnmatch
import time
import argparse
import json


def get_all_files(name, wdir):
    allfiles = os.listdir(wdir)
    return filter(lambda x: fnmatch.fnmatch(x, name), allfiles)


def import_old_ck(args):
    csvfiles = get_all_files('ci.%s.*.csv' % args.subject, args.dir)
    print(csvfiles)

    for f in csvfiles:
        df = pd.read_csv(f, skipinitialspace=True)
        df['bg'] = np.round(df['bg'] / np.pi * 180.0, 2)
        df['fg'] = np.round(df['fg'] / np.pi * 180.0, 2)
        df['phi'] = df['match'] / np.pi * 180.0
        df['phi_start'] = np.nan
        df['duration'] = np.nan
        del df['match']
        st = os.stat(f)
        tstr = time.strftime("%Y%m%dT%H%M", time.gmtime(st.st_ctime))
        bgs = np.unique(df['bg'])
        bg_id = 'on' if 0 in bgs else 'off'
        sizes = '+'.join(map(str, map(int, sorted(np.unique(df['size'])))))
        sides = ''.join(sorted(np.unique(df['side'])))
        newfn = '%s_%s_off_%s_%s.dat' % (tstr, bg_id, sizes, sides)
        df.to_csv(newfn, sep=',', encoding='utf-8')
        print(newfn)


def make_df(data, subject, bg):
    df = pd.DataFrame(np.squeeze(data), columns=['fg', 'shift', 'err'])
    df['bg'] = bg
    df['subject'] = subject
    df['date'] = 0
    df['size'] = 40
    df['side'] = 'n'
    df['N'] = 1
    df['fg'][df['fg'] > 180.0] -= 360.0
    return df


def make_subject(raw, subject):
    data = np.array(raw)
    surrounds = np.arange(0, 360.0, 45.0)
    frames = [make_df(data[i, :, :], subject, bg) for i, bg in enumerate(surrounds)]
    alldata = pd.concat(frames, ignore_index=True)
    return alldata



def make_filter_subject(subject):
    if subject is None:
        return lambda t: True
    else:
        return lambda s: print(s) and subject == s


def import_32(args):
    f32 = get_all_files('*.32', args.dir)
    for f in f32:
        with open(f) as fd:
            dt = json.load(fd)
            dfs = [make_subject(raw, subject) for subject, raw in dt.iteritems()]
            alldata = pd.concat(dfs, ignore_index=True)
            alldata.to_csv(sys.stdout, index=False)

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis - import data')
    parser.add_argument('data', choices=['csv', '32'])
    parser.add_argument('--subject', type=str, default=None)
    parser.add_argument('--dir', type=str, default='.')
    args = parser.parse_args()

    if args.data == 'csv':
        import_old_ck(args)
    elif args.data == '32':
        import_32(args)
    else:
        raise ValueError('Invalid choice')

if __name__ == "__main__":
    main()