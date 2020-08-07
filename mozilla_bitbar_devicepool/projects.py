# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mozilla_bitbar_devicepool import (
    TESTDROID,
    get_filter,
)


def get_projects(**kwargs):
    """Return list of matching Bitbar projects.

    :param **kwargs: keyword arguments containing fieldnames and
                     values with which to filter the projects to
                     be returned. If a fieldname is missing, it is
                     not used in the filter.
                     {
                       'frameworkid': int,
                       'id': int,
                       'name': str,
                       'ostype': str,
                     }

    Examples:
       get_projects() # Return all projects
       get_projects(name='mozilla-unittests-p2')
    """
    fields = {
        "frameworkid": int,
        "id": int,
        "name": str,
        "ostype": str,
    }

    filter = get_filter(fields, **kwargs)
    response = TESTDROID.get("/api/v2/projects", payload={"limit": 0, "filter": filter})
    # remove the archived projects
    projects = [
        project for project in response["data"] if project["archiveTime"] is None
    ]
    return projects


def get_project(id):
    """Return Bitbar project with specified id.

    :param id: integer id of project to be returned.

    Examples:
       get_project(1) # Return project with id 1
    """
    response = TESTDROID.get(
        "/api/v2/projects/{}".format(id), payload={"limit": 0, "filter": filter}
    )
    return response


def create_project(name, project_type="GENERIC"):
    """Create a project.

    :param name: name for the project.
    :param project_type: project type. One of
        ANDROID, IOS, UIAUTOMATOR, CALABASH, CALABASH_IOS, XCTEST, XCUITEST,
        APPIUM_ANDROID, APPIUM_ANDROID_SERVER_SIDE, APPIUM_IOS,
        APPIUM_IOS_SERVER_SIDE, GENERIC


    Examples:
       create_project('test-project')
    """
    me = TESTDROID.get_me()
    payload = {
        "name": name,
        "type": project_type,
    }

    response = TESTDROID.post(
        path="/users/{}/projects".format(me["id"]), payload=payload
    )
    return response


def update_project(
    id, name, archiving_item_count=365, archiving_strategy="DAYS", description=None
):
    """Update a project.

    :param id: integer id of project.
    :param archiving_item_count: integer number of archiving_strategy before project is archived.
    :param archiving_strategy: string. One of NEVER, DAYS, RUNS.
    :param description: string description of project.
    :param name: name for the project.


    Examples:
       update_project(250331, 'mozilla-batttest-p2',
                     archiving_item_count=365,
                     archiving_strategy='DAYS',
                     description='Mozilla battery test project for Pixel 2')

    https://mozilla.testdroid.com/cloud/swagger-ui.html#/Project/updateUserProjectUsingPOST
    """
    me = TESTDROID.get_me()
    payload = {
        "archivingItemCount": archiving_item_count,
        "archivingStrategy": archiving_strategy,
        "description": description,
        "name": name,
    }

    response = TESTDROID.post(
        path="/users/{}/projects/{}".format(me["id"], id), payload=payload
    )
    return response


def get_project_test_run_config_parameters(id):
    """Get Project test run config parameters.

    We will primarily set the test run config parameters on demand
    with mozilla_bitbar_devicepool.runs.run_test_with_configuration()
    as this alleviates dealing with parameters will null parameterIds.

    :param id: integer id for the project.

    Examples:
       get_project_test_run_config_parameters(250331)

    """
    me = TESTDROID.get_me()
    payload = {
        "limit": 0,
    }

    response = TESTDROID.get(
        path="/api/v2/users/{}/projects/{}/config/parameters".format(me["id"], id),
        payload=payload,
    )
    return response["data"]


def add_project_test_run_config_parameter(id, key, value):
    """Add Project test run config parameter.

    :param id: integer id for the project.
    :param key: string name for parameter.
    :param value: string value for parameter.

    Examples:
       add_project_test_run_config_parameters(250331)
    """
    me = TESTDROID.get_me()
    payload = {
        "key": key,
        "value": value,
    }

    response = TESTDROID.post(
        path="/users/{}/projects/{}/config/parameters".format(me["id"], id),
        payload=payload,
    )
    return response


def delete_project_test_run_config_parameter(id, parameter_id):
    """Delete Project test run config parameter.

    :param id: integer id for the project.
    :param parameter_id: integer id for parameter.

    Note this will not work for parameters that have been stored with
    a null id.

    Examples:
       delete_project_test_run_config_parameters(250331, 334343)

    """
    me = TESTDROID.get_me()

    TESTDROID.delete(
        path="/users/{}/projects/{}/config/parameters/{}".format(
            me["id"], id, parameter_id
        )
    )
