# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import requests

def get_taskcluster_pending_tasks(provisioner_id, worker_type):
    taskcluster_queue_url = 'https://queue.taskcluster.net/v1/pending/%s/%s' % (
        provisioner_id, worker_type)
    r = requests.get(taskcluster_queue_url)
    if r.ok:
        return r.json()['pendingTasks']
    return 0


