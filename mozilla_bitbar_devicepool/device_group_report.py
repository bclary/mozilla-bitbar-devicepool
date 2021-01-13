#!/usr/bin/env python3

import os
import sys

import yaml


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
        self.device_dict = {}  # device types to count
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
            the_item = conf_yaml["device_groups"][group]
            # filter out the test queue and the builder job
            if "-builder" not in group:
                if "test" in group:
                    self.test_result_dict[group] = get_len(the_item)
                elif group.endswith("2") or group.startswith("s7"):
                    self.gw_result_dict[group] = get_len(the_item)
                else:
                    self.tcw_result_dict[group] = get_len(the_item)

        for group in conf_yaml["device_groups"]:
            the_item = conf_yaml["device_groups"][group]
            # print(the_item)
            if the_item:
                for device in the_item:
                    if "s7" in device:
                        self.device_dict["s7"] = self.device_dict.get("s7", 0) + 1
                    if "pixel2" in device:
                        self.device_dict["p2"] = self.device_dict.get("p2", 0) + 1
                    if "motog5" in device:
                        self.device_dict["g5"] = self.device_dict.get("g5", 0) + 1

    def main(self):
        self.get_report_dict()

        # print("/// tc-w  workers ///")
        # for key in sorted(self.tcw_result_dict.keys()):
        #     print("%s: %s" % (key, self.tcw_result_dict[key]))
        print("/// g-w workers ///")
        for key in sorted(self.gw_result_dict.keys()):
            print("%s: %s" % (key, self.gw_result_dict[key]))
        print("/// test workers ///")
        for key in sorted(self.test_result_dict.keys()):
            print("%s: %s" % (key, self.test_result_dict[key]))
        print("/// device summary ///")
        total_count = 0
        for item in self.device_dict:
            total_count += int(self.device_dict[item])
            print("%s: %s" % (item, self.device_dict[item]))
        print("total: %s" % total_count)
