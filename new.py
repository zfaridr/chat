import inspect

def fun():
    print (inspect.stack()[1][3])

def func():
    fun()

func()