word_1 = 'разработка'
word_2 = 'администрирование'
word_3 = 'protocol'
word_4 = 'standard'

word_list = [word_1, word_2, word_3, word_4]

word_b_list = []

for word in word_list:
    word_b = word.encode('utf-8')
    word_b_list.append(word_b)

print(word_b_list)

word_str_list = []
for word_b in word_b_list:
    word_str = word_b.decode('utf-8')
    word_str_list.append(word_str)

print(word_str_list)