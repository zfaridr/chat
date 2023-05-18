import subprocess

processes_num = int(input('amount of processes: '))

num = 1

for num in range(processes_num):
    result = subprocess.Popen(f"python3 client_1.py", shell=True, stdout=subprocess.PIPE, encoding = 'utf-8')
    result.stdout
    out = result.stdout.read()
    num += 1
    

