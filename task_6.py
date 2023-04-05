from chardet import detect

with open('project/chat/test_file.txt', 'rb') as file:
    content = file.read()

print(detect(content))
encoding = detect(content)['encoding']
print(encoding)

with open('project/chat/test_file.txt', 'r', encoding=encoding) as file:
    content = file.read()
print(content)