#!/bin/bash
pip install -q -r requirements.txt
pip install -q -r test_requirements.txt

nosetests --with-coverage --cover-package=testwithbaton --cover-html