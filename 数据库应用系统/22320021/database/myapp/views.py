from django.shortcuts import render, redirect
import psycopg2
import threading
import time
from django.views.decorators.csrf import csrf_exempt
from requests import get
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import *
from decimal import Decimal
# Create your views here.




# @receiver(post_save, sender=Product)
# @receiver(post_delete, sender=Product)
# def merchant_product_op_refresh(sender, instance, created, **kwargs):
#     # 实现你的逻辑
#     login.occupation = 'signal'
#     get('http://127.0.0.1:8000/myapp/merchant_product_op/')

login = threading.local()

def login(request):
    if request.method == 'GET':
        # 如果是 GET 请求，渲染并返回登录表单
        return render(request, 'login.html')
    elif request.method == 'POST':
        try :
            connection = psycopg2.connect(
            database = "postgres",
            user = "testuser",
            password = "ccc2osuRm7o",
            host = "192.168.132.101",
            port = 5432,
            )
            cur = connection.cursor()
        except BaseException as e:
            print(e)
        index = request.POST.get('ID')
        username = request.POST.get('username')
        password = request.POST.get('password')
        occupation = request.POST.get('occupation')
        if occupation == "客户":
            cur.execute('''SELECT * FROM myapp_client where "CID" = %s and "Cname" = %s and "Passward" = %s;''', [index,username,password])
        elif occupation == "商家":
            cur.execute('''SELECT * FROM myapp_merchant where "MID" = %s and "Mname" = %s and "Passward" = %s;''', [index,username,password])
        elif occupation == "快递员":
            cur.execute('''SELECT * FROM myapp_delivery_person where "DID" = %s and "Dname" = %s and "Passward" = %s;''', [index,username,password])
        rows = cur.fetchall()
        if rows:
            login.ID = index
            login.occupation = occupation
            if occupation == "客户":
                connection.close()
                return redirect('client')
            elif occupation == "商家":
                connection.close()
                return redirect('merchant')
            elif occupation == "快递员":
                connection.close()
                return redirect('delivery_person')
        else:
            error = '登录失败！请重试'
            connection.close()
            return render(request, 'login.html', {'error': error})





def create_account(request):
    if request.method == 'GET':
        # 如果是 GET 请求，渲染并返回登录表单
        return render(request, 'create_account.html')
    
    elif request.method == 'POST':
        try :
            connection = psycopg2.connect(
            database = "postgres",
            user = "testuser",
            password = "ccc2osuRm7o",
            host = "192.168.132.101",
            port = 5432,
            )
            cur = connection.cursor()
        except BaseException as e:
            print(e)
        index = request.POST.get('ID')
        username = request.POST.get('username')
        address = request.POST.get('address')
        account_balance = float(request.POST.get('account_balance'))
        phone_number = request.POST.get('phone_number')
        occupation = request.POST.get('occupation')
        passward = request.POST.get('passward')
        if occupation == "客户":
            cur.execute('''SELECT * FROM myapp_client where "CID" = %s;''', [index])
        elif occupation == "商家":
            cur.execute('''SELECT * FROM myapp_merchant where "MID" = %s;''', [index])
        elif occupation == "快递员":
            cur.execute('''SELECT * FROM myapp_delivery_person where "DID" = %s;''', [index])
        rows = cur.fetchall()
        if rows:
            error = '用户已经存在！'
            connection.close()
            return render(request, 'create_account.html', {'error': error})
        else:
            try:
                if occupation == "客户":
                    cur.execute('''INSERT INTO myapp_client VALUES(%s,%s,%s,%s,%s,%s);''', [index,username,account_balance,phone_number,address,passward])
                    connection.commit()
                elif occupation == "商家":
                    cur.execute('''INSERT INTO myapp_merchant VALUES(%s,%s,%s,%s,%s,%s);''', [index,username,account_balance,phone_number,address,passward])
                    connection.commit()
                elif occupation == "快递员":
                    # 这里是因为表的属性顺序原因
                    cur.execute('''INSERT INTO myapp_delivery_person VALUES(%s,%s,%s,%s,%s,%s);''', [index,phone_number,account_balance,address,username,passward])
                    connection.commit()
            except BaseException as e:
                print(e)
                error = '用户创建失败！'
                connection.close()
                return render(request, 'create_account.html', {'error': error})
            success = '用户创建成功！'
            connection.close()
            return render(request, 'create_account.html', {'success': success})




