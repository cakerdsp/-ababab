def unity(s1,s2,ans) :
    if '(' in s1 and '(' in s2 :#有两个嵌套的
        f1,its1 = split_items(s1)
        f2,its2 = split_items(s2)
        if f1 == f2 :
            if len(its1) != len(its2) :
                return False
            for i in range(len(its1)) :
                flag = unity(its1[i],its2[i],ans)
                if not flag :
                    return False
            return True
        else :
            return False
    elif '(' in s1 :#有一个嵌套的
        if not judge_var(s2) :
            return False
        vall = find(s2,ans) 
        if vall != None :
            if vall != s1 :
                return False
            else :
                return True
        f1,its1 = split_items(s1)
        for it in its1 :
            if it == s2 :
                return False
            val = find(it,ans)
            if val is not None :
                id = its1.index(it)
                its1[id] = val
            if '(' in it :
                flag = unity(s2,it,ans)
                if flag == False :
                    return False
                else :
                    val = ans[s2]
                    id = its1.index(it)
                    its1[id] = val
                    ans.pop(s2)
        new_s1 = f1 + "(" + ','.join(its1) + ")"
        ans[s2] = new_s1
        return True
    elif '(' in s2 :#有一个嵌套的
        if not judge_var(s1) :
            return False
        vall2 = find(s1,ans) 
        if vall2 != None :
            if vall2 != s2 :
                return False
            else :
                return True
        f1,its1 = split_items(s2)
        for it in its1 :
            if it == s1 :
                return False
            val2 = find(it,ans)
            if val2 is not None :
                id = its1.index(it)
                its1[id] = val2
            if '(' in it :
                flag = unity(s1,it,ans)
                if flag == False :
                    return False
                else :
                    val = ans[s1]
                    id = its1.index(it)
                    its1[id] = val
                    ans.pop(s1)
        new_s2 = f1 + "(" + ','.join(its1) + ")"
        ans[s1] = new_s2
        return True     
    else :#两个都是不嵌套的
        val = find(s1,ans)
        val2 = find(s2,ans)
        if judge_var(s1) and judge_var(s2) :
            if val is not None and val2 is not None :
                flag = unity(val,val2,ans)
                return flag
            elif val is not None :
                ans[s2] = val
                return True
            elif val2 is not None :
                ans[s1] = val2
                return True
            else :
                ans[s1] = s2
                return True
        elif judge_var(s1) :
            if val is not None and val2 is not None :
                flag = unity(val,val2,ans)
                return flag
            elif val is not None :
                flag = unity(val,s2,ans)
                return flag
            elif val2 is not None :
                ans[s1] = val2
                return True
            else :
                ans[s1] = s2
                return True
        elif judge_var(s2) :
            if val is not None and val2 is not None :
                flag = unity(val,val2,ans)
                return flag
            elif val is not None :
                ans[s2] = val
                return True
            elif val2 is not None :
                flag = unity(s1,val2,ans)
                return flag
            else :
                ans[s2] = s1
                return True
        else :
            return False
        
def dict_to_string_with_equals(dictionary):
    # 使用列表推导式遍历字典的键值对，并将冒号替换为等号
    items = ['{}={}'.format(str(key), str(value)) for key, value in dictionary.items()]
    # 将替换后的键值对用逗号连接成字符串
    result = ', '.join(items)
    result_with_brackets = '{' + result + '}'
    return result_with_brackets

#在合一集里面找
def find(var,ans) :
    if var in ans.keys() :
        return ans[var]

#def search(s1,s2,ans) :
#    val = find(s1,ans)
#    if val != None and val != s2 :
#        return False
#    elif val == s2:

#这个函数的出现纯粹是为了函数项有多个参数而考虑的，目的是为了将因逗号分割开的一个完整的函数合并起来
def merge(pos,list) :
    new_list = []
    for it in list[pos+1:] :
        if '(' in it :
            id = list.index(it)
            new_list = merge(id,list)
            break
        if ')' in it :
            id = list.index(it)
            new_list = list[:pos] + [','.join(list[pos:id+1])] + list[id+1:]
            return new_list
    for it in new_list[pos+1:] :
        if ('(' not in it) and (')' in it) :
            id = new_list.index(it)
            new_list = new_list[:pos] + [','.join(new_list[pos:id+1])] + new_list[id+1:]
            return new_list


