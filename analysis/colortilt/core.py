#!/usr/bin/env python
from __future__ import print_function
from __future__ import division

import pandas as pd
import yaml
import sys, os
import fnmatch
import datetime


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