def client(request):
    try :
        connection = psycopg2.connect(
        database = "postgres",
        user = "testuser",
        password = "ccc2osuRm7o",
        host = "192.168.132.101",
        port = 5432,
        )
        cur = connection.cursor()
    except BaseException as e:
        msg = str(e)
        
    cur.execute('''SELECT * FROM myapp_product''')
    Products=cur.fetchall()
    
    if request.method == 'GET':
        # 如果是 GET 请求，渲染并返回登录表单
        connection.close()
        return render(request, 'client.html',{'products' : Products})
    
    msg=''
    if request.method == 'POST':
        button = request.POST.get('submitted_button')
        index = request.POST.get('ID')
        if button=='search':
            connection.close()
            return redirect('client_search')#跳转到订单显示界面
        

        try:
            if button == 'Product_Insert':
                # cur.execute(''' ''')
                cur.execute('''SELECT * FROM myapp_product WHERE "PID" = %s;''', [index])
                gett = cur.fetchall()
                price = gett[0][2]
                cur.execute('''SELECT "Account_balance" FROM myapp_client WHERE "CID" = %s;''', [login.ID])
                gett2 = cur.fetchall()
                account = gett2[0][0]
                if account >= Decimal('1.05') * price:

                    unique_ID = f"{int(time.time())}"
                    cur.execute('''INSERT INTO myapp_order ("OID","CID_id","PID_id","Status","Date","Payment") VALUES (%s,%s,%s,'ordered','0',%s);''',
                                [unique_ID,login.ID,gett[0][0],float(gett[0][2])])

                    account = account - Decimal('1.05') * price
                    cur.execute('''UPDATE myapp_client SET "Account_balance" = %s WHERE "CID" = %s''',[account,login.ID])
                    msg = f'下单成功！'
                    connection.commit()
                else:
                    msg = '余额不足！'
        except BaseException as e:
            msg = str(e)
            connection.rollback()
        connection.close()
        return render(request, 'client.html', {'products' : Products,'msg': msg})


def client_search(request):
    try :
        connection = psycopg2.connect(
        database = "postgres",
        user = "testuser",
        password = "ccc2osuRm7o",
        host = "192.168.132.101",
        port = 5432,
        )
        cur = connection.cursor()
    except BaseException as e:
        msg = str(e)

    if request.method == 'GET':
        msg = f'{login.occupation}'
        # 如果是 GET 请求，渲染并返回登录表单
        cur.execute('''SELECT o."OID",p."Pname",o."Status"
                    FROM myapp_order o   JOIN myapp_product p ON o."PID_id" = p."PID"
                    WHERE o."CID_id" = %s;''',[login.ID])
        orders = cur.fetchall()
        connection.close()
        return render(request,'client_search.html' ,{'orders' : orders})
    if request.method == 'POST':
        button = request.POST.get('submitted_button')
        if button=='search':
            return redirect('client')#跳转到订单显示界面
        if button == 'done':
            try:  
                index = request.POST.get('ID')
                cur.execute('''SELECT o."Status" FROM myapp_order o WHERE o."OID" = %s;''',[index])
                status = cur.fetchall()
                if status[0][0] == 'done':
                    msg = '收货成功！'          
                    cur.execute('''UPDATE myapp_order SET "Status" = 'over'  WHERE "OID" = %s;''', [index])
                    # 更新order表
                    cur.execute('''SELECT "DID_id","Payment" FROM myapp_transport WHERE "OID_id" = %s ;''', [index])
                    OID = cur.fetchall()
                    # 获取order中的金额和product表中的pid
                    cur.execute('''SELECT "Payment","PID_id" FROM myapp_order WHERE "OID" = %s;''', [index])
                    OID2 = cur.fetchall()
                    # 利用pid找到供货商id
                    cur.execute('''SELECT "Belong_id" FROM myapp_product WHERE "PID" = %s;''', [OID2[0][1]])
                    OID3 = cur.fetchall()

                    # 修改金额
                    cur.execute('''UPDATE myapp_delivery_person SET "Account_balance" = "Account_balance" + %s  WHERE "DID" = %s;''', [OID[0][1],OID[0][0]])
                    cur.execute('''UPDATE myapp_merchant SET "Account_balance" = "Account_balance" + %s  WHERE "MID" = %s;''', [OID2[0][0],OID3[0][0]])
                    connection.commit()
                else:
                    msg = '请输入满足条件的ID'
            except BaseException as e:
                connection.rollback()
                msg = str(e)


            cur.execute('''SELECT o."OID",p."Pname",o."Status"
                    FROM myapp_order o   JOIN myapp_product p ON o."PID_id" = p."PID"
                    WHERE o."CID_id" = %s;''',[login.ID])
            orders = cur.fetchall()
            connection.close()
            return render(request,'client_search.html' ,{'orders' : orders,'msg' : msg})


