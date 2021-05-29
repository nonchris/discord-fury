#!/bin/bash

# Set groups and permissions
groupadd python -g ${GID:-1000}
useradd -u ${UID:-1000} -g ${GID:-1000} python
chown -R  python:python /app

su python -c 'python3 fury-bot.py'
