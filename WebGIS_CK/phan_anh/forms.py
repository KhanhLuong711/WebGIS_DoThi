from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import DiemPhanAnh, BinhLuan


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/jpg",
}

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_uploaded_image(uploaded_file):
    if not uploaded_file:
        return

    content_type = getattr(uploaded_file, "content_type", "")
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError("Chỉ chấp nhận ảnh JPG, JPEG, PNG hoặc WEBP.")

    if uploaded_file.size > MAX_IMAGE_SIZE:
        raise ValidationError("Ảnh vượt quá dung lượng 5MB.")


class DangKyForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()

        if not username:
            raise ValidationError("Vui lòng nhập tên đăng nhập.")

        if len(username) < 3:
            raise ValidationError("Tên đăng nhập phải có ít nhất 3 ký tự.")

        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Tài khoản đã tồn tại.")

        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()

        if not email:
            raise ValidationError("Vui lòng nhập email.")

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email đã được sử dụng.")

        return email

    def clean_password(self):
        password = self.cleaned_data.get("password") or ""

        if len(password) < 6:
            raise ValidationError("Mật khẩu phải có ít nhất 6 ký tự.")

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm")

        if password and confirm and password != confirm:
            raise ValidationError("Mật khẩu không khớp.")

        return cleaned_data


class PhanAnhForm(forms.ModelForm):
    class Meta:
        model = DiemPhanAnh
        fields = [
            "tieu_de",
            "mo_ta_chi_tiet",
            "quan_huyen",
            "vi_do",
            "kinh_do",
            "an_danh",
        ]

    def clean_tieu_de(self):
        tieu_de = (self.cleaned_data.get("tieu_de") or "").strip()

        if not tieu_de:
            raise ValidationError("Vui lòng nhập tiêu đề phản ánh.")

        if len(tieu_de) < 5:
            raise ValidationError("Tiêu đề phải có ít nhất 5 ký tự.")

        return tieu_de

    def clean_mo_ta_chi_tiet(self):
        mo_ta = (self.cleaned_data.get("mo_ta_chi_tiet") or "").strip()
        return mo_ta

    def clean_quan_huyen(self):
        quan_huyen = (self.cleaned_data.get("quan_huyen") or "").strip()
        return quan_huyen if quan_huyen else "Chưa xác định"

    def clean_vi_do(self):
        vi_do = self.cleaned_data.get("vi_do")

        if vi_do is None:
            raise ValidationError("Thiếu vĩ độ.")

        if vi_do < -90 or vi_do > 90:
            raise ValidationError("Vĩ độ không hợp lệ.")

        return vi_do

    def clean_kinh_do(self):
        kinh_do = self.cleaned_data.get("kinh_do")

        if kinh_do is None:
            raise ValidationError("Thiếu kinh độ.")

        if kinh_do < -180 or kinh_do > 180:
            raise ValidationError("Kinh độ không hợp lệ.")

        return kinh_do

    def clean(self):
        cleaned_data = super().clean()
        files = self.files.getlist("hinh_anh")

        if len(files) > 5:
            raise ValidationError("Chỉ được tải lên tối đa 5 ảnh.")

        for file in files:
            validate_uploaded_image(file)

        return cleaned_data


class BinhLuanForm(forms.ModelForm):
    class Meta:
        model = BinhLuan
        fields = ["noi_dung", "hinh_anh_minh_chung"]

    def clean_noi_dung(self):
        noi_dung = (self.cleaned_data.get("noi_dung") or "").strip()

        hinh = self.files.get("hinh_anh_minh_chung")
        if not noi_dung and not hinh:
            raise ValidationError("Vui lòng nhập nội dung hoặc tải ảnh minh chứng.")

        return noi_dung

    def clean_hinh_anh_minh_chung(self):
        hinh = self.cleaned_data.get("hinh_anh_minh_chung")

        if hinh:
            validate_uploaded_image(hinh)

        return hinh


class CapNhatTrangThaiForm(forms.ModelForm):
    class Meta:
        model = DiemPhanAnh
        fields = ["trang_thai", "ghi_chu", "hinh_anh_xong"]

    def clean_trang_thai(self):
        trang_thai = (self.cleaned_data.get("trang_thai") or "").strip()
        ds_hop_le = {"ChoDuyet", "Moi", "DangXuLy", "DaXuLy"}

        if trang_thai not in ds_hop_le:
            raise ValidationError("Trạng thái không hợp lệ.")

        return trang_thai

    def clean_ghi_chu(self):
        ghi_chu = (self.cleaned_data.get("ghi_chu") or "").strip()
        return ghi_chu

    def clean_hinh_anh_xong(self):
        hinh = self.cleaned_data.get("hinh_anh_xong")

        if hinh:
            validate_uploaded_image(hinh)

        return hinh

    def clean(self):
        cleaned_data = super().clean()
        trang_thai = cleaned_data.get("trang_thai")
        ghi_chu = cleaned_data.get("ghi_chu")
        hinh_anh_xong = cleaned_data.get("hinh_anh_xong")

        if trang_thai == "DaXuLy":
            if not ghi_chu:
                raise ValidationError("Khi hoàn tất xử lý, vui lòng nhập ghi chú.")
            if not hinh_anh_xong and not getattr(self.instance, "hinh_anh_xong", None):
                raise ValidationError("Khi hoàn tất xử lý, vui lòng tải ảnh đã xử lý xong.")

        return cleaned_data