import os

def host_ping():
    host_name = input('input host name ')
    response = os.system(f'ping -c 4 {host_name} ')

    if response == 0:
        print(f'host {host_name} is reachable')
    else:
        print(f'host {host_name} is unreacheble')

host_ping()
