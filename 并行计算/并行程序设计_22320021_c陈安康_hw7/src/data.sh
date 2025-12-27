#!/bin/bash

# 输出 CSV 表头
echo "threads,schedule,implementation,time" > performance.csv

# 线程数和调度类型列表
threads_list="1 2 4 8 16 20"
schedule_types=(0 1 2)  # 0: static, 1: dynamic, 2: guided

# 测试自定义 parallel_for 实现 (diy)
for threads in $threads_list; do
    for sched in "${schedule_types[@]}"; do
        echo "Running diy with $threads threads and schedule $sched..."
        output=$(./diy $threads $sched 10 | grep "耗时 =")
        time=$(echo "$output" | grep -oP "[0-9.]+(?= 秒)")
        echo "$threads,$sched,diy,$time" >> performance.csv
    done
done

# 测试 OpenMP heated_plate 实现（无调度策略参数）
for threads in $threads_list; do
    echo "Running heated_plate_openmp with $threads threads..."
    output=$(./heated_plate_openmp $threads | grep "Wallclock time")
    time=$(echo "$output" | awk '{print $4}')
    echo "$threads,NA,openmp,$time" >> performance.csv
done

echo "所有实验数据已写入 performance.csv"
