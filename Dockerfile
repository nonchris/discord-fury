ARG ARCH=
FROM ${ARCH}python:3.8

RUN apt-get update && apt-get -y upgrade && apt-get install -y \
    python3-pip


VOLUME /app/
WORKDIR /app

COPY src/* /app/
RUN python3 -m pip install -r /app/requirements.txt

VOLUME /app/cogs
COPY src/cogs/ /app/cogs/

COPY ./entrypoint.sh /
ENTRYPOINT ["sh", "/entrypoint.sh"]
