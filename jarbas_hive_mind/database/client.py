from sqlalchemy import Column, Text, String, Integer, create_engine, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from jarbas_hive_mind.database import Base
from os.path import join, expanduser


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
    default_db = "sqlite:///" + join(expanduser("~/.mycroft/hivemind/database"), "clients.db")

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

        Session = sessionmaker(bind=self.db)
        self.session = Session()
        Base.metadata.create_all(self.db)

    def update_timestamp(self, api, timestamp):
        user = self.get_client_by_api_key(api)
        if not user:
            return False
        user.last_seen = timestamp
        return self.commit()

    def delete_client(self, api):
        user = self.get_client_by_api_key(api)
        if user:
            self.session.delete(user)
            return self.commit()
        return False

    def change_api(self, user_name, new_key):
        user = self.get_client_by_name(user_name)
        if not user:
            return False
        user.api_key = new_key
        return self.commit()

    def change_name(self, new_name, key):
        user = self.get_client_by_api_key(key)
        if not user:
            return False
        user.name = new_name
        return self.commit()

    def get_client_by_api_key(self, api_key):
        return self.session.query(Client).filter_by(api_key=api_key).first()

    def get_client_by_name(self, name):
        return self.session.query(Client).filter_by(name=name).first()

    def add_client(self, name=None, mail=None, api="", admin=False):
        user = Client(api_key=api, name=name, mail=mail,
                      id=self.total_clients() + 1, is_admin=admin)
        self.session.add(user)
        return self.commit()

    def total_clients(self):
        return self.session.query(Client).count()

    def commit(self):
        try:
            self.session.commit()
            return True
        except IntegrityError:
            self.session.rollback()
        return False


if __name__ == "__main__":
    db = ClientDatabase(debug=True)
    name = "jarbas"
    mail = "jarbasaai@mailfence.com"
    api = "admin_key"
    db.add_client(name, mail, api, admin=True)


