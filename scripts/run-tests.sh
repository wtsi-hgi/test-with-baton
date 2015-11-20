#!/bin/bash
# Run Python unit tests
pip install -q -r requirements.txt
pip install -q -r test_requirements.txt

nosetests -v