import redis
import threading

# 创建一个Redis连接
redis_client = redis.StrictRedis(host='localhost', port=6379, db=2, password='123456')

# 定义一个全局变量，用于存储加1的次数
counter = 0

def increment_age():
    global counter
    for _ in range(1000):
        # 自增操作
        redis_client.incr('age')
        # 原子操作，避免多线程竞争
        counter += 1
print("运行之前的值", redis_client.get('age'))

# 创建两条线程
thread1 = threading.Thread(target=increment_age)
thread2 = threading.Thread(target=increment_age)

# 启动两条线程
thread1.start()
thread2.start()

# 等待两条线程执行完毕
thread1.join()
thread2.join()

# 输出结果
final_value = int(redis_client.get('age'))
print(f"Final value in Redis: {final_value}")
print(f"Total increments: {counter}")