from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime
from sqlalchemy.orm import registry


class ServerDataBase:
    
    class AllClients:
        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.id = None

    class ActiveClients:
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class LoginHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    class ClientsContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class ClientHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self , path):
        self.database_engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200, connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
                            )

        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )

        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('Users.id')),
                         Column('contact', ForeignKey('Users.id'))
                         )

        users_history_table = Table('History', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('Users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer)
                                    )

        self.metadata.create_all(self.database_engine)

        
        registry.map_imperatively(self.AllClients, users_table)
        registry.map_imperatively(self.ActiveClients, active_users_table)
        registry.map_imperatively(self.LoginHistory, user_login_history)
        registry.map_imperatively(self.ClientsContacts, contacts)
        registry.map_imperatively(self.ClientHistory, users_history_table)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port):
        rez = self.session.query(self.AllClients).filter_by(name=username)

        if rez.count():
            user = rez.first()
            user.last_login = datetime.datetime.now()
        
        else:
            user = self.AllClients(username)
            self.session.add(user)
            self.session.commit()
            user_in_history = self.ClientHistory(user.id)
            self.session.add(user_in_history)

        new_active_user = self.ActiveClients(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    
    def user_logout(self, username):
        
        user = self.session.query(self.AllClients).filter_by(name=username).first()

        self.session.query(self.ActiveClients).filter_by(user=user.id).delete()

        self.session.commit()

    
    def process_message(self, sender, recipient):
        
        sender = self.session.query(self.AllClients).filter_by(name=sender).first().id
        recipient = self.session.query(self.AllClients).filter_by(name=recipient).first().id
        
        sender_row = self.session.query(self.ClientHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.ClientsHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):
        
        user = self.session.query(self.AllClients).filter_by(name=user).first()
        contact = self.session.query(self.AllClients).filter_by(name=contact).first()

        if not contact or self.session.query(self.ClientsContacts).filter_by(user=user.id, contact=contact.id).count():
            return

        contact_row = self.ClientsContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    
    def remove_contact(self, user, contact):
        user = self.session.query(self.AllClients).filter_by(name=user).first()
        contact = self.session.query(self.AllClients).filter_by(name=contact).first()

        if not contact:
            return

        print(self.session.query(self.ClientsContacts).filter(
            self.ClientsContacts.user == user.id,
            self.ClientsContacts.contact == contact.id
        ).delete())
        self.session.commit()

    def users_list(self):
        # Запрос строк таблицы пользователей.
        query = self.session.query(
            self.AllClients.name,
            self.AllClients.last_login
        )
        # Возвращаем список кортежей
        return query.all()

    def active_users_list(self):
        query = self.session.query(
            self.AllClients.name,
            self.ActiveClients.ip_address,
            self.ActiveClients.port,
            self.ActiveClients.login_time
        ).join(self.AllClients)
        return query.all()

    def login_history(self, username=None):
        query = self.session.query(self.AllClients.name,                                   
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllClients.name == username)
        
        return query.all()

    
    def get_contacts(self, username):
        
        user = self.session.query(self.AllClients).filter_by(name=username).one()

        query = self.session.query(self.ClientsContacts, self.AllClients.name). \
            filter_by(user=user.id). \
            join(self.AllClients, self.ClientsContacts.contact == self.AllClients.id)

        return [contact[1] for contact in query.all()]

    def message_history(self):
        query = self.session.query(
            self.AllClients.name,
            self.AllClients.last_login,
            self.ClientHistory.sent,
            self.ClientHistory.accepted
        ).join(self.AllClients)
        
        return query.all()




    