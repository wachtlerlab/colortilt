#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
plt.style.use('ggplot')

def calc_angle_shift(phi, baseline, input_is_radiants=False):
    if input_is_radiants:
        phi = phi/np.pi*180.0
        baseline = baseline/np.pi*180.0
    shift = float(phi - baseline)
    shift += (shift >  180.0) * -360
    shift += (shift < -180.0) *  360
    return shift


def stdnerr(x):
    return np.std(x)/np.sqrt(len(x))


def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('data', nargs='+', type=str)
    args = parser.parse_args()

    df = pd.read_csv(args.data[0])
    if len(args.data) > 1:
        for data in args.data[1:]:
            to_append = pd.read_csv(data)
            df = df.append(to_append, ignore_index=True)

    print(df)

    # everything in degree
    df['fg'] = df['fg'].apply(lambda x: np.round(x/np.pi*180.0, decimals=2))
    df['bg'] = df['bg'].apply(lambda x: np.round(x/np.pi*180.0, decimals=1))
    df['match'] = df['match'].apply(lambda x: np.round(x/np.pi*180.0, decimals=2))

    df['shift'] = df['match'].combine(df['fg'], calc_angle_shift)
    df['fg_rel'] = df['fg'].combine(df['bg'], calc_angle_shift)

    gpd = df[['bg', 'fg_rel', 'size', 'shift']].groupby(['bg', 'size', 'fg_rel'])
    dfg = gpd.agg([np.mean, stdnerr])

    gl = [g for g, n in gpd]
    ad = np.concatenate((np.array(gl), dfg.as_matrix()), axis=1)
    dfc = pd.DataFrame({'bg': ad[:, 0], 'size': ad[:, 1], 'fg': ad[:, 2], 'shift': ad[:, 3], 'err': ad[:,  4]})

    dfc_group = dfc.groupby(['size', 'bg'])

    plt.figure()
    bgs = dfc['bg'].unique()

    n_x = np.ceil(np.sqrt(len(bgs)))
    n_y = np.ceil(len(bgs) / n_x)

    for idx, bg in enumerate(bgs):
        for s in dfc['size'].unique():
            plt.subplot(n_x, n_y, idx+1)
            arr = dfc_group.get_group((s, bg))
            plt.errorbar(arr['fg'], arr['shift'], yerr=arr['err'], label=str(s))
            if idx == 0:
                plt.legend(loc=2)

        plt.xlabel(str(bg))

    plt.show()

if __name__ == "__main__":
    main()