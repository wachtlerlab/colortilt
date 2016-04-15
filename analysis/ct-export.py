#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import numpy as np
import argparse
import sys, os
import json

from colortilt.io import read_data
from collections import defaultdict

def main():
    parser = argparse.ArgumentParser(description='CT analysis - Exporter')
    parser.add_argument('data', nargs='?', type=str, default='-')
    args = parser.parse_args()

    df = read_data([args.data])

    bgs = sorted(np.unique(df['bg']))
    if len(bgs) != 8:
        print('bgs != 8', file=sys.stderr)
        sys.exit(-1)

    sizes = np.unique(df['size'])
    if len(sizes) != 1:
        print('size != 1', file=sys.stderr)
        sys.exit(-1)

    
    
    subjects = np.unique(df['subject'])
    lst = []
    res = {"*": lst}
    
    for bg in bgs:
        part = df.loc[df['bg'] == bg]
        fgs = sorted(np.unique(part['fg']))
        
        rdat = []
        for fg in fgs:
            row = part.loc[part['fg'] == fg]            
            rdat+= [[fg, float(row['shift']), float(row['err'])]]
        lst += [rdat]
    
    s = json.dumps(res)
    print(s)

if __name__ == "__main__":
    main()
