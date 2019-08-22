#!/usr/bin/env python

import yaml
import os
import sys


def get_len(an_object):
    if an_object:
        return len(an_object)
    else:
        return 0


class DeviceGroupReport:
    def __init__(self, config_path=None):
        self.gw_result_dict = {}
        self.tcw_result_dict = {}
        self.test_result_dict = {}
        if not config_path:
            pathname = os.path.dirname(sys.argv[0])
            root_dir = os.path.abspath(os.path.join(pathname, ".."))
            self.config_path = os.path.join(root_dir, "config", "config.yml")
            print("Using config file at '%s'." % self.config_path)
        else:
            self.config_path = config_path

    def get_report_dict(self):
        with open(self.config_path, "r") as stream:
            try:
                conf_yaml = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        for group in conf_yaml["device_groups"]:
            print("*** %s" % group)
            the_item = conf_yaml["device_groups"][group]
            # filter out the test queue and the builder job
            if "-builder" not in group:
                if 'test' in group:
                    self.test_result_dict[group] = get_len(the_item)
                elif group.endswith('unit') or group.endswith('perf') or group.endswith('batt'):
                    self.tcw_result_dict[group] = get_len(the_item)
                else:
                    self.gw_result_dict[group] = get_len(the_item)


    def main(self):
        self.get_report_dict()

        for key in sorted(self.tcw_result_dict.keys()):
            print("%s: %s" % (key, self.tcw_result_dict[key]))
        for key in sorted(self.gw_result_dict.keys()):
            print("%s: %s" % (key, self.gw_result_dict[key]))
        for key in sorted(self.test_result_dict.keys()):
            print("%s: %s" % (key, self.test_result_dict[key]))
