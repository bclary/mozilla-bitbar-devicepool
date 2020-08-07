# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mozilla_bitbar_devicepool import (
    TESTDROID,
    get_filter,
)


def get_files(**kwargs):
    """Return list of matching Bitbar files.

    :param **kwargs: keyword arguments containing fieldnames and
                     values with which to filter the files to
                     be returned. If a fieldname is missing, it is
                     not used in the filter.

                     Returns files sorted by createTime ascending.
    Examples:
       get_files(name='ignore.apk')

    https://mozilla.testdroid.com/cloud/swagger-ui.html#/File/getFilesUsingGET
    """
    fields = {
        "createtime": int,
        "direction": str,
        "id": int,
        "mimetype": str,
        "name": str,
        "size": int,
        "state": str,
    }

    filter = get_filter(fields, **kwargs)
    response = TESTDROID.get(
        "/api/v2/files", payload={"limit": 0, "filter": filter, "sort": "createTime_a"}
    )
    return response["data"]
