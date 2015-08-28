#!/usr/bin/env python
from __future__ import print_function, division

__author__ = 'gicmo'

import matplotlib as mpl
import pandas as pd
import numpy as np
import argparse
import sys


versions = {
    "Python": "%d.%d.%d" % tuple(sys.version_info[:3]),
    "NumPy": np.__version__,
    "Pandas": pd.__version__,
    "Matplotlib": mpl.__version__,
}


def dump_stdout():
    for k, v in versions.iteritems():
        print("%10s: %s" % (k, v))


def dump_latex():
    def mk_command(pkg, version):
        return "\\newcommand{\%sVersion}{%s}" % (pkg, version)

    txt = "\n".join(map(lambda x: mk_command(*x), versions.iteritems()))
    print(txt)


def main():
    parser = argparse.ArgumentParser(description='CT - Versions')
    parser.add_argument('--latex', action="store_true")
    args = parser.parse_args()

    if args.latex:
        dump_latex()
    else:
        dump_stdout()


if __name__ == "__main__":
    main()