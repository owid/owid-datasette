FROM ubuntu:22.10

# Version of Datasette to install, e.g. 0.55
#   docker build . -t datasette --build-arg VERSION=0.55
ARG VERSION=0.64.1

RUN apt-get update && \
    apt-get -y --no-install-recommends install wget python3 python3-pip libsqlite3-mod-spatialite lzma && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ADD docker-entrypoint.sh docker-entrypoint.sh
ADD requirements.txt requirements.txt
ADD metadata.yml metadata.yml
ADD static-files static-files

RUN pip install https://github.com/simonw/datasette/archive/refs/tags/${VERSION}.zip && \
    rm -rf /root/.cache/pip

RUN pip install -r requirements.txt

EXPOSE 8001
CMD ["/bin/bash", "docker-entrypoint.sh"]
