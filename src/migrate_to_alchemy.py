import os
import sys
import time
import sqlite3

from datetime import datetime

import log_setup
import database.access_settings_db as settings_db
import database.access_channels_db as channels_db

logger = log_setup.logger

"""
Script for migration of an old v1 style SQLite database into a v2 style SQLAlchemy db
"""

# translate old entry names into new naming scheme
translator = {
    "pub-channel": "public_channel",
    "pub": "public_channel",
    "priv-channel": "private_channel",
    "priv": "private_channel",
    "edit_channel": "allow_public_rename",
    "archive": "archive_category",
    "log": "log_channel",
    "brout": "breakout_room",
}


def split_time(date: str) -> datetime:
    """
    takes date string from old database format, converts it to datetime object

    expected format: "yyyy-mm-dd hh-mm-ss"
    """
    date = date.replace(" ", "-")  # replace space between date and time
    date_split = date.split("-")

    # print(date_split)
    year = int(date_split[0])
    month = int(date_split[1])
    day = int(date_split[2])

    time_split = date_split[3].split(":")
    hour = int(time_split[0])
    minute = int(time_split[1])
    second = int(time_split[2])

    return datetime(year, month, day, hour, minute, second)


def migrate_from_v1(db_path: str):
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # get all tables in database

    logger.info("LOADING ALL TABLES")
    print("LOADING ALL TABLES")

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [e[0] for e in cur.fetchall()]

    # sort tables in categories
    server_tables = []  # names like s714480452240670800
    channel_tables = []  # names like ch714480452240670800

    for table in tables:
        if table.startswith("s"):
            server_tables.append(table)

        elif table.startswith("ch"):
            channel_tables.append(table)

        else:
            logger.error(f"SOMETHING WENT WRONG DURING TABLE COLLECTION! Can't match table: {table}")
            return

    print("MIGRATING SERVER/ SETTINGS TABLES")
    logger.info("MIGRATING SERVER/ SETTINGS TABLES")

    # go over server tables, extract values from columns
    # migrate them into central settings_table

    # example entry:
    # primary key (dropped), setting name, channel_name (never used, dropped), ...
    # ...actual setting, creation date, sql version (dropped)
    # (2, 'priv-channel', 'value_name', 817178514646106142, '2021-03-04 23:36:23', 1)

    settings_count = 0
    for table in server_tables:
        cur.execute(f"SELECT * FROM {table}")
        entries = cur.fetchall()
        for entry in entries:
            guild_id = int(table[1:])
            setting = translator[entry[1]]
            value = int(entry[3])
            set_date = split_time(entry[4])

            # print(guild_id, setting, value, set_date)

            settings_db.add_setting(
                guild_id=guild_id,
                setting=setting,
                value=value,
                active=True,
                set_by="migration_from_v1",
                set_date=set_date
            )
            settings_count += 1

    logger.info("MIGRATING CHANNEL TABLES")
    print("MIGRATING CHANNEL TABLES")

    # go over channel tables, extract values from columns
    # migrate them into central settings_table

    # example entry:
    # channel type, voice channel id, text channel id, creation date, sql version (will be dropped)
    # ('pub', 839424125478240276, 839424126124294145, '2021-05-05 08:51:47', 1)

    channels_count = 0
    for table in channel_tables:
        cur.execute(f"SELECT * FROM {table}")

        entries = cur.fetchall()
        for entry in entries:

            guild_id = int(table[2:])

            ch_type = translator[entry[0]]
            voice_channel = entry[1]
            text_channel = entry[2]
            set_date = split_time(entry[3])

            # print(ch_type, voice_channel, text_channel, set_date)

            channels_db.add_channel(
                voice_channel_id=voice_channel,
                text_channel_id=text_channel,
                guild_id=guild_id,
                internal_type=ch_type,
                set_by="migration_from_v1",
                set_date=set_date
            )
            channels_count += 1

    logger.info("MIGRATION COMPLETED!")
    logger.info(f"MIGRATED {settings_count} settings from {len(server_tables)} tables")
    logger.info(f"MIGRATED {channels_count} channels from {len(channel_tables)} tables")
    print("MIGRATION COMPLETED!")
    print(f"MIGRATED {settings_count} settings from {len(server_tables)} tables")
    print(f"MIGRATED {channels_count} channels from {len(channel_tables)} tables")


if __name__ == '__main__':
    old_path_to_db = os.getenv("OLD_DB_PATH")
    if not old_path_to_db:
        logger.error(f"CANT LOAD PATH TO OLD DATABASE!\n"
                     f"env variable: OLD_DB_PATH={old_path_to_db}")

        sys.exit()

    if not os.path.isfile(old_path_to_db):
        logger.error("CAN'T FIND OLD DATABASE - please validate the path!\n"
                     f"env variable: OLD_DB_PATH={old_path_to_db}")
        sys.exit()

    # start migration
    migrate_from_v1(old_path_to_db)

    print("sleeping for an hour - please stop the container and run the bot")
    time.sleep(3600)
