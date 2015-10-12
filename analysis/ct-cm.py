#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import sys, os
import fnmatch
import time
import argparse


def main():
    parser = argparse.ArgumentParser(description='CT - Analysis - import data')
    parser.add_argument('shift', type=str)
    parser.add_argument('modulation', type=str)
    args = parser.parse_args()

    shift = pd.DataFrame.from_csv(args.shift)
    mod = pd.DataFrame.from_csv(args.modulation)

    print(shift, len(shift), file=sys.stderr)
    print(mod, len(mod), file=sys.stderr)

    shift['shift'] *= np.abs(mod['shift'])
    shift.to_csv(sys.stdout)

if __name__ == "__main__":
    main()