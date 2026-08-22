import re
from django import forms


class FamilyConnectionForm(forms.Form):
    RELATIONSHIPS = (
        ("", "Chọn mối quan hệ"),
        ("child", "Con"), ("grandchild", "Cháu"),
        ("sibling", "Anh / chị / em"), ("niece_nephew", "Cháu họ"),
        ("other", "Quan hệ khác"),
    )

    full_name = forms.CharField(label="Họ và tên", min_length=2, max_length=120)
    relationship = forms.ChoiceField(label="Quan hệ với liệt sĩ", choices=RELATIONSHIPS)
    phone = forms.CharField(label="Số điện thoại", required=False, max_length=20)
    email = forms.EmailField(label="Email", required=False, max_length=254)
    hometown = forms.CharField(label="Quê quán / nơi đang sinh sống", required=False, max_length=300)
    message = forms.CharField(
        label="Thông tin muốn bổ sung", min_length=20, max_length=3000,
        widget=forms.Textarea(attrs={"rows": 6}),
    )
    evidence = forms.FileField(label="Tài liệu hoặc ảnh xác minh", required=False)
    allow_publication = forms.BooleanField(label="Cho phép biên tập nội dung phù hợp để công khai", required=False)
    consent = forms.BooleanField(label="Tôi đồng ý để Ban quản trị liên hệ và xử lý thông tin đã gửi")
    website = forms.CharField(required=False, widget=forms.HiddenInput, label="")
    started_at = forms.CharField(widget=forms.HiddenInput)

    def clean_full_name(self):
        value = re.sub(r"\s+", " ", self.cleaned_data["full_name"]).strip()
        if re.search(r"https?://|www\.", value, re.I):
            raise forms.ValidationError("Họ tên không được chứa liên kết.")
        return value

    def clean_phone(self):
        value = re.sub(r"[\s.()-]", "", self.cleaned_data.get("phone", ""))
        if value and not re.fullmatch(r"(?:\+84|0)\d{8,10}", value):
            raise forms.ValidationError("Vui lòng nhập số điện thoại Việt Nam hợp lệ.")
        return value

    def clean_evidence(self):
        upload = self.cleaned_data.get("evidence")
        if not upload:
            return upload
        if upload.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Tệp xác minh không được vượt quá 10 MB.")
        allowed = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
        if upload.content_type not in allowed:
            raise forms.ValidationError("Chỉ nhận JPG, PNG, WebP hoặc PDF.")
        return upload

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("phone") and not cleaned.get("email"):
            raise forms.ValidationError("Vui lòng cung cấp số điện thoại hoặc email để Ban quản trị liên hệ xác minh.")
        return cleaned

class TributeForm(forms.Form):
    author_name = forms.CharField(label="Tên của bạn", min_length=2, max_length=100)
    phone = forms.CharField(label="Số điện thoại", min_length=9, max_length=20)
    content = forms.CharField(label="Lời tri ân", min_length=10, max_length=1000, widget=forms.Textarea)
    website = forms.CharField(required=False, widget=forms.HiddenInput, label="")
    started_at = forms.CharField(widget=forms.HiddenInput)

    def clean_author_name(self):
        value = re.sub(r"\s+", " ", self.cleaned_data["author_name"]).strip()
        if re.search(r"https?://|www\.", value, re.I):
            raise forms.ValidationError("Tên không được chứa liên kết.")
        return value

    def clean_phone(self):
        value = re.sub(r"[\s.()-]", "", self.cleaned_data["phone"])
        if not re.fullmatch(r"(?:\+84|0)\d{8,10}", value):
            raise forms.ValidationError("Vui lòng nhập số điện thoại Việt Nam hợp lệ.")
        return value

    def clean_content(self):
        value = re.sub(r"\s+", " ", self.cleaned_data["content"]).strip()
        if re.search(r"https?://|www\.|\b(?:telegram|zalo|whatsapp)\b", value, re.I):
            raise forms.ValidationError("Lời tri ân không được chứa liên kết hoặc nội dung quảng bá.")
        if re.search(r"(.)\1{9,}", value):
            raise forms.ValidationError("Nội dung có quá nhiều ký tự lặp lại.")
        return value
