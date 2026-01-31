from django.db import models

class DiemPhanAnh(models.Model):
    # Các lựa chọn cho trạng thái xử lý
    TRANG_THAI_CHOICES = [
        ('Moi', 'Mới tiếp nhận'),
        ('DangXuLy', 'Đang xử lý'),
        ('DaXong', 'Đã xử lý xong'),
    ]

    # Định nghĩa các cột dữ liệu
    tieu_de = models.CharField(max_length=200, verbose_name="Tiêu đề")
    vi_do = models.FloatField(verbose_name="Vĩ độ (Lat)")  
    kinh_do = models.FloatField(verbose_name="Kinh độ (Lon)") 
    noi_dung = models.TextField(verbose_name="Nội dung phản ánh")
    trang_thai = models.CharField(max_length=20, choices=TRANG_THAI_CHOICES, default='Moi')
    
    # Cột thời gian tự động lấy lúc tạo
    ngay_tao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tieu_de