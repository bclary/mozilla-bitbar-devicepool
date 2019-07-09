# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import os

import yaml

from mozilla_bitbar_devicepool import (
    TESTDROID,
    apply_dict_defaults,
)

from mozilla_bitbar_devicepool.devices import get_devices
from mozilla_bitbar_devicepool.files import get_files
from mozilla_bitbar_devicepool.frameworks import get_frameworks

from mozilla_bitbar_devicepool.device_groups import (
    add_devices_to_device_group,
    create_device_group,
    delete_device_from_device_group,
    get_device_group_devices,
    get_device_groups,
)

from mozilla_bitbar_devicepool.projects import (
    create_project,
    get_projects,
    update_project,
)

BITBAR_CACHE = {
    'device_groups': {},
    'devices': {},
    'files': {},
    'frameworks': {},
    'projects': {},
    'test_runs': {},
}

FILESPATH = None
CONFIG = None


def get_filespath():
    """Return files path where application and test files are kept.
    """
    return FILESPATH

def configure(bitbar_configpath, filespath=None, do_updates=False):
    """Parse and load the configuration yaml file
    defining the Mozilla Bitbar test setup.

    :param bitbar_configpath: string path to the config.yml
                              containing the Mozilla Bitbar
                              configuration.
    :param filespath: string path to the files directory where
                      application and test files are kept.
    """
    global CONFIG, FILESPATH

    FILESPATH=filespath

    with open(bitbar_configpath) as bitbar_configfile:
        CONFIG = yaml.load(bitbar_configfile.read(), Loader=yaml.SafeLoader)

    configure_device_groups(do_updates)
    configure_projects(do_updates)


def configure_device_groups(do_updates=False):
    """Configure device groups from configuration.

    :param config: parsed yaml configuration containing
                   a device_groups attribute which contains
                   and object for each device group which contains
                   objects for each contained device.
    """
    # Cache the bitbar device data in the configuration.
    devices_cache = BITBAR_CACHE['devices'] = {}
    for device in get_devices():
        devices_cache[device['displayName']] = device

    device_groups_config = CONFIG['device_groups']
    for device_group_name in device_groups_config:
        device_group_config = device_groups_config[device_group_name]
        if device_group_config is None:
            # Handle the case where the configured device group is empty.
            device_group_config = device_groups_config[device_group_name] = {}
        new_device_group_names = set(device_group_config.keys())

        # get the current definition of the device group at bitbar.
        bitbar_device_groups = get_device_groups(displayname=device_group_name)
        if len(bitbar_device_groups) == 0:
            # no such device group. create it.
            bitbar_device_group = create_device_group(device_group_name)
        elif len(bitbar_device_groups) == 1:
            bitbar_device_group = bitbar_device_groups[0]
        else:
            raise Exception('device group {} has {} duplicates'.format(device_group_name, len(bitbar_device_groups) - 1))

        bitbar_device_group_devices = get_device_group_devices(bitbar_device_group['id'])
        bitbar_device_group_names = set([device['displayName'] for device in bitbar_device_group_devices])

        # determine which devices need to be deleted from or added to
        # the device group at bitbar.
        delete_device_names = bitbar_device_group_names - new_device_group_names
        add_device_names = new_device_group_names - bitbar_device_group_names

        delete_device_ids = [ devices_cache[name]['id'] for name in delete_device_names ]
        add_device_ids = [ devices_cache[name]['id'] for name in add_device_names ]

        for device_id in delete_device_ids:
            delete_device_from_device_group(bitbar_device_group['id'], device_id)
            bitbar_device_group['deviceCount'] -= 1
            if bitbar_device_group['deviceCount'] < 0:
                raise Exception('device group {} has negative deviceCount'.format(device_group_name))

        if add_device_ids:
            bitbar_device_group = add_devices_to_device_group(bitbar_device_group['id'], add_device_ids)

        BITBAR_CACHE['device_groups'][device_group_name] = bitbar_device_group

def configure_projects(do_updates=False):
    """Configure projects from configuration.

    :param config: parsed yaml configuration containing
                   a projects attribute which contains
                   and object for each project.

    CONFIG['projects']['defaults'] contains values which will be set
    on the other projects if they are not already explicitly set.

    """
    projects_config = CONFIG['projects']
    project_defaults = projects_config['defaults']

    for project_name in projects_config:
        if project_name == 'defaults':
            continue

        project_config = projects_config[project_name]
        # Set the default project values.
        project_config = projects_config[project_name] = apply_dict_defaults(project_config, project_defaults)

        bitbar_projects = get_projects(name=project_name)
        if len(bitbar_projects) == 0:
            # no such project. create it.
            bitbar_project = create_project(project_name, project_type=project_config['project_type'])
        elif len(bitbar_projects) == 1:
            bitbar_project = bitbar_projects[0]
        else:
            raise Exception('project {} has {} duplicates'.format(project_name, len(bitbar_projects) - 1))

        framework_name = project_config['framework_name']
        BITBAR_CACHE['frameworks'][framework_name] = get_frameworks(name=framework_name)[0]

        file_name =  project_config.get('test_file')
        if file_name:
            bitbar_files = get_files(name=file_name, inputtype='test')
            if len(bitbar_files) > 0:
                bitbar_file = bitbar_files[-1]
            else:
                TESTDROID.upload_test_file(bitbar_project['id'],
                                           os.path.join(FILESPATH, file_name))
                bitbar_file = get_files(name=file_name, inputtype='test')[-1]
            BITBAR_CACHE['files'][file_name] = bitbar_file

        file_name = project_config.get('application_file')
        if file_name:
            bitbar_files = get_files(name=file_name, inputtype='application')
            if len(bitbar_files) > 0:
                bitbar_file = bitbar_files[-1]
            else:
                TESTDROID.upload_application_file(bitbar_project['id'],
                                                  os.path.join(FILESPATH, file_name))
                bitbar_file = get_files(name=file_name, inputtype='application')[-1]
            BITBAR_CACHE['files'][file_name] = bitbar_file

        # Sync the base project properties if they have changed.
        if (project_config['archivingStrategy'] != bitbar_project['archivingStrategy'] or
            project_config['archivingItemCount'] != bitbar_project['archivingItemCount'] or
            project_config['description'] != bitbar_project['description']):
            # project basic attributes changed in config, update bitbar version.
            bitbar_project = update_project(
                bitbar_project['id'],
                project_name,
                archiving_item_count=project_config['archivingItemCount'],
                archiving_strategy=project_config['archivingStrategy'],
                description=project_config['description'])

        additional_parameters = project_config['additional_parameters']
        if 'TC_WORKER_TYPE' in additional_parameters:
            # Add the TASKCLUSTER_ACCESS_TOKEN from the environment to
            # the additional_parameters in order that the bitbar
            # projects may be configured to use it. Non-taskcluster
            # projects such as mozilla-docker-build are not invoke by
            # Taskcluster currently.
            taskcluster_access_token_name = additional_parameters['TC_WORKER_TYPE'].replace('-', '_')
            additional_parameters['TASKCLUSTER_ACCESS_TOKEN'] = os.environ[taskcluster_access_token_name]

        BITBAR_CACHE['projects'][project_name] = bitbar_project
