import utils
import threading
from models.coupon_finder_db_model import Coupon

# 创建 threadlocal 对象
thread_local_data = threading.local()

def set_thread_local_data(value):
    # 设置线程局部数据
    thread_local_data.val = value

def get_thread_local_data():
    # 获取线程局部数据
    return thread_local_data.val

def worker_thread(value):
    set_thread_local_data(value)
    result = get_thread_local_data()
    print(f"Thread {threading.current_thread().name}: {result}")
    utils.get_current_ts()

# 创建多个线程
threads = []
for i in range(5):
    t = threading.Thread(target=worker_thread, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()