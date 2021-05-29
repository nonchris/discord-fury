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
from sqlalchemy import Column, Integer, String
# prints if a table was created - neat check for making sure nothing is overwritten
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

if not os.path.exists('data/'):
    os.mkdir('data/')

engine = create_engine('sqlite:///data/main.db', echo=False)
Base: declarative_base = declarative_base()

logger = logging.getLogger('my-bot')


class Settings(Base):
    __tablename__ = 'SETTINGS'

    # setting names:
    # mod-role, tracked channel

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer)      # ID of guild setting is applied to
    channel_id = Column(Integer)    # to make settings per channel possible
    setting = Column(String)        # type of setting - example: mod-role
    value = Column(String)          # setting value - example: id of a moderator role
    active = Column(Boolean)  # future: maybe don't delete unused settings and rather deactivate them -> better logging?
    set_by = Column(String)         # user id or name of the user who set entry
    set_date = Column(DateTime)     # date the setting was altered the last time

    def __repr__(self):
        return f"<Setting: guild='{self.guild_id}', channel_id='{self.channel_id}' setting='{self.setting}'," \
               f"value='{self.value}', set_by='{self.set_by}', set_date='{self.set_date}', active='{self.active}'>"


class LinkedChannels(Base):
    __tablename__ = 'LINKED_CHANNELS'

    voice_channel = Column(Integer, primary_key=True)  # id of voice channel is primary key
    channel_type = Column(String)       # type of channel public, private, persistent etc
    text_channel = Column(Integer)      # id of the linked text channel
    guild = Column(Integer)             # guild the channels are on
    category = Column(Integer)          # category they're in - not sure if needed but neat to have
    set_by = Column(String)             # system the entry was set by bot/ user
    set_date = Column(DateTime)         # date the value was changed the last time

    def __repr__(self):
        return f"LinkedChannel: channel_type='{self.channel_type}' guild='{self.guild}', " \
               f"voice_channel={self.voice_channel}, text_channel='{self.text_channel}, category='{self.category}' " \
               f"set_by='{self.set_by}', set_date={self.set_date}"


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
