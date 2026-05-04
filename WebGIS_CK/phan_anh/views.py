import csv
import json
import math
import random

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    BinhLuanForm,
    CapNhatTrangThaiForm,
    DangKyForm,
    PhanAnhForm,
)
from .models import BinhLuan, DiemPhanAnh, HinhAnhPhanAnh


def tinh_khoang_cach(lat1, lng1, lat2, lng2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def point_in_poly(lat, lng, poly):
    x, y = float(lat), float(lng)
    inside = False
    n = len(poly)

    if n < 3:
        return False

    p1x, p1y = float(poly[0][0]), float(poly[0][1])

    for i in range(n + 1):
        p2x, p2y = float(poly[i % n][0]), float(poly[i % n][1])

        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        xints = p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside

        p1x, p1y = p2x, p2y

    return inside


def xu_ly_loc_ban_kinh_va_format(
    queryset, center_lat, center_lng, radius, polygon_data, is_admin, current_user
):
    ket_qua = []
    count = 0
    poly_coords = json.loads(polygon_data) if polygon_data else None

    for d in queryset:
        if not is_admin and d.trang_thai == "ChoDuyet":
            continue

        if center_lat and center_lng and radius:
            try:
                kc = tinh_khoang_cach(
                    float(center_lat), float(center_lng), d.vi_do, d.kinh_do
                )
                if kc > float(radius) * 1.02:
                    continue
            except Exception:
                pass

        if poly_coords:
            if not point_in_poly(d.vi_do, d.kinh_do, poly_coords):
                continue

        danh_sach_hinh = [h.hinh_anh.url for h in d.cac_hinh_anh.all() if h.hinh_anh]

        ngay_vn = (
            timezone.localtime(d.ngay_bao_cao)
            if timezone.is_aware(d.ngay_bao_cao)
            else d.ngay_bao_cao
        )

        binh_luans = d.cac_binh_luan.filter(is_hidden=False).order_by("-ngay_tao")

        so_nguoi_theo_doi = d.nguoi_theo_doi.count()
        da_theo_doi = (
            current_user.is_authenticated
            and d.nguoi_theo_doi.filter(id=current_user.id).exists()
        )
        is_owner = current_user.is_authenticated and d.nguoi_tao == current_user

        nguoi_tao_ten = (
            "🕵️ Người dân (Ẩn danh)"
            if d.an_danh
            else (d.nguoi_tao.username if d.nguoi_tao else "Khách")
        )

        ket_qua.append(
            {
                "id": d.id,
                "tieu_de": d.tieu_de,
                "mo_ta_chi_tiet": d.mo_ta_chi_tiet or "Không có mô tả chi tiết.",
                "lat": d.vi_do,
                "lng": d.kinh_do,
                "trang_thai": d.trang_thai,
                "quan": d.quan_huyen,
                "ngay": ngay_vn.strftime("%d/%m/%Y %H:%M"),
                "danh_sach_hinh": danh_sach_hinh,
                "ghi_chu": d.ghi_chu or "",
                "hinh_xong": d.hinh_anh_xong.url if d.hinh_anh_xong else "",
                "so_nguoi_theo_doi": so_nguoi_theo_doi,
                "da_theo_doi": da_theo_doi,
                "is_owner": is_owner,
                "nguoi_tao_ten": nguoi_tao_ten,
                "binh_luans": [
                    {
                        "id": b.id,
                        "user": b.nguoi_dung.username,
                        "nd": b.noi_dung,
                        "hinh": b.hinh_anh_minh_chung.url
                        if b.hinh_anh_minh_chung
                        else None,
                    }
                    for b in binh_luans
                ],
            }
        )
        count += 1

    return ket_qua, count

def lay_thong_ke_trang_thai():
    return {
        "moi": DiemPhanAnh.objects.filter(trang_thai="Moi").count(),
        "dang_xu_ly": DiemPhanAnh.objects.filter(trang_thai="DangXuLy").count(),
        "da_xong": DiemPhanAnh.objects.filter(trang_thai="DaXuLy").count(),
        "cho_duyet": DiemPhanAnh.objects.filter(trang_thai="ChoDuyet").count(),
    }

def home_view(request):
    tong_phan_anh = DiemPhanAnh.objects.count()
    da_xu_ly = DiemPhanAnh.objects.filter(trang_thai='DaXuLy').count()
    dang_xu_ly = DiemPhanAnh.objects.filter(trang_thai='DangXuLy').count()
    cho_duyet = DiemPhanAnh.objects.filter(trang_thai='ChoDuyet').count()

    thong_ke_ca_nhan = None
    phan_anh_gan_day = []

    if request.user.is_authenticated:
        ds_cua_toi = DiemPhanAnh.objects.filter(nguoi_tao=request.user).order_by('-ngay_bao_cao')
        thong_ke_ca_nhan = {
            'tong_phan_anh': ds_cua_toi.count(),
            'cho_duyet': ds_cua_toi.filter(trang_thai='ChoDuyet').count(),
            'dang_xu_ly': ds_cua_toi.filter(trang_thai='DangXuLy').count(),
            'da_xu_ly': ds_cua_toi.filter(trang_thai='DaXuLy').count(),
            'dang_theo_doi': request.user.cac_diem_dang_theo_doi.exclude(trang_thai='ChoDuyet').count(),
        }
        phan_anh_gan_day = ds_cua_toi[:3]

    context = {
        'tong_phan_anh': tong_phan_anh,
        'da_xu_ly': da_xu_ly,
        'dang_xu_ly': dang_xu_ly,
        'cho_duyet': cho_duyet,
        'is_logged_in': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else '',
        'is_admin': request.user.is_staff if request.user.is_authenticated else False,
        'thong_ke_ca_nhan': thong_ke_ca_nhan,
        'phan_anh_gan_day': phan_anh_gan_day,
    }
    return render(request, 'phan_anh/home.html', context)

def ban_do_view(request):
    center_lat = request.GET.get("center_lat")
    center_lng = request.GET.get("center_lng")
    radius = request.GET.get("radius")
    tu_ngay = request.GET.get("tu_ngay")
    den_ngay = request.GET.get("den_ngay")
    polygon_data = request.GET.get("polygon")

    is_logged_in = request.user.is_authenticated
    is_admin = request.user.is_staff if is_logged_in else False

    data_qs = DiemPhanAnh.objects.all().order_by("-ngay_bao_cao")

    if tu_ngay:
        data_qs = data_qs.filter(ngay_bao_cao__date__gte=tu_ngay)
    if den_ngay:
        data_qs = data_qs.filter(ngay_bao_cao__date__lte=den_ngay)

    data_list, so_luong = xu_ly_loc_ban_kinh_va_format(
        data_qs,
        center_lat,
        center_lng,
        radius,
        polygon_data,
        is_admin,
        request.user,
    )

    tk_quan = list(
        DiemPhanAnh.objects.exclude(trang_thai="ChoDuyet")
        .values("quan_huyen")
        .annotate(total=Count("id"))
        .order_by("-total")[:7]
    )

    return render(
        request,
        "phan_anh/index.html",
        {
            "danh_sach_diem": json.dumps(data_list),
            "raw_data": data_list,
            "stats": lay_thong_ke_trang_thai(),
            "so_luong": so_luong,
            "radius_info": {"lat": center_lat, "lng": center_lng, "r": radius}
            if radius
            else None,
            "polygon_info": polygon_data,
            "tu_ngay": tu_ngay or "",
            "den_ngay": den_ngay or "",
            "is_logged_in": is_logged_in,
            "is_admin": is_admin,
            "username": request.user.username if is_logged_in else "",
            "tk_quan": json.dumps(tk_quan),
        },
    )

@login_required(login_url='/login/')
def theo_doi_su_co(request):
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Phương thức không hợp lệ.'
        })

    try:
        diem = DiemPhanAnh.objects.get(id=request.POST.get('id'))

        if request.user in diem.nguoi_theo_doi.all():
            diem.nguoi_theo_doi.remove(request.user)
            da_theo_doi = False
        else:
            diem.nguoi_theo_doi.add(request.user)
            da_theo_doi = True

        return JsonResponse({
            'status': 'success',
            'da_theo_doi': da_theo_doi,
            'so_nguoi_theo_doi': diem.nguoi_theo_doi.count(),
        })

    except DiemPhanAnh.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Không tìm thấy phản ánh.'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })

