#!/bin/bash
FILE=""
DIR="/app/data"
if [ "$(ls -A $DIR)" ]; then
     echo "$DIR is not Empty. Userdata allready there."
else
    echo "$DIR is Empty. Example data is being copied"
    cp /app/config.py.example /app/data/config.py
    echo "Please fill up the example file mounted to your container. Container is being restarted in 30 seconds"
    sleep 30
fi

# Set groups and permissions
groupadd python -g ${GID:-1000}
useradd -u ${UID:-1000} -g ${GID:-1000} python
chown -R  python:python /app

su python -c 'python3 fury-bot.py'
