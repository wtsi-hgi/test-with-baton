[![Build Status](https://travis-ci.org/wtsi-hgi/test-with-baton.svg)](https://travis-ci.org/wtsi-hgi/test-with-baton)
[![codecov.io](https://codecov.io/github/wtsi-hgi/test-with-baton/coverage.svg?branch=master)](https://codecov.io/github/wtsi-hgi/test-with-baton?branch=master)

# Test with baton
Test with baton exploits [Docker](http://docker.com) to simplify the testing of software that depends on
[baton](https://github.com/wtsi-npg/baton).


## Introduction
Compiling and configuring both baton and iRODS is non-trivial task. This software has been created to manage this
automatically, leaving the developer with baton-like binaries<sup>*</sup> that have been pre-configured to work with an
a clean iRODS installation (pre-existing iRODS installations can be used if required). These binaries can then be
used in the testing of software that depends on baton or for just seeing how iRODS and baton work in a safe environment.

Thanks to the use [wtsi-hgi's baton Docker image](https://github.com/wtsi-hgi/docker-baton) and
[wtsi-hgi's iRODS server Docker image](https://hub.docker.com/r/mercury/icat), the configuration of the test machine
is not changed upon use of this software. 

By default, a new iRODS server (running in Docker on an unused port), with a clean database, is used. If this fresh
setup is exploited in each test case, a known test environment is ensured, thus reducing the "flakiness" of your tests.
However, if desired, a pre-existing iRODS setup can be used.

Each setup creates baton-like binaries<sup>*</sup> that are linked to the iRODS server. Therefore, tests cases may be
ran in parallel without interference between them. icommands connected to the same iRODS server are also make available.

<i><sup>*</sup> These binaries are not the real baton binaries, as baton is run inside a Docker image; they are instead
transparent "proxies" to the real binaries. However, they produce the same results and therefore are indistinguishable
in the eyes of the SUT to a real baton installation.</i>


## How to use in your project
**A correctly configured Docker daemon must be running on your machine!**
(If you do not know whether this is the case, try running `docker ps` via the command line.)


### With Python
#### Including the `testwithbaton` library
In ``/test_requirements.txt`` or in your ``/setup.py`` script:
```
git+https://github.com/wtsi-hgi/test-with-baton.git@master#egg=testwithbaton
```
*See more information about how to use packages not on PyPI in [this documentation about specifying dependencies]
(http://python-packaging.readthedocs.org/en/latest/dependencies.html#packages-not-on-pypi).*

#### API
Basic usage:
```python
from testwithbaton.api import TestWithBatonSetup

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
from testwithbaton.api import TestWithBatonSetup
from testwithbaton.models import IrodsServer, IrodsUser

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
from testwithbaton.api import TestWithBatonSetup, get_irods_server_from_environment_if_defined

# Pre-existing iRODS server used if all of the following environment variables are set:
# IRODS_HOST, IRODS_PORT, IRODS_USERNAME, IRODS_PASSWORD, IRODS_ZONE
test_with_baton = TestWithBatonSetup(get_irods_server_from_environment_if_defined())
test_with_baton.setup()
```

To help with the setup of tests, a number of Python setup helper methods are available:
```python
from testwithbaton.helpers import SetupHelper, AccessLevel
from testwithbaton.models import IrodsResource
from testwithbaton.collections import Metadata

setup_helper = SetupHelper("icommands_location")
setup_helper.create_data_object("name", contents="contents")   # type: str
setup_helper.replicate_data_object("/path/to/data_object, "resourceName")
setup_helper.create_collection("name")   # type: str
setup_helper.add_metadata_to("/path/to/entity", Metadata({"attribute": "value"})
setup_helper.get_checksum("/path/to/entity")   # type: str
setup_helper.create_replica_storage()   # type: IrodsResource
setup_helper.create_user("username", "zone")    # type: IrodsUser
setup_helper.set_access("username_or_group", level: AccessLevel.OWN, "/path/to/entity")
setup_helper.run_icommand(["icommand_binary", "--any", "arguments"])    # type: str
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
