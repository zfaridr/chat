from socket import *
import os
import threading
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
from dbase import ServerDataBase
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_wind import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

# engine = create_engine('sqlite:///:memory:', echo=True)
# Session = sessionmaker(bind=engine)


# metadata = MetaData()
# clients_table = Table('clients', metadata,
#     Column('login', String, primary_key=True),
#     Column('info', String),
# )

# clients_history = Table('clients_history', metadata,
#     Column('login_time', DateTime),
#     Column('ip_adress', String, primary_key=True),
# )

# contacts_list = Table('contacts_list', metadata,
#     Column('id', String, primary_key=True),
#     Column('client_id', String)
# )

# metadata.create_all(engine)

# class Client:
#     def __init__(self, login, info):
#         self.login = login
#         self.info = info
#     def __repr__(self):
#         return "<Client('%s','%s', '%s')>" % \
#         (self.login, self.info)

# m_client = registry.map_imperatively(Client, clients_table)
# print('Classic Mapping. Mapper: ', m_client)
# client_n = Client('timur', 'timur')


# class History:
#     def __init__(self, login_time, ip_adress):
#         self.login_time = login_time
#         self.ip_adress = ip_adress
#     def __repr__(self):
#         return "<History('%s','%s', '%s')>" % \
#         (self.login_time, self.ip_adress)

# m_history = registry.map_imperatively(History, clients_history)
# print('Classic Mapping. Mapper: ', m_history)

# class Contacts:
#     def __init__(self, id, client_id):
#         self.id = id
#         self.client_id = client_id
#     def __repr__(self):
#         return "<Contacts('%s','%s', '%s')>" % \
#         (self.id, self.client_id)

# m_contacts = registry.map_imperatively(Contacts, contacts_list)
# print('Classic Mapping. Mapper: ', m_contacts)

# with sqlite3.connect('chat.db3') as conn:
#     cursor = conn.cursor()
    
#     session = Session()

#     session.add(client_n)


#     q_user = session.query(Client).filter_by(login='timur').first()
#     print('Simple query:', q_user)

#     session.add_all([Client('ivan', 'simply ivan'),
#     Client('fast', 'very fast')])

#     session.commit()
#     print('Client login after commit:', client_n.login)

#     z = cursor.fetchone()
#     while z:
#         print(z)
#         z = cursor.fetchone()

# conn.close()


# p1 = subprocess.Popen("ls -l", shell=True, stdout=subprocess.PIPE)
# p2 = subprocess.Popen("wc", shell=True, stdin=p1.stdout, stdout=subprocess.PIPE)
# out = p2.stdout.read()



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


class Server(threading.Thread, metaclass=ServerVer):
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
           
def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    

    
    database = ServerDataBase('chat.db3')
        
    server = Server(database)
    server.daemon = True
    server.start()

    
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            if 1023 < port < 65536:
                print(port)
                with open('server.ini', 'w') as conf:
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    
    server_app.exec_()

if __name__ == "__main__":
    main()

    

    