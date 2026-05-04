from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class DiemPhanAnh(models.Model):
    tieu_de = models.CharField(max_length=200, verbose_name="Tiêu đề")
    mo_ta_chi_tiet = models.TextField(blank=True, null=True, verbose_name="Mô tả chi tiết")
    dia_chi = models.CharField(max_length=500, blank=True, null=True, verbose_name="Địa chỉ cụ thể") # ĐOẠN THÊM MỚI
    quan_huyen = models.CharField(max_length=100, default='Chưa xác định', verbose_name="Khu vực") 
    vi_do = models.FloatField()
    kinh_do = models.FloatField()
    
    trang_thai = models.CharField(max_length=50, default='ChoDuyet') 
    nguoi_tao = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) 
    
    # TÍNH NĂNG MỚI: ẨN DANH VÀ THEO DÕI
    an_danh = models.BooleanField(default=False, verbose_name="Ẩn danh")
    nguoi_theo_doi = models.ManyToManyField(User, related_name='cac_diem_dang_theo_doi', blank=True)
    ngay_cap_nhat = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật cuối")
    nguoi_xac_nhan = models.ManyToManyField(User, related_name='cac_diem_da_xac_nhan', blank=True)
    ngay_bao_cao = models.DateTimeField(default=timezone.now)
    ghi_chu = models.TextField(blank=True, null=True, verbose_name="Ghi chú xử lý")
    hinh_anh_xong = models.ImageField(upload_to='anh_da_xu_ly/', blank=True, null=True, verbose_name="Ảnh đã xử lý xong")

    def __str__(self):
        return self.tieu_de

class HinhAnhPhanAnh(models.Model):
    diem_phan_anh = models.ForeignKey(DiemPhanAnh, related_name='cac_hinh_anh', on_delete=models.CASCADE)
    hinh_anh = models.ImageField(upload_to='anh_hien_truong/')

class BinhLuan(models.Model):
    diem_phan_anh = models.ForeignKey(DiemPhanAnh, related_name='cac_binh_luan', on_delete=models.CASCADE)
    nguoi_dung = models.ForeignKey(User, on_delete=models.CASCADE)
    noi_dung = models.TextField()
    hinh_anh_minh_chung = models.ImageField(upload_to='anh_binh_luan/', blank=True, null=True)
    ngay_tao = models.DateTimeField(default=timezone.now)

        # 🔥 THÊM MỚI
    is_hidden = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)  # báo cáo vi phạm (optional)

    def __str__(self):
        return f"{self.nguoi_dung.username}: {self.noi_dung[:30]}"

