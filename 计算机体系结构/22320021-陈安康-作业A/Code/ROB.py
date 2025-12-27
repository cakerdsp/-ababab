class ROB_item:
    def __init__(self):
        self.op = ''
        self.status = 'idle'
        self.result = ''

        self.destination = ''
    
    # 更新寄存器，内存我默认不会有冲突
    def commit(self,registers):
        if self.status == 'ready':
            if self.destination in registers.registers and self.result == registers.registers[self.destination]:
                registers.registers[self.destination] = ''
            self.clear()
            return True
        return False



    def fill(self,words,result):
        self.status = 'busy'
        self.op = words[0]
        self.result = result
        if self.op == "sd" or self.op == "fsd":
            self.destination = 'memary'
        else:
            self.destination = words[1]


    # 针对cdb
    def listen(self,cdb):
        if self.status == 'busy' and cdb.broadcast() == self.result:
            self.status = 'ready'


    def clear(self):
        self.op = ''
        self.status = 'idle'
        self.result = ''
        self.destination = ''
    
    def __str__(self):
        p = str({'status' : self.status,
        'op' : self.op,
        'result' : self.result,
        'destination' : self.destination
        }) + '\n'
        return p


class ROB:
    def __init__(self,size = 10):
        self.size = size
        # 指示头部位置
        self.start = 0
        self.items = [ROB_item() for _ in range(self.size)]

    def commit(self,registers):
        while self.items[self.start].status == 'ready':
            self.items[self.start].commit(registers)
            self.start = (self.start + 1) % self.size

    def fill(self,words):
        i = self.start
        for _ in range(self.size):
            if self.items[i].status == 'idle':
                self.items[i].fill(words,i)
                return i
            i = (i + 1) % self.size
        return -1

    def listen(self,cdb):
        for item in self.items:
            item.listen(cdb)

    def clear(self,i):
        if i == -1:
            return 
        self.items[i].clear()

    def __str__(self):
        p = "ROB:\n"
        for item in self.items:
            p = p + str(item)
        return p

        