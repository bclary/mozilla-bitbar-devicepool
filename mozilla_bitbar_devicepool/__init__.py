# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

# mozilla_bitbar_devicepool
# https://mozilla.testdroid.com/cloud/swagger-ui.html

import logging
import os

# we need to run basicConfig before any other module does
# TODO: put %(asctime)s back in?
logging.basicConfig(format="%(threadName)26s %(levelname)-8s %(message)s")

from testdroid import Testdroid

logger = logging.getLogger()

modulepath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TESTDROID_URL = os.environ.get("TESTDROID_URL")
TESTDROID_APIKEY = os.environ.get("TESTDROID_APIKEY")
if TESTDROID_URL and TESTDROID_APIKEY:
    TESTDROID = Testdroid(apikey=TESTDROID_APIKEY, url=TESTDROID_URL)
else:
    TESTDROID = None
