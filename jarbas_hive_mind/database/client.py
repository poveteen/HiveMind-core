from contextlib import contextmanager
from os import makedirs
from os.path import join, expanduser, isdir

from sqlalchemy import Column, Text, String, Integer, create_engine, Boolean
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from jarbas_hive_mind.database import Base


@contextmanager
def session_scope(db):
    """Provide a transactional scope around a series of operations."""
    Session = sessionmaker(bind=db)
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    description = Column(Text)
    api_key = Column(String)
    name = Column(String)
    mail = Column(String)
    last_seen = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)


class ClientDatabase(object):
    db_dir = expanduser("~/jarbas_hivemind/database")
    if not isdir(db_dir):
        makedirs(db_dir)
    default_db = "sqlite:///" + join(db_dir, "clients.db")

    def __init__(self, path=None, debug=False):
        if path is None:
            try:
                from mycroft.configuration.config import Configuration
                path = Configuration.get().get("hivemind", {})\
                    .get("sql_client_db", self.default_db)
            except ImportError:
                path = self.default_db

        self.db = create_engine(path)
        self.db.echo = debug

        Base.metadata.create_all(self.db)

    def update_timestamp(self, api, timestamp):
        with session_scope(self.db) as session:
            user = self.get_client_by_api_key(api)
            if not user:
                return False
            user.last_seen = timestamp
            return True

    def delete_client(self, api):
        with session_scope(self.db) as session:
            user = self.get_client_by_api_key(api)
            if user:
                session.delete(user)
                return True
            return False

    def change_api(self, user_name, new_key):
        with session_scope(self.db) as session:
            user = self.get_client_by_name(user_name)
            if not user:
                return False
            user.api_key = new_key

    def change_name(self, new_name, key):
        with session_scope(self.db) as session:
            user = self.get_client_by_api_key(key)
            if not user:
                return False
            user.name = new_name

    def get_client_by_api_key(self, api_key):
        with session_scope(self.db) as session:
            return session.query(Client).filter_by(api_key=api_key).first()

    def get_client_by_name(self, name):
        with session_scope(self.db) as session:
            return session.query(Client).filter_by(name=name).first()

    def add_client(self, name=None, mail=None, api="", admin=False):
        with session_scope(self.db) as session:
            user = Client(api_key=api, name=name, mail=mail,
                      id=self.total_clients() + 1, is_admin=admin)

            session.add(user)

    def total_clients(self):
        with session_scope(self.db) as session:
            return session.query(Client).count()

    def commit(self, handler):
        Session = sessionmaker(bind=self.db)
        session = Session()
        try:
            handler(session)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise
        finally:
            session.close()


if __name__ == "__main__":
    db = ClientDatabase(debug=True)
    name = "jarbas"
    mail = "jarbasaai@mailfence.com"
    api = "test_key"
    db.add_client(name, mail, api, admin=False)
