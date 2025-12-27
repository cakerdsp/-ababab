class StuData():
    def __init__(self,file):
        with open(file) as f_obj:
            self.data=[]
            for line in f_obj.readlines():
                line.rstrip('\n')
                row=line.split()
                self.data.append(row)
    
    def AddData(self,name,stu_num,gender,age):
        row=[name,stu_num,gender,age]
        self.data.append(row)

    def SortData(self,rule):
        if rule=='name':
            self.data.sort(key=(lambda obj:obj[0]))
        elif rule=='stu_num':
            self.data.sort(key=(lambda obj:int(obj[1])))
        elif rule=='gender':
            self.data.sort(key=(lambda obj:obj[2]))
        else:
            self.data.sort(key=(lambda obj:int(obj[3])))

    def ExportFile(self,filename):
        with open(filename,'w') as f_obj:
            s=' '
            for line in self.data:
                f_obj.write(s.join(line)+'\n')

test=StuData("student.txt")
print(test.data)
test.AddData('hhh', '250', 'M', '1080')
print(test.data)
test.SortData('stu_num')
print(test.data)
test.ExportFile('test.txt')
print(test.data)