#拆分括号的函数
def split_items(strr) :
    p, items = strr.split('(',1)
    items = items[:-1]
    items = items.split(',')
    flag = True
    while flag :
        for it in items :
            if '(' in it and ')' not in it :
                id = items.index(it)
                flag = True
                items = merge(id,items)
                break
            else :
                flag = False
    return p,items


#判断是不是变量
def judge_var(it) :
    if len(it) ==2 and it[0] == it[1] :
        return True
    else :
        return False



def MGU(str1,str2) :
    ans = {}
    queue1 = {}
    queue2 = {}
    queue3 = {}

    _,items1 = split_items(str1)
    _,items2 = split_items(str2)
    if len(items1) != len(items2) :
        return {}
    n = len(items1)
    for i in range(n) :
        if items1[i] != items2[i] :
            if ((judge_var(items1[i]) and (not judge_var(items2[i]) and '(' not in items2[i])) or ((not judge_var(items1[i]) and '(' not in items1[i]) and judge_var(items2[i]))) :
                flag = unity(items1[i],items2[i],ans)
                if not flag :
                    return {}
            elif judge_var(items1[i]) and judge_var(items2[i]) :
                queue3[items1[i]] = items2[i]
            elif '(' in items1[i] and '(' in items2[i] :
                queue1[items1[i]] = items2[i]
            elif '(' in items1[i] or '(' in items2[i] :
                queue2[items1[i]] = items2[i]
            else :
                flag = unity(items1[i],items2[i],ans)
                if not flag :
                    return {}
    for key,value in queue3.items() :
        flag = unity(key,value,ans)
        if not flag :
            return {}
    for key,value in queue1.items() :
        flag = unity(key,value,ans)
        if not flag :
            return {}
    for key,value in queue2.items() :
        flag = unity(key,value,ans)
        if not flag :
            return {}
    return ans


def sort_rule(it) :
    return len(it)








def replacement(dist,res) :#这个res是已经归结后的子句
    new_res = []
    for it in res :
        p,items = split_items(it)
        for a in items :
            if find(a,dist) :#会有问题吗？
                val = find(a,dist)
                id = items.index(a)
                items[id] = val
        strr = p + '(' + ','.join(items) + ')'
        new_res.append(strr)
    return new_res

def merge2(c1,c2):
    for l1 in c1 :
        for l2 in c2 :
            p1,_ = split_items(l1)
            p2,_ = split_items(l2)
            if p1 == '~' + p2 or '~' + p1 == p2 :
                mgu = MGU(l1,l2)#返回了一个字典
                if l1 == '~' + l2 or '~' + l1 == l2 or mgu != {} :
                    res = [l for l in c1 if l != l1]+[l for l in c2 if l != l2]
                    res = list(set(res))
                    new_res = replacement(mgu,res)
                    new_res = list(set(new_res))
                    new_res.append(c1.index(l1))
                    new_res.append(c2.index(l2))
                    return mgu,new_res#归结完的元组，这里要有一个函数依据字典进行替换
    return None,None






def backtracking(visited,tmp2_kb,kb,pos_in_ziju) :
    for i in range(len(kb)) :
        visited.insert(0,[])
    #先将初始子句放入
    res = []
    step = len(kb)
    #visited和tmp_kb里面的每个归结产生的子句是--对应的
    i = 0
    step_index = [len(tmp2_kb)-1]
    for it in step_index :
        pos = visited[it]
        for e in pos :
            if e > step - 1 :
                step_index.append(e)
    step_index = list(set(step_index))#去重
    step_index = sorted(step_index)#对子句在tmp_kb里面的标号从小到大排序
    #step_index.remove(-1)#去掉-1
    for i in step_index :#step_index里面存放了所有有用的非原始的子句的标号
        res.append(tmp2_kb[i])
    #step_index和visited同时也天然形成了给了我们查询对应关系的一个映射表
    return res,step_index