def delivery_person(request):
    try :
        connection = psycopg2.connect(
        database = "postgres",
        user = "testuser",
        password = "ccc2osuRm7o",
        host = "192.168.132.101",
        port = 5432,
        )
        cur = connection.cursor()
    except BaseException as e:
        msg = str(e)
    if request.method == 'GET':
        msg = f'{login.occupation}'
        # 如果是 GET 请求，渲染并返回登录表单
        cur.execute('''SELECT myapp_transport.* , myapp_client."Address" 
                        FROM 
                        myapp_transport  LEFT JOIN  myapp_order ON myapp_transport."OID_id" = myapp_order."OID"
                        LEFT JOIN myapp_client ON myapp_order."CID_id" = myapp_client."CID"
                        WHERE ("DID_id" = %s or "DID_id" IS NULL);''',[login.ID])
        transports = cur.fetchall()
        connection.close()
        return render(request, 'delivery_person.html',{'transports' : transports, 'msg' : msg})
    if request.method == 'POST':
        button = request.POST.get('submitted_button')
        index = request.POST.get('ID')
        if button == 'Accept':
            msg = f'接受成功！'
            try:
                cur.execute('''SELECT "Status" FROM myapp_transport WHERE "TID" = %s;''', [index])
                status = cur.fetchall()
                if status[0][0] == 'wait': 
                    # 更新transportport表
                    cur.execute('''UPDATE myapp_transport SET "Status" = 'accepted' WHERE "TID" = %s;''', [index])
                    cur.execute('''UPDATE myapp_transport SET "DID_id" = %s WHERE "TID" = %s;''', [login.ID,index])

                    # 更新order表
                    cur.execute('''SELECT "OID_id" FROM myapp_transport WHERE "TID" = %s;''', [index])
                    OID = cur.fetchall()

                    cur.execute('''UPDATE myapp_order SET "Status" = 'transporting' WHERE "OID" = %s;''', [OID[0][0]])
                    connection.commit()
            except BaseException as e:
                msg = str(e)
                connection.rollback()
            cur.execute('''SELECT myapp_transport.* , myapp_client."Address" 
                        FROM 
                        myapp_transport  LEFT JOIN  myapp_order ON myapp_transport."OID_id" = myapp_order."OID"
                        LEFT JOIN myapp_client ON myapp_order."CID_id" = myapp_client."CID"
                        WHERE ("DID_id" = %s or "DID_id" IS NULL);''',[login.ID])
            transports = cur.fetchall()
            connection.close()
            return render(request, 'delivery_person.html',{'transports' : transports, 'msg' : msg})
        # 删除操作，先实现按照ID进行删除
        elif button == 'Done':
            msg = '交付成功！'
            try:
                cur.execute('''SELECT "Status" FROM myapp_transport WHERE "TID" = %s;''', [index])
                status = cur.fetchall()
                if status[0][0] == 'accepted': 
                    cur.execute('''SELECT "OID_id", "DID_id","Payment" FROM myapp_transport WHERE "TID" = %s;''', [index])
                    OID = cur.fetchall()
                    # 更新transportport表
                    cur.execute('''UPDATE myapp_transport SET "Status" = 'done' WHERE "TID" = %s;''', [index])
                    # 更新order表
                    cur.execute('''UPDATE myapp_order SET "Status" = 'done' WHERE "OID" = %s;''', [OID[0][0]])

                    connection.commit()      
                    # print(OID)
                    # print(OID2)
                    # print(OID3)  
            except BaseException as e:
                    msg = str(e)
                    connection.rollback()   
            cur.execute('''SELECT myapp_transport.* , myapp_client."Address" 
                        FROM 
                        myapp_transport  LEFT JOIN  myapp_order ON myapp_transport."OID_id" = myapp_order."OID"
                        LEFT JOIN myapp_client ON myapp_order."CID_id" = myapp_client."CID"
                        WHERE ("DID_id" = %s or "DID_id" IS NULL);''',[login.ID])
            transports = cur.fetchall()
            connection.close()
            return render(request, 'delivery_person.html',{'transports' : transports, 'msg' : msg})


