import re
import Clock
import Result

# 浮点数加法
FA = 2
# 浮点数乘法
FM = 6
# 浮点数除法 
FD = 12
# 整数运算
IU = 2
# 访问内存
AM = 2




class Instruction_Queue:
    def __init__(self,size = 10, filepath = '',issue_count = 2):
        # 用来存放指令的队列
        self.instruction_queue = []
        # 规定指令队列的大小
        self.size = size
        # 用来模拟加载到哪一个指令了
        self.pc = 1
        # 命令存放文件
        self.filepath = filepath
        self.issue_count = issue_count

    # 这个函数是为了将指令的字符串形式进行处理
    def read(self,instruction):
        words = instruction.split()
        return words

    # 将未处理过的指令读入到指令队列中,count表示一次性读取的命令数,用于多发射技术
    def push(self):
        if len(self.instruction_queue) < self.size:
            with open(self.filepath, "r") as file:
                for _ in range(self.issue_count):
                    # 每次将文件读取位置重置到开头
                    file.seek(0)
                    for current_line_number, line in enumerate(file, start=1):
                        if current_line_number == self.pc:
                            # 尝试添加
                            if len(self.instruction_queue) < self.size:
                                self.instruction_queue.append(line)
                            else:
                                return 
                            # 更新PC
                            words = self.read(line)
                            if words[0] == 'bne':
                                self.pc = self.jump
                            else:
                                if words[0] == 'Loop:':
                                    self.jump = self.pc
                                self.pc += 1
                            break
                return
            
    def issue(self,reservationstations,registers,clock,load_buffer,save_buffer,rob):
        if not Result.SE_H:
            return
        # 每次发射前都尝试加载数据到指令队列
        self.push()
        # 读取最新的指令
        for _ in range(self.issue_count):
            # 这里的SE_H是为了双发射场景下，另外的指令在bne之后被发射
            if self.instruction_queue == [] or not Result.SE_H:
                return 
            words = self.read(self.instruction_queue[0])
            op = words[0]


            # 因为都预测正确，所以肯定要跳转到这里，记录跳转的pc
            if op == 'Loop:':
                # self.jump = self.pc - 1
                # 重新获取操作符
                del words[0]
                op = words[0]


            timer = -1
            if op == "fadd.d" or op == "fsub.d":
                timer = FA
            # 判断是不是浮点数乘除法操作，放入浮点数乘法功能单元的保留站
            elif op == "fmul.d":
                timer = FM
            elif op == "fdiv.d":
                timer = FD
            # 判断是不是加载操作
            elif op == "ld" or op == "fld" or op == "sd" or op == "fsd":
                timer = AM
            # 整数功能单元
            # bne暂时归为整数单元中,
            elif op == 'bne':
                timer = IU
            else:
                timer = IU
            

            if op == "bne":
                # 不启用推测执行
                if Result.SE == False:
                    # 关闭issue功能，不再发射指令，直到执行完成
                    Result.SE_H = False
                words = [words[0],'pad',words[1],words[2]]
                # self.pc = self.jump
                index2 = rob.fill(words)
                if index2 != -1 and reservationstations.fill(words,registers,timer,index2,rob):
                    Result.ans[Result.index] = [self.instruction_queue[0],clock,-1,-1,-1]
                    Result.index += 1
                    del self.instruction_queue[0]
                else:
                    rob.clear(index2)
                    return

            elif op == "ld" or op == "fld" or op == "sd" or op == "fsd":
                # 拆一下
                result = re.split(r'\(|\)', words[-1])
                result = [item for item in result if item]
                words = [words[0],words[1]] + result
                if op == "ld" or op == "fld":
                    # 有bug，可能会出现，保留站填进去了，load_buffer没填进去
                    index2 = rob.fill(words)
                    index1 = load_buffer.fill([words[0],words[1],f'{index2}_{op}'],registers,timer,index2)
                    if index1 != -1 and index2 != -1 and reservationstations.fill(words,registers,timer,index2,rob):
                        Result.ans[Result.index] = [self.instruction_queue[0],clock,-1,-1,-1]
                        Result.index += 1
                        del self.instruction_queue[0]
                    # 回滚
                    else:
                        load_buffer.clear(index1)
                        rob.clear(index2)
                        return

                if op == "sd" or op == "fsd":
                    index2 = rob.fill(words)
                    index1 = save_buffer.fill([words[0],words[1],f'{index2}_{op}'],registers,timer,index2,rob)
                    if index1 != -1 and index2 != -1 and reservationstations.fill(words,registers,timer,index2,rob):
                        Result.ans[Result.index] = [self.instruction_queue[0],clock,-1,-1,-1]
                        Result.index += 1
                        del self.instruction_queue[0]
                    # 回滚
                    else:
                        save_buffer.clear(index1)
                        rob.clear(index2)
                        return
            else:
                index2 = rob.fill(words)
                # 判定顺序不能变！！依靠代码短路来保证正确性！！
                if index2 != -1 and reservationstations.fill(words,registers,timer,index2,rob):
                    # 成功填入
                    Result.ans[Result.index] = [self.instruction_queue[0],clock,-1,-1,-1]
                    Result.index += 1
                    del self.instruction_queue[0]
                else:
                    rob.clear(index2)
                    return