import os
import logging


### @package environment
#
# Interactions with the environment variables.
#


def load_env(key: str, default: str) -> str:
    """!
    os.getenv() wrapper that handles the case of None-types for not-set env-variables\n

    @param key: name of env variable to load
    @param default: default value if variable couldn't be loaded
    @return value of env variable or default value
    """
    value = os.getenv(key)
    if value:
        return value

    logger.warning(f"Can't load env-variable for: '{key}' - falling back to DEFAULT {key}='{default}'")
    return default


logger = logging.getLogger('my-bot')

TOKEN = os.getenv("TOKEN")  # reading in the token from environment 

# loading optional env variables
PREFIX = load_env("PREFIX", "f!")
MAX_PREFIX_LENGTH = int(load_env("MAX_PREFIX_LENGTH", "3"))  # length including the non-letter char
VERSION = load_env("VERSION", "unknown")  # version of the bot
OWNER_NAME = load_env("OWNER_NAME", "unknown")  # owner name with tag e.g. pi#3141
OWNER_ID = int(load_env("OWNER_ID", "100000000000000000"))  # discord id of the owner
CHANNEL_TRACK_LIMIT = int(load_env("CHANNEL_TRACK_LIMIT", "20"))  # how many channels tracked per guild

# probably temporary for migration only
# switch that contains emote IDs for online status display
EMOTE_SWITCH = {
    "online": 314159265358979323,
    "idle": 314159265358979323,
    "dnd": 314159265358979323,
    "offline": 314159265358979323,
    "mobile": 314159265358979323,  # gained trough that keyword no status
}
