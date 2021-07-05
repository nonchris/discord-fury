"""
Written by:
https://github.com/nonchris/
"""

import logging
from datetime import datetime
from typing import Union, List

from sqlalchemy import select, and_, delete

import database.db_models as db
from environment import CHANNEL_TRACK_LIMIT

logger = logging.getLogger('my-bot')


def get_all_settings_for(guild_id: int, setting: str,
                         session=db.open_session()) -> Union[List[db.Settings], None]:
    """
    Searches db for setting in a guild that matches the setting name

    :param guild_id: id of the guild to search for
    :param setting: name of the setting to search for
    :param session: session to search with, helpful if object shall be edited, since the same session is needed for this

    :return: list of settings that match the given given setting name
    """

    sel_statement = select(db.Settings).where(
        and_(
            db.Settings.guild_id == guild_id,
            db.Settings.setting == setting
        )
    )
    entries = session.execute(sel_statement).all()
    return [entry[0] for entry in entries] if entries else None


def get_first_setting_for(guild_id: int, setting: str,
                          session=db.open_session()) -> Union[db.Settings, None]:
    """
    Wrapper around get_all_settings_for() that extracts the first entry from returned list

    :param guild_id: id of the guild to search for
    :param setting: name of the setting to search for
    :param session: session to search with, helpful if object shall be edited, since the same session is needed for this

    :return: first setting to match the query
    """

    entries = get_all_settings_for(guild_id, setting, session)

    return entries[0] if entries else None


def get_setting(guild_id: int, setting: str, value: str,
                session=db.open_session()) -> Union[db.Settings, None]:
    """
    Searches db for one specific setting and returns if if exists

    :param guild_id: id of the guild to search for
    :param value: value of the setting to search for
    :param setting: name of the setting to search for
    :param session: session to search with, helpful if object shall be edited, since the same session is needed for this.

    :return: database entry if exists with those specific parameters, else None
    """

    sel_statement = select(db.Settings).where(
        and_(
            db.Settings.guild_id == guild_id,
            db.Settings.setting == setting,
            db.Settings.value == value
        )
    )
    entry = session.execute(sel_statement).first()
    return entry[0] if entry else None


def get_setting_by_value(guild_id: int, value: Union[str, int], session=db.open_session()) -> Union[db.Settings, None]:
    """
    Used to extract a setting that has a channel id as value and an unknown setting-name

    :param guild_id: guild  to search on
    :param value: settings value to search for
    :param session: will be created if none is passed in

    :return: database entry if exists with those specific parameters, else None
    """

    statement = select(db.Settings).where(
        and_(
            db.Settings.guild_id == guild_id,
            db.Settings.value == str(value)
        )
    )
    entry = session.execute(statement).first()
    return entry[0] if entry else None


def add_setting(guild_id: int, setting: str, value: Union[str, int],
                active=True, set_by="", set_date=datetime.now()):
    """
    Add an entry to the settings database

    :param guild_id: id the setting is in
    :param value: value of the setting - probably name of a word-list
    :param set_by: user id or name of the member who entered that setting - could be neat for logs
    :param set_date: date the setting was configured
    :param setting: setting type to add
    :param active: if setting shall be active, not used at the moment
    """

    if type(value) is int:
        value = str(value)

    session = db.open_session()
    entry = db.Settings(guild_id=guild_id, setting=setting, value=value,
                        is_active=active, set_by=set_by, set_date=set_date)
    session.add(entry)
    session.commit()


def del_setting(guild_id: int, setting: str, value: Union[str, int]):
    """
    Delete an entry from the settings table

    :param guild_id: id the setting is in
    :param value: value of the setting - probably name of a word-list
    :param setting: setting type to delete
    """

    if type(value) is int:
        value = str(int)

    session = db.open_session()
    statement = delete(db.Settings).where(
        and_(
            db.Settings.guild_id == guild_id,
            db.Settings.setting == setting,
            db.Settings.value == value
        )
    )
    session.execute(statement)
    session.commit()


def del_setting_by_setting(guild_id: int, setting: str):
    """
    Delete an entry from the settings table by giving only the settings name

    :param guild_id: id the setting is in
    :param setting: the setting - like archive or prefix
    """

    session = db.open_session()
    statement = delete(db.Settings).where(
        and_(
            db.Settings.guild_id == guild_id,
            db.Settings.setting == setting
        )
    )
    session.execute(statement)
    session.commit()


def del_setting_by_value(guild_id: int, value: Union[str, int]):
    """
    Delete an entry from the settings table by giving only the value

    :param guild_id: id the setting is in
    :param value: value of the setting like a channel id
    """

    if type(value) is int:
        value = str(int)

    session = db.open_session()
    statement = delete(db.Settings).where(
        and_(
            db.Settings.guild_id == guild_id,
            db.Settings.value == value
        )
    )
    session.execute(statement)
    session.commit()


def is_track_limit_reached(guild_id: int, *channel_types: str) -> bool:
    """
    Check if new channels of asked types can be created without reaching any tracking limit\n

    All types are checked if no types are given

    :param guild_id: guild id to check settings for
    :param channel_types: strings of channel_types that the db shall be checked for e.g. private_channel

    :return: True if limit is reached, False if not
    """

    # if no specific is given - check all known 'classes'
    if not channel_types:
        channel_types = ('public_channel', 'private_channel')

    for channel_type in channel_types:

        # get list of all tracked channels that match the given type
        tracked_channels = get_all_settings_for(guild_id, channel_type)

        if tracked_channels and len(tracked_channels) >= CHANNEL_TRACK_LIMIT:
            return True

    return False