#打印出了初始子句外的其他子句
def print_steps(res,step_index,visited,pos_in_ziju,mgu,kb,tmp2_kb) :
    step = 1
    ans = []
    for c in kb:
        s = f"{str(step)} " + str(c) + ","
        step = step + 1
        ans.append(s)
    a = step - 1
    for i in range(a) :
        mgu.insert(0,[])
        pos_in_ziju.insert(0,[])
    for i in range(len(res)) :
        v = list(visited[step_index[i]])
        v = sorted(v)#因为set是无序的，想要和pos_in_zifu对应，要从大到小排序
        if v[0] >= a :
            id1 = step_index.index(v[0]) + a + 1
        else :
            id1 = v[0] + 1
        if v[1] >= a:
            id2 = step_index.index(v[1]) + a + 1
        else :
            id2 = v[1] + 1
        idt1 = pos_in_ziju[step_index[i]][0]
        idt2 = pos_in_ziju[step_index[i]][1]
        #上面这些代码主要是做一个有用子句当前的依赖关系的获取，通过在tmp2_kb中位置信息以及依赖关系进行映射得到
        if len(tmp2_kb[v[0]]) != 1 :
            c1 = 97 + idt1
        else :
            c1 = 0
        if len(tmp2_kb[v[1]]) != 1 :
            c2 = 97 + idt2
        else :
            c2 = 0
        strr = str(step) + f" R[{str(id1)}{chr(c1)},{str(id2)}{chr(c2)}]" + str(mgu[step_index[i]]) + " = " + str(res[i]) + f"{',' if res[i] != () else ''}"
        ans.append(strr)
        step = step + 1#执行的步骤
    return ans


def ResolutionProp(KB):#直接加入
    visited = []#放归结过的句子的序号对，同时作为映射为后续回溯提供依据
    tmp_KB = []#存放排序的子句
    pos_in_ziju = []#存放子句内的位置用来标定abcd的
    tmp2_KB = KB[:]#按照进入顺序存放子句
    mgu_list = []#存放mgu结果
    hhh = False
    while True :
        flag = False
        for i, c1 in enumerate(tmp_KB) :
            for j, c2 in enumerate(tmp_KB) :
                if i < j :
                    suoyin1 = tmp2_KB.index(c1)
                    suoyin2 = tmp2_KB.index(c2)
                    if {suoyin1,suoyin2} not in visited :
                        mgu1,new_list = merge2(c1,c2)
                        if new_list is not None :
                            idt1 = new_list[-2]#merge2函数默认将子句内的位置信息放置在最后两个元素中
                            idt2 = new_list[-1]
                            new_list.remove(idt1)
                            new_list.remove(idt2)
                            new_tuple = tuple(new_list)#归结的子句转成元组
                            mgu = dict_to_string_with_equals(mgu1)#mgu转成特定的输出形式
                            if new_tuple not in tmp2_KB :
                                tmp2_KB.append(new_tuple)
                                id1 = tmp2_KB.index(c1) + 1
                                id2 = tmp2_KB.index(c2) + 1
                                visited.append({suoyin1,suoyin2})
                                mgu_list.append(mgu)
                                pos_in_ziju.append([idt1,idt2])
                                if new_tuple == () :
                                    hhh = True
                                    break
            if hhh :
                break
        if hhh :
            break
        tmp_KB = tmp2_KB[:]   #排序，单字句优先放置可以减少搜索的压力
        tmp_KB = sorted(tmp_KB,key = sort_rule)

    res2,step_index = backtracking(visited,tmp2_KB,KB,pos_in_ziju)#得到有用子句的序列表以及相关的信息
    ans = print_steps(res2,step_index,visited,pos_in_ziju,mgu_list,KB,tmp2_KB)#打印用的
    return ans 


#注意！！！！！所有的变量规定为小写双字符才行！！！！
#注意！！！！！所有的变量规定为小写双字符才行！！！！
#注意！！！！！所有的变量规定为小写双字符才行！！！！
#注意！！！！！所有的变量规定为小写双字符才行！！！！
#注意！！！！！所有的变量规定为小写双字符才行！！！！
KB = [('GradStudent(sue)',),('~GradStudent(xx)','Student(xx)'),('~Student(xx)','HardWorker(xx)'),('~HardWorker(sue)',)]

KB2 = [('A(tony)',),('A(mike)',),('A(john)',),('L(tony,rain)',),('L(tony,snow)',),
 ('~A(xx)','S(xx)','C(xx)'),('~C(yy)','~L(yy,rain)'),('L(zz,snow)','~S(zz)'),
 ('~L(tony,uu)','~L(mike,uu)'),('L(tony,vv)','L(mike,vv)'),('~A(ww)','~C(ww)','S(ww)')]
 
KB3 = [('On(tony,mike)',),('On(mike,john)',),('Green(tony)',),('~Green(john)',),
 ('~On(xx,yy)','~Green(xx)','Green(yy)')]
resolution_steps = ResolutionProp(KB)

# 输出归结步骤列表
for step in resolution_steps:
    print(step)


#注意！！！！！所有的变量规定为小写双字符才行！！！！