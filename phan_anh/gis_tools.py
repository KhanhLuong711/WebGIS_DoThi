# File: phan_anh/gis_tools.py
from django.db.models import Q

def tool_xu_ly_mau_sac(danh_sach_phan_anh):
    """
    TOOL 1: Chuẩn hóa dữ liệu sang JSON và Tô màu theo trạng thái GIS
    """
    ket_qua = []
    for item in danh_sach_phan_anh:
        # Logic tô màu: Mới=Đỏ, Đang làm=Cam, Xong=Xanh
        mau = 'gray'
        if item.trang_thai == 'Moi': mau = 'red'
        elif item.trang_thai == 'DangXuLy': mau = 'orange'
        elif item.trang_thai == 'DaXong': mau = 'green'
            
        ket_qua.append({
            'lat': item.vi_do,
            'lng': item.kinh_do,
            'popup': f"<b>{item.tieu_de}</b><br>Trạng thái: {item.get_trang_thai_display()}",
            'color': mau
        })
    return ket_qua

def tool_loc_va_tim_kiem(queryset, params):
    """
    TOOL 2: Lọc dữ liệu theo Trạng thái và Từ khóa tìm kiếm
    """
    trang_thai = params.get('trang_thai', 'TatCa')
    tu_khoa = params.get('q', '')

    # 1. Lọc theo trạng thái
    if trang_thai and trang_thai != 'TatCa':
        queryset = queryset.filter(trang_thai=trang_thai)
    
    # 2. Lọc theo từ khóa tìm kiếm (nếu có)
    if tu_khoa:
        queryset = queryset.filter(tieu_de__icontains=tu_khoa)
        
    # 3. Thống kê số lượng
    so_luong = queryset.count()
    
    return queryset, so_luong, trang_thai, tu_khoa