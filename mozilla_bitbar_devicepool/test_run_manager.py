# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import signal
import time
import threading
import sys

from mozilla_bitbar_devicepool import configuration
from mozilla_bitbar_devicepool.taskcluster import get_taskcluster_pending_tasks
from mozilla_bitbar_devicepool.devices import get_offline_devices
from mozilla_bitbar_devicepool.device_groups import get_device_group_devices
from mozilla_bitbar_devicepool.runs import (
    abort_test_run,
    delete_test_run,
    get_test_run,
    get_test_runs,
    run_test_for_project,
)

#
# WARNING: not used everywhere yet!!!
#
# don't fire calls at bitbar, just mention you would
TESTING = False

CACHE = None
CONFIG = None

logger = logging.getLogger()

class TestRunManager(object):
    """Model state and control from Apache's example:
    https://httpd.apache.org/docs/2.4/stopping.html

    DevicePoolTestRunManager starts Bitbar test runs to service the
    test jobs from Taskcluster.
    """
    def __init__(self, wait=60, delete_bitbar_tests=False):
        global CACHE, CONFIG

        CACHE = configuration.BITBAR_CACHE
        CONFIG = configuration.CONFIG

        self.wait = wait
        self.delete_bitbar_tests = delete_bitbar_tests
        self.state = 'RUNNING'

        signal.signal(signal.SIGUSR2, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        bitbar_projects = CACHE['projects']
        bitbar_test_runs = CACHE['test_runs']

        for project_name in bitbar_projects:
            bitbar_project = bitbar_projects[project_name]
            project_id = bitbar_project['id']
            while True:
                try:
                    bitbar_test_runs[project_name] = get_test_runs(project_id, active=True)
                    # Insert a delay to give Bitbar a break and hopefully reduce
                    # ConnectionErrors.
                    time.sleep(5)
                    break
                except Exception as e:
                    logger.error(
                        'Failed to get tests for project %s (%s: %s).'
                        % (project_name, e.__class__.__name__, e.message),
                        exc_info=True,
                    )
                    time.sleep(self.wait)

    def handle_signal(self, signalnum, frame):
        if self.state != 'RUNNING':
            return
        if signalnum == signal.SIGUSR2:
            self.state = 'STOP'
        elif signalnum == signal.SIGTERM:
            self.state = 'TERM'

    def get_bitbar_test_stats(self, project_name, project_config):
        project_id = CACHE['projects'][project_name]['id']
        device_group_name = project_config['device_group_name']
        device_group = CONFIG['device_groups'][device_group_name]
        bitbar_device_group = CACHE['device_groups'][device_group_name]
        bitbar_test_runs = CACHE['test_runs']
        device_group_count = bitbar_device_group['deviceCount']

        offline_devices = []
        temp_offline_devices = get_offline_devices(device_model=project_config['device_model'])
        for device_name in temp_offline_devices:
            if device_name in device_group:
                offline_devices.append(device_name)
        enabled_devices = get_device_group_devices(bitbar_device_group['id'])
        stats = {
            'COUNT': device_group_count,
            'IDLE': 0,
            'OFFLINE_DEVICES': offline_devices,
            'OFFLINE': len(offline_devices),
            'DISABLED': device_group_count - len(enabled_devices),
            'FINISHED': 0,
            'RUNNING': 0,
            'WAITING': 0,
            }

        for i, test_run in enumerate(bitbar_test_runs[project_name]):
            test_run_id = test_run['id']
            test_run_state = test_run['state']
            # Refresh test_run from bitbar and update the cache.
            test_run = bitbar_test_runs[project_name][i] = get_test_run(project_id, test_run_id)
            stats[test_run_state] += 1
            if test_run_state == 'FINISHED':
                logger.info('{:10s} test run {} finished'.format(device_group_name, test_run['id']))
                del bitbar_test_runs[project_name][i]
                if self.delete_bitbar_tests:
                    delete_test_run(project_id, test_run_id)

        stats['IDLE'] = (stats['COUNT'] -
                         stats['DISABLED'] -
                         stats['OFFLINE'] -
                         stats['RUNNING'])

        return stats

    def abort_tests(self, state=None):
        bitbar_projects = CACHE['projects']

        for project_name in bitbar_projects:
            bitbar_project = bitbar_projects[project_name]
            project_id = bitbar_project['id']
            bitbar_test_runs = CACHE['test_runs']

            for test_run in bitbar_test_runs[project_name]:
                test_run_id = test_run['id']

                # No need to cache the result since we are removing them all.
                test_run = get_test_run(project_id, test_run_id)
                if test_run['state'] == 'FINISHED':
                    continue
                if state is None or test_run['state'] == state:
                    logger.info('aborting test run {} {}'.format(project_name, test_run_id))
                    abort_test_run(project_id, test_run_id)
                    if self.delete_bitbar_tests:
                        delete_test_run(project_id, test_run_id)
            bitbar_test_runs[project_name] = []

    # TODO: add taskcluster_provisioner_id to self so we don't have to pass
    def handle_queue(self, project_name, projects_config, taskcluster_provisioner_id):
        project_config = projects_config[project_name]
        device_group_name = project_config['device_group_name']
        additional_parameters = project_config['additional_parameters']
        worker_type = additional_parameters.get('TC_WORKER_TYPE')

        try:
            stats = self.get_bitbar_test_stats(project_name, project_config)
        except Exception as e:
            logger.error(
                'Failed to get stats for project %s (%s: %s).'
                % (project_name, e.__class__.__name__, e.message),
                exc_info=True,
            )
            # continue
            # hmm, just pass and keep going

        if stats['OFFLINE'] or stats['DISABLED']:
            logger.warning('{:10s} DISABLED {} OFFLINE {} {}'.format(
                device_group_name,
                stats['DISABLED'],
                stats['OFFLINE'],
                ', '.join(stats['OFFLINE_DEVICES'])))

        if stats['FINISHED'] or stats['RUNNING'] or stats['WAITING']:
            logger.info(
                '{:10s} COUNT {} IDLE {} OFFLINE {} DISABLED {} FINISHED {} RUNNING {} WAITING {}'.format(
                    device_group_name,
                    stats['COUNT'],
                    stats['IDLE'],
                    stats['OFFLINE'],
                    stats['DISABLED'],
                    stats['FINISHED'],
                    stats['RUNNING'],
                    stats['WAITING']))

        # If the test_group has available devices, then query
        # taskcluster to see if any tasks are pending and
        # queue up tests for the available devices.
        bitbar_device_group = CACHE['device_groups'][device_group_name]
        bitbar_device_group_count = bitbar_device_group['deviceCount']
        available_devices = bitbar_device_group_count - stats['RUNNING'] - stats['WAITING']
        bitbar_test_runs = CACHE['test_runs']
        if available_devices > 0:
            pending_tasks = get_taskcluster_pending_tasks(
                taskcluster_provisioner_id, worker_type
            )
            if pending_tasks > available_devices:
                pending_tasks = available_devices

            for task in range(pending_tasks):
                try:
                    test_run = run_test_for_project(project_name)
                    bitbar_test_runs[project_name].append(test_run)

                    logger.info('{:10s} test run {} started'.format(
                        device_group_name,
                        test_run['id']))
                except Exception as e:
                    logger.error(
                        'Failed to create test run for group %s (%s: %s).'
                        % (device_group_name, e.__class__.__name__, e.message),
                        exc_info=True,
                    )

        time.sleep(self.wait)

    def run(self):
        projects_config = CONFIG['projects']

        # while self.state == 'RUNNING':
        for project_name in projects_config:
            if project_name == 'defaults':
                continue

            project_config = projects_config[project_name]
            # device_group_name = project_config['device_group_name']
            additional_parameters = project_config['additional_parameters']
            worker_type = additional_parameters.get('TC_WORKER_TYPE')
            if not worker_type:
                # Only manage projects initiated via Taskcluster.
                continue

            # TESTIZNG
            t1 = threading.Thread(target=self.thread_test, args=(project_name,))
            t1.start()

            # TODO: multithread handle_queue

        # we need the main thread to keep running so it can handle signals
        # - https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/
        while self.state == 'RUNNING':
            try:
                time.sleep(0.5)
            except KeyboardInterrupt:
                # TODO: use handle_signal vs just setting this
                self.state = 'STOP'
                # allow threads see state change
                time.sleep(5)
                # TODO: should really join so they exit cleanly?
                # exit
                sys.exit(0)

        # TODO: how to handle this?
        if self.state == 'TERM':
            self.abort_tests()

    def thread_test(self, project_name):
        while self.state == 'RUNNING':
        # while True:
            # TODO: use screen semaphore to avoid interleaved output
            # https://stackoverflow.com/questions/26688424/python-threads-are-printing-at-the-same-time-messing-up-the-text-output
            print("working on queue: %s" % project_name)
            time.sleep(5)
        print("exiting: %s" % project_name)