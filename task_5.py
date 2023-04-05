import subprocess
import chardet

args_youtube = ['ping', 'youtube.com']
youtube_ping = subprocess.Popen(args_youtube, stdout=subprocess.PIPE)
for line in youtube_ping.stdout:
    result = chardet.detect(line)
    print(result)
    line = line.decode(result['encoding']).encode('utf-8')
    print(line.decode('utf-8'))

args_yandex = ['ping', 'yandex.ru']
yandex_ping = subprocess.Popen(args_yandex, stdout=subprocess.PIPE)
for line in yandex_ping.stdout:
    result = chardet.detect(line)
    print(result)
    line = line.decode(result['encoding']).encode('utf-8')
    print(line.decode('utf-8'))
