# File: phan_anh/gis_tools.py
from django.db.models import Q  # <-- Quan trọng: Phải có dòng này mới tìm được

def tool_loc_va_tim_kiem(queryset, params):
    # 1. Lấy dữ liệu từ ô tìm kiếm
    tu_khoa = params.get('q', '').strip()
    trang_thai = params.get('trang_thai', 'TatCa')
    
    # 2. Lọc theo Trạng Thái (Nếu có chọn)
    if trang_thai and trang_thai != 'TatCa':
        queryset = queryset.filter(trang_thai=trang_thai)
        
    # 3. Tìm kiếm từ khóa (Fix lỗi tiếng Việt cơ bản)
    if tu_khoa:
        # Tìm tiêu đề CHỨA từ khóa (icontains = không phân biệt hoa thường với tiếng Anh)
        # Với SQLite, bạn nên nhắc người dùng nhập đúng chữ cái đầu nếu cần
        queryset = queryset.filter(tieu_de__icontains=tu_khoa)
        
    return queryset, queryset.count(), trang_thai, tu_khoa

def tool_xu_ly_mau_sac(queryset):
    # Chuyển dữ liệu sang dạng JSON nhẹ hều cho bản đồ
    danh_sach = []
    for diem in queryset:
        danh_sach.append({
            'tieu_de': diem.tieu_de,
            'lat': diem.vi_do,
            'lng': diem.kinh_do,
            'trang_thai': diem.trang_thai
        })
    return danh_sach