# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import signal
import time
import threading

from mozilla_bitbar_devicepool import configuration
from mozilla_bitbar_devicepool.taskcluster import get_taskcluster_pending_tasks
from mozilla_bitbar_devicepool.devices import get_offline_devices
from mozilla_bitbar_devicepool.device_groups import get_device_group_devices
from mozilla_bitbar_devicepool.runs import (
    run_test_for_project,
    get_active_test_runs,
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
    def __init__(self, wait=60):
        global CACHE, CONFIG

        CACHE = configuration.BITBAR_CACHE
        CONFIG = configuration.CONFIG

        self.wait = wait
        self.state = 'RUNNING'

        signal.signal(signal.SIGUSR2, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)

        logger.info('test-run-manager: loading existing runs')
        self.process_active_runs()

    def handle_signal(self, signalnum, frame):
        if self.state != 'RUNNING':
            return

        if signalnum == signal.SIGINT or signalnum == signal.SIGUSR2:
            self.state = 'STOP'
        elif signalnum == signal.SIGTERM:
            self.state = 'STOP'

    def get_bitbar_test_stats(self, project_name, project_config):
        device_group_name = project_config['device_group_name']
        device_group = CONFIG['device_groups'][device_group_name]
        bitbar_device_group = CACHE['device_groups'][device_group_name]
        bitbar_test_runs = CACHE['test_runs']
        stats = CACHE['projects'][project_name]['stats']
        device_group_count = bitbar_device_group['deviceCount']

        offline_devices = []
        temp_offline_devices = get_offline_devices(device_model=project_config['device_model'])
        for device_name in temp_offline_devices:
            if device_name in device_group:
                offline_devices.append(device_name)
        enabled_devices = get_device_group_devices(bitbar_device_group['id'])

        stats = CACHE['projects'][project_name]['stats']
        stats['OFFLINE_DEVICES'] = offline_devices
        stats['OFFLINE'] = len(offline_devices)
        stats['DISABLED'] = device_group_count - len(enabled_devices)
        stats['RUNNING'] = 0
        stats['WAITING'] = 0

        for test_run in bitbar_test_runs[project_name]:
            test_run_state = test_run['state']
            stats[test_run_state] += 1

        stats['IDLE'] = (stats['COUNT'] -
                         stats['DISABLED'] -
                         stats['OFFLINE'] -
                         stats['RUNNING'])

    def handle_queue(self, project_name, projects_config):
        logger.info("thread starting: %s" % project_name)
        stats = CACHE['projects'][project_name]['stats']

        while self.state == 'RUNNING':
            project_config = projects_config[project_name]
            device_group_name = project_config['device_group_name']
            additional_parameters = project_config['additional_parameters']
            worker_type = additional_parameters.get('TC_WORKER_TYPE')

            if stats['OFFLINE'] or stats['DISABLED']:
                logger.warning('{:10s} DISABLED {} OFFLINE {} {}'.format(
                    device_group_name,
                    stats['DISABLED'],
                    stats['OFFLINE'],
                    ', '.join(stats['OFFLINE_DEVICES'])))

            bitbar_device_group = CACHE['device_groups'][device_group_name]
            bitbar_device_group_count = bitbar_device_group['deviceCount']
            taskcluster_provisioner_id = projects_config['defaults']['taskcluster_provisioner_id']

            # create enough tests to service either the pending tasks or twice the number
            # of the devices in the group (whichever is smaller).
            pending_tasks = get_taskcluster_pending_tasks(taskcluster_provisioner_id, worker_type)
            jobs_to_start = min(pending_tasks, 2*bitbar_device_group_count) - stats['WAITING']

            if stats['RUNNING'] or stats['WAITING']:
                logger.info(
                    '{:10s} COUNT {} IDLE {} OFFLINE {} DISABLED {} RUNNING {} WAITING {} PENDING {}'.format(
                        device_group_name,
                        stats['COUNT'],
                        stats['IDLE'],
                        stats['OFFLINE'],
                        stats['DISABLED'],
                        stats['RUNNING'],
                        stats['WAITING'],
                        pending_tasks))

            for _task in range(jobs_to_start):
                try:
                    if TESTING:
                        print('TESTING MODE: {}: Would be starting test run.'.format(project_name))
                    else:
                        test_run = run_test_for_project(project_name)

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
        logger.info("thread exiting: %s" % project_name)

    def process_active_runs(self):
        bitbar_projects = CACHE['projects']
        bitbar_test_runs = CACHE['test_runs']

        # init the temporary dict
        accumulation_dict = {}
        for project_name in bitbar_projects:
            accumulation_dict[project_name] = []

        # gather all runs per project
        result = get_active_test_runs()
        for item in result:
            project_name = item['projectName']
            accumulation_dict[project_name].append(item)

        # replace current values with what we got above
        for project_name in bitbar_projects:
            bitbar_test_runs[project_name] = accumulation_dict[project_name]


    def run(self):
        projects_config = CONFIG['projects']
        CONFIG['threads'] = []

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

            # multithread handle_queue
            t1 = threading.Thread(target=self.handle_queue, args=(project_name, projects_config,))
            CONFIG['threads'].append(t1)
            t1.start()

        # we need the main thread to keep running so it can handle signals
        # - https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/
        while self.state == 'RUNNING':
            for project_name in projects_config:
                self.get_bitbar_test_stats(project_name, projects_config)
            self.process_active_runs()
            time.sleep(60)
