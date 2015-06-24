#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import argparse
import yaml
import sys, os
import fnmatch
from datetime import date
import time


def main():
    allfiles = os.listdir(sys.argv[1])
    subject = sys.argv[2]
    csvfiles = filter(lambda x: fnmatch.fnmatch(x, 'ci.%s.*.csv' % subject), allfiles)
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


if __name__ == "__main__":
    main()