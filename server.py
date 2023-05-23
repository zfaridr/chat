from socket import *
import select
import time
import json
import logging
import log.server_log_config
import subprocess
import dis
import sys
import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime, create_engine
import sqlite3
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.orm import registry

engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=engine)


metadata = MetaData()
clients_table = Table('clients', metadata,
    Column('login', String, primary_key=True),
    Column('info', String),
)

clients_history = Table('clients_history', metadata,
    Column('login_time', DateTime),
    Column('ip_adress', String, primary_key=True),
)

contacts_list = Table('contacts_list', metadata,
    Column('id', String, primary_key=True),
    Column('client_id', String)
)

metadata.create_all(engine)

class Client:
    def __init__(self, login, info):
        self.login = login
        self.info = info
    def __repr__(self):
        return "<Client('%s','%s', '%s')>" % \
        (self.login, self.info)

m_client = registry.map_imperatively(Client, clients_table)
print('Classic Mapping. Mapper: ', m_client)
client_n = Client('timur', 'timur')


class History:
    def __init__(self, login_time, ip_adress):
        self.login_time = login_time
        self.ip_adress = ip_adress
    def __repr__(self):
        return "<History('%s','%s', '%s')>" % \
        (self.login_time, self.ip_adress)

m_history = registry.map_imperatively(History, clients_history)
print('Classic Mapping. Mapper: ', m_history)

class Contacts:
    def __init__(self, id, client_id):
        self.id = id
        self.client_id = client_id
    def __repr__(self):
        return "<Contacts('%s','%s', '%s')>" % \
        (self.id, self.client_id)

m_contacts = registry.map_imperatively(Contacts, contacts_list)
print('Classic Mapping. Mapper: ', m_contacts)



session = Session()

session.add(client_n)


q_user = session.query(Client).filter_by(login='timur').first()
print('Simple query:', q_user)

session.add_all([Client('ivan', 'simply ivan'),
Client('fast', 'very fast')])

session.commit()
print('Client login after commit:', client_n.login)

p1 = subprocess.Popen("ls -l", shell=True, stdout=subprocess.PIPE)
p2 = subprocess.Popen("wc", shell=True, stdin=p1.stdout, stdout=subprocess.PIPE)
out = p2.stdout.read()



class ServerVer(type):
    def __init__(self, clsname, bases, clsdict):
        clsmethods = []
        clsattributes = []
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in clsmethods:
                            clsmethods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in clsattributes:
                            clsattributes.append(i.argval)
        
       
        super().__init__(clsname, bases, clsdict)





chat_log = logging.getLogger('app.chat')

class Logging():
    def __init__(self):
        pass
    
    def __call__(self, func):
        def decorate(*args, **kwargs):
            result = func(*args, **kwargs)
            chat_log.info(f'function was called: {func.__name__}')
            return result
        
        return decorate


class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            chat_log.critical(f'port is not allowed {value}. allowed adresses from 1024 to 65535')
            exit(1)
        instance.__dict__[self.name] = value

    def __set_clsname__(self, name):
        self.name = name


class Server(metaclass=ServerVer):
    port = Port()

    @Logging()
    def read_requests(self, r_clients, all_clients):
        responses = {}
        for s in r_clients:
            try:
                data = s.recv(1024).decode('utf-8')
                responses[s] = data
            except:
                print('Client {} {} leaved'.format(s.fileno(), s.getpeername()))
                all_clients.remove(s)
        
        return responses

    @Logging()
    def write_responses(self, requests, w_clients, all_clients):
        for s in w_clients:
            if s in requests:
                try:
                    resp = requests[s].encode('utf-8')
                    s.send(resp)
                except: 
                    print('Client {} {} out'.format(s.fileno(), s.getpeername()))
                    s.close()
                    all_clients.remove(s)

    @Logging()
    def new_socket(self, adress):
        s = socket(AF_INET, SOCK_STREAM)
        s.bind((adress))
        s.listen(10)
        s.settimeout(0.2)

        return s



    @Logging()
    def process_client(self):
        adress = ('', 8668)
        clients = []
        messages = []
        s_connect = self.new_socket(adress)

        while True:
            try:
                connect, addr = s_connect.accept()
            except OSError as e:
                pass
            else:
                print("Получен запрос на соединение с %s" % str(addr))
                clients.append(connect)
                
            finally:
                wait = 1
                r = []
                w = []
                try:
                    r, w, e = select.select(clients, clients, [], wait)
                except:
                    pass
                
                requests = self.read_requests(r, clients)
                if requests:
                    self.write_responses(requests, w, clients)
           
    
if __name__ == "__main__":
    print('Server is working')
    new_server=Server()
    new_server.process_client()

    

    