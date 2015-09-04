#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import numpy as np
import argparse
import yaml
import sys, os
import fnmatch
import datetime


def calc_angle_shift(phi, baseline, input_is_radiants=False):
    if input_is_radiants:
        phi = phi/np.pi*180.0
        baseline = baseline/np.pi*180.0
    shift = float(phi - baseline)
    shift += (shift >  180.0) * -360
    shift += (shift < -180.0) *  360
    return shift


def read_data(file_list):
    df = pd.read_csv(file_list[0], skipinitialspace=True)
    if len(file_list) > 1:
        for data in file_list[1:]:
            to_append = pd.read_csv(data, skipinitialspace=True)
            df = df.append(to_append, ignore_index=True)
    return df


def is_experiment_file(path):
    try:
        fd = open(path)
        l = open.readline()
        fd.close()
        return l.startswith('colortilt')
    except:
        return False


def check_args(args):
    ok = True
    if args.experiment is None and args.data is None:
        sys.stderr.write('Need --data or experiment argument\n')
        ok = False
    elif args.experiment is not None and args.data is not None:
        sys.stderr.write('Cannot have --data AND experiment argument\n')
        ok = False
    return True


class ColortiltExperiment(object):

    def __init__(self, data, path):
        self.__data = data
        self.path = path

    @staticmethod
    def load_from_path(path):
        path = os.path.expanduser(path)
        sys.stderr.write("[I] loading exp: %s\n" % path)
        f = open(path)
        exp_yaml = yaml.safe_load(f)
        f.close()
        exp = exp_yaml['colortilt']
        return ColortiltExperiment(exp, path)

    @property
    def datapath(self):
        data_dir = os.path.expanduser(self.__data['data-path'])
        data_path = os.path.join(os.path.dirname(self.path), data_dir)
        return data_path

    def subject_data_path(self, subject):
        data_path = os.path.join(self.datapath, subject)
        if not os.path.exists(data_path):
            raise IOError('Could not load data from %s\n' % data_path)
        return data_path

    def result_file_list(self, subject, filterfn=None):
        data_path = self.subject_data_path(subject)
        filelist = map(lambda x: os.path.join(data_path, x),
                       filter(lambda x: fnmatch.fnmatch(x, "*.dat"),
                              os.listdir(data_path)))
        if filterfn is not None:
            if not callable(filterfn):
                if type(filterfn) == str:
                    filterfn = lambda x: not fnmatch.fnmatch(x, filterfn)
                else:
                    raise ValueError('Unsupported filter')
            filelist = filter(filterfn, filelist)
        return filelist

    def load_result_data(self, subject, filterfn=None):
        file_list = self.result_file_list(subject, filterfn=filterfn)
        df = pd.read_csv(file_list[0], skipinitialspace=True)
        if len(file_list) > 1:
            for data in file_list[1:]:
                to_append = pd.read_csv(data, skipinitialspace=True)
                fname = os.path.basename(data)
                to_append['date'] = datetime.datetime.strptime(fname[:13], '%Y%m%dT%H%M')
                df = df.append(to_append, ignore_index=True)

        notused = set(df.columns) - {'size', 'bg', 'fg', 'phi_start', 'side', 'duration', 'phi', 'date'}
        for column in list(notused):
            del df[column]
        df['subject'] = subject
        return df

    @property
    def subjects(self):
        dpath = self.datapath
        dirs = filter(os.path.isdir, map(lambda x: os.path.join(dpath, x), os.listdir(dpath)))
        return map(os.path.basename, dirs)


def main():
    parser = argparse.ArgumentParser(description='CT - Analysis')
    parser.add_argument('--data', nargs='+', type=str)
    parser.add_argument('--exclude-files', dest='fnfilter', type=str)
    parser.add_argument('experiment', nargs='?', type=str, default=None)
    parser.add_argument('subjects', nargs='*', type=str, default=None)
    args = parser.parse_args()

    args_ok = check_args(args)
    if not args_ok:
        parser.print_help(sys.stderr)
        sys.exit(-1)

    if args.experiment:
        exp = ColortiltExperiment.load_from_path(args.experiment)
        subjects = args.subjects or exp.subjects
        print('[i] subjects: ' + ' '.join(subjects), file=sys.stderr)
        dfs = map(lambda subject: exp.load_result_data(subject, args.fnfilter), subjects)
        df = pd.concat(dfs, ignore_index=True)
    else:
        df = read_data(args.data)
        df['subject'] = 'data'

    df['shift'] = df['phi'].combine(df['fg'], calc_angle_shift)
    df['fg_rel'] = df['fg'].combine(df['bg'], calc_angle_shift)

    df.to_csv(sys.stdout, index=False)

if __name__ == "__main__":
    main()
