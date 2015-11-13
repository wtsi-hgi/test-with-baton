# Test with baton
Simplifying the testing of software that depends on baton.


```bash
test_with_baton = setup_test_with_baton()
test_with_baton.setup()

baton_binaries_location = test_with_baton.get_baton_binaries_location()
# Do stuff with containerised baton via "proxies" in the `baton_binaries_location` directory.

test_with_baton.tear_down()
```