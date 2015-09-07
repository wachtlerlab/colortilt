# coding=utf-8
from __future__ import (print_function, division)

import numpy as np


def mk_rgb(value):
    if type(value) == str and len(value) == 7 and value[0] == '#':
        import struct
        t = map(lambda x: x/255.0, struct.unpack('BBB', value[1:].decode('hex')))
        return list(t + [1.0, ])
    raise ValueError('Invalid input')


def angles_to_color(angles):
    def rgb(r, g, b):
        return "#%02x%02x%02x" % (r, g, b)

    bg = list(np.arange(0, 360, 360.0/8))

    cls = [rgb(252, 38, 28),
           rgb(253, 77, 252),
           rgb(13, 66, 251),
           rgb(49, 183, 229),
           rgb(26, 176, 29),
           rgb(181, 248, 50),
           rgb(216, 202, 43),
           rgb(252, 151, 39),
           rgb(0, 0, 0)  #fallback color
           ]
    return [cls[bg.index(a) if a in bg else 8] for a in angles]
