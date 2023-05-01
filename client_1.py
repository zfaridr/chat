from socket import *
from select import select
import sys
import logging
import log.client_log_config
import inspect
import threading
import time

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

@Logging()
def message_from_server(sock, user_name):
    with socket(AF_INET, SOCK_STREAM) as s: 
        s.connect(adress)
        while True:
            message = s.recv(1024).decode('utf-8')
            print('Message from server: ', message)
              


@Logging()
def interact_with_server():
    user = input('Input user name: ')
    with socket(AF_INET, SOCK_STREAM) as s: 
        s.connect(adress)
        while True:
            message = input('Ваше сообщение: ')
            if message == 'exit':
                break
            s.send(message.encode('utf-8'))
            # data = s.recv(1024).decode('utf-8')
            # print('Response from server:', data)
            time.sleep(5)
            receiver = threading.Thread(target=message_from_server, args=(s, user))
            receiver.daemon = True
            receiver.start()
    

if __name__ == '__main__':
    interact_with_server()