# Cấu hình

Các preset nghiên cứu trong environments/, vehicles/, sensors/ và experiments/ vẫn là dự thảo, có `runtime_ready = false`. [lab_v1.toml](lab_v1.toml) là cấu hình kỹ thuật riêng của bãi thử Webots, có world/controller được triển khai; trạng thái kiểm chứng được ghi trong hồ sơ nghiên cứu.

- [project.toml](project.toml): tên dự án, manifest module và các ràng buộc nền.
- [environments/level_b.toml](environments/level_b.toml): phạm vi môi trường.
- [vehicles/drone.toml](vehicles/drone.toml): mô hình phương tiện cần xác định.
- [sensors/local_ranges.toml](sensors/local_ranges.toml): hướng cảm biến khoảng cách đề xuất.
- [experiments/level_b.toml](experiments/level_b.toml): điều kiện và chỉ số cần đặc tả.
- [agents/codex.toml](agents/codex.toml): cấu hình Codex dùng qua launcher; không phải preset thí nghiệm.

Mọi thuật toán tương lai phải kiểm tra cấu hình trước khi chạy. Khi bổ sung tham số số học cần khai báo đơn vị và miền hợp lệ. Chưa chọn phiên bản Webots hay dependency huấn luyện trong milestone này.
