from socket import *
from select import select
import sys
import logging
import log.client_log_config
import threading
import time
import subprocess
import dis



class ClientVer(type):
    def __init__(self, clsname, bases, clsdict):
        clsmethods = []
        for func in clsdict:
            # Пробуем
            try:
                ret = dis.get_instructions(clsdict[func])
                # Если не функция то ловим исключение
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in clsmethods:
                            clsmethods.append(i.argval)
        for command in ('accept', 'listen', 'socket'):
            if command in clsmethods:
                raise TypeError('method is not allowed')
       
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


adress = ('localhost', 8668)

class Client(metaclass=ClientVer):
    def __init__(self, adress, user_name):
        self.adress = adress
        self.user_name = user_name
    
    @Logging()
    def message_from_server(self, adress):
        with socket(AF_INET, SOCK_STREAM) as s: 
            s.connect(adress)
            while True:
                message = s.recv(1024).decode('utf-8')
                print('Message from server: ', message)


    @Logging()
    def interact_with_server(self, adress, user_name):
        # user = input('Input user name: ')
        with socket(AF_INET, SOCK_STREAM) as s: 
            s.connect(adress)
            while True:
                message = input('Ваше сообщение: ')
                if message == 'exit':
                    break
                s.send(message.encode('utf-8'))
                data = s.recv(1024).decode('utf-8')
                print('Response from server:', data)
                time.sleep(1)
                receiver = threading.Thread(target=Client.message_from_server(self, adress))
                receiver.daemon = True
                receiver.start()


# @Logging()
# def message_from_server(sock, user_name):
#     with socket(AF_INET, SOCK_STREAM) as s: 
#         s.connect(adress)
#         while True:
#             message = s.recv(1024).decode('utf-8')
#             print('Message from server: ', message)
              


# @Logging()
# def interact_with_server():
#     user = input('Input user name: ')
#     with socket(AF_INET, SOCK_STREAM) as s: 
#         s.connect(adress)
#         while True:
#             message = input('Ваше сообщение: ')
#             if message == 'exit':
#                 break
#             s.send(message.encode('utf-8'))
#             # data = s.recv(1024).decode('utf-8')
#             # print('Response from server:', data)
#             time.sleep(5)
#             receiver = threading.Thread(target=message_from_server, args=(s, user))
#             receiver.daemon = True
#             receiver.start()
    

if __name__ == '__main__':
    client_1 = Client(adress, 'client_1')
    client_1.interact_with_server(adress, 'client_1')