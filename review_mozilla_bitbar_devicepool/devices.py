# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

from mozilla_bitbar_devicepool import (
    TESTDROID,
    get_filter,
)


def get_devices(**kwargs):
    """Return list of matching Bitbar devices.

    :param **kwargs: keyword arguments containing fieldnames and
                     values with which to filter the devices to
                     be returned. If a fieldname is missing, it is
                     not used in the filter.
                     {
                       'displayname': str,
                       'enabled': bool,
                       'id': int,
                       'locked': bool,
                       'online': bool,
                       'ostype': str,
                     }

    Examples:
       get_devices() # Return all devices
       get_devices(displayname='pixel2-25') # Return pixel2-25
    """
    fields = {
        'displayname': str,
        'enabled': bool,
        'id': int,
        'locked': bool,
        'online': bool,
        'ostype': str
        }

    filter = get_filter(fields, **kwargs)
    response = TESTDROID.get('/api/v2/devices',
                             payload={'limit': 0, 'filter': filter})
    return response['data']


def get_device(id):
    """Return Bitbar device with specified id.

    :param id: integer id of device to be returned.

    Examples:
       get_device(1) # Return device with id 1
    """
    response = TESTDROID.get('/api/v2/devices/{}'.format(id),
                             payload={'limit': 0, 'filter': filter})
    return response

def get_device_problems(device_model=None):
    """Return list of matching Bitbar devices with device problems.

    :param device_model: string prefix of device names to match.
    """
    path = 'admin/device-problems'
    payload={'limit': 0}
    data = TESTDROID.get(path=path, payload=payload)['data']
    if device_model:
        data = [d for d in data
                if d['deviceName'].startswith(device_model)]
    else:
        data = [d for d in data
                if d['deviceName'] != "Docker Builder"]
    return data

def get_offline_devices(device_model=None):
    device_problems = get_device_problems(device_model=device_model)
    offline_devices = []
    for device_problem in device_problems:
        problems = device_problem['problems']
        for problem in problems:
            if problem['type'] == 'OFFLINE':
                offline_devices.append(device_problem['deviceModelName'])
    return offline_devices
