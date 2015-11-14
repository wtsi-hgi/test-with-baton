# Test with baton
Simplifying the testing of software that depends on [baton](https://github.com/wtsi-npg/baton).


## Introduction
Compiling and configuring both baton and an iRODS server is not a trivial task. This software has been created to manage
all of this and leave the developer with a directory containing baton binaries<sup>*</sup>, configured to use an empty
iRODS database. These binaries can then be exploited in the testing of software that uses baton. 

Thanks to the use [wtsi-hgi's baton Docker image](https://github.com/wtsi-hgi/docker-baton) and
[agaveapi's iRODS server Docker image](https://hub.docker.com/r/agaveapi/irods/), the configuration of the test machine
is not changed and setups can be simply thrown away after use. If a fresh setup, with a clean database, is used for each
test case, a clean test environment is ensured, thus reducing the "flakiness" of your tests.
 
Each setup creates baton binaries<sup>*</sup> that are linked to a different iRODS server (running on an unused port).
Therefore, tests cases may be ran in parallel without fear of interference between them.


## How to use in your project
** A correctly configured Docker daemon must be running on your machine! **
(If you do not know whether this is the case, try running `docker ps` (for example) via the command line.)

### Python API
```bash
# Setup environment to test with baton - this could take a while on the first run (anticipate up to 10 minutes)!
# Thanks to Docker's caching systems it should only take a couple of seconds after the first run
test_with_baton = setup_test_with_baton()

baton_binaries_location = test_with_baton.get_baton_binaries_location()
# Do stuff with containerised baton via "proxies" in the `baton_binaries_location` directory.

# Important: remember to tear down! Failure to do so will not kill the Docker daemon running the iRODS test server
test_with_baton.tear_down()
```

### Running via the command line
*TODO*


### Known issues
[Issue 1](https://github.com/wtsi-hgi/test-with-baton/issues/1): It is currently hardcoded to use
[baton version 0.16.1](https://github.com/wtsi-npg/baton/tree/release-0.16.1) and
[iRODS version 3.3.1](https://github.com/irods/irods-legacy).
