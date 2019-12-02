# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mozilla_bitbar_devicepool import configuration

import pytest
import yaml

test_configuration_1 = '''
projects:
  defaults:
    application_file: aerickson-Testdroid.apk
    test_file: aerickson-empty-test.zip
    additional_parameters:
      DOCKER_IMAGE_VERSION: 20191119T130125
  blah1:
    device_group_name: blah1-group
    device_model: pixel2
    test_file: aerickson-empty-test2.zip
    framework_name: mozilla-usb
    description: blah1 is great
    additional_parameters:
      TASKCLUSTER_CLIENT_ID: project/autophone/blah1
      TC_WORKER_TYPE: blah1
  blah2:
    device_group_name: blah2-group
    device_model: pixel2
    framework_name: mozilla-usb
    description: blah2 is fabulous
    additional_parameters:
      TASKCLUSTER_CLIENT_ID: project/autophone/blah2
      TC_WORKER_TYPE: blah2
 '''

test_configuration_2 = '''
projects:
  defaults:
    application_file: aerickson-Testdroid.apk
    test_file: aerickson-empty-test.zip
    additional_parameters:
      DOCKER_IMAGE_VERSION: 20191119T130125
  blah1:
    device_group_name: blah1-group
    device_model: pixel2
    test_file: aerickson-empty-test.zip
    framework_name: mozilla-usb
    description: blah1 is great
    additional_parameters:
      TASKCLUSTER_CLIENT_ID: project/autophone/blah1
      TC_WORKER_TYPE: blah1
  blah2:
    device_group_name: blah2-group
    device_model: pixel2
    framework_name: mozilla-usb
    description: blah2 is fabulous
    additional_parameters:
      TASKCLUSTER_CLIENT_ID: project/autophone/blah2
      TC_WORKER_TYPE: blah2
 '''

def test_unique_filenames_extraction():
  config = yaml.load(test_configuration_1, Loader=yaml.SafeLoader)
  assert (configuration.ensure_filenames_are_unique(config) ==
          ['aerickson-empty-test2.zip',
          'aerickson-Testdroid.apk',
          'aerickson-empty-test.zip']
  )

def test_unique_filenames_ok_config():
  config = yaml.load(test_configuration_1, Loader=yaml.SafeLoader)
  try:
    configuration.ensure_filenames_are_unique(config)
  except Exception:
    pytest.fail("shouldn't be any exceptions")

def test_unique_filenames_bad_config():
  config = yaml.load(test_configuration_2, Loader=yaml.SafeLoader)
  with pytest.raises(configuration.ConfigurationFileDuplicateFilenamesException):
    configuration.ensure_filenames_are_unique(config)
