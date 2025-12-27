import Clock
import Result
# load 只有busy和address
class Load_Buffer_Item:
    def __init__(self):
        self.address = ''
        # self.data = ''
        self.status = 'idle'
        self.timer = 0
        self.result = ''
        self.index = -1
        self.op_clock = -1

    def fill(self,words,registers,timer,result):
        op = words[0]
        self.address = words[2]
        self.status = 'wait'
        self.result = result
        self.index = Result.index
        self.timer = timer
        registers.registers[words[1]] = result



    def listen(self,cdb):
        if self.address == cdb.broadcast():
            self.address = ''
        # if self.data == cdb.broadcast():
        #     self.data = ''

    
    def update(self,cdb):
        if self.op_clock != Clock.clock:
            if self.status == 'wait':
                if self.address == '' and Result.LOCK_LOAD_STORE:
                    self.status = 'run'
                    # self.timer -= 1
                    Result.ans[self.index][3] = Clock.clock + 1
                    self.op_clock = Clock.clock
                    # 关锁
                    Result.LOCK_LOAD_STORE = False
                return
            if self.status == 'run' and self.timer == 0:
                # 首先写表格
                Result.ans[self.index][4] = Clock.clock
                # load 要写cdb
                if cdb.write(self.result):
                # 然后清空
                    self.clear()
                    # 应该是不用要
                # self.op_clock = Clock.clock
                    Result.LOCK_LOAD_STORE = True
                return
            if self.status == 'run':
                if self.timer != 0:
                    self.timer -= 1
                self.op_clock = Clock.clock
                return
    

    def clear(self):
        self.address = ''
        # self.data = ''
        self.status = 'idle'
        self.timer = 0
        self.result = ''
        self.index = -1
        self.op_clock = -1
    
    def __str__(self):
        p = str({
            "status" : self.status,
            "timer" : self.timer,
            "result" : self.result,
            "address" : self.address
        }) + '\n'
        return p

class Load_Buffer:
    def __init__(self,size = 5):
        self.items = [Load_Buffer_Item() for _ in range(size)]
        self.size = size
        self.op_clock = -1
    
    def update(self,cdb):
            for item in self.items:
                item.update(cdb)


    def listen(self,cdb):
        for item in self.items:
            item.listen(cdb)


    def fill(self,words,registers,timer,result):
            for item in self.items:
                if item.status == 'idle':
                    item.fill(words,registers,timer,result)
                    return self.items.index(item)
            return -1

    def clear(self,i):
        if i == -1:
            return 
        self.items[i].clear()

    def __str__(self):
        p = 'Load_Buffer:\n'
        for item in self.items:
            p = p + str(item)
        return p


class Save_Buffer_Item:
    def __init__(self):
        self.address = ''
        self.data = ''
        self.status = 'idle'
        self.timer = 0
        self.index = -1
        self.op_clock = -1
        self.result = ''
        


    def fill(self,words,registers,timer,result,rob):
        op = words[0]
        self.address = words[2]
        self.status = 'wait'
        self.timer = timer
        self.index = Result.index
        if registers.registers[words[1]] == '' or rob.items[registers.registers[words[1]]].status == 'ready':
            self.data = ''
        else:
            self.data = registers.registers[words[1]]
        self.result = result

        



    def listen(self,cdb,rob):
        if self.address == cdb.broadcast():
            self.address = ''
        if self.data == cdb.broadcast():
            self.data = ''

        # rob 只影响data
        if self.data != '' and rob.items[self.data].status == 'ready':
            self.data = ''

    
    def update(self,rob):
        if self.op_clock != Clock.clock:
            if self.status == 'wait':
                if self.address == '' and self.data == '' and Result.LOCK_LOAD_STORE:
                    self.status = 'run'
                    self.timer -= 1
                    Result.ans[self.index][3] = Clock.clock + 1
                    self.op_clock = Clock.clock
                    Result.LOCK_LOAD_STORE = False
                return 
            if self.status == 'run' and self.timer == 0:
                # 然后清空
                # result 对应rob中的编号
                rob.items[self.result].status = 'ready' 
                Result.LOCK_LOAD_STORE = True
                Result.Store_Done = True
                self.clear()
                self.op_clock = Clock.clock
                return
            if self.status == 'run':
                self.timer -= 1
                self.op_clock = Clock.clock
                return



    def clear(self):
        self.address = ''
        self.data = ''
        self.status = 'idle'
        self.timer = 0
        self.op_clock = -1
        self.index = -1
        self.result = ''
    
    def __str__(self):
        p = str({
            "status" : self.status,
            "timer" : self.timer,
            "result" : self.result,
            "data" : self.data,
            "address" : self.address
        }) + '\n'
        return p

# store有busy、address、和存入数据
class Save_Buffer:
    def __init__(self,size = 5):
        self.items = [Save_Buffer_Item() for _ in range(size)]
        self.size = size
    
    def update(self,rob):
            for item in self.items:
                item.update(rob)


    def listen(self,cdb,rob):
        for item in self.items:
            item.listen(cdb,rob)


    def fill(self,words,registers,timer,result,rob):
        for item in self.items:
            if item.status == 'idle':
                item.fill(words,registers,timer,result,rob)
                return self.items.index(item)
        return -1
    
    def clear(self,i):
        if i == -1:
            return
        self.items[i].clear()
    
    def __str__(self):
        p = 'Store_Buffer:\n'
        for item in self.items:
            p = p + str(item)
        return p