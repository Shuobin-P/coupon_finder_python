def log(func):
    def wrapper(x, y):
        func(x,y)
        print("运行了一些东西. 参数是")
    return wrapper
@log
def add(x, y):
    print("x+y= ", x+y)

add(4, 5)