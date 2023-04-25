from socket import *
import select
import time
import json
import logging
import log.server_log_config
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

@Logging()
def read_requests(r_clients, all_clients):
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
def write_responses(requests, w_clients, all_clients):
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
def new_socket(adress):
    s = socket(AF_INET, SOCK_STREAM)
    s.bind((adress))
    s.listen(10)
    s.settimeout(0.2)

    return s



@Logging()
def process_client():
    adress = ('', 8668)
    clients = []
    s_connect = new_socket(adress)

    while True:
        try:
            connect, addr = s_connect.accept()
        except OSError as e:
            pass
        else:
            print("Получен запрос на соединение с %s" % str(addr))
            clients.append(connect)
        finally:
            wait = 10
            r = []
            w = []
            try:
                r, w, e = select.select(clients, clients, [], wait)
            except:
                pass
            
            requests = read_requests(r, clients)
            if requests:
                write_responses(requests, w, clients)

# @Logging()
# def process_message():
#     client, addr = s.accept()
#     data_client = client.recv(1000000)
#     data_decode = data_client.decode('utf-8')
#     data = json.loads(data_decode)
#     if data['action'] == 'presence':
#         data_to_send = 'You are online'
#         client.send(json.dumps(data_to_send).encode('utf-8'))
#     elif data['action'] == 'join':
#         data_to_send = 'You are in the chat'
#         client.send(json.dumps(data_to_send).encode('utf-8'))
#     elif data['action'] == 'msg':
#         data_to_send = 'Your message was recieved in the chat'
#         client.send(json.dumps(data_to_send).encode('utf-8'))
#         chat_log.info(data['message'])
#     elif data['action'] == 'quit':
#         data_to_send = 'Goodbye'
#         client.send(json.dumps(data_to_send).encode('utf-8'))
#         chat_log.info('Client leaved the chat')
#         client.close()
    
#     return data_to_send
              
    
if __name__ == "__main__":
    print('Server is working')
    process_client()

    

    