# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import copy

# TODO: use m-c utility functions vs writing our own
# see https://github.com/bclary/mozilla-bitbar-devicepool/pull/2


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
    filter = []
    for fieldname in kwargs:
        fieldvalue = kwargs[fieldname]
        fieldtype = type(fieldvalue)
        if fieldtype != fields[fieldname]:
            raise ValueError(
                "filter field name {} type {} does not match {}".format(
                    fieldname, fieldtype, fields[fieldname]
                )
            )
        fieldflag = ""
        if fieldtype == int:
            if "time" in fieldname:
                fieldflag = "d"
            else:
                fieldflag = "n"
        elif fieldtype == str:
            fieldflag = "s"
        elif fieldtype == bool:
            fieldflag = "b"
        else:
            raise ValueError("Unknown filter field type %s" % fieldtype)
        filter.append("{}_{}_eq_{}".format(fieldflag, fieldname, fieldvalue))
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
                attribute, defaults_dict[attribute_name]
            )
        else:
            new_dict[attribute_name] = attribute

    return new_dict
