#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import sys, os
import fnmatch
import time
import argparse


def rotate(data, fg, angle):
    delta = np.diff(fg)
    assert(all(map(lambda x: x == delta[0], delta)))
    delta = delta[0]
    print(u"Δ ° = %f" % delta, file=sys.stderr)
    N, r = divmod(angle, delta)
    assert(r == 0.0)
    print(u"q, r = %f + %f" % (N, r), file=sys.stderr)
    return np.roll(data, int(N))


def gen_for_bg(shift, mod, bg):
    res = shift.copy()
    mshift = np.abs(mod['shift'])
    mshift = mshift / np.mean(mshift)
    mfg = np.array(mod['fg'])
    res['shift'] *= rotate(mshift, mfg, bg)
    res['bg'] = bg
    return res

def main():
    parser = argparse.ArgumentParser(description='CT - Analysis - import data')
    parser.add_argument('shift', type=str)
    parser.add_argument('modulation', type=str)
    args = parser.parse_args()

    shift = pd.DataFrame.from_csv(args.shift)
    mod = pd.DataFrame.from_csv(args.modulation)

    print(shift, len(shift), file=sys.stderr)
    print(mod, len(mod), file=sys.stderr)

    surrounds = np.arange(0, 360, 45)
    frames = [gen_for_bg(shift, mod, bg) for bg in surrounds]
    data = pd.concat(frames, ignore_index=True)
    data.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()