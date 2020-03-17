# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.



from mozilla_bitbar_devicepool import (
    TESTDROID,
    get_filter,
)


def get_device_groups(**kwargs):
    """Return list of matching Bitbar device_groups.

    :param **kwargs: keyword arguments containing fieldnames and
                     values with which to filter the devices to
                     be returned. If a fieldname is missing, it is
                     not used in the filter.
                     {
                       'displayname': str,
                       'id': int,
                       'ostype': str
                     }

    Examples:
       get_device_groups() # Return all device groups
       get_device_groups(displayname='pixel2-perf') # Return pixel2-perf device group.
    """
    fields = {
        'displayname': str,
        'id': int,
        'ostype': str
        }

    filter = get_filter(fields, **kwargs)
    response = TESTDROID.get('/api/v2/device-groups',
                             payload={'limit': 0, 'filter': filter})
    return response['data']


def get_device_group(id):
    """Return Bitbar device group with specified id.

    :param id: integer id of device group to be returned.

    Examples:
       get_device_group(27) # Return device group with id 27
    """
    response = TESTDROID.get('/api/v2/device-groups/{}'.format(id),
                             payload={'limit': 0, 'filter': filter})
    return response['data']


def get_device_group_devices(id, **kwargs):
    """Return list of matching Bitbar devices for device group with specified id.

    :param id: integer id of device group.
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
                       'ostype': str
                     }


    Examples:
       get_device_group_devices(27) # Return devices for device group with id 27
       get_device_group_devices(27, displayname='pixel2-27') # Return devices for device group with id 27 and displayname pixel2-27.
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
    response = TESTDROID.get('/api/v2/device-groups/{}/devices'.format(id),
                             payload={'limit': 0, 'filter': filter})
    return response['data']


def create_device_group(displayname, ostype='ANDROID'):
    """Create a device group for the current user.

    :param displayname: display name for the device group.
    :param ostype: device operating system type. One of
                   IOS, ANDROID, UNDEFINED. Defaults to
                   ANDROID.

    Examples:
       create_device_group('test-dummy-group')
    """
    me = TESTDROID.get_me()
    payload = {
        'displayName': displayname,
        'osType': ostype,
    }

    response = TESTDROID.post(path='/users/{}/device-groups'.format(me['id']),
                             payload=payload)
    return response


def add_devices_to_device_group(id, deviceids):
    """Add devices to a device group.

    :param id: device group id.
    :param deviceids: list of device ids to add to the group

    Examples:
       add_device_to_device_group(40, [31])')
    """
    payload = {
        'deviceIds[]': deviceids,
    }

    response = TESTDROID.post(path='/device-groups/{}/devices'.format(id),
                             payload=payload)
    return response


def delete_device_from_device_group(id, deviceid):
    """Delete a device from a device group.

    :param id: device group id.
    :param deviceid: device id.

    Examples:
       delete_device_group(99, 31)
    """
    TESTDROID.delete(path='/device-groups/{}/devices/{}'.format(id, deviceid))


def delete_device_group(id):
    """Delete a device group.

    :param id: device group id.

    Examples:
       delete_device_group(99)
    """

    TESTDROID.delete(path='/device-groups/{}'.format(id))
