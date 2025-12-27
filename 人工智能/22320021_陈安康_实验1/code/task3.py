def ReverseKeyValue(dict1):
    dict2={}
    for key,value in dict1.items():
        dict2[value]=key
    return dict2

test={'Alice':'001','Bob':'002'}
ans=ReverseKeyValue(test)
print(ans)
