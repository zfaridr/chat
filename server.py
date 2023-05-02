from socket import *
import select
import time
import json
import logging
import log.server_log_config
import subprocess

p1 = subprocess.Popen("ls -l", shell=True, stdout=subprocess.PIPE)
p2 = subprocess.Popen("wc", shell=True, stdin=p1.stdout, stdout=subprocess.PIPE)
out = p2.stdout.read()

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
    messages = []
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
            wait = 1
            r = []
            w = []
            try:
                r, w, e = select.select(clients, clients, [], wait)
            except:
                pass
            
            requests = read_requests(r, clients)
            if requests:
                write_responses(requests, w, clients)
           
    
if __name__ == "__main__":
    print('Server is working')
    process_client()

    

    