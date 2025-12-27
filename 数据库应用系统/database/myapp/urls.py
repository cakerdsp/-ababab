from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.login,name = 'login'),
    url(r'create_account/', views.create_account,name='create_account'),
    url(r'client/', views.client,name='client'),
    url(r'client_information', views.client_information,name='client_information'),
    url(r'client_search/', views.client_search,name='client_search'),
    url(r'merchant/', views.merchant,name='merchant'),
    url(r'delivery_person/', views.delivery_person,name='delivery_person'),
    url(r'merchant_product_op/',views.merchant_product_op,name='merchant_product_op'),
    url(r'merchant_check_order/',views.merchant_check_order,name='merchant_check_order'),
]