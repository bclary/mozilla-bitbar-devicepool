# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mozilla_bitbar_devicepool import TESTDROID
from mozilla_bitbar_devicepool.util.template import get_filter


def get_frameworks(**kwargs):
    """Return list of matching Bitbar frameworks.

    :param **kwargs: keyword arguments containing fieldnames and
                     values with which to filter the frameworks to
                     be returned. If a fieldname is missing, it is
                     not used in the filter.
                     {
                       'id': int,
                       'jobconfigid': int,
                       'labelname': str,
                        'name': str,
                        'ostype': str,
                        'type': str,
                     }

    Examples:
       get_frameworks() # Return all frameworks
       get_devices(displayname='pixel2-25') # Return pixel2-25
    """
    fields = {
        "id": int,
        "jobconfigid": int,
        "labelname": str,
        "name": str,
        "ostype": str,
        "type": str,
    }

    filter = get_filter(fields, **kwargs)
    response = TESTDROID.get(
        "/api/v2/admin/frameworks", payload={"limit": 0, "filter": filter}
    )
    return response["data"]
