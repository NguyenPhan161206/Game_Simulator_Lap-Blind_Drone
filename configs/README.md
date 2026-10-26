# Cấu hình

Các preset nghiên cứu trong environments/, vehicles/, sensors/ và experiments/ vẫn là dự thảo, có `runtime_ready = false`. [lab_v1.toml](lab_v1.toml) là cấu hình kỹ thuật riêng của bãi thử Webots, có world/controller được triển khai; trạng thái kiểm chứng được ghi trong hồ sơ nghiên cứu.

- [project.toml](project.toml): tên dự án, manifest module và các ràng buộc nền.
- [navigation_v1.toml](navigation_v1.toml): tham số baseline, scoring và fixture development; chỉ bảng navigation được chuyển sang drone. [Kết quả kiểm chứng](../docs/research/2026-10-26-navigation-v1.md).
- [scenario_suite_v1.toml](scenario_suite_v1.toml): seed/family/split và các tham số kỹ thuật của suite ngang. [Manifest](scenarios/seeded_v1.json) là fixture tái lập, không phải dữ liệu cảm biến; [protocol lock](scenarios/protocol_v1.lock.json) ghi checksum runtime/config. Xem [cách sử dụng](../docs/seeded-environments-v1.md).
- [environments/level_b.toml](environments/level_b.toml): phạm vi môi trường.
- [vehicles/drone.toml](vehicles/drone.toml): mô hình phương tiện cần xác định.
- [sensors/local_ranges.toml](sensors/local_ranges.toml): hướng cảm biến khoảng cách đề xuất.
- [experiments/level_b.toml](experiments/level_b.toml): điều kiện và chỉ số cần đặc tả.
- [agents/codex.toml](agents/codex.toml): cấu hình Codex dùng qua launcher; không phải preset thí nghiệm.

Khi bổ sung tham số số học cần khai báo đơn vị và miền hợp lệ, chạy lại kiểm tra liên quan. Webots được ghim R2025a; chưa chọn dependency huấn luyện. Preset kỹ thuật có thể chạy không có nghĩa các ngưỡng nghiên cứu đã được khóa.
