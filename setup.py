from setuptools import setup, find_packages

setup(
    name="test-with-baton",
    version="1.1.0",
    author="Colin Nolan",
    author_email="colin.nolan@sanger.ac.uk",
    packages=find_packages(exclude=["tests"]),
    url="https://github.com/wtsi-hgi/test-with-baton",
    license="LICENSE.txt",
    description="Simplifying the testing of software that depends on baton.",
    long_description=open("README.md").read(),
    install_requires=[x for x in open("requirements.txt").read().splitlines() if "://" not in x],
    dependency_links=[x for x in open("requirements.txt").read().splitlines() if "://" in x],
    test_suite="testwithbaton.tests"
)
