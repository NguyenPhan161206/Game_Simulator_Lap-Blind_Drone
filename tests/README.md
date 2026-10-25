# Kiểm tra

Chạy make check cho foundation, file generated và các kiểm tra Python. tests/test_lab_core.py kiểm tra cân bằng lực/mô-men, dấu điều khiển, đổi frame, dữ liệu không hợp lệ, giới hạn command, phím và ranh giới cấu hình/scene.

Chạy python3 tools/run_webots.py --smoke với Webots R2025a cho kiểm chứng simulator thật: hover, chuyển động, phanh, cảm biến, che khuất, va chạm và reset. Missing Webots trả lỗi, không bỏ qua rồi báo đạt.

Chưa có kiểm tra chất lượng mô hình học hoặc thực nghiệm ngoài đời. Thao tác GUI bằng tay phải báo riêng với chuỗi operator script của smoke.
