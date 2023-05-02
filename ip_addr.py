import ipaddress
import tabulate
import os

ip_range = '80.0.1.0/28'
reachable_lst = []
unreachable_lst = []
lst_tab = []
columns = ['reachable', 'unreachable']


def host_ping(ip_addr):
    response = os.system(f'ping -c 4 {ip_addr} ')

    if response == 0:
        lst_tab.append((ip_addr, '-'))

    else:
        lst_tab.append(('-', ip_addr))
        


def host_range_ping(ip_ip):
    subnet = ipaddress.ip_network(ip_ip)
    ip_lst = list(subnet.hosts())
    for ip_addr in ip_lst:
        host_ping(ip_addr)
        

def host_range_ping_tab():
    host_range_ping(ip_range)
    print(lst_tab)
    print(tabulate(lst_tab))
   

host_range_ping_tab()



