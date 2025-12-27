# 保留站是有三种的，所以目前的思路是实现保留站中的每一项实现一个类，然后再一个类去包含项，然后再来一个类去统领它们
import Clock
import Result

# 要传输结果，这里就传时间clock
import CDB
import Registers

# 用来实现基本的保留站项
class RS_item:
    def __init__(self):
        # 计数器，当指令处于执行状态时用于计数
        self.timer = 0
        # 记录保留项的状态
        self.status = 'idle'
        # 有关项
        self.op =''
        self.vj = ''
        self.vk = ''
        self.qj = ''
        self.qk = ''
        self.index = -1
        self.result = ''
        self.op_clock = -1


    # 装填保留站,结果是ROB的序号，用来广播时握手
    def fill(self,words,registers,timer,result,rob):
        self.status = 'wait'
        self.timer = timer
        # 获取操作字
        self.op = words[0]
        # 判断是不是寄存器,这里分别对应常数，寄存器已经是最新值，寄存器不是最新值，但是ROB中结果已经计算，只是没有提交
        if words[2] not in registers.registers or registers.registers[words[2]] == '' or (rob.items[registers.registers[words[2]]].status == 'ready'):
           self. vj = words[2]
        else:
            self.qj = registers.registers[words[2]]
        if words[3] not in registers.registers or registers.registers[words[3]] == '' or (rob.items[registers.registers[words[3]]].status == 'ready'):
           self. vk = words[3]
        else:
            self.qk = registers.registers[words[3]]
        # 更新保留站的结果
        self.index = Result.index
        self.result = result
        # 对寄存器组状态的更新
        # load由缓冲区自己更新，store不更新
        if not(self.op == "ld" or self.op == "fld" or self.op == "sd" or self.op == "fsd"):
            if words[1] in registers.registers:
                registers.registers[words[1]] = result


    # 监听CDB
    def listen(self,cdb,rob):
        # 插cdb
        if self.qj == cdb.broadcast():
            self.vj = cdb.broadcast()
            self.qj = ''
        if self.qk == cdb.broadcast():
            self.vk = cdb.broadcast()
            self.qk = ''
        # 查rob
        if self.qj != '' and rob.items[self.qj].status == 'ready':
            self.vj = rob.items[self.qj].result
            self.qj = ''
        if self.qk != '' and rob.items[self.qk].status == 'ready':
            self.vk = rob.items[self.qk].result
            self.qk = ''    

    # 更新状态的
    # 这里的fcu传进来的是状态
    # 状态转移图
    #  用返回值来告诉上层它改没改fcu，便于判断其是不是fcu目前的使用者
    # rob只有bne才用得到
    def update(self, fcu_status,cdb,rob = False):
        if self.op_clock != Clock.clock:
            if self.status == 'wait':
                if self.qj == '' and self.qk == '' and  fcu_status == 'idle':
                    # 这里到底要不要减1还是要考虑考虑
                    Result.ans[self.index][2] = Clock.clock + 1
                    # 这里的减1在硬件上没有逻辑，纯粹是为了使bne store指令这些不写CDB的指令在观感上跳过写CDB的停顿
                    if self.op == 'bne':
                        self.timer -= 1
                    self.status = 'run'
                    # self.timer -= 1
                    fcu_status = 'run'
                    self.op_clock = Clock.clock
                    return 1, fcu_status# 修改了fcu
                return -1, fcu_status
            # 为了逻辑正确，这个要放减法前面
            # 执行结束
            if self.status == 'run' and self.timer == 0:
                # cdb 获取数据
                # bne没有写回阶段
                if self.op != 'bne':
                    if self.op != 'sd' or self.op != 'fsd':
                        Result.ans[self.index][4] = Clock.clock
                    if cdb.write(self.result):
                    # 写表格
                    # 清空
                        fcu_status = 'idle'
                        self.clear()
                        return 2, fcu_status
                else:
                    # 解除发射限制
                    Result.SE_H = True
                    rob.items[self.result].status = 'ready'
                    fcu_status = 'idle'
                    self.clear()
                    return 2, fcu_status
                return -1, fcu_status # 告知当前fcu没人使用，把使用者设为-1
            if self.status == 'run':
                if self.timer != 0: 
                    self.timer -= 1
                self.op_clock = Clock.clock
                return -1, fcu_status
            # 已经执行完成
            return -1, fcu_status
        else:
            return -1,fcu_status
  

    def clear(self):
        self.timer = 0
        # 记录保留项的状态
        self.status = 'idle'
        # 有关项
        self.op =''
        self.vj = ''
        self.vk = ''
        self.qj = ''
        self.qk = ''
        self.index = -1
        self.result = ''
        self.op_clock = -1

    def __str__(self):
        p = str({"status" : self.status, 
        "timer" : self.timer,
        "op" : self.op, 
        "result" : self.result,
        "vj" : self.vj, 
        "vk" : self.vk,
        "qj" : self.qj,
        "qk" : self.qk,
        }) + '\n'
        return p


