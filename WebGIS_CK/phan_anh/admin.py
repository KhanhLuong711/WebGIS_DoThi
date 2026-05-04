from django.contrib import admin
from .models import DiemPhanAnh

# Tạo class tùy chỉnh giao diện Admin
class DiemPhanAnhAdmin(admin.ModelAdmin):
    list_display = ('tieu_de', 'quan_huyen', 'trang_thai', 'ngay_bao_cao', 'vi_do', 'kinh_do')
    list_filter = ('quan_huyen', 'trang_thai', 'ngay_bao_cao') # Bộ lọc bên phải
    search_fields = ('tieu_de',) # Ô tìm kiếm

# Đăng ký model với giao diện tùy chỉnh
admin.site.register(DiemPhanAnh, DiemPhanAnhAdmin)