# Kiểm tra

Hiện dùng python3 tools/check_scaffold.py để kiểm tra foundation.

Khi triển khai runtime, thêm kiểm tra hành vi vào các nhóm phù hợp:
- Hợp đồng: đơn vị, frame, validity, timestamp.
- Quan sát: vật cản ẩn/ngoài tầm không được lộ vào policy.
- Cảm biến: tầm, góc, nhiễu, trễ và phép đo thiếu.
- Nhiệm vụ: va chạm, tới đích, dừng, timeout và ưu tiên kết thúc.
- Webots: world load, thiết bị, reset và controller thực sự hoạt động.
- Đánh giá: chia tập, chạy ghép cặp và tính cả thất bại.

Không có kết quả simulator/training nào được tạo bởi scaffold này.