# # 浮点数加法的保留站
# class RS_FA:
#     def __init__(self,size = 3):
#         self.items = [RS_item() for _ in range(size)]
#         self.size = size

#     def update(self,fcu_status,cdb):
#         for item in self.items:
#             item.update()

#     # 若保留站满了，你就要阻塞，所以要返回bool值来供指令队列判断
#     def fill(self,words,registers,timer):
#         for item in self.items:
#             if item.status == 'idle':
#                 item.fill(words,registers,timer)
#                 return True
#         return False
        



# # 浮点数乘法的保留站
# class RS_FM:
#     def __init__(self,size = 2):
#         self.items = [RS_item() for _ in range(size)]
#         self.size = size

#     def update(self,fcu_status,cdb):
#         for item in self.items:
#             item.update()

#     # 若保留站满了，你就要阻塞，所以要返回bool值来供指令队列判断
#     def fill(self,words,registers,timer):
#         for item in self.items:
#             if item.status == 'idle':
#                 item.fill(words,registers,timer)
#                 return True
#         return False




# # 整数单元（Integer Unit）的保留站
# class RS_IU:
#     def __init__(self,size = 2):
#         self.items = [RS_item() for _ in range(size)]
#         self.size = size

#     def update(self,fcu_status,cdb):
#         for item in self.items:
#             item.update()

#     # 若保留站满了，你就要阻塞，所以要返回bool值来供指令队列判断
#     def fill(self,words,registers,timer):
#         for item in self.items:
#             if item.status == 'idle':
#                 item.fill(words,registers,timer)
#                 return True
#         return False

        



# 包括fcu
class RS_ITEMS:
    def __init__(self,size = 3):
        self.items = [RS_item() for _ in range(size)]
        self.size = size

        self.fcu_status = "idle"
        self.fcu_user = -1 # -1表示未使用,可能没有用,应该真没用
    # rob只有bne用得到
    def update(self,cdb,rob = False):
        for item in self.items:
            code,self.fcu_status = item.update(self.fcu_status,cdb,rob)
            if code == 1:
                self.fcu_user = self.items.index(item)
            if code == 2:
                self.fcu_user = -1

    # 若保留站满了，你就要阻塞，所以要返回bool值来供指令队列判断
    def fill(self,words,registers,timer,result,rob):
        for item in self.items:
            if item.status == 'idle':
                item.fill(words,registers,timer,result,rob)
                return True
        return False

    def listen(self,cdb,rob):
        for item in self.items:
            item.listen(cdb,rob)

    def __str__(self):
        p = ""
        for item in self.items:
            p = p + str(item)

        return p

# 最后统管算有保留站的
class RS:
    def __init__(self):
        self.rs_fa = RS_ITEMS(3)
        self.rs_fm = RS_ITEMS(2)
        self.rs_iu = RS_ITEMS(5)
        self.rs_sd_ld = RS_ITEMS(5)
        self.rs_bne = RS_ITEMS(2)



    def update(self,cdb,rob):
        self.rs_fa.update(cdb)
        self.rs_fm.update(cdb)
        self.rs_iu.update(cdb)
        self.rs_sd_ld.update(cdb)
        self.rs_bne.update(cdb,rob)



    def listen(self,cdb,rob):
        self.rs_fa.listen(cdb,rob)
        self.rs_fm.listen(cdb,rob)
        self.rs_iu.listen(cdb,rob)
        self.rs_sd_ld.listen(cdb,rob)
        self.rs_bne.listen(cdb,rob)

    # 供instruction_queue调用的,clock是结果
    def fill(self,words,registers,timer,clock,rob):
        # 获取op
        op = words[0]
        # 判断是不是浮点数加减法操作，放入浮点数加法功能单元的保留站
        if op == "fadd.d" or op == "fsub.d":
            return self.rs_fa.fill(words,registers,timer,clock,rob)
        # 判断是不是浮点数乘除法操作，放入浮点数乘法功能单元的保留站
        elif op == "fmul.d" or op == "fdiv.d":
             return self.rs_fm.fill(words,registers,timer,clock,rob)
        # 判断是不是加载操作
        elif op == "ld" or op == "fld" or op == "sd" or op == "fsd":
            return self.rs_sd_ld.fill(words,registers,timer,f'{clock}_{op}',rob)
        # 整数功能单元
        elif op == 'bne':
            return self.rs_bne.fill(words,registers,timer,clock,rob)
        else:
            return self.rs_iu.fill(words,registers,timer,clock,rob)


    def __str__(self):
        p = ""
        p = p + "rs_fa:\n"
        p = p + str(self.rs_fa)
        p = p + "rs_fm:\n"
        p = p + str(self.rs_fm)
        p = p + "rs_iu:\n"
        p = p + str(self.rs_iu)
        p = p + "rs_sd_ld:\n"
        p = p + str(self.rs_sd_ld)
        p = p + "rs_bne:\n"
        p = p + str(self.rs_bne)
        return str(p)
