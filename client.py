import socket
import time
import json
import threading
from PyQt5.QtCore import pyqtSignal, QObject
from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime
import logging
import logging.handlers
import argparse
import sys
from PyQt5.QtWidgets import QApplication   
import os
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QApplication, QListView
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, QEvent, Qt
from PyQt5.QtWidgets import QDialog, QLabel, QComboBox, QPushButton, QApplication
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QApplication, QLabel

sys.path.append('../')

DEFAULT_PORT = 7788
DEFAULT_IP_ADDRESS = '127.0.0.1'
MAX_CONNECTIONS = 5
MAX_PACKAGE_LENGTH = 1024
ENCODING = 'utf-8'
LOGGING_LEVEL = logging.DEBUG
SERVER_CONFIG = 'server.ini'

ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'

PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
EXIT = 'exit'
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'


RESPONSE_200 = {RESPONSE: 200}

RESPONSE_202 = {RESPONSE: 202,
                LIST_INFO:None
                }

RESPONSE_400 = {
            RESPONSE: 400,
            ERROR: None
        }
LOGGING_LEVEL = logging.DEBUG

client_formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'client.log')

steam = logging.StreamHandler(sys.stderr)
steam.setFormatter(client_formatter)
steam.setLevel(logging.INFO)
log_file = logging.FileHandler(path, encoding='utf8')
log_file.setFormatter(client_formatter)

logger = logging.getLogger('client')
logger.addHandler(steam)
logger.addHandler(log_file)
logger.setLevel(LOGGING_LEVEL)

class ServerError(Exception):
    def __init__(self, text):
        self.text = text

    def __str__(self):
        return self.text


class ReqFieldMissingError(Exception):
    def __init__(self, missing_field):
        self.missing_field = missing_field

    def __str__(self):
        return f'В принятом словаре отсутствует обязательное поле {self.missing_field}.'


client_formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'client.log')

steam = logging.StreamHandler(sys.stderr)
steam.setFormatter(client_formatter)
steam.setLevel(logging.INFO)
log_file = logging.FileHandler(path, encoding='utf8')
log_file.setFormatter(client_formatter)

logger = logging.getLogger('client')
logger.addHandler(steam)
logger.addHandler(log_file)
logger.setLevel(LOGGING_LEVEL)


server_formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(path, 'server.log')

steam = logging.StreamHandler(sys.stderr)
steam.setFormatter(server_formatter)
steam.setLevel(logging.INFO)
log_file = logging.handlers.TimedRotatingFileHandler(path, encoding='utf8', interval=1, when='D')
log_file.setFormatter(server_formatter)

logger = logging.getLogger('server')
logger.addHandler(steam)
logger.addHandler(log_file)
logger.setLevel(LOGGING_LEVEL)


if sys.argv[0].find('client') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def log(func_to_log):
    def log_saver(*args , **kwargs):
        logger.debug(f'Была вызвана функция {func_to_log.__name__} c параметрами {args} , {kwargs}. Вызов из модуля {func_to_log.__module__}')
        ret = func_to_log(*args , **kwargs)
        return ret
    return log_saver

@log
def get_message(client):
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    json_response = encoded_response.decode(ENCODING)
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise TypeError


@log
def send_message(sock, message):
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)


