ARG ARCH=
FROM ${ARCH}ubuntu:20.04

COPY ./Dockerfile.yml /root/.ansible/site.yml

RUN apt update && \
    apt install -y ansible aptitude python3-apt && \
    ansible-playbook /root/.ansible/site.yml && \
    apt-get remove -y --purge ansible python3-apt && \
    apt-get autoremove -y && \
    apt-get autoclean && \
    apt-get clean

VOLUME /app/
WORKDIR /app

COPY src/* /app/
RUN python3 -m pip install -r /app/requirements.txt

VOLUME /app/cogs
COPY src/cogs/ /app/cogs/

COPY ./entrypoint.sh /
ENTRYPOINT ["sh", "/entrypoint.sh"]
