word_1 = 'attribute'
word_2 = 'класс'
word_3 = 'функция'
word_4 = 'type'

word_list = [word_1, word_2, word_3, word_4]

# Вариант 1
for word in word_list:
    try:
        print(bytes(word, 'ascii'))
    except UnicodeEncodeError:
        print(f' "{word}" can not be bytes string')