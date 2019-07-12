# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import signal
import time
import threading

from mozilla_bitbar_devicepool import configuration, logger
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
        signal.signal(signal.SIGINT, self.handle_signal)

    def handle_signal(self, signalnum, frame):
        if self.state != 'RUNNING':
            return

        if signalnum == signal.SIGINT or signalnum == signal.SIGUSR2:
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

        if stats['RUNNING'] + stats['WAITING'] + stats['PENDING'] + stats['JOBS_TO_START'] > 0:
            logger.info(
                '{:10s} COUNT {} IDLE {} OFFLINE {} DISABLED {} RUNNING {} WAITING {} PENDING {} STARTING {}'.format(
                    device_group_name,
                    stats['COUNT'],
                    stats['IDLE'],
                    stats['OFFLINE'],
                    stats['DISABLED'],
                    stats['RUNNING'],
                    stats['WAITING'],
                    stats['PENDING'],
                    stats['JOBS_TO_START']))

    def handle_queue(self, project_name, projects_config):
        logger.info("thread starting")
        stats = CACHE['projects'][project_name]['stats']
        lock = CACHE['projects'][project_name]['lock']

        while self.state == 'RUNNING':
            project_config = projects_config[project_name]
            device_group_name = project_config['device_group_name']
            additional_parameters = project_config['additional_parameters']
            worker_type = additional_parameters.get('TC_WORKER_TYPE')

            with lock:
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
                jobs_to_start = min(pending_tasks, stats['IDLE'] - stats['WAITING']) 
                if jobs_to_start < 0:
                    jobs_to_start = 0
                stats['PENDING'] = pending_tasks
                stats['JOBS_TO_START'] = jobs_to_start

            for _task in range(jobs_to_start):
                if self.state != 'RUNNING':
                    break
                try:
                    # increment so we don't start too many jobs before main thread updates stats
                    with lock:
                        stats['WAITING'] += 1
                    if TESTING:
                        logger.info('TESTING MODE: Would be starting test run.')
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

            if self.state == 'RUNNING':
                time.sleep(self.wait)
        logger.info("thread exiting")

    def thread_active_jobs(self):
        while self.state == 'RUNNING':
            logger.info('getting active runs')
            self.process_active_runs()
            time.sleep(20)

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
            # only accumulate for projects in our config
            if project_name in bitbar_projects:
                accumulation_dict[project_name].append(item)

        # replace current values with what we got above
        for project_name in bitbar_projects:
            stats = CACHE['projects'][project_name]['stats']
            lock = CACHE['projects'][project_name]['lock']
            with lock:
                bitbar_test_runs[project_name] = accumulation_dict[project_name]

                stats['RUNNING'] = 0
                stats['WAITING'] = 0
                for test_run in bitbar_test_runs[project_name]:
                    test_run_state = test_run['state']
                    stats[test_run_state] += 1

                stats['IDLE'] = (stats['COUNT'] -
                                stats['DISABLED'] -
                                stats['OFFLINE'] -
                                stats['RUNNING'])
                if stats['IDLE'] < 0:
                    stats['IDLE'] = 0

    def run(self):
        projects_config = CONFIG['projects']
        CONFIG['threads'] = []

        active_job_thread = threading.Thread(target=self.thread_active_jobs, name='active_jobs', args=())
        logger.info('test-run-manager: loading existing runs')
        active_job_thread.start()
        CONFIG['threads'].append(active_job_thread)
        time.sleep(2)

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

            # prepopulate stats
            self.get_bitbar_test_stats(project_name, projects_config[project_name])
            time.sleep(1)

            # multithread handle_queue
            # TODO: should name be project_name or device group name?
            t1 = threading.Thread(target=self.handle_queue, name=project_name, args=(project_name, projects_config,))
            CONFIG['threads'].append(t1)
            t1.start()

        # we need the main thread to keep running so it can handle signals
        # - https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/
        lock = CACHE['projects'][project_name]['lock']
        while self.state == 'RUNNING':
            time.sleep(60)
            logger.info('getting stats for all projects')
            for project_name in projects_config:
                if project_name == 'defaults':
                    continue
                with lock:
                    self.get_bitbar_test_stats(project_name, projects_config[project_name])
                time.sleep(1)
        logger.info('main thread exiting')
