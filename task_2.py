word_1 = b'class'
word_2 = b'function'
word_3 = b'method'

word_list = [word_1, word_2, word_3]

for word in word_list:
    wt = type(word)
    lw = len(word)
    print(word, ' ', wt, ' ', lw)

    
