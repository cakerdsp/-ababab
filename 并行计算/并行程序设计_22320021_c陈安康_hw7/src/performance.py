import csv
import matplotlib.pyplot as plt
import seaborn as sns

# 使用 Seaborn 样式
sns.set(style="whitegrid")

# 数据结构: {implementation: {schedule: {threads: time}}}
data = {'diy': {0: {}, 1: {}, 2: {}}, 'openmp': {'NA': {}}}

# 读取 CSV 文件
with open('performance.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # 处理 'NA' 值
        try:
            threads = int(row['threads'])
            schedule = row['schedule']
            time = float(row['time']) if row['time'] != 'NA' else float('nan')  # 将 'NA' 转为 NaN
            implementation = row['implementation']
        except ValueError:
            continue  # 跳过无法转换的数据

        if implementation in data:
            if schedule != 'NA':  # 对 diy 进行处理
                schedule = int(schedule)  # 转换为整数
                data[implementation][schedule][threads] = time
            else:  # 对 openmp 只按 NA 进行处理
                data[implementation]['NA'][threads] = time

# 绘图
schedules = {0: 'static', 1: 'dynamic', 2: 'guided'}
colors = {0: 'red', 1: 'green', 2: 'blue'}

plt.figure(figsize=(12, 8))

# 绘制 diy 的数据
for sched in data['diy']:
    threads = sorted(data['diy'][sched].keys())
    times = [data['diy'][sched].get(t, float('nan')) for t in threads]  # 如果没有时间，使用 NaN
    plt.plot(threads, times, marker='o', label=f'diy - {schedules[sched]}', color=colors[sched], linewidth=2, markersize=8)

# 绘制 openmp 的数据
threads_openmp = sorted(data['openmp']['NA'].keys())
times_openmp = [data['openmp']['NA'].get(t, float('nan')) for t in threads_openmp]
plt.plot(threads_openmp, times_openmp, marker='s', label='openmp', color='black', linewidth=2, markersize=8)

# 美化图表
plt.title('Execution Time vs Threads for Different Implementations and Schedules', fontsize=16, fontweight='bold')
plt.xlabel('Number of Threads', fontsize=14)
plt.ylabel('Execution Time (seconds)', fontsize=14)
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.legend(fontsize=12, loc='upper right')
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.tight_layout()

# 保存和显示图表
plt.savefig('performance_plot_beautified.png')
plt.show()
