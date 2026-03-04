# Run tests in a more reproducible and isolated environment.
#
# Build the docker image once with:
#   docker build -t eccodes .
# Run the container with:
#   docker run --rm -it -v `pwd`:/src eccodes-python
#
FROM python:3.9-slim

ARG DEBIAN_FRONTEND="noninteractive"

RUN apt-get -y update && apt-get install -y --no-install-recommends \
        build-essential \
        libeccodes0 \
 && rm -rf /var/lib/apt/lists/*

COPY . /src/

RUN --mount=type=cache,target=/root/.cache/pip cd /src \
    && pip install --upgrade pip \
    && make local-install-test-req \
    && make local-develop \
    && make local-install-dev-req \
 && make distclean

WORKDIR /src
