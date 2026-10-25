# Phát triển và kiểm tra

## Milestone hiện tại

Scaffold kiến trúc và tooling. Chưa có lệnh chạy Webots hoặc train model vì các phần đó chưa được triển khai. Python 3.11+ đủ cho các kiểm tra nền; chưa cần pip install.

```bash
python3 tools/check_scaffold.py
python3 tools/run_codex.py --dry-run
```

## Cấu hình agent

Đọc [agents/README.md](../agents/README.md). Cấu hình portable dùng launcher; chạy trực tiếp Codex vẫn nhận root AGENTS.md. Model, tài khoản, quyền và trust do môi trường/người dùng quản lý.

## Git trong workspace managed

Checkout bình thường dùng Git như thường lệ. Trong phiên AI_Lap hiện tại, .git là thư mục rỗng được quản lý đặt chỉ đọc; không sửa quyền hoặc xóa nó.

[tools/git.sh](../tools/git.sh) ưu tiên metadata cục bộ đã khởi tạo trong .local/git; nếu không có thì dùng repo chuẩn. Cách này giữ đúng lịch sử của workspace khi môi trường managed tạo thêm .git rỗng/chỉ đọc. Lệnh helper không tự khởi tạo hoặc thay thế repository.

```bash
bash tools/git.sh status --short --branch
bash tools/git.sh diff --check
```

Khi clone repo từ GitHub vào thư mục thông thường, helper tự dùng .git bình thường. .local/ không được push.

## Bước triển khai tiếp theo

1. Chốt đặc tả môi trường tối thiểu và các tham số còn mở.
2. Chọn phiên bản Webots/asset, ghi provenance.
3. Tạo world và điều khiển thủ công; kiểm tra va chạm.
4. Kiểm tra đầu ra cảm biến và ranh giới quan sát.
5. Thêm baseline và đánh giá nhiệm vụ.
6. Chỉ sau đó tích hợp huấn luyện.

## Trạng thái kiểm chứng

CI kiểm tra cấu trúc, TOML và các bất biến khai báo. Nó không chứng minh độ đúng vật lý, không có rò rỉ thông tin lúc chạy hoặc chất lượng AI. Cần kiểm tra hành vi tương ứng khi runtime được triển khai.
