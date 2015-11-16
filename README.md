# Test with baton
Simplifying the testing of software that depends on [baton](https://github.com/wtsi-npg/baton).


## Introduction
Compiling and configuring both baton and an iRODS server is not a trivial task. This software has been created to manage
all of this and leave the developer with a directory containing baton binaries<sup>*</sup>, configured to use an empty
iRODS database. These binaries can then be exploited in the testing of software that uses baton. 

Thanks to the use [wtsi-hgi's baton Docker image](https://github.com/wtsi-hgi/docker-baton) and
[agaveapi's iRODS server Docker image](https://hub.docker.com/r/agaveapi/irods/), the configuration of the test machine
is not changed upon use of this software. Futhermore, setups can be simply thrown away after use. If a fresh setup, with
a clean database, is used for each test case, a known test environment is ensured, thus reducing the "flakiness" of your
tests.

Each setup creates baton binaries<sup>*</sup> that are linked to a new iRODS server (running in Docker on an unused
port). Therefore, tests cases may be ran in parallel without fear of interference between them.

<i><sup>*</sup> These binaries are not the real baton binaries, as baton is run inside a Docker image; they are instead
transparent "proxies" to the real binaries. However, they produce the same results and therefore are indistinguishable
to the SUT to a real baton installation.</i>


## How to use in your project
**A correctly configured Docker daemon must be running on your machine!**
(If you do not know whether this is the case, try running `docker ps` via the command line.)

### Python API
```bash
from testwithbaton import create_test_with_baton, TestWithBatonSetup

# Setup environment to test with baton - this could take a while on the first run (anticipate up to 10 minutes)!
# Thanks to Docker's caching systems it should only take a couple of seconds after the first run
test_with_baton = create_test_with_baton()

baton_location = test_with_baton.get_baton_binaries_location()
icommands_location = test_with_baton.get_baton_binaries_location()
# Do stuff with containerised baton via "proxies" in the `baton_location` directory. Can also use icommands.

# Tear down tests. `TestWithBatonSetup` uses `atexit` (https://docs.python.org/3/library/atexit.html) in the attempt to
# ensure this is always done eventually, even if forgotten about/a failure occurs.
test_with_baton.tear_down()

```

### Running via the command line
To use outside of Python, run with:
```bash
PYTHONPATH=. python3 testwithbaton/testwithbaton.py
``` 

The program will setup and then output (on one line):
```json
{
    "baton": test_with_baton.baton_location,
    "icommands": test_with_baton.icommands_location
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


## Known issues
[Issue 1](https://github.com/wtsi-hgi/test-with-baton/issues/1): It is currently hardcoded to use
[baton version 0.16.1](https://github.com/wtsi-npg/baton/tree/release-0.16.1) and
[iRODS version 3.3.1](https://github.com/irods/irods-legacy).
