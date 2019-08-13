# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

# mozilla_bitbar_devicepool
# https://mozilla.testdroid.com/cloud/swagger-ui.html

from __future__ import absolute_import

# we need to run basicConfig before any other module does
import logging

# TODO: put %(asctime)s back in?
logging.basicConfig(format='%(threadName)24s %(levelname)-8s %(message)s')

import copy
import os
import urlparse
import requests
from testdroid import Testdroid

modulepath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger()

TESTDROID_URL=os.environ.get('TESTDROID_URL')
TESTDROID_APIKEY=os.environ.get('TESTDROID_APIKEY')
if TESTDROID_URL and TESTDROID_APIKEY:
    TESTDROID = Testdroid(apikey=TESTDROID_APIKEY, url=TESTDROID_URL)
else:
    TESTDROID = None

def lookup_key_value(dict_list, keyname):
    """Utility function to look up an object by key name from a list of
    objects which contain the attribute.

    :param dict_list: list of dictionary items.
    :param keyname: string name of key attribute.

    Examples:
        given dict_list = [ {'key1': 'value1'}, {'key2': 'value2'} ]
        obj = lookup_key_value(dict_list, 'key1')
        where obj = { 'key': 'value1' }
    """
    for d in dict_list:
        if keyname in d:
            return d[keyname]
    return None


def get_filter(fields, **kwargs):
    filter=[]
    for fieldname in kwargs:
        fieldvalue = kwargs[fieldname]
        fieldtype = type(fieldvalue)
        if fieldtype != fields[fieldname]:
            raise ValueError('filter field name {} type {} does not match {}'.format(
                fieldname, fieldtype, fields[fieldname]))
        fieldflag = ''
        if fieldtype == int:
            if 'time' in fieldname:
                fieldflag = 'd'
            else:
                fieldflag = 'n'
        elif fieldtype == str:
            fieldflag = 's'
        elif fieldtype == bool:
            fieldflag = 'b'
        else:
            raise ValueError('Unknown filter field type %s' % fieldtype)
        filter.append('{}_{}_eq_{}'.format(
            fieldflag, fieldname, fieldvalue))
    return filter

def apply_dict_defaults(input_dict, defaults_dict):
    """Recursively sets the missing values in input_dict to those defined
    in defaults_dict.

    :param input_dist: dict to apply default values.
    :param defaults_dict: dict of defaults
    """

    # Set the default  values.
    new_dict = copy.deepcopy(defaults_dict)
    for attribute_name in input_dict:
        attribute = input_dict[attribute_name]
        if isinstance(attribute, dict):
            # Recursively do nested dicts.
            new_dict[attribute_name] = apply_dict_defaults(
                attribute, defaults_dict[attribute_name])
        else:
            new_dict[attribute_name] = attribute

    return new_dict


# download_file() cloned from autophone's urlretrieve()

def download_file(url, dest, max_attempts=3):
    """Download file from url and save to dest.

    :param: url: string url to file to download.
                 Can be either http, https or file scheme.
    :param dest: string path where to save file.
    :max_attempts: integer number of times to attempt download.
                   Defaults to 3.
    """
    parse_result = urlparse.urlparse(url)
    if not parse_result.scheme or parse_result.scheme.startswith('file'):
        local_file = open(parse_result.path)
        with local_file:
            with open(dest, 'wb') as dest_file:
                while True:
                    chunk = local_file.read(4096)
                    if not chunk:
                        break
                    dest_file.write(chunk)
            return

    for attempt in range(max_attempts):
        try:
            r = requests.get(url, stream=True)
            if not r.ok:
                r.raise_for_status()
            with open(dest, 'wb') as dest_file:
                for chunk in r.iter_content(chunk_size=4096):
                    dest_file.write(chunk)
            break
        except requests.HTTPError as http_error:
            logger.info("download_file(%s, %s) %s", url, dest, http_error)
            raise
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.warning("utils.download_file: %s: Attempt %s: %s",
                           url, attempt, e)
            if attempt == max_attempts - 1:
                raise

__all__ = ["configuration", "device_groups", "devices", "files", "frameworks", "projects", "runs"]
