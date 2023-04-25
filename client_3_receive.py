from socket import *
from select import select
import sys
import logging
import log.client_log_config
import inspect


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
def message_from_server():
    s = socket(AF_INET, SOCK_STREAM)
    s.connect(adress)
    while True:
        message = s.recv(1024).decode('utf-8')
        print('Message from server: ', message)
    
        s.close()

if __name__ == '__main__':
    message_from_server()