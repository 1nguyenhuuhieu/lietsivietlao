# Ký ức Việt – Lào

Website cộng đồng phi lợi nhuận để tra cứu, tưởng niệm và từng bước xây dựng trải nghiệm 360° cho Nghĩa trang Liệt sĩ Việt – Lào.

## Nguyên tắc dữ liệu

- Chỉ đồng bộ các trang công khai dưới `/tra-cuu-phan-mo/`.
- Tuân thủ `robots.txt`; không truy cập các vùng quản trị, dữ liệu nội bộ hoặc tài khoản.
- Giới hạn mặc định tối thiểu 1 giây giữa hai trang danh sách.
- Lưu URL nguồn và hash; không tự đoán các trường bị thiếu.
- Website thử nghiệm độc lập, không tự nhận là website chính thức.

## Chạy phát triển

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py crawl_graves --end-page 2
python manage.py runserver
```

## Triển khai

Các mẫu cấu hình tách biệt cho systemd và nginx nằm trong `deploy/`. Ứng dụng chỉ lắng nghe ở `127.0.0.1:8240`; nginx là cổng truy cập công khai.

`lietsivietlao-sync.timer` đồng bộ lại toàn bộ 217 trang danh sách công khai mỗi ngày lúc khoảng 02:20 (Asia/Bangkok). Timer có chế độ `Persistent`, nên nếu máy chủ tắt đúng giờ thì lượt bị lỡ sẽ chạy sau khi máy hoạt động trở lại. Kết quả mỗi lượt được lưu trong bảng `SyncRun` và xem được qua Django Admin/journal systemd.
