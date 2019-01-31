# mozilla-bitbar-devicepool

This project supports the execution of Mozilla's Android Hardware tests
at [Bitbar](https://bitbar.com/).

Bitbar Projects and Device Groups will be created or updated as needed
to match the specified configuration.

Bitbar Frameworks must be managed via the Testdroid user interface.

## Installation

```
# Clone the repository
git clone https://github.com/bclary/mozilla-bitbar-devicepool.git
cd mozilla-bitbar-devicepool

# Create a Python virtual environment
python -m virtualenv venv

# Activate the virtual environment
. venv/bin/activate

# Install the requirements
pip install -r requirements.txt
```

## Configuration

Configuring mozilla-bitbar-devicepool requires creating environment
variables and a yaml configuration file for Bitbar.

### Environment Variables

```
export TESTDROID_URL=https://mozilla.testdroid.com
export TESTDROID_APIKEY=<testdroid apikey>
export <taskcluster worker type>=<taskcluster access token for worker type>
...
```

where `TESTDROID_URL` is the url of the Mozilla instance of the Bitbar
cloud service and `TESTDROID_APIKEY` is the access token for the
account under which tests will be executed.

For each Taskcluster worker type defined for Bitbar tests, an
environment variable whose name is constructed from the actual
workerType by replacing any dashes `-` with underscores `_` and whose
value is set to the Taskcluster access token for the corresponding
Taskcluster client.

The [Service Installation](#Service Installation) assumes these
environment variables are stored in `/etc/bitbar/bitbar.env`.

### Bitbar Configuration

The Bitbar configuration is specified as a YAML file with the
following layout:

<pre>
# The projects section contains definitions for each of the projects
# defined for mozilla-bitbar-devicepool. Each subsection of projects
# consists of a project name followed by the project properties.
projects:
  # defaults is a special project name which is used to define
  # properties which will be set on the other projects. This
  # allows common properties to be specified once for defaults
  # rather than having to specify them for each individual project.
  # If a project also defines the same property, it will override
  # the default value.
  defaults:
    os_type: ANDROID
    project_type: APPIUM_ANDROID_SERVER_SIDE
    # Files should have unique names which prevent collisions
    # with files from other users. These examples use a prefix
    # to distinguish them.
    application_file: bclary-Testdroid.apk
    test_file: bclary-empty-test.zip
    timeout: 0
    scheduler: SINGLE
    archivingStrategy: DAYS
    archivingItemCount: 365
    taskcluster_provisioner_id: proj-autophone
    # additional_parameters specify a set of environment
    # variables which will be passed to the Docker container
    # executing the test.
    additional_parameters:
      bitbar_cloud_url: https://mozilla.testdroid.com
      DOCKER_IMAGE_VERSION: 20190109T064727
      TC_WORKER_CONF: gecko-t-ap
  # Each Bitbar project has its own section.
  mozilla-unittest-p2:
    device_group_name: pixel2-unit
    device_model: pixel2
    framework_name: mozilla-usb
    description: Mozilla Unit tests for Pixel2
    additional_parameters:
      TASKCLUSTER_CLIENT_ID: project/autophone/bitbar-x-unit-p2
      TC_WORKER_TYPE: gecko-t-ap-unit-p2
  #...
# The device-groups section contains definitions for each of the
# device groups. Each subsection of device_groups contains sections
# which list the names of the devices assigned to the device group.
device_groups:
  motog4-docker-builder:
    Docker Builder:
  motog5-batt:
    motog5-08:
    motog5-15:
  motog5-perf:
  #...
</pre>

## Usage

### Main

The `main.py` script is used to perform tasks related to running
the Mozilla Android Hardware tests. It is implemented using `sub-command`
arguments.

```
$ python main.py --help
usage: main.py [-h] [--files FILES]
               [--log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG}]
               {download-testdroid-apk,empty-test-zip,start-test-run-manager,run-test}
               ...

Mozilla Android Hardware testing at Bitbar.

positional arguments:
  {download-testdroid-apk,empty-test-zip,start-test-run-manager,run-test}
                        Specify one of the positional arguments to select the
                        command to execute.
    download-testdroid-apk
                        Download Testdroid.apk from https://github.com/bitbar
                        /bitbar-samples/blob/master/apps/builds/Testdroid.apk
                        to files/ then exit.
    empty-test-zip      Generate empty test zip file in files/ directory then
                        exit.
    start-test-run-manager
                        Run the test run manager.
    run-test            Run test for a project then exit.

optional arguments:
  -h, --help            show this help message and exit
  --files FILES         Directory where downloaded files are saved. Defaults
                        to /home/bclary/mozilla/projects/android-hardware-
                        testing/github.com/bclary/mozilla-bitbar-
                        devicepool/files
  --log-level {CRITICAL,ERROR,WARNING,INFO,DEBUG}
                        Logging level. Defaults to INFO.

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
```

### download-testdroid-apk

The Bitbar tests require an Android application apk be specified even
though it is not used in the current tests. The `download-testdroid-apk`
sub-command downloads the Testdroid.apk sample application and saves it
to the `files/` directory. You can specify a unique name to prevent name
collisions with files from other users.

```
$ python main.py download-testdroid-apk --help
usage: main.py download-testdroid-apk [-h] [--filename FILENAME] [--force]

optional arguments:
  -h, --help           show this help message and exit
  --filename FILENAME  Specify filename to save Testdroid.apk to in the files
                       directory.
  --force              Overwrite existing file.

```

### empty-test-zip

The Bitbar tests require a zip test file be specified. The only
project which currently uses a non-empty test zip file is the
`mozilla-docker-build` project.  The `empty-test-zip` sub-command
create an empty zip file in the `files/` directory. You can specify a
unique name to prevent name collisions with files from other users.

```
$ python main.py empty-test-zip --help
usage: main.py empty-test-zip [-h] [--filename FILENAME]

optional arguments:
  -h, --help           show this help message and exit
  --filename FILENAME  Specify filename to save in the files directory.
                       Defaults to empty-test.zip.
```

### start-test-run-manager

The sub-command `start-test-run-manager` starts a long running process
which polls the Taskcluster queues for the worker types specified in
the configuration for pending tasks and starts a corresponding Bitbat
test run to service the task.

```
$ python main.py start-test-run-manager --help
usage: main.py start-test-run-manager [-h] [--bitbar-config BITBAR_CONFIG]
                                      [--wait WAIT] [--delete-bitbar-tests]

optional arguments:
  -h, --help            show this help message and exit
  --bitbar-config BITBAR_CONFIG
                        Path to Bitbar yaml configuration file.
  --wait WAIT           Seconds to wait between checks. Defaults to 60.
  --delete-bitbar-tests
                        Delete bitbar tests after finishing. Defaults to
                        False.
```

### run-test

The sub-command `run-test` is used to start a single test at Bitbar
for a project. The primary use for this command apart from one-off
test runs, is to execute test runs for the `mozilla-docker-build`
project which creates a new Docker image for use in further testing.

```
$ python main.py run-test --help
usage: main.py run-test [-h] --project_name PROJECT_NAME

optional arguments:
  -h, --help            show this help message and exit
  --project_name PROJECT_NAME
                        Specify a project name for which to start a test.
```

### Service Installation

These instructions assume that you will be setting up the
mozilla-bitbar-devicepool to run as a systemd service.

Customize [bitbar.service](service/bitbar.service) to fit the
location where you will install mozilla-bitbar-devicepool. By default,
it assumes it will be installed into the `/home/bitbar` directory.

It uses the `start_android_hardware_testing.sh` and
`stop_android_hardware_testing.sh` scripts in the `bin` directory to
start and stop the test run manager.

```
sudo cp service/bitbar.service /etc/systemd/system/
sudo chmod 664 /etc/systemd/system/bitbar.service
sudo systemctl daemon-reload
```

Start the bitbar.service

```
systemctl start bitbar.service
```

Enable the bitbar.service to start on boot.

```
systemctl enable bitbar.service
```

### Service Logs

To follow the log output of the bitbar service

```
sudo journalctl _SYSTEMD_UNIT=bitbar.service --follow
```