@login_required(login_url="/login/")
def xuat_csv_phan_anh(request):
    if not request.user.is_staff:
        return JsonResponse({"status": "forbidden", "message": "Không có quyền truy cập."})

    qs = DiemPhanAnh.objects.all().order_by("-ngay_bao_cao")

    tu_ngay = request.GET.get("tu_ngay")
    den_ngay = request.GET.get("den_ngay")

    if tu_ngay:
        qs = qs.filter(ngay_bao_cao__date__gte=tu_ngay)
    if den_ngay:
        qs = qs.filter(ngay_bao_cao__date__lte=den_ngay)

    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="bao_cao_su_co.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Khu Vực",
            "Tiêu Đề Sự Cố",
            "Tọa Độ (Lat, Lng)",
            "Trạng Thái",
            "Ngày Ghi Nhận",
            "Người Tạo",
            "Phản Hồi CQCN",
        ]
    )

    for obj in qs:
        ngay_vn = (
            timezone.localtime(obj.ngay_bao_cao)
            if timezone.is_aware(obj.ngay_bao_cao)
            else obj.ngay_bao_cao
        )

        if obj.trang_thai == "ChoDuyet":
            tt_str = "Chờ Duyệt"
        elif obj.trang_thai == "Moi":
            tt_str = "Đã Tiếp Nhận"
        elif obj.trang_thai == "DangXuLy":
            tt_str = "Đang Xử Lý"
        else:
            tt_str = "Hoàn Tất"

        ng_tao = "Ẩn danh" if obj.an_danh else (obj.nguoi_tao.username if obj.nguoi_tao else "Khách")

        writer.writerow(
            [
                obj.id,
                obj.quan_huyen,
                obj.tieu_de,
                f"{obj.vi_do}, {obj.kinh_do}",
                tt_str,
                ngay_vn.strftime("%d/%m/%Y %H:%M"),
                ng_tao,
                obj.ghi_chu or "",
            ]
        )

    return response


