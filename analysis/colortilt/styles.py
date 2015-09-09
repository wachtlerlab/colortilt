# coding=utf-8
from __future__ import (print_function, division)

import numpy as np

def size_colors_seq_bmr():
    cs_map = {
        '10':  [20, 64, 168, 255],  # blue
        '40': [244, 60, 103, 255],  # magenta
        '160': [243, 121, 255, 255] # red
    }

    for k, v in cs_map.iteritems():
        cs_map[k] = map(lambda x: x/255.0, v)

    return cs_map


def size_colors_ck01():
    cs_map = {
        '10':  [0.4910111613133375, 0.77181085558498608, 0.38794311670696036, 1.0],
        '40': [0.65098041296005249, 0.80784314870834351, 0.89019608497619629, 1.0],
        '160':  [0.9020069262560676, 0.1649519457244405, 0.17131872735187115, 1.0]
    }

    return cs_map


def size_colors_gray():
    cs_map = { '10':  [0.60, 0.60, 0.60, 1.0],
               '40': [0.35, 0.35, 0.35, 1.0],
               '160':  [0.1, 0.1, 0.1, 1.0]}

    return cs_map