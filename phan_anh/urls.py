# File: phan_anh/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ban_do_view, name='trang_chu'),
    path('tao-du-lieu/', views.tao_du_lieu_mau, name='tao_du_lieu'),
    path('gui-phan-anh/', views.gui_phan_anh, name='gui_phan_anh'),
    path('cap-nhat/', views.cap_nhat_trang_thai, name='cap_nhat'),
]