from django.contrib.auth.models import User

def login_view(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        try:
            user_obj = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "Sai tài khoản hoặc mật khẩu!")
            return redirect("login")

        # ❌ CHECK PASSWORD
        if not user_obj.check_password(password):
            messages.error(request, "Sai tài khoản hoặc mật khẩu!")
            return redirect("login")

        # 🔒 CHECK BỊ KHÓA
        if not user_obj.is_active:
            messages.error(request, "Tài khoản của bạn đã bị khóa!")
            return redirect("login")

        # ✅ OK thì login
        login(request, user_obj)
        return redirect("trang_chu")

    return render(request, "login.html")


def register_view(request):
    if request.method == "POST":
        form = DangKyForm(request.POST)

        if form.is_valid():
            User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            messages.success(request, "Đăng ký thành công! Vui lòng đăng nhập.")
            return redirect("login")

        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)

        return redirect("register")

    return render(request, "register.html")


def dang_xuat(request):
    logout(request)
    return redirect("/")


@login_required(login_url="/login/")
def gui_phan_anh(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Phương thức không hợp lệ."})

    hom_nay = timezone.localtime().date()

    if (
        not request.user.is_staff
        and DiemPhanAnh.objects.filter(
            nguoi_tao=request.user, ngay_bao_cao__date=hom_nay
        ).count()
        >= 3
    ):
        return JsonResponse(
            {"status": "error", "message": "🚫 Đạt giới hạn gửi 3 phản ánh/ngày!"}
        )

    data = request.POST.copy()

    if "lat" in data and "vi_do" not in data:
        data["vi_do"] = data.get("lat")
    if "lng" in data and "kinh_do" not in data:
        data["kinh_do"] = data.get("lng")

    an_danh_raw = str(data.get("an_danh", "")).lower()
    data["an_danh"] = an_danh_raw in ["true", "1", "on", "yes"]

    form = PhanAnhForm(data, request.FILES)

    if not form.is_valid():
        loi_dau = next(iter(form.errors.values()))[0]
        return JsonResponse({"status": "error", "message": loi_dau})

    diem = form.save(commit=False)
    diem.nguoi_tao = request.user
    diem.trang_thai = "Moi" if request.user.is_staff else "ChoDuyet"
    diem.save()

    for hinh in request.FILES.getlist("hinh_anh"):
        HinhAnhPhanAnh.objects.create(diem_phan_anh=diem, hinh_anh=hinh)

    msg = (
        "Sự cố đã được ghi nhận trực tiếp!"
        if request.user.is_staff
        else "Đã gửi! Đang chờ Cán bộ duyệt."
    )

    return JsonResponse({"status": "success", "message": msg})

@login_required(login_url="/login/")
def gui_binh_luan(request):

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Phương thức không hợp lệ."})

    id_diem = request.POST.get("id_diem")
    redirect_to = request.POST.get("redirect_to")

    if not id_diem:
        if redirect_to:
            messages.error(request, "Thiếu ID sự cố.")
            return redirect(redirect_to)
        return JsonResponse({"status": "error", "message": "Thiếu ID sự cố."})

    try:
        diem = DiemPhanAnh.objects.get(id=id_diem)
    except DiemPhanAnh.DoesNotExist:
        if redirect_to:
            messages.error(request, "Không tìm thấy sự cố.")
            return redirect(redirect_to)
        return JsonResponse({"status": "error", "message": "Không tìm thấy sự cố."})

    # 1. Giới hạn 5 bình luận / ngày
    hom_nay = timezone.localdate()

    so_binh_luan = BinhLuan.objects.filter(
        nguoi_dung=request.user,
        ngay_tao__date=hom_nay
    ).count()

    if so_binh_luan >= 5:
        msg = "🚫 Bạn chỉ được gửi tối đa 5 bình luận mỗi ngày!"
        if redirect_to:
            messages.error(request, msg)
            return redirect(redirect_to)
        return JsonResponse({"status": "error", "message": msg})

    # 2. Chống spam (30 giây)
    last_comment = BinhLuan.objects.filter(
        nguoi_dung=request.user
    ).order_by('-ngay_tao').first()

    if last_comment and (timezone.now() - last_comment.ngay_tao).total_seconds() < 30:
        msg = "⏳ Vui lòng chờ 30 giây trước khi bình luận tiếp!"
        if redirect_to:
            messages.error(request, msg)
            return redirect(redirect_to)
        return JsonResponse({"status": "error", "message": msg})
    

    # ================== END ==================

    form = BinhLuanForm(request.POST, request.FILES)

    if not form.is_valid():
        loi_dau = next(iter(form.errors.values()))[0]

        if redirect_to:
            messages.error(request, loi_dau)
            return redirect(redirect_to)

        return JsonResponse({"status": "error", "message": loi_dau})

    bl = form.save(commit=False)
    bl.diem_phan_anh = diem
    bl.nguoi_dung = request.user
    bl.save()

    if redirect_to:
        messages.success(request, "Đã gửi bình luận thành công!")
        return redirect(redirect_to)

    return JsonResponse({"status": "success", "message": "Đã gửi bình luận!"})

@login_required(login_url="/login/")
def xoa_binh_luan(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Phương thức không hợp lệ."})

    if not request.user.is_staff:
        return JsonResponse({"status": "forbidden", "message": "Không có quyền xóa!"})

    try:
        bl = BinhLuan.objects.get(id=request.POST.get("id"))
        bl.delete()
        return JsonResponse({"status": "success"})
    except BinhLuan.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Không tìm thấy bình luận."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


@login_required(login_url="/login/")
def cap_nhat_trang_thai(request):
    if not request.user.is_staff:
        return JsonResponse({"status": "forbidden", "message": "Không có quyền."})

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Phương thức không hợp lệ."})

    try:
        obj = DiemPhanAnh.objects.get(id=request.POST.get("id"))
    except DiemPhanAnh.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Không tìm thấy phản ánh."})

    trang_thai_cu = obj.trang_thai
    form = CapNhatTrangThaiForm(request.POST, request.FILES, instance=obj)

    if not form.is_valid():
        loi_dau = next(iter(form.errors.values()))[0]
        return JsonResponse({"status": "error", "message": loi_dau})

    obj = form.save()

    if (
        obj.trang_thai == "DaXuLy"
        and trang_thai_cu != "DaXuLy"
        and obj.nguoi_tao
        and obj.nguoi_tao.email
    ):
        noi_dung_mail = (
            f"Chào {obj.nguoi_tao.username},\n\n"
            f"Sự cố '{obj.tieu_de}' mà bạn phản ánh tại khu vực {obj.quan_huyen} "
            f"đã được đội ngũ Cán bộ xử lý hoàn tất!\n\n"
            f"Ghi chú từ cơ quan chức năng: {obj.ghi_chu}\n\n"
            f"Cảm ơn bạn đã đóng góp xây dựng Đô thị xanh sạch đẹp.\n"
            f"Trân trọng,\nHệ thống WebGIS Đô Thị."
        )

        try:
            send_mail(
                subject="[WebGIS] Thông báo: Sự cố đã được khắc phục!",
                message=noi_dung_mail,
                from_email=None,
                recipient_list=[obj.nguoi_tao.email],
                fail_silently=False,
            )
        except Exception:
            pass

    return JsonResponse({"status": "success"})


@login_required(login_url="/login/")
def xoa_phan_anh(request):
    if not request.user.is_staff:
        return JsonResponse({"status": "forbidden", "message": "Không có quyền."})

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Phương thức không hợp lệ."})

    try:
        DiemPhanAnh.objects.get(id=request.POST.get("id")).delete()
        return JsonResponse({"status": "success"})
    except DiemPhanAnh.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Không tìm thấy phản ánh."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

@login_required(login_url="/login/")
def phan_anh_cua_toi(request):
    trang_thai = (request.GET.get("trang_thai") or "").strip()
    tu_khoa = (request.GET.get("q") or "").strip()

    ds = (
        DiemPhanAnh.objects.filter(nguoi_tao=request.user)
        .prefetch_related("cac_hinh_anh", "cac_binh_luan", "nguoi_theo_doi")
        .order_by("-ngay_bao_cao")
    )

    if trang_thai and trang_thai != "TatCa":
        ds = ds.filter(trang_thai=trang_thai)

    if tu_khoa:
        ds = ds.filter(tieu_de__icontains=tu_khoa)

    danh_sach = []
    for item in ds:
        danh_sach.append(
            {
                "id": item.id,
                "tieu_de": item.tieu_de,
                "mo_ta_chi_tiet": item.mo_ta_chi_tiet or "",
                "quan_huyen": item.quan_huyen or "Chưa xác định",
                "vi_do": item.vi_do,
                "kinh_do": item.kinh_do,
                "trang_thai": item.trang_thai,
                "ngay_bao_cao": timezone.localtime(item.ngay_bao_cao),
                "ghi_chu": item.ghi_chu or "",
                "so_hinh_anh": item.cac_hinh_anh.count(),
                "anh_dau": item.cac_hinh_anh.first().hinh_anh.url if item.cac_hinh_anh.exists() else "",
                "so_binh_luan": item.cac_binh_luan.count(),
                "so_nguoi_theo_doi": item.nguoi_theo_doi.count(),
                "hinh_anh_xong": item.hinh_anh_xong.url if item.hinh_anh_xong else "",
                "an_danh": item.an_danh,
            }
        )

    thong_ke = {
        "tat_ca": ds.count(),
        "cho_duyet": DiemPhanAnh.objects.filter(nguoi_tao=request.user, trang_thai="ChoDuyet").count(),
        "moi": DiemPhanAnh.objects.filter(nguoi_tao=request.user, trang_thai="Moi").count(),
        "dang_xu_ly": DiemPhanAnh.objects.filter(nguoi_tao=request.user, trang_thai="DangXuLy").count(),
        "da_xu_ly": DiemPhanAnh.objects.filter(nguoi_tao=request.user, trang_thai="DaXuLy").count(),
    }

    return render(
        request,
        "phan_anh/my_reports.html",
        {
            "danh_sach": danh_sach,
            "trang_thai_hien_tai": trang_thai or "TatCa",
            "tu_khoa": tu_khoa,
            "thong_ke": thong_ke,
        },
    )

@login_required(login_url='/login/')
def chi_tiet_phan_anh(request, id):
    diem = get_object_or_404(
        DiemPhanAnh.objects.prefetch_related('cac_hinh_anh', 'cac_binh_luan__nguoi_dung', 'nguoi_theo_doi'),
        id=id
    )

    if not request.user.is_staff:
        la_chu_so_huu = diem.nguoi_tao == request.user
        la_cong_khai = diem.trang_thai != 'ChoDuyet'
        if not la_chu_so_huu and not la_cong_khai:
            messages.error(request, "Bạn không có quyền xem phản ánh này.")
            return redirect('phan_anh_cua_toi')

    danh_sach_hinh = list(diem.cac_hinh_anh.all().order_by('id'))
    danh_sach_binh_luan = list(diem.cac_binh_luan.filter(is_hidden=False).order_by('-ngay_tao'))

    if diem.trang_thai == 'ChoDuyet':
        trang_thai_hien_thi = 'Chờ duyệt'
    elif diem.trang_thai == 'Moi':
        trang_thai_hien_thi = 'Đã tiếp nhận'
    elif diem.trang_thai == 'DangXuLy':
        trang_thai_hien_thi = 'Đang xử lý'
    elif diem.trang_thai == 'DaXuLy':
        trang_thai_hien_thi = 'Hoàn tất'
    else:
        trang_thai_hien_thi = diem.trang_thai

    nguoi_tao_hien_thi = (
        "🕵️ Người dân (Ẩn danh)"
        if diem.an_danh
        else (diem.nguoi_tao.username if diem.nguoi_tao else "Khách")
    )

    context = {
        'diem': diem,
        'danh_sach_hinh': danh_sach_hinh,
        'danh_sach_binh_luan': danh_sach_binh_luan,
        'trang_thai_hien_thi': trang_thai_hien_thi,
        'nguoi_tao_hien_thi': nguoi_tao_hien_thi,
        'so_nguoi_theo_doi': diem.nguoi_theo_doi.count(),
        'da_theo_doi': request.user.is_authenticated and diem.nguoi_theo_doi.filter(id=request.user.id).exists(),
        'la_chu_so_huu': request.user.is_authenticated and diem.nguoi_tao == request.user,
        'form_binh_luan': BinhLuanForm(),
    }
    return render(request, 'phan_anh/report_detail.html', context)

@login_required(login_url='/login/')
def ho_so_ca_nhan(request):
    user = request.user

    ds_cua_toi = DiemPhanAnh.objects.filter(nguoi_tao=user).order_by('-ngay_bao_cao')
    ds_theo_doi = user.cac_diem_dang_theo_doi.exclude(trang_thai='ChoDuyet').order_by('-ngay_cap_nhat')

    thong_ke = {
        'tong_phan_anh': ds_cua_toi.count(),
        'cho_duyet': ds_cua_toi.filter(trang_thai='ChoDuyet').count(),
        'moi': ds_cua_toi.filter(trang_thai='Moi').count(),
        'dang_xu_ly': ds_cua_toi.filter(trang_thai='DangXuLy').count(),
        'da_xu_ly': ds_cua_toi.filter(trang_thai='DaXuLy').count(),
        'dang_theo_doi': ds_theo_doi.count(),
        'tong_binh_luan': BinhLuan.objects.filter(nguoi_dung=user).count(),
    }

    phan_anh_gan_day = ds_cua_toi[:6]
    theo_doi_gan_day = ds_theo_doi[:6]

    context = {
        'user_obj': user,
        'thong_ke': thong_ke,
        'phan_anh_gan_day': phan_anh_gan_day,
        'theo_doi_gan_day': theo_doi_gan_day,
    }
    return render(request, 'phan_anh/profile.html', context)

def tao_du_lieu_mau(request):
    User.objects.filter(username__in=["admin1", "khach1", "khach2", "khach3"]).delete()

    User.objects.create_superuser("admin1", "admin@web.com", "1234")
    khach_users = [
        User.objects.create_user(f"khach{i}", f"khach{i}@gmail.com", "1234")
        for i in range(1, 4)
    ]

    DiemPhanAnh.objects.all().delete()

    khu_vuc_hcm = {
        "Quận 1": (10.776, 106.701),
        "Quận 3": (10.781, 106.685),
        "Thủ Đức": (10.823, 106.763),
    }
    van_de = ["Nắp cống bị bể", "Đèn đường hỏng", "Rác bốc mùi"]

    count = 0

    for quan, (lat_tam, lng_tam) in khu_vuc_hcm.items():
        for _ in range(15):
            tt = random.choices(
                ["Moi", "DangXuLy", "DaXuLy", "ChoDuyet"],
                weights=[30, 30, 25, 15],
            )[0]

            if tt == "DangXuLy":
                ghi_chu = "Đã cử đội thi công."
            elif tt == "DaXuLy":
                ghi_chu = "Đã khắc phục hoàn tất."
            else:
                ghi_chu = "Đã tiếp nhận."

            an_danh_ngau_nhien = random.choice([True, False])

            diem = DiemPhanAnh.objects.create(
                dia_chi=request.POST.get('dia_chi'),
                tieu_de=random.choice(van_de),
                mo_ta_chi_tiet="Chi tiết mô tả sự cố...",
                vi_do=lat_tam + random.gauss(0, 0.015),
                kinh_do=lng_tam + random.gauss(0, 0.015),
                trang_thai=tt,
                quan_huyen=quan,
                ghi_chu=ghi_chu if tt != "ChoDuyet" else "",
                nguoi_tao=khach_users[0],
                an_danh=an_danh_ngau_nhien,
            )

            count += 1

            if tt != "ChoDuyet" and random.random() > 0.4:
                for u in random.sample(khach_users, random.randint(1, 2)):
                    BinhLuan.objects.create(
                        diem_phan_anh=diem,
                        nguoi_dung=u,
                        noi_dung="Tuyệt vời!",
                    )
                    if random.random() > 0.5:
                        diem.nguoi_theo_doi.add(u)

    return HttpResponse(
        f"<h1 style='color:green; text-align:center; padding:50px;'>"
        f"Đã nạp {count} điểm! Vào test Bản đồ Nhiệt nhé!"
        f"<br><br><a href='/ban-do/'>Về bản đồ</a></h1>"
    )

@login_required
def nhap_csv_phan_anh(request):
    if not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Chỉ cán bộ mới được nhập file'})
    if request.method == 'POST' and request.FILES.get('file_csv'):
        csv_file = request.FILES['file_csv']
        decoded_file = csv_file.read().decode('utf-8-sig').splitlines()
        reader = csv.DictReader(decoded_file)
        count = 0
        for row in reader:
            DiemPhanAnh.objects.create(
                tieu_de=row.get('Tiêu đề', 'Không có tiêu đề'),
                dia_chi=row.get('Địa chỉ cụ thể', ''),
                quan_huyen=row.get('Quận/Huyện', 'Chưa xác định'),
                vi_do=float(row.get('Vĩ độ', 0)),
                kinh_do=float(row.get('Kinh độ', 0)),
                trang_thai='Moi',
                nguoi_tao=request.user
            )
            count += 1
        return JsonResponse({'status': 'success', 'message': f'Đã nhập thành công {count} điểm từ file Excel!'})
    return JsonResponse({'status': 'error', 'message': 'File không hợp lệ'})

@login_required
def xac_nhan_su_co(request):
    if request.method == 'POST':
        diem_id = request.POST.get('id')
        diem = get_object_or_404(DiemPhanAnh, id=diem_id)
        if request.user in diem.nguoi_xac_nhan.all():
            diem.nguoi_xac_nhan.remove(request.user)
        else:
            diem.nguoi_xac_nhan.add(request.user)
        return JsonResponse({'status': 'success', 'upvotes': diem.nguoi_xac_nhan.count()})
    return JsonResponse({'status': 'error'})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
# ===== ADMIN PANEL =====

from django.db.models import Count
from django.db.models.functions import TruncDate

@login_required(login_url="/login/")
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('/')

    trang_thai_data = list(
        DiemPhanAnh.objects.values('trang_thai')
        .annotate(count=Count('id'))
    )

    quan_data = list(
        DiemPhanAnh.objects.values('quan_huyen')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    ngay_data = list(
        DiemPhanAnh.objects.annotate(date=TruncDate('ngay_bao_cao'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')[:7]
    )

    return render(request, "admin_panel/dashboard.html", {
        "tong": DiemPhanAnh.objects.count(),
        "cho_duyet": DiemPhanAnh.objects.filter(trang_thai="ChoDuyet").count(),
        "dang_xu_ly": DiemPhanAnh.objects.filter(trang_thai="DangXuLy").count(),
        "da_xu_ly": DiemPhanAnh.objects.filter(trang_thai="DaXuLy").count(),

        "trang_thai_data": trang_thai_data,
        "quan_data": quan_data,
        "ngay_data": ngay_data,
    })


@login_required(login_url="/login/")
def admin_reports(request):
    if not request.user.is_superuser:
        return redirect('/')

    trang_thai = request.GET.get("status")
    keyword = request.GET.get("q")

    qs = DiemPhanAnh.objects.all().order_by("-ngay_bao_cao")

    if trang_thai and trang_thai != "all":
        qs = qs.filter(trang_thai=trang_thai)

    if keyword:
        qs = qs.filter(tieu_de__icontains=keyword)

    return render(request, "admin_panel/reports.html", {
        "reports": qs
    })


@login_required(login_url="/login/")
def admin_users(request):
    if not request.user.is_superuser:
        return redirect('/')

    users = User.objects.all()

    # ===== SEARCH =====
    q = request.GET.get("q")
    if q:
        users = users.filter(username__icontains=q)

    # ===== FILTER ROLE =====
    role = request.GET.get("role")
    if role == "admin":
        users = users.filter(is_superuser=True)
    elif role == "user":
        users = users.filter(is_superuser=False)

    return render(request, "admin_panel/users.html", {
        "users": users
    })


from django.core.paginator import Paginator

@login_required(login_url="/login/")
def admin_comments(request):
    if not request.user.is_superuser:
        return redirect('/')

    # Query gốc
    qs = BinhLuan.objects.select_related(
        "nguoi_dung", "diem_phan_anh"
    ).order_by("-ngay_tao")

    # 🔍 SEARCH nội dung
    q = request.GET.get("q")
    if q:
        qs = qs.filter(noi_dung__icontains=q)

    # 🔽 FILTER trạng thái
    status = request.GET.get("status")
    if status == "hidden":
        qs = qs.filter(is_hidden=True)
    elif status == "visible":
        qs = qs.filter(is_hidden=False)

    # 📄 PAGINATION
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "admin_panel/comments.html", {
        "comments": page_obj,
        "q": q or "",
        "status": status or ""
    })


@login_required(login_url="/login/")
def delete_report(request, id):
    if request.method == "POST" and request.user.is_superuser:
        DiemPhanAnh.objects.filter(id=id).delete()
    return redirect('/admin/reports/')


@login_required(login_url="/login/")
def delete_user(request, id):
    if request.method == "POST" and request.user.is_superuser:
        User.objects.filter(id=id).delete()
    return redirect('/admin/users/')

@login_required(login_url="/login/")
def toggle_user(request, id):
    if request.method == "POST" and request.user.is_superuser:
        user = get_object_or_404(User, id=id)

        # ❌ CHẶN TỰ KHÓA
        if user == request.user:
            messages.error(request, "Bạn không thể tự khóa tài khoản của chính mình!")
            return redirect('/admin/users/')

        user.is_active = not user.is_active
        user.save()

    return redirect('/admin/users/')

@login_required(login_url="/login/")
def toggle_admin(request, id):
    if request.method == "POST" and request.user.is_superuser:
        user = get_object_or_404(User, id=id)

        total_admins = User.objects.filter(is_superuser=True).count()

        # ❌ Không cho tự sửa
        if user == request.user:
            messages.error(request, "Không thể tự thay đổi quyền của chính mình!")
            return redirect('/admin/users/')

        # ❌ Không cho xóa admin cuối cùng
        if user.is_superuser and total_admins <= 1:
            messages.error(request, "Phải có ít nhất 1 admin trong hệ thống!")
            return redirect('/admin/users/')

        user.is_superuser = not user.is_superuser
        user.save()

        messages.success(request, "Cập nhật quyền thành công!")

    return redirect('/admin/users/')


@login_required(login_url="/login/")
def delete_comment(request, id):
    if request.method == "POST" and request.user.is_superuser:
        comment = get_object_or_404(BinhLuan, id=id)
        comment.delete()
    return redirect('admin_comments')

@login_required(login_url="/login/")
def toggle_comment(request, id):
    if request.method == "POST" and request.user.is_superuser:
        comment = get_object_or_404(BinhLuan, id=id)
        comment.is_hidden = not comment.is_hidden
        comment.save()
    return redirect('admin_comments')

@login_required(login_url="/login/")
def bulk_action_comments(request):
    if request.method == "POST" and request.user.is_superuser:
        ids = request.POST.getlist("ids")
        action = request.POST.get("action")

        qs = BinhLuan.objects.filter(id__in=ids)

        if action == "delete":
            qs.delete()
        elif action == "hide":
            qs.update(is_hidden=True)
        elif action == "show":
            qs.update(is_hidden=False)

    return redirect('admin_comments')

@login_required(login_url="/login/")
def update_status(request, id, status):
    if request.method == "POST" and request.user.is_superuser:
        report = get_object_or_404(DiemPhanAnh, id=id)
        report.trang_thai = status
        report.save()
    return redirect('/admin/reports/')
    report = get_object_or_404(DiemPhanAnh, id=id)
    report.trang_thai = status
    report.save()
    return redirect('/admin/reports/')