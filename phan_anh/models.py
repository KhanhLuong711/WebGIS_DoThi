from django.db import models
from django.utils import timezone

class DiemPhanAnh(models.Model):
    QUAN_HUYEN_CHOICES = [
        ('NinhKieu', 'Quận Ninh Kiều'),
        ('CaiRang', 'Quận Cái Răng'),
        ('BinhThuy', 'Quận Bình Thủy'),
        ('OMon', 'Quận Ô Môn'),
        ('ThotNot', 'Quận Thốt Nốt'),
        ('PhongDien', 'Huyện Phong Điền'),
        ('CoDo', 'Huyện Cờ Đỏ'),
        ('VinhThanh', 'Huyện Vĩnh Thạnh'),
        ('ThoiLai', 'Huyện Thới Lai'),
    ]

    tieu_de = models.CharField(max_length=200, verbose_name="Tiêu đề")
    quan_huyen = models.CharField(max_length=50, choices=QUAN_HUYEN_CHOICES, default='NinhKieu')
    
    vi_do = models.FloatField()
    kinh_do = models.FloatField()
    
    trang_thai = models.CharField(max_length=50, default='Moi')
    ngay_bao_cao = models.DateTimeField(default=timezone.now)
    
    # --- MỚI THÊM ---
    hinh_anh = models.ImageField(upload_to='anh_hien_truong/', blank=True, null=True, verbose_name="Ảnh hiện trường")
    ghi_chu = models.TextField(blank=True, null=True, verbose_name="Ghi chú xử lý")
    ngay_cap_nhat = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật cuối")

    def __str__(self):
        return self.tieu_de