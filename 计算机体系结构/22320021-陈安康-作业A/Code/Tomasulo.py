# 除法与乘法共享一个功能单元

# 多发射情况下，每周期的指令读取是按照指令队列中的顺序读取多条指令的

# 浮点数的加载存储和普通的加载存储都是使用同一个缓冲区
# 没有双向箭头 放心大胆做就行

# 所有模块解耦开吧
# 由于load 和 store也有保留站，这里在load和store里集成一下，不用！直接放进去就行，在iq里面处理一下就可以

# tomasulo 算法

# 要传输结果，这里就传时间clock

# 假设内存可以随时访问
# cdb 冲突，排队等待 占fcu？

# 先全部更新一波，然后看cdb有没有值，若有，就listen + update来一波
# fill放最后，等该清的都差不多后再装填


# rob只会影响rob的标号和寄存器的更新


# 因为bne和store指令都不会写cdb，若要通知rob，则需要直接与rob通信

# 不能只从ROB拿值，最好ROB和CDB都拿

# 尝试解决双发射的顺序问题，这里实现效果是在同一个周期依次发射，若某一个发射失败，就中断

# 当保留站的多个项抢占FCU时，谁能抢到是和它们在保留栈中的位置以及执行情况决定的，不依据入栈先后顺序

# 单独写一个文件去放
# bne 和 store指令因为不写CDB，但实现代码中统一留出来了CDB的时钟周期，所以为了平衡掉，这里通过获取满足的数据时直接计时器减1来平衡掉写CDB的一周期延迟
# bne和store指令显示告诉rob，因为这俩不写cdb


# 如何不使用ROB：把ROB大小设无限大，寄存器走cdb更新，rob的提交中的更新寄存器操作被注释掉即可
import Clock
import Result
from Registers import *
from Instruction_Queue import *
from ReservationStation import *
from Load_Save_Buffer import *
from CDB import *
from ROB import *

rob = ROB()
instruction_queue = Instruction_Queue(filepath = "../set2.txt")
reservationstation = RS()
load_buffer = Load_Buffer()
save_buffer = Save_Buffer()
cdb = CDB()
registers = registers()


instruction_queue.issue(reservationstation,registers,Clock.clock,load_buffer,save_buffer,rob)
while(Clock.clock < 30):
    # 指令发射
    # 如果CDB没有更新，那么ROB如果有之前有想要的值，也不会拿到了，所以要每次都看一遍ROB
    load_buffer.listen(cdb)
    load_buffer.update(cdb)
    save_buffer.listen(cdb,rob)
    save_buffer.update(rob)
    reservationstation.listen(cdb,rob)
    reservationstation.update(cdb,rob)

    if cdb.broadcast() != '' or Result.Store_Done:

        # registers.update(cdb)

        rob.listen(cdb)
        load_buffer.listen(cdb)
        load_buffer.update(cdb)

        save_buffer.listen(cdb,rob)
        save_buffer.update(rob)

        reservationstation.listen(cdb,rob)
        reservationstation.update(cdb,rob)

        # rob.listen(cdb)
        rob.commit(registers)
        Result.Store_Done = False

    # 输出函数
    # with open('output3_rob.txt', 'a', encoding='utf-8') as file:
    #     file.write(f"CLOCK : {Clock.clock}\n")
    #     file.write(str(rob))
    #     file.write('\n')
    #     file.write(str(registers))
    #     file.write('\n')
    #     file.write(str(reservationstation))
    #     file.write('\n')
    #     file.write(str(load_buffer))
    #     file.write('\n')
    #     file.write(str(save_buffer))
    #     file.write('\n')
    #     file.write('\n')


    Clock.clock += 1
    instruction_queue.issue(reservationstation,registers,Clock.clock,load_buffer,save_buffer,rob)
    cdb.clear()

# with open('example.txt', 'a', encoding='utf-8') as file:
#     file.write(f"CLOCK : {Clock.clock}\n")
#     file.write(str(rob))
#     file.write('\n')
#     file.write(str(registers))
#     file.write('\n')
#     file.write(str(reservationstation))
#     file.write('\n')

print(Result.ans) 


