from socket import *
import time
import json

s = socket(AF_INET,SOCK_STREAM)
s.connect(('localhost', 8866))


def presence(name):
    
    data = {
        "action": "presence",
        "time": time.time(),
        "type": "status",
        "user": {
            "account_name": name,
            "status": "online"

        }
    }
    data_to_send = json.dumps(data).encode("utf-8")
    s.send(data_to_send)
    msg_probe = s.recv(1000000).decode('utf-8')
    data_to_print = json.loads(msg_probe)
    print(data_to_print)
    
    return data

def chat_join():
    
    data = {
        "action": "join",
        "time": time.time(),
        "room": "#room_name"
    }

    data_to_send = json.dumps(data).encode("utf-8")
    s.send(data_to_send)
    msg_join = s.recv(1000000).decode('utf-8')
    data_to_print = json.loads(msg_join)
    print(data_to_print)

    return data_to_print

def chat_message(name):
  
    message = str(input("Input you message "))
    data = {
        "action": "msg",
        "time": time.time(),
        "to": "#room_name",
        "from": name,
        "message": message,
    }
    data_to_send = json.dumps(data).encode("utf-8")
    s.send(data_to_send)
    msg_msg = s.recv(1000000).decode('utf-8')
    data_to_print = json.loads(msg_msg)
    print(data_to_print)
    
    return data_to_print

def chat_quit():
    
    data = {
        "action": "quit",
        "time": time.time(),
        "room": "#room_name",
    }
    data_to_send = json.dumps(data).encode("utf-8")
    s.send(data_to_send)
    msg_quit = s.recv(1000000).decode('utf-8')
    data_to_print = json.loads(msg_quit)
    print(data_to_print)
    s.close()

    return data_to_print
    

def main(option):
   
    if option == 1:
        presence('zfaridr')
    elif option == 2:
        chat_join()
    elif option == 3:
        chat_message('zfaridr')
    elif option == 4:
        chat_quit()
        

if __name__ == "__main__":
    while True:
        option = int(input("Choose option: 1 - Connect to server, 2 - Join chat, 3 - Send a message, 4- Quit "))
        
        main(option)
    

    

    