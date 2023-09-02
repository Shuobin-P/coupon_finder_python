import threading

# 定义一个线程执行的任务函数
def print_numbers():
    for i in range(1, 6):
        print(f"Thread {threading.current_thread().name}: {i}")

# 创建10个线程并启动它们
threads = []
for i in range(10):
    thread = threading.Thread(target=print_numbers)
    threads.append(thread)
    thread.start()

# 等待所有线程完成
for thread in threads:
    thread.join()

print("All threads have finished.")
