import Clock
import Result
# 以字典的形式组织
class registers:
    def __init__(self):
        self.registers = {
            'f0' : '',
            'f2' : '',
            'f4' : '',
            'f6' : '',
            'f8' : '',
            'x1' : '',
            'x2' : '',
            'x3' : '',
        }
    def update(self,cdb):
        for key,values in self.registers.items():
            if values == cdb.data:
                self.registers[key] = ''
    
    def __str__(self):
        p = ""
        p = p + "registers:\n"
        p = p + str(self.registers) + '\n'
        return p