import re

s = "32(f2)"
# 使用正则表达式分割字符串
result = re.split(r'\(|\)', s)
# 过滤空字符串
result = [item for item in result if item]
print(result)  # 输出: ['32', 'x2']