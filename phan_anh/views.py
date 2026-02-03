# File: phan_anh/views.py
from django.shortcuts import render
from .models import DiemPhanAnh
from .gis_tools import tool_xu_ly_mau_sac, tool_loc_va_tim_kiem

def ban_do_view(request):
    # Lấy dữ liệu thô
    data_goc = DiemPhanAnh.objects.all()
    
    # GỌI TOOL: Lọc và Tìm kiếm
    data_loc, so_luong, tt_hien_tai, k_word = tool_loc_va_tim_kiem(data_goc, request.GET)
    
    # GỌI TOOL: Xử lý màu sắc hiển thị
    data_map = tool_xu_ly_mau_sac(data_loc)
    
    context = {
        'danh_sach_diem': data_map,
        'so_luong': so_luong,
        'trang_thai_chon': tt_hien_tai,
        'tu_khoa': k_word
    }
    return render(request, 'phan_anh/index.html', context)