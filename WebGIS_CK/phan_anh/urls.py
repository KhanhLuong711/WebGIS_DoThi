from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='trang_chu'),
    path('ban-do/', views.ban_do_view, name='ban_do'),

    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.dang_xuat, name='logout'),
    path('ho-so/', views.ho_so_ca_nhan, name='ho_so'),
    path('phan-anh-cua-toi/', views.phan_anh_cua_toi, name='phan_anh_cua_toi'),
    path('phan-anh/<int:id>/', views.chi_tiet_phan_anh, name='chi_tiet_phan_anh'),

    path('gui-phan-anh/', views.gui_phan_anh, name='gui_phan_anh'),
    path('cap-nhat/', views.cap_nhat_trang_thai, name='cap_nhat'),
    path('xoa-phan-anh/', views.xoa_phan_anh, name='xoa_phan_anh'),
    path('gui-binh-luan/', views.gui_binh_luan, name='gui_binh_luan'),
    path('xoa-binh-luan/', views.xoa_binh_luan, name='xoa_binh_luan'),
    path('nhap-csv/', views.nhap_csv_phan_anh, name='nhap_csv'),
    path('xac-nhan/', views.xac_nhan_su_co, name='xac_nhan'),
    path('xuat-csv/', views.xuat_csv_phan_anh, name='xuat_csv'),
    path('theo-doi-su-co/', views.theo_doi_su_co, name='theo_doi_su_co'),
    path('tao-du-lieu/', views.tao_du_lieu_mau, name='tao_du_lieu'),
    path('admin/update-status/<int:id>/<str:status>/', views.update_status, name='update_status'),
    path('admin/delete-report/<int:id>/', views.delete_report, name='delete_report'),
    path('chi-tiet-phan-anh/<int:id>/', views.chi_tiet_phan_anh, name='chi_tiet_phan_anh'),
    path('admin/dashboard/', views.admin_dashboard),
    path('admin/reports/', views.admin_reports),
    path('admin/users/', views.admin_users),
    path('admin/comments/', views.admin_comments),

    path('admin/delete-user/<int:id>/', views.delete_user, name='delete_user'),
    path('admin/toggle-user/<int:id>/', views.toggle_user, name='toggle_user'),
    path('admin/toggle-admin/<int:id>/', views.toggle_admin, name='toggle_admin'),
    # ===== ADMIN COMMENTS =====
    path('admin/comments/', views.admin_comments, name='admin_comments'),
    path('admin/comments/delete/<int:id>/', views.delete_comment, name='delete_comment'),
    path('admin/comments/toggle/<int:id>/', views.toggle_comment, name='toggle_comment'),
    path('admin/comments/bulk-action/', views.bulk_action_comments, name='bulk_action_comments'),
    
]