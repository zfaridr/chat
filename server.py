from socket import *
import time
import json

s = socket(AF_INET, SOCK_STREAM)
s.bind(('', 8866))
s.listen(10)

def probe():
    data_to_send = f"You are online + {time.ctime(time.time())}"
    client.send(json.dumps(data_to_send).encode('utf-8'))
    

def process_message():
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
        print(data['message'])
    elif data['action'] == 'quit':
        client.send(json.dumps('Goodbye').encode('utf-8'))
        print('Client leaved the chat')
        client.close()
       
              
    
if __name__ == "__main__":
    while True:
        client, addr = s.accept()
        print("Получен запрос на соединение от %s" % str(addr))
        process_message()

    

    