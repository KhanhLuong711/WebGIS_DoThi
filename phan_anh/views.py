from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import DiemPhanAnh
from django.views.decorators.csrf import csrf_exempt
import random, math, json

# ======================================================
# PHẦN 1: CÁC HÀM XỬ LÝ LOGIC (HELPER FUNCTIONS)
# Thầy bạn muốn phần này: Input -> Xử lý -> Output
# ======================================================

def tinh_khoang_cach(lat1, lng1, lat2, lng2):
    """
    Input: Tọa độ điểm A và B
    Output: Khoảng cách (km)
    """
    R = 6371 # Bán kính trái đất (km)
    dLat = math.radians(lat2 - lat1)
    dLng = math.radians(lng2 - lng1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def xu_ly_loc_theo_quan(queryset, quan_id):
    """
    Input: Danh sách dữ liệu, Mã quận
    Output: Danh sách đã lọc
    """
    if quan_id and quan_id != 'TatCa':
        return queryset.filter(quan_huyen=quan_id)
    return queryset

def xu_ly_loc_ban_kinh_va_format(queryset, center_lat, center_lng, radius):
    """
    Input: Danh sách data, Tâm quét, Bán kính
    Output: (List kết quả JSON, Số lượng tìm thấy)
    Hàm này vừa lọc bán kính vừa chuẩn hóa dữ liệu để hiển thị
    """
    ket_qua = []
    count = 0
    
    for d in queryset:
        is_in_radius = True
        
        # 1. Tính toán khoảng cách (Logic GIS)
        if center_lat and radius:
            try:
                dist = tinh_khoang_cach(float(center_lat), float(center_lng), d.vi_do, d.kinh_do)
                if dist > float(radius): 
                    is_in_radius = False
            except:
                pass # Bỏ qua lỗi nếu input không phải số
        
        # 2. Đóng gói dữ liệu (Data Formatting)
        if is_in_radius:
            ket_qua.append({
                'id': d.id,
                'tieu_de': d.tieu_de,
                'lat': d.vi_do, 
                'lng': d.kinh_do,
                'trang_thai': d.trang_thai,
                'quan': d.get_quan_huyen_display(),
                'ngay': d.ngay_bao_cao.strftime("%d/%m/%Y %H:%M"),
                'hinh_anh': d.hinh_anh.url if d.hinh_anh else '',
                'ghi_chu': d.ghi_chu or ''
            })
            count += 1
            
    return ket_qua, count

def lay_thong_ke_trang_thai():
    """
    Output: Dictionary số lượng {moi, dang_xu_ly, da_xong}
    """
    return {
        'moi': DiemPhanAnh.objects.filter(trang_thai='Moi').count(),
        'dang_xu_ly': DiemPhanAnh.objects.filter(trang_thai='DangXuLy').count(),
        'da_xong': DiemPhanAnh.objects.filter(trang_thai='DaXong').count()
    }

# ======================================================
# PHẦN 2: VIEW CONTROLLER (ĐIỀU PHỐI REQUEST)
# ======================================================

def ban_do_view(request):
    # 1. Nhận Input từ Request
    quan_filter = request.GET.get('quan_huyen')
    center_lat = request.GET.get('center_lat')
    center_lng = request.GET.get('center_lng')
    radius = request.GET.get('radius')

    # 2. Lấy dữ liệu gốc
    data_qs = DiemPhanAnh.objects.all().order_by('-ngay_bao_cao')

    # 3. Gọi các hàm xử lý (Logic tách biệt)
    data_qs = xu_ly_loc_theo_quan(data_qs, quan_filter)
    data_list, so_luong = xu_ly_loc_ban_kinh_va_format(data_qs, center_lat, center_lng, radius)
    stats = lay_thong_ke_trang_thai()

    # 4. Trả về Output (Render HTML)
    context = {
        'danh_sach_diem': json.dumps(data_list), # JSON cho Map
        'raw_data': data_list,                   # List cho Table
        'stats': stats,
        'so_luong': so_luong,
        'filter_quan': quan_filter,
        'radius_info': {'lat': center_lat, 'lng': center_lng, 'r': radius} if radius else None
    }
    return render(request, 'phan_anh/index.html', context)

# --- CÁC VIEW KHÁC (API) ---

@csrf_exempt
def gui_phan_anh(request):
    if request.method == 'POST':
        tieu_de = request.POST.get('tieu_de')
        lat = request.POST.get('lat')
        lng = request.POST.get('lng')
        hinh = request.FILES.get('hinh_anh')
        
        if tieu_de and lat:
            DiemPhanAnh.objects.create(
                tieu_de=tieu_de, vi_do=float(lat), kinh_do=float(lng),
                hinh_anh=hinh, trang_thai='Moi'
            )
            return JsonResponse({'status': 'success', 'message': 'Gửi thành công!'})
    return JsonResponse({'status': 'error'})

@csrf_exempt
def cap_nhat_trang_thai(request):
    if request.method == 'POST':
        try:
            obj = DiemPhanAnh.objects.get(id=request.POST.get('id'))
            obj.trang_thai = request.POST.get('trang_thai')
            obj.ghi_chu = request.POST.get('ghi_chu')
            obj.save()
            return JsonResponse({'status': 'success'})
        except:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})

# --- CÔNG CỤ TẠO DỮ LIỆU MẪU (ĐÃ CHUẨN HÓA TỪ NGỮ) ---
def tao_du_lieu_mau(request):
    DiemPhanAnh.objects.all().delete()
    
    khu_vuc = {
        'NinhKieu': (10.034, 105.779),
        'CaiRang': (10.008, 105.749),
        'BinhThuy': (10.063, 105.763)
    }
    
    # Danh sách vấn đề chuẩn (Không dùng từ Hố ga)
    van_de = [
        "Nắp cống bị vỡ/mất", 
        "Đèn chiếu sáng hỏng", 
        "Rác thải chưa thu gom", 
        "Đường ngập nước cục bộ", 
        "Biển báo bị che khuất"
    ]
    
    count = 0
    for quan, (lat_tam, lng_tam) in khu_vuc.items():
        for i in range(15):
            tieu_de = f"{random.choice(van_de)} ({quan})"
            lat = lat_tam + random.gauss(0, 0.015)
            lng = lng_tam + random.gauss(0, 0.015)
            trang_thai = random.choice(['Moi', 'DangXuLy', 'DaXong'])
            
            DiemPhanAnh.objects.create(
                tieu_de=tieu_de, vi_do=lat, kinh_do=lng, 
                trang_thai=trang_thai, quan_huyen=quan,
                ghi_chu="Dữ liệu giả lập hệ thống"
            )
            count += 1
            
    return HttpResponse(f"""
        <div style='text-align:center; padding:50px; font-family:sans-serif'>
            <h1 style='color:green'>✅ Đã cập nhật {count} dữ liệu chuẩn!</h1>
            <p>Đã thay thế thuật ngữ 'Hố ga' thành 'Nắp cống'.</p>
            <a href='/' style='padding:10px 20px; background:#2563eb; color:white; text-decoration:none; border-radius:8px'>Về Bản Đồ</a>
        </div>
    """)