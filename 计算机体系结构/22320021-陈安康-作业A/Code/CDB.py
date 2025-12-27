import Clock
import Result
class CDB:
    def __init__(self):
        self.data = ''

    def write(self,data):
        if self.data == '':
            self.data = data
            return True
        else:
            return False

    def broadcast(self):
        return self.data
    
    def clear(self):
        self.data = ''