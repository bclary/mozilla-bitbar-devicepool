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
    def main(self):
        pathname = os.path.dirname(sys.argv[0])
        root_dir = os.path.abspath(os.path.join(pathname, ".."))
        bitbar_config_path = os.path.join(root_dir, "config", "config.yml")

        with open(bitbar_config_path, "r") as stream:
            try:
                conf_yaml = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

        tcw_result_dict = {}
        gw_result_dict = {}
        for group in conf_yaml["device_groups"]:
            the_item = conf_yaml["device_groups"][group]
            # filter out the test queue and the builder job
            if "-test" not in group and "-builder" not in group:
                if group.endswith("-2"):
                    gw_result_dict[group] = get_len(the_item)
                else:
                    tcw_result_dict[group] = get_len(the_item)

        for a_dict in [tcw_result_dict, gw_result_dict]:
            for item in sorted(a_dict):
                print("%s: %s" % (item, a_dict[item]))
