# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import urllib.parse

import requests

logger = logging.getLogger(__name__)


# download_file() cloned from autophone's urlretrieve()
def download_file(url, dest, max_attempts=3):
    """Download file from url and save to dest.

    :param: url: string url to file to download.
                 Can be either http, https or file scheme.
    :param dest: string path where to save file.
    :max_attempts: integer number of times to attempt download.
                   Defaults to 3.
    """
    parse_result = urllib.parse.urlparse(url)
    if not parse_result.scheme or parse_result.scheme.startswith("file"):
        local_file = open(parse_result.path)
        with local_file:
            with open(dest, "wb") as dest_file:
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
            with open(dest, "wb") as dest_file:
                for chunk in r.iter_content(chunk_size=4096):
                    dest_file.write(chunk)
            break
        except requests.HTTPError as http_error:
            logger.info("download_file(%s, %s) %s", url, dest, http_error)
            raise
        except (requests.ConnectionError, requests.Timeout) as e:
            logger.warning("utils.download_file: %s: Attempt %s: %s", url, attempt, e)
            if attempt == max_attempts - 1:
                raise
