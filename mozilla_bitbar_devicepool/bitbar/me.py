# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mozilla_bitbar_devicepool import TESTDROID


def get_me():
    """Return information about the current API user.

    Examples:
       get_me() # Return information about the current API user
    """
    response = TESTDROID.get("api/v2/me")
    return response
