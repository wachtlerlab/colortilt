#!/usr/bin/env python
from __future__ import print_function

import numpy as np
import scipy.optimize

def ellipse(a, b, phi, x):
    return (a*b)/(np.sqrt((a*np.sin(x - phi))**2+(b*np.cos(x - phi))**2))

def to_fit_func(x, y, a, b, phi):
    res = y - ellipse(a, b, phi, x)
    return res


def fit_ellipse(x, y):
    # print('Fitting ellipse...', file=sys.stderr)
    func = lambda param: to_fit_func(x, y, *list(param))
    rx, cov_x, infodict, mesg, ier = scipy.optimize.leastsq(func, (10, 15, 20/180*np.pi), full_output=True)
    if ier not in range(1, 5):
        raise ArithmeticError(mesg)
    return [i for i in rx]

def get_parameters(params):
    a, b, phi = params[:]
    return [a, b], b, phi

def create_ellipse(params, how_many):
    a, b, phi = params[:]
    x = np.linspace(0, 2*np.pi, how_many)
    y =  ellipse(a, b, phi, x)
    return x, y

