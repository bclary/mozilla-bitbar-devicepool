# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import argparse
import os
import sys
import zipfile

from mozilla_bitbar_devicepool import (
    TESTDROID,
    configuration,
    download_file,
    logger,
    modulepath,
)

from mozilla_bitbar_devicepool.runs import run_test_for_project
from mozilla_bitbar_devicepool.test_run_manager import TestRunManager


testdroid_apk_url = "https://github.com/bitbar/bitbar-samples/blob/master/apps/builds/Testdroid.apk"

def download_testdroid_apk(args):
    if args.filename:
        testdroid_apk = os.path.join(args.files, args.filename)
    else:
        testdroid_apk = os.path.join(args.files, os.path.basename(testdroid_apk_url))
    if os.path.exists(testdroid_apk) and not args.force:
        logger.warning('%s exists. Skipping download.' % testdroid_apk)
    else:
        # Add ?raw=true to force download.
        download_file(testdroid_apk_url+'?raw=true', testdroid_apk)


def empty_test_zip(args):
    # Create an empty zip file
    test_zip = os.path.join(args.files, args.filename)
    with zipfile.ZipFile(test_zip, mode="w"):
        pass


def test_run_manager(args):
    if not TESTDROID:
        logger.error("The environment variabels TESTDROID_URL, TESTDROID_APIKEY both need to be set.")
        sys.exit(1)

    if args.bitbar_config is None:
        bitbar_configpath = os.path.join(modulepath, 'config', 'config.yml')
    else:
        bitbar_configpath = args.bitbar_config

    try:
        configuration.configure(bitbar_configpath, filespath=args.files, update_bitbar=args.update_bitbar)
    except configuration.DuplicateProjectException as e:
        logger.error("Duplicate project found! Please archive all but one and restart. Exiting...")
        logger.error(e)
        sys.exit(1)

    manager = TestRunManager(wait=args.wait)
    manager.run()


def run_test(args):
    if not TESTDROID:
        logger.error("The environment variabels TESTDROID_URL, TESTDROID_APIKEY both need to be set.")
        sys.exit(1)

    if args.bitbar_config is None:
        bitbar_configpath = os.path.join(modulepath, 'config', 'config.yml')
    else:
        bitbar_configpath = args.bitbar_config

    configuration.configure(bitbar_configpath, filespath=args.files, update_bitbar=args.update_bitbar)

    run_test_for_project(args.project_name)

def main():

    parser = argparse.ArgumentParser(
        description="Mozilla Android Hardware testing at Bitbar.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:

The following environment variables must be set prior to attempting to
start the test_run_manager.

TESTDROID_URL
TESTDROID_APIKEY

To get additional help for each positional sub-command, add
--help to the sub-command.

Controlling the test_run_manager via signals:

Stop Now
    kill -USR2 <pid>

    Stop process while leaving test containers running.

Terminate Now
    kill -TERM  <pid>

    Abort any running test containers and exit immediately.

"""
)
    parser.add_argument("--files",
                        default=os.path.join(modulepath, "files"),
                        help="Directory where downloaded files are saved. "
                        "Defaults to %s/files" % modulepath)
    parser.add_argument('--log-level', dest='log_level',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                        default='INFO',
                        help='Logging level. Defaults to INFO.')

    subparsers = parser.add_subparsers(help="Specify one of the positional arguments to select the command to execute.")

    ### download-test-apk ###
    subparser = subparsers.add_parser("download-testdroid-apk",
                                      help="Download Testdroid.apk from %s to files/ then exit." % testdroid_apk_url)
    subparser.add_argument("--filename",
                           help="Specify filename to save Testdroid.apk to in the files directory.")
    subparser.add_argument("--force",
                           action="store_true", default=False,
                           help="Overwrite existing file.")
    subparser.set_defaults(func=download_testdroid_apk)

    ### empty-test-zip ###
    subparser = subparsers.add_parser("empty-test-zip",
                                      help="Generate empty test zip file in files/ directory then exit.")
    subparser.add_argument("--filename",
                           default="empty-test.zip",
                           help="Specify filename to save in the files directory. "
                           "Defaults to empty-test.zip.")
    subparser.set_defaults(func=empty_test_zip)

    ### test-run-manager ###
    subparser = subparsers.add_parser('start-test-run-manager',
                        help='Run the test run manager.')
    subparser.add_argument("--bitbar-config",
                           help="Path to Bitbar yaml configuration file.")
    subparser.add_argument('--wait', dest='wait',
                           type=int,
                           default=20,
                           help='Seconds to wait between checks. Defaults to 20.')
    subparser.add_argument("--update-bitbar",
                           action="store_true", default=False,
                           help="Update the remote bitbar configuration to reflect the config file.")
    subparser.set_defaults(func=test_run_manager)

    ### run-test ###
    subparser = subparsers.add_parser("run-test",
                                      help="Run test for a project then exit.")
    subparser.add_argument("--bitbar-config",
                           help="Path to Bitbar yaml configuration file.")
    subparser.add_argument("--update-bitbar",
                           action="store_true", default=False,
                           help="Update the remote bitbar configuration to reflect the config file.")
    subparser.add_argument("--project-name",
                           required=True,
                           help="Specify a project name for which to start a test.")
    subparser.set_defaults(func=run_test)

    args = parser.parse_args()

    logger.setLevel(level=args.log_level)

    args.func(args)

if __name__ == '__main__':
    main()
