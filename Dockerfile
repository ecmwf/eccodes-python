# Run tests in a more reproducible and isolated environment.
#
# Build the docker image once with:
#   docker build -t eccodes .
# Run the container with:
#   docker run --rm -it -v `pwd`:/src eccodes-python
#
FROM bopen/ubuntu-pyenv:latest

ARG DEBIAN_FRONTEND="noninteractive"

RUN apt-get -y update && apt-get install -y --no-install-recommends \
        libeccodes0 \
 && rm -rf /var/lib/apt/lists/*

COPY . /src/

RUN cd /src \
    && make local-install-test-req \
    && make local-develop \
    && make local-install-dev-req \
 && make distclean

WORKDIR /src