class ClientDatabase:
    class KnownUsers:
        def __init__(self, user):
            self.id = None
            self.username = user

    class MessageHistory:
        def __init__(self, contact, direction, message):
            self.id = None
            self.contact = contact
            self.direction = direction
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact

    def __init__(self, name):
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{name}.db3'
        self.database_engine = create_engine(f'sqlite:///{os.path.join(path, filename)}', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        users = Table('known_users', self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )



logger = logging.getLogger('client')
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username
        self.transport = None
        self.connection_init(port, ip_address)
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                logger.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            logger.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            logger.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
            
        self.running = True

    
    def connection_init(self, port, ip):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.transport.settimeout(5)

        connected = False
        for i in range(5):
            logger.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        
        if not connected:
            logger.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        logger.debug('Установлено соединение с сервером')

        
        try:
            with socket_lock:
                send_message(self.transport, self.create_presence())
                self.process_server_ans(get_message(self.transport))
        except (OSError, json.JSONDecodeError):
            logger.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')

        
        logger.info('Соединение с сервером успешно установлено.')

    
    def create_presence(self):
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: self.username
            }
        }
        logger.debug(f'Сформировано {PRESENCE} сообщение для пользователя {self.username}')
        return out

    
    def process_server_ans(self, message):
        logger.debug(f'Разбор сообщения от сервера: {message}')

        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return
            elif message[RESPONSE] == 400:
                raise ServerError(f'{message[ERROR]}')
            else:
                logger.debug(f'Принят неизвестный код подтверждения {message[RESPONSE]}')

        
        elif ACTION in message and message[ACTION] == MESSAGE and SENDER in message and DESTINATION in message \
                and MESSAGE_TEXT in message and message[DESTINATION] == self.username:
            logger.debug(f'Получено сообщение от пользователя {message[SENDER]}:{message[MESSAGE_TEXT]}')
            self.database.save_message(message[SENDER] , 'in' , message[MESSAGE_TEXT])
            self.new_message.emit(message[SENDER])


    
    def contacts_list_update(self):
        logger.debug(f'Запрос контакт листа для пользователся {self.name}')
        req = {
            ACTION: GET_CONTACTS,
            TIME: time.time(),
            USER: self.username
        }
        logger.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        logger.debug(f'Получен ответ {ans}')
        if RESPONSE in ans and ans[RESPONSE] == 202:
            for contact in ans[LIST_INFO]:
                self.database.add_contact(contact)
        else:
            logger.error('Не удалось обновить список контактов.')

    
    def user_list_update(self):
        logger.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            ACTION: USERS_REQUEST,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if RESPONSE in ans and ans[RESPONSE] == 202:
            self.database.add_users(ans[LIST_INFO])
        else:
            logger.error('Не удалось обновить список известных пользователей.')

    
    def add_contact(self, contact):
        logger.debug(f'Создание контакта {contact}')
        req = {
            ACTION: ADD_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    
    def remove_contact(self, contact):
        logger.debug(f'Удаление контакта {contact}')
        req = {
            ACTION: REMOVE_CONTACT,
            TIME: time.time(),
            USER: self.username,
            ACCOUNT_NAME: contact
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    
    def transport_shutdown(self):
        self.running = False
        message = {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.username
        }
        with socket_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        logger.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    
    def send_message(self, to, message):
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.username,
            DESTINATION: to,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        
        with socket_lock:
            send_message(self.transport, message_dict)
            self.process_server_ans(get_message(self.transport))
            logger.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        logger.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            
            time.sleep(1)
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    logger.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                
                else:
                    logger.debug(f'Принято сообщение с сервера: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)


logger = logging.getLogger('client')



class Ui_MainClientWindow(object):
    def setupUi(self, MainClientWindow):
        MainClientWindow.setObjectName("MainClientWindow")
        MainClientWindow.resize(756, 534)
        MainClientWindow.setMinimumSize(QtCore.QSize(756, 534))
        self.centralwidget = QtWidgets.QWidget(MainClientWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label_contacts = QtWidgets.QLabel(self.centralwidget)
        self.label_contacts.setGeometry(QtCore.QRect(10, 0, 101, 16))
        self.label_contacts.setObjectName("label_contacts")
        self.btn_add_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_add_contact.setGeometry(QtCore.QRect(10, 450, 121, 31))
        self.btn_add_contact.setObjectName("btn_add_contact")
        self.btn_remove_contact = QtWidgets.QPushButton(self.centralwidget)
        self.btn_remove_contact.setGeometry(QtCore.QRect(140, 450, 121, 31))
        self.btn_remove_contact.setObjectName("btn_remove_contact")
        self.label_history = QtWidgets.QLabel(self.centralwidget)
        self.label_history.setGeometry(QtCore.QRect(300, 0, 391, 21))
        self.label_history.setObjectName("label_history")
        self.text_message = QtWidgets.QTextEdit(self.centralwidget)
        self.text_message.setGeometry(QtCore.QRect(300, 360, 441, 71))
        self.text_message.setObjectName("text_message")
        self.label_new_message = QtWidgets.QLabel(self.centralwidget)
        self.label_new_message.setGeometry(QtCore.QRect(300, 330, 450, 16)) # Правка тут
        self.label_new_message.setObjectName("label_new_message")
        self.list_contacts = QtWidgets.QListView(self.centralwidget)
        self.list_contacts.setGeometry(QtCore.QRect(10, 20, 251, 411))
        self.list_contacts.setObjectName("list_contacts")
        self.list_messages = QtWidgets.QListView(self.centralwidget)
        self.list_messages.setGeometry(QtCore.QRect(300, 20, 441, 301))
        self.list_messages.setObjectName("list_messages")
        self.btn_send = QtWidgets.QPushButton(self.centralwidget)
        self.btn_send.setGeometry(QtCore.QRect(610, 450, 131, 31))
        self.btn_send.setObjectName("btn_send")
        self.btn_clear = QtWidgets.QPushButton(self.centralwidget)
        self.btn_clear.setGeometry(QtCore.QRect(460, 450, 131, 31))
        self.btn_clear.setObjectName("btn_clear")
        MainClientWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainClientWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 756, 21))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(self.menubar)
        self.menu_2.setObjectName("menu_2")
        MainClientWindow.setMenuBar(self.menubar)
        self.statusBar = QtWidgets.QStatusBar(MainClientWindow)
        self.statusBar.setObjectName("statusBar")
        MainClientWindow.setStatusBar(self.statusBar)
        self.menu_exit = QtWidgets.QAction(MainClientWindow)
        self.menu_exit.setObjectName("menu_exit")
        self.menu_add_contact = QtWidgets.QAction(MainClientWindow)
        self.menu_add_contact.setObjectName("menu_add_contact")
        self.menu_del_contact = QtWidgets.QAction(MainClientWindow)
        self.menu_del_contact.setObjectName("menu_del_contact")
        self.menu.addAction(self.menu_exit)
        self.menu_2.addAction(self.menu_add_contact)
        self.menu_2.addAction(self.menu_del_contact)
        self.menu_2.addSeparator()
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())

        self.retranslateUi(MainClientWindow)
        self.btn_clear.clicked.connect(self.text_message.clear)
        QtCore.QMetaObject.connectSlotsByName(MainClientWindow)

    def retranslateUi(self, MainClientWindow):
        _translate = QtCore.QCoreApplication.translate
        MainClientWindow.setWindowTitle(_translate("MainClientWindow", "Чат Программа alpha release"))
        self.label_contacts.setText(_translate("MainClientWindow", "Список контактов:"))
        self.btn_add_contact.setText(_translate("MainClientWindow", "Добавить контакт"))
        self.btn_remove_contact.setText(_translate("MainClientWindow", "Удалить контакт"))
        self.label_history.setText(_translate("MainClientWindow", "История сообщений:"))
        self.label_new_message.setText(_translate("MainClientWindow", "Введите новое сообщение:"))
        self.btn_send.setText(_translate("MainClientWindow", "Отправить сообщение"))
        self.btn_clear.setText(_translate("MainClientWindow", "Очистить поле"))
        self.menu.setTitle(_translate("MainClientWindow", "Файл"))
        self.menu_2.setTitle(_translate("MainClientWindow", "Контакты"))
        self.menu_exit.setText(_translate("MainClientWindow", "Выход"))
        self.menu_add_contact.setText(_translate("MainClientWindow", "Добавить контакт"))
        self.menu_del_contact.setText(_translate("MainClientWindow", "Удалить контакт"))




class AddContactDialog(QDialog):
    def __init__(self, transport, database):
        super().__init__()
        self.transport = transport
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Выберите контакт для добавления:')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для добавления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_refresh = QPushButton('Обновить список', self)
        self.btn_refresh.setFixedSize(100, 30)
        self.btn_refresh.move(60, 60)

        self.btn_ok = QPushButton('Добавить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        
        self.possible_contacts_update()
        
        self.btn_refresh.clicked.connect(self.update_possible_contacts)

    
    def possible_contacts_update(self):
        self.selector.clear()
        contacts_list = set(self.database.get_contacts())
        users_list = set(self.database.get_users())
        users_list.remove(self.transport.username)
        self.selector.addItems(users_list - contacts_list)

    def update_possible_contacts(self):
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            logger.debug('Обновление списка пользователей с сервера выполнено')
            self.possible_contacts_update()




logger = logging.getLogger('client')


class DelContactDialog(QDialog):
    def __init__(self, database):
        super().__init__()
        self.database = database

        self.setFixedSize(350, 120)
        self.setWindowTitle('Выберите контакт для удаления:')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel('Выберите контакт для удаления:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton('Удалить', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)

        self.btn_cancel = QPushButton('Отмена', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.selector.addItems(sorted(self.database.get_contacts()))




# Стартовый диалог с выбором имени пользователя
class UserNameDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle('Привет!')
        self.setFixedSize(175, 93)

        self.label = QLabel('Введите имя пользователя:', self)
        self.label.move(10, 10)
        self.label.setFixedSize(150, 10)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.btn_ok = QPushButton('Начать', self)
        self.btn_ok.move(10, 60)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Выход', self)
        self.btn_cancel.move(90, 60)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    # Обработчик кнопки ОК, если поле вводе не пустое, ставим флаг и завершаем приложение.
    def click(self):
        if self.client_name.text():
            self.ok_pressed = True
            qApp.exit()


logger = logging.getLogger('client')


class ClientMainWindow(QMainWindow):
    def __init__(self, database, transport):
        super().__init__()
        self.database = database
        self.transport = transport

        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)

        self.ui.menu_exit.triggered.connect(qApp.exit)

        self.ui.btn_send.clicked.connect(self.send_message)

        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)

        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)

        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)

    
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def set_disabled_input(self):
        self.ui.label_new_message.setText('Для выбора получателя дважды кликните на нем в окне контактов.')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

    def history_list_update(self):
        list = sorted(self.database.get_history(self.current_chat), key=lambda item: item[3])
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        
        self.history_model.clear()
        length = len(list)
        start_index = 0
        if length > 20:
            start_index = length - 20
        
        for i in range(start_index, length):
            item = list[i]
            if item[1] == 'in':
                mess = QStandardItem(f'Входящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Исходящее от {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    def select_active_user(self):
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()

    def set_active_user(self):
        self.ui.label_new_message.setText(f'Введите сообщенние для {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)

        self.history_list_update()

    def clients_list_update(self):
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    def add_contact_window(self):
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    
    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    def add_contact(self, new_contact):
        try:
            self.transport.add_contact(new_contact)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            logger.info(f'Успешно добавлен контакт {new_contact}')
            self.messages.information(self, 'Успех', 'Контакт успешно добавлен.')

    def delete_contact_window(self):
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    def delete_contact(self, item):
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except ServerError as err:
            self.messages.critical(self, 'Ошибка сервера', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        else:
            self.database.del_contact(selected)
            self.clients_list_update()
            logger.info(f'Успешно удалён контакт {selected}')
            self.messages.information(self, 'Успех', 'Контакт успешно удалён.')
            item.close()
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    
    def send_message(self):
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        try:
            self.transport.send_message(self.current_chat, message_text)
            pass
        except ServerError as err:
            self.messages.critical(self, 'Ошибка', err.text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
                self.close()
            self.messages.critical(self, 'Ошибка', 'Таймаут соединения!')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Ошибка', 'Потеряно соединение с сервером!')
            self.close()
        else:
            self.database.save_message(self.current_chat, 'out', message_text)
            logger.debug(f'Отправлено сообщение для {self.current_chat}: {message_text}')
            self.history_list_update()

    @pyqtSlot(str)
    def message(self, sender):
        if sender == self.current_chat:
            self.history_list_update()
        else:
            if self.database.check_contact(sender):
                if self.messages.question(self, 'Новое сообщение', \
                                          f'Получено новое сообщение от {sender}, открыть чат с ним?', QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                print('NO')
                
                if self.messages.question(self, 'Новое сообщение', \
                                          f'Получено новое сообщение от {sender}.\n Данного пользователя нет в вашем контакт-листе.\n Добавить в контакты и открыть чат с ним?',
                                          QMessageBox.Yes,
                                          QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Сбой соединения', 'Потеряно соединение с сервером. ')
        self.close()

    def make_connection(self, trans_obj):
        trans_obj.new_message.connect(self.message)
        trans_obj.connection_lost.connect(self.connection_lost)




@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. Допустимы адреса с 1024 до 65535. Клиент завершается.')
        exit(1)

    return server_address, server_port, client_name



if __name__ == '__main__':
    server_address, server_port, client_name = arg_parser()

    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект, инааче выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    
    logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {client_name}')

    
    database = ClientDatabase(client_name)

    
    try:
        transport = ClientTransport(server_port, server_address, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    
    transport.transport_shutdown()