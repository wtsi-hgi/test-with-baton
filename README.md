# Test with baton
Simplifying the testing of software that depends on [baton](https://github.com/wtsi-npg/baton).


## Introduction
Compiling and configuring both baton and an iRODS server is not a trivial task. This software has been created to manage
all of this and leave the developer with a directory containing baton binaries<sup>*</sup>, configured to use an empty
iRODS database by default. These binaries can then be exploited in the testing of software that uses baton or just
seeing how iRODS and baton work in a safe environment.

Thanks to the use [wtsi-hgi's baton Docker image](https://github.com/wtsi-hgi/docker-baton) and
[agaveapi's iRODS server Docker image](https://hub.docker.com/r/agaveapi/irods/), the configuration of the test machine
is not changed upon use of this software. 

By default, a new iRODS server (running in Docker on an unused port), with a clean database, is used. If this fresh
setup is exploited for each test case, a known test environment is ensured, thus reducing the "flakiness" of your tests.
However, if desired, a pre-existing iRODS setup can be used.

Each setup creates baton binaries<sup>*</sup> that are linked to the iRODS server. Therefore, tests cases may be ran in
parallel without fear of interference between them.

<i><sup>*</sup> These binaries are not the real baton binaries, as baton is run inside a Docker image; they are instead
transparent "proxies" to the real binaries. However, they produce the same results and therefore are indistinguishable
in the eyes of the SUT to a real baton installation.</i>


## How to use in your project
**A correctly configured Docker daemon must be running on your machine!**
(If you do not know whether this is the case, try running `docker ps` via the command line.)


### With Python
#### Including the `testwithbaton` library
In ``/requirements.txt`` or in your ``/setup.py`` script:
```
git+https://github.com/wtsi-hgi/test-with-baton.git@master#egg=testwithbaton
```
*See more about using libraries for git repositories in the 
[pip documentation](https://pip.readthedocs.org/en/1.1/requirements.html#git).*

#### API
Basic usage:
```python
from testwithbaton import TestWithBatonSetup

# Setup environment to test with baton - this could take a while on the first run (anticipate more than 2 minutes)!
# Thanks to Docker's caching systems it should only take a couple of seconds after the first run
test_with_baton = TestWithBatonSetup()
test_with_baton.setup()

baton_location = test_with_baton.baton_location
icommands_location = test_with_baton.icommands_location
# Do stuff with containerised baton via "proxies" in the `baton_location` directory. Can also use icommands

# Tear down tests. `TestWithBatonSetup` uses `atexit` (https://docs.python.org/3/library/atexit.html) in the attempt to
# ensure this is always done eventually, even if forgotten about/a failure occurs
test_with_baton.tear_down()
```

It is possible to use a pre-existing iRODS server in tests. This will make it quicker to run tests but the state of the
environment that they run in can no longer be guaranteed, potentially making your tests flaky.
```python
from testwithbaton import TestWithBatonSetup, IrodsServer, IrodsUser

# Define the configuration of the pre-existing iRODS server
irods_server = IrodsServer("host", "port", [IrodsUser("username", "password", "zone")])

# Setup test with baton
test_with_baton = TestWithBatonSetup(irods_server)
test_with_baton.setup()

# Do testing
```

In addition, a pre-existing iRODS server, defined through environment variables, can be optionally used if setup. This
could be useful to speed up the running of tests during development but can be "turned off" during CI testing, with no
additional code.
```python 
from testwithbaton import TestWithBatonSetup, get_irods_server_from_environment_if_defined

# Pre-existing iRODS server used if all of the following environment variables are set:
# IRODS_HOST, IRODS_PORT, IRODS_USERNAME, IRODS_PASSWORD, IRODS_ZONE
test_with_baton = TestWithBatonSetup(get_irods_server_from_environment_if_defined())
test_with_baton.setup()
```

To help with the setup of tests, a number of Python setup helper methods are available:
```python
from testwithbaton import SetupHelper
from hgicommon.models import File

setup_helper = SetupHelper("icommands_location")
setup_helper.create_irods_file("file_name", file_contents="contents")
setup_helper.create_irods_collection("collection_name")
setup_helper.add_irods_metadata_to_file(File("directory", "filename"), Metadata("attribute", "value")
setup_helper.get_checksum(File("file_directory", "file_name"))
setup_helper.run_icommand("icommand_binary", command_arguments=["any", "arguments"], error_if_stdout=False)
```


### Elsewhere
To use outside of Python, run (from the repository's root directory) with:
```bash
pip3 install -r requirements.txt
PYTHONPATH=. python3 testwithbaton/main.py
``` 

The program will setup and then output (on one line):
```json
{
    "baton": "<baton_location>",
    "icommands": "<icommands_location>"
}
```

It will then block, keeping the test environment alive, until it receives a `SIGHUP` signal. Upon receipt of this
signal, the test environment is torn down and then the program will exit.


### Setting up with PyCharm IDE
The environment must be [setup for configurations in PyCharm]
(https://www.jetbrains.com/pycharm/help/run-debug-configuration-python.html#d427982e277) that run projects that use
`testwithbaton` in order for Docker to be used. In particular, `DOCKER_TLS_VERIFY`, `DOCKER_HOST` and `DOCKER_CERT_PATH`
must be set. For example, the configuration's environment variables may include:
```
DOCKER_TLS_VERIFY=1
DOCKER_HOST=tcp://192.168.99.100:2376
DOCKER_CERT_PATH=/Users/you/.docker/machine/machines/default
```
