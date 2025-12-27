from django.db import models

# Create your models here.
# 客户表
class Client(models.Model):
    CID = models.CharField(max_length=32, unique=True,primary_key=True)
    Cname = models.CharField(max_length=32)
    Account_balance = models.DecimalField(max_digits=10, decimal_places=2)
    Phone_number = models.CharField(max_length=32)
    Address = models.CharField(max_length=100)
    Passward = models.CharField(max_length=32,default='123456')


class Merchant(models.Model):
    MID = models.CharField(max_length=32, unique=True,primary_key=True)
    Mname = models.CharField(max_length=32)
    Account_balance = models.DecimalField(max_digits=10, decimal_places=2)
    Phone_number = models.CharField(max_length=32)
    Address = models.CharField(max_length=100)
    Passward = models.CharField(max_length=32,default='123456')


class Product(models.Model):
    PID = models.CharField(max_length=32, unique=True,primary_key=True)
    Belong = models.ForeignKey(Merchant, on_delete=models.CASCADE,null=True)
    Pname = models.CharField(max_length=32)
    Price = models.DecimalField(max_digits=6, decimal_places=2)



class Order(models.Model):
    OID = models.CharField(max_length=32, unique=True,primary_key=True)
    CID = models.ForeignKey(Client, on_delete=models.CASCADE)
    PID = models.ForeignKey(Product, on_delete=models.CASCADE)
    # Source_address = models.CharField(max_length=100)
    # Destination = models.CharField(max_length=100)
    Status = models.CharField(max_length=32)
    Date = models.CharField(max_length=32)
    Payment = models.DecimalField(max_digits=6, decimal_places=2)




class Delivery_Person(models.Model):
    DID = models.CharField(max_length=32, unique=True,primary_key=True)
    Dname = models.CharField(max_length=32,default='xxx')
    Account_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    Phone_number = models.CharField(max_length=32)
    Address = models.CharField(max_length=100,default='xxx')
    Passward = models.CharField(max_length=32,default='123456')



class Transport(models.Model):
    TID = models.CharField(max_length=32, unique=True,primary_key=True)
    OID = models.ForeignKey(Order, on_delete=models.CASCADE)
    DID = models.ForeignKey(Delivery_Person, on_delete=models.CASCADE,null=True)
    Payment = models.DecimalField(max_digits=6, decimal_places=2)
    Status = models.CharField(max_length=32)