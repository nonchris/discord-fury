"""
Modified SQLAlchemy quickstart gist by
https://github.com/nonchris/

Link to gist:
https://gist.github.com/nonchris/046f58bcefdcea5606f670b74f375254

discord bot template:
https://github.com/nonchris/discord-bot
"""

# core interface to the database
import os
import logging

import sqlalchemy.orm
from sqlalchemy import create_engine, Boolean, DateTime
# base contains a metaclass that produces the right table
from sqlalchemy.ext.declarative import declarative_base
# setting up a class that represents our SQL Database
from sqlalchemy import Column, Integer, String, BigInteger
# prints if a table was created - neat check for making sure nothing is overwritten
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

# responsible for postgress compatibility
import psycopg2

if not os.path.exists('data/'):
    os.mkdir('data/')

logger = logging.getLogger('my-bot')

POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_SERVER = os.environ["POSTGRES_SERVER"]
POSTGRES_DB = os.environ["POSTGRES_DB"]

DB_URL = f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"
engine = create_engine(f'postgresql+psycopg2://{DB_URL}', echo=False)


Base: declarative_base = declarative_base()


class Settings(Base):
    __tablename__ = 'SETTINGS'

    # setting names:
    # mod_role, public_channel, private_channel, archive_category, log_channel, allow_public_rename

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)      # ID of guild setting is applied to
    applied_to_channel_id = Column(BigInteger)    # to make settings per channel possible
    setting = Column(String)        # type of setting - example: mod-role
    value = Column(String)          # setting value - example: id of a moderator role
    is_active = Column(Boolean)  # future: maybe don't delete unused settings and rather deactivate them -> better logging?
    set_by = Column(String)         # user id or name of the user who set entry
    set_date = Column(DateTime)     # date the setting was altered the last time

    def __repr__(self):
        return f"<Setting: guild='{self.guild_id}', channel_id='{self.applied_to_channel_id}' setting='{self.setting}'," \
               f"value='{self.value}', set_by='{self.set_by}', set_date='{self.set_date}', is_active='{self.is_active}'>"


class CreatedChannels(Base):
    __tablename__ = 'CREATED_CHANNELS'

    # types: public_channel, private_channel, breakout_room

    id = Column(Integer, primary_key=True)
    voice_channel_id = Column(BigInteger)  # id of voice channel that was created
    internal_type = Column(String)       # type of channel public, private, persistent etc
    text_channel_id = Column(BigInteger)    # id of the linked text channel
    guild_id = Column(BigInteger)           # guild the channels are on
    category = Column(BigInteger)           # category they're in - not sure if needed but neat to have
    set_by = Column(String)              # system the entry was set by bot/ user
    set_date = Column(DateTime)          # date the value was changed the last time

    def __repr__(self):
        return f"CreatedChannel: internal_type='{self.internal_type}' guild_id='{self.guild_id}', " \
               f"voice_channel_id={self.voice_channel_id}, text_channel_id='{self.text_channel_id}," \
               f"category='{self.category}', set_by='{self.set_by}', set_date={self.set_date}"


@event.listens_for(Base.metadata, 'after_create')
def receive_after_create(target, connection, tables, **kw):
    """listen for the 'after_create' event"""
    logger.info('A table was created' if tables else 'No table was created')
    print('A table was created' if tables else 'No table was created')


def open_session() -> sqlalchemy.orm.Session:
    """
    :return: new active session
    """
    return sessionmaker(bind=engine)()


# creating db which doesn't happen when it should?
database = Base.metadata.create_all(bind=engine)
