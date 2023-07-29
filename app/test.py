import copy

# 浅拷贝
list1 = [1, 2, [3, 4]]
list2 = copy.deepcopy(list1)
list2[2][0] = 999  # 修改浅拷贝对象的子对象，不会影响到原始对象
print(list1)  # 输出：[1, 2, [3, 4]]
    
    