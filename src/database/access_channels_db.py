import logging
from datetime import datetime
from typing import Union, List

from sqlalchemy import select, and_, delete

import database.db_models as db

logger = logging.getLogger('my-bot')


def get_voice_channel_by_id(channel_id: int, session=db.open_session()):

    statement = select(db.CreatedChannels).where(
        db.CreatedChannels.voice_channel_id == channel_id
    )

    entry = session.execute(statement).first()
    return entry[0] if entry else None


def add_channel(voice_channel_id: int, text_channel_id: str, guild_id: int, internal_type: str,
                category=None, set_by='unknown', set_date=datetime.now()):
    """
    :param voice_channel_id: id of created voice channel
    :param text_channel_id: id of linked text_channel
    :param guild_id: id of the guild the channels were created on
    :param internal_type: type of the channels 'public' or 'private' etc
    :param category: optional category the channels are in
    :param set_by: optional which module issued creation
    :param set_date: date the channel was created - default is datetime.now()
    """

    session = db.open_session()

    entry = db.CreatedChannels(
        voice_channel_id=voice_channel_id,
        text_channel_id=text_channel_id,
        guild_id=guild_id,
        internal_type=internal_type,
        category=category,
        set_by=set_by,
        set_date=set_date
    )

    session.add(entry)
    session.commit()


def del_channel(voice_channel_id: int):
    session = db.open_session()

    statement = delete(db.CreatedChannels).where(
            db.CreatedChannels.voice_channel_id == voice_channel_id
    )
    session.execute(statement)
    session.commit()