def merchant(request):
    if request.method == 'GET':
        # 如果是 GET 请求，渲染并返回登录表单
        return render(request, 'merchant.html')
    if request.method == 'POST':
        button = request.POST.get('submitted_button')
        # check_order = request.POST.get('check_order')
        if button == 'Product_Operate':
            return redirect('merchant_product_op')
        
        if button == 'Check_Order':
            return redirect('merchant_check_order')



@csrf_exempt
def merchant_product_op(request):
    try :
        connection = psycopg2.connect(
        database = "postgres",
        user = "testuser",
        password = "ccc2osuRm7o",
        host = "192.168.132.101",
        port = 5432,
        )
        cur = connection.cursor()
    except BaseException as e:
        msg = str(e)
    if request.method == 'GET':
        msg = f'{login.occupation}'
        # 如果是 GET 请求，渲染并返回登录表单
        cur.execute('''SELECT * FROM myapp_product WHERE "Belong_id" = %s;''',[login.ID])
        # cur.execute('''SELECT * FROM myapp_product WHERE "Belong_id" = %s;''',[login.ID])
        products = cur.fetchall()
        connection.close()
        return render(request, 'merchant_product_op.html',{'products' : products, 'msg' : msg})

    elif request.method == 'POST':
        button = request.POST.get('submitted_button')

        #  增加操作
        if button == 'Product_Insert':
            msg = f'添加成功！'
            index = request.POST.get('ID')
            username = request.POST.get('username')
            account_balance = request.POST.get('account_balance')
            try:
                cur.execute('''INSERT INTO myapp_product VALUES(%s,%s,%s,%s);''', [index,username,float(account_balance),login.ID])
                connection.commit()
            except BaseException as e:
                msg = str(e)
                connection.rollback()
            cur.execute('''SELECT * FROM myapp_product WHERE "Belong_id" = %s;''',[login.ID])
            products = cur.fetchall()
            connection.close()
            return render(request, 'merchant_product_op.html', {'products' : products,'msg': msg})

        # 删除操作，先实现按照ID进行删除
        elif button == 'Product_Delete':
            msg = '删除成功！'
            index = request.POST.get('ID2')
            try:
                cur.execute('''DELETE FROM myapp_product WHERE "PID" = %s;''', [index])
                connection.commit()            
            except BaseException as e:
                msg = str(e)
                connection.rollback()   
            cur.execute('''SELECT * FROM myapp_product WHERE "Belong_id" = %s;''',[login.ID])
            products = cur.fetchall()
            connection.close()
            return render(request, 'merchant_product_op.html', {'products' : products,'msg': msg})

        # 修改操作，目前想着按照ID，修改价格和商品名称 
        elif button == 'Product_Update':
            msg = f'更新成功！'
            index = request.POST.get('ID3')
            username = request.POST.get('username3')
            account_balance = request.POST.get('account_balance3')
            try:
                if username != '':
                    cur.execute('''UPDATE myapp_product SET "Pname" = %s WHERE "PID" = %s;''', [username,index])
                if account_balance != '':
                    cur.execute('''UPDATE myapp_product SET "Price" = %s WHERE "PID" = %s;''', [float(account_balance),index])
                connection.commit()
            except BaseException as e:
                msg = f'{request.POST.get('username3')}'
                connection.rollback()
            cur.execute('''SELECT * FROM myapp_product WHERE "Belong_id" = %s;''',[login.ID])
            products = cur.fetchall()
            return render(request, 'merchant_product_op.html', {'products' : products,'msg': msg})
        elif button == 'Select':
            cur.execute('''SELECT * FROM myapp_product WHERE "Belong_id" = %s;''',[login.ID])
            products = cur.fetchall()
            msg = '查询成功！'
            try:
                sql = request.POST.get('select')
                cur.execute(f'''SELECT * FROM myapp_product WHERE {sql} and "Belong_id" = %s;''',[login.ID])
                products = cur.fetchall()
            except BaseException as e:
                msg = str(e)
            connection.close()
            return render(request, 'merchant_product_op.html', {'products' : products,'msg': msg})
        elif button == 'Q_select':
            msg = ''
            cur.execute('''SELECT * FROM myapp_product WHERE "Belong_id" = %s;''',[login.ID])
            products = cur.fetchall()
            return render(request, 'merchant_product_op.html', {'products' : products,'msg': msg})
        else:
            msg = f'刷新'
            cur.execute('''SELECT * FROM myapp_product WHERE "Belong_id" = %s;''',[login.ID])
            products = cur.fetchall()
            connection.close()
            return render(request, 'merchant_product_op.html', {'products' : products,'msg': msg}) 


