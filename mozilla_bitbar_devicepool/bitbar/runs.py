# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from mozilla_bitbar_devicepool import (
    TESTDROID,
    configuration,
)


def run_test_with_configuration(test_configuration):
    """Run a test on demand with full configuration.

    Examples:
       run_test_with_configuration(test_configuration)
    """

    response = TESTDROID.post(
        path="runs",
        payload=json.dumps(test_configuration),
        headers={"Content-type": "application/json", "Accept": "application/json"},
    )
    return response


def run_test_for_project(project_name):
    CACHE = configuration.BITBAR_CACHE
    CONFIG = configuration.CONFIG

    bitbar_test_file = None
    bitbar_application_file = None
    project_config = CONFIG["projects"][project_name]

    test_configuration = {
        "frameworkId": CACHE["frameworks"][project_config["framework_name"]]["id"],
        "osType": project_config["os_type"],
        "projectId": CACHE["projects"][project_name]["id"],
        "scheduler": project_config["scheduler"],
        "timeout": project_config["timeout"],
        "deviceGroupId": CACHE["device_groups"][project_config["device_group_name"]][
            "id"
        ],
        "testRunParameters": [],
        "files": [],
    }

    if "test_file" in project_config:
        test_file = project_config["test_file"]
        bitbar_test_file = CACHE["files"][test_file]
        test_configuration["files"].append(
            {"id": bitbar_test_file["id"], "action": "RUN_TEST"}
        )
    if "application_file" in project_config:
        application_file = project_config["application_file"]
        bitbar_application_file = CACHE["files"][application_file]
        test_configuration["files"].append(
            {"id": bitbar_application_file["id"], "action": "INSTALL"}
        )

    additional_parameters = project_config["additional_parameters"]
    for parameter_name in additional_parameters:
        parameter_value = additional_parameters[parameter_name]
        test_configuration["testRunParameters"].append(
            {"key": parameter_name, "value": parameter_value}
        )

    return run_test_with_configuration(test_configuration)


def get_test_run(project_id, test_run_id):
    data = TESTDROID.get_test_run(project_id, test_run_id)
    return data


def get_test_runs(project_id, active=None):
    test_runs = TESTDROID.get_project_test_runs(project_id)["data"]
    if active:
        test_runs = [run for run in test_runs if run["state"] in ("WAITING", "RUNNING")]
    else:
        test_runs = [
            run for run in test_runs if run["state"] not in ("WAITING", "RUNNING")
        ]
    return test_runs


def delete_test_run(project_id, test_run_id):
    me = TESTDROID.get_me()
    path = "/users/%s/projects/%s/runs/%s" % (me["id"], project_id, test_run_id)
    data = TESTDROID.delete(path=path)
    return data


def abort_test_run(project_id, test_run_id):
    return TESTDROID.abort_test_run(project_id, test_run_id)


# https://mozilla.testdroid.com/cloud/api/v2/admin/runs?filter=d_endTime_isnull&limit=0
def get_active_test_runs(**kwargs):
    """Gets active test runs.
    """
    response = TESTDROID.get("/api/v2/admin/runs?filter=d_endTime_isnull&limit=0")
    return response["data"]
