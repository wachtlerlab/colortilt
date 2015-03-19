#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('ggplot')

def calc_angle_shift(phi, baseline, input_is_radiants=False):
    if input_is_radiants:
        phi = phi/np.pi*180.0
        baseline = baseline/np.pi*180.0
    shift = float(phi - baseline)
    shift += (shift >  180.0) * -360
    shift += (shift < -180.0) *  360
    return shift


def stderr2(x):
    return np.std(x)/np.sqrt(2)


def main():
    df = pd.read_csv('../data/ci.ck.18032015-1.csv')
    print(df)

    # everything in degree
    df['fg'] = df['fg'].apply(lambda x: np.round(x/np.pi*180.0, decimals=2))
    df['bg'] = df['bg'].apply(lambda x: np.round(x/np.pi*180.0, decimals=1))
    df['match'] = df['match'].apply(lambda x: np.round(x/np.pi*180.0, decimals=2))

    df['shift'] = df['match'].combine(df['fg'], calc_angle_shift)
    df['fg_rel'] = df['fg'].combine(df['bg'], calc_angle_shift)

    gpd = df[['bg', 'fg_rel', 'size', 'shift']].groupby(['bg', 'size', 'fg_rel'])
    dfg = gpd.agg([np.mean, stderr2])

    gl = [g for g, n in gpd]
    ad = np.concatenate((np.array(gl), gpd.agg([np.mean, stderr2]).as_matrix()), axis=1)
    dfc = pd.DataFrame({'bg': ad[:, 0], 'size': ad[:, 1], 'fg': ad[:, 2], 'shift': ad[:, 3], 'err': ad[:,  4]})

    dfc_group = dfc.groupby(['size', 'bg'])

    plt.figure()
    bgs = [45, 135, 225, 315]
    for idx, bg in enumerate(bgs):
        for s in [20, 40, 60]:
            plt.subplot(2,2,idx+1)
            ga = dfc_group.get_group((s, bg))
            arr = dfc_group.get_group((s, bg))
            plt.errorbar(arr['fg'], arr['shift'], yerr=arr['err'], label=str(s))
            if idx == 0:
                plt.legend(loc=2)

        plt.xlabel(str(bg))

    plt.show()

if __name__ == "__main__":
    main()