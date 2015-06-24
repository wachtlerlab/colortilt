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
    data = sys.argv[1]
    subject = sys.argv[2]
    df = pd.read_csv(data, skipinitialspace=True)
    df['subject'] = subject
    df['size'] = float(sys.argv[3])

    df.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()