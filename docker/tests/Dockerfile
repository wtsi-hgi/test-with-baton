FROM python:3.5
MAINTAINER Colin Nolan <hgi@sanger.ac.uk>

COPY . /test-with-baton
WORKDIR test-with-baton

RUN ./scripts/pip-install-requirements.sh

CMD ["./scripts/run-tests.sh"]