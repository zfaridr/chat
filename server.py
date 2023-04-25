from socket import *
import time
import json
import logging
import log.server_log_config
import inspect

chat_log = logging.getLogger('app.chat')

s = socket(AF_INET, SOCK_STREAM)
s.bind(('', 8866))
s.listen(10)

class Logging():
    def __init__(self):
        pass
    
    def __call__(self, func):
        def decorate(*args, **kwargs):
            result = func(*args, **kwargs)
            chat_log.info(f'function was called: {func.__name__}')
            return result
        
        return decorate

@Logging()
def probe():
    data_to_send = f"You are online + {time.ctime(time.time())}"
    client.send(json.dumps(data_to_send).encode('utf-8'))
    

@Logging()
def process_message():
    client, addr = s.accept()
    data_client = client.recv(1000000)
    data_decode = data_client.decode('utf-8')
    data = json.loads(data_decode)
    if data['action'] == 'presence':
        data_to_send = 'You are online'
        client.send(json.dumps(data_to_send).encode('utf-8'))
    elif data['action'] == 'join':
        data_to_send = 'You are in the chat'
        client.send(json.dumps(data_to_send).encode('utf-8'))
    elif data['action'] == 'msg':
        data_to_send = 'Your message was recieved in the chat'
        client.send(json.dumps(data_to_send).encode('utf-8'))
        chat_log.info(data['message'])
    elif data['action'] == 'quit':
        data_to_send = 'Goodbye'
        client.send(json.dumps(data_to_send).encode('utf-8'))
        chat_log.info('Client leaved the chat')
        client.close()
    
    return data_to_send
              
    
if __name__ == "__main__":
    while True:
        client, addr = s.accept()
        chat_log.info("Получен запрос на соединение от %s" % str(addr))
        process_message()

    

    