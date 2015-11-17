from setuptools import setup, find_packages

setup(
    name="test-with-baton",

    version="0.1.0",

    author="Colin Nolan",
    author_email="hgi@sanger.ac.uk",

    packages=find_packages(exclude=["tests"]),

    url="https://github.com/wtsi-hgi/test-with-baton",

    license="LICENSE",

    description="Simplifying the testing of software that depends on baton.",
    long_description=open("README.md").read(),

    install_requires=open("requirements.txt").read().splitlines(),

    test_suite="sequencescape.tests"
)