def merchant_check_order(request):
    try :
        connection = psycopg2.connect(
        database = "postgres",
        user = "testuser",
        password = "ccc2osuRm7o",
        host = "192.168.132.101",
        port = 5432,
        )
        cur = connection.cursor()
    except BaseException as e:
        msg = str(e)
    if request.method == 'GET':
        # 如果是 GET 请求，渲染并返回登录表单
        msg = ''
        # 如果是 GET 请求，渲染并返回登录表单
        cur.execute('''SELECT * FROM myapp_order WHERE "PID_id" in (SELECT "PID" FROM myapp_product WHERE "Belong_id" = %s);''',[login.ID])
        orders = cur.fetchall()
        connection.close()
        return render(request, 'merchant_check_order.html' ,{'orders' : orders})
    if request.method == 'POST':
        # 商家这边只能通过OID去修改订单的状态
        msg = f'状态更新成功！'
        index = request.POST.get('ID')
        try:
            cur.execute('''SELECT "Status" FROM myapp_order WHERE "OID" = %s;''', [index])
            status = cur.fetchall()
            if status and status[0][0] == 'ordered': 
                # 先更新Order表
                msg = '状态更新成功'
                cur.execute('''UPDATE myapp_order SET "Status" = 'Shipped' WHERE "OID" = %s;''', [index])
                # 插入transport表
                cur.execute('''SELECT "Payment" FROM myapp_order WHERE "OID" = %s;''',[index])
                price = cur.fetchall()
                payment = price[0][0] * Decimal('0.05')
                unique_ID = f"{int(time.time())}"
                cur.execute('''INSERT INTO myapp_transport VALUES(%s,%s,%s,%s,%s);''', [unique_ID,payment,'wait',None,index])
                connection.commit()
            else:
                msg = '当前订单状态不可更新！'
        except BaseException as e:
                msg = str(e)
                connection.rollback()


        cur.execute('''SELECT * FROM myapp_order WHERE "PID_id" in (SELECT "PID" FROM myapp_product WHERE "Belong_id" = %s);''',[login.ID])
        orders = cur.fetchall()
        connection.close()
        return render(request, 'merchant_check_order.html' ,{'orders' : orders, 'msg' : msg})
        


def client_information(request):
    msg = ''
    try :
        connection = psycopg2.connect(
        database = "postgres",
        user = "testuser",
        password = "ccc2osuRm7o",
        host = "192.168.132.101",
        port = 5432,
        )
        cur = connection.cursor()
    except BaseException as e:
        msg = str(e)
    if request.method == 'GET':
        cur.execute('''select * from myapp_client where "CID" = %s''',[login.ID])
        info = cur.fetchall()
        return render(request, 'login_information.html' ,{'info' : info, 'msg' : msg})
    if request.method == 'POST':
        button = request.POST.get('submitted_button')
        # check_order = request.POST.get('check_order')
        if button == 'Free':
            msg = '充值成功！'
            try:
                free = request.POST.get('free')
                cur.execute('''update myapp_client set "Account_balance" = "Account_balance" + %s where "CID" = %s''',[float(free),login.ID])
                connection.commit()
            except BaseException as e:
                msg = str(e)
                connection.rollback()
            cur.execute('''select * from myapp_client where "CID" = %s''',[login.ID])
            info = cur.fetchall()
            return render(request, 'login_information.html' ,{'info' : info, 'msg' : msg})