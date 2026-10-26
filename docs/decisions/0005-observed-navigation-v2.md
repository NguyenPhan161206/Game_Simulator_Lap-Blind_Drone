# ADR 0005 — quan sát có bộ nhớ và điều hướng v2

Ngày: 2026-10-26. Thực hiện mốc tiếp theo sau seeded v1 theo yêu cầu người dùng.

- Giữ v1 runtime/lock để tái lập. V2 có controller/world/runner/protocol riêng, dùng cùng vật lý và cảm biến lý tưởng.
- Grid chỉ dựng từ ray và pose đo được, không từ full scene. Unknown khác free. Supervisor chỉ tạo/reset/chấm, không cấp route.
- So sánh reactive, guarded và mapped như các gói thành phần. Guarded/mapped thêm quét, hull guard và giảm tốc; mapped thêm lập đường từ grid tự đo. Không coi đây là ablation đơn yếu tố.
- Chọn tham số trên development, kiểm tra recovery bằng unit/contract và Webots dev, khóa trước fresh validation/test. Các code/config đã khóa giữ nguyên sau exposure.
- Theo dõi sampling, storage cell và CPU riêng. Tăng bộ nhớ có thể tăng thông tin bố trí được giữ; không coi không camera là chứng minh riêng tư.

[Kết quả chính thức](../research/2026-10-26-navigation-v2.md): đủ 108 lượt và 64 unit test; mục tiêu development đạt và fresh outcomes được giữ đầy đủ. Mốc này không mở rộng sang huấn luyện, logistics hoặc phần cứng. V2 test hiện đã exposed.
