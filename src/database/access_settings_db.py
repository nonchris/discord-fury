"""
Written by:
https://github.com/nonchris/
"""

import logging
from datetime import datetime
from typing import Union, List

from sqlalchemy import select, and_, delete

import database.db_models as db

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


def add_setting(guild_id: int, setting: str, value: str,
                active=True, set_by="", set_date=datetime.now(), session=db.open_session()):
    """
    Add an entry to the settings database

    :param guild_id: id the setting is in
    :param value: value of the setting - probably name of a word-list
    :param set_by: user id or name of the member who entered that setting - could be neat for logs
    :param set_date: date the setting was configured
    :param setting: setting type to add
    :param active: if setting shall be active, not used at the moment
    :param session: session to search with, helpful if object shall be edited, since the same session is needed for this
    """
    entry = db.Settings(guild_id=guild_id, setting=setting, value=value,
                        active=active, set_by=set_by, set_date=set_date)
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


def del_setting_by_value(guild_id: int, value: Union[str, int]):
    """
    Delete an entry from the settings table

    :param guild_id: id the setting is in
    :param value: value of the setting - probably name of a word-list
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
