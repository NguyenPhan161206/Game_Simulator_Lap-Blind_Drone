# Webots lab v1

World và robot được tạo từ [configs/lab_v1.toml](../../configs/lab_v1.toml), không phụ thuộc tải asset lúc mở. Xem [hướng dẫn chạy, phím và giới hạn](../../docs/lab-v1.md).

- worlds/minimal_lab.wbt: bãi 3D, ba vật cản, điểm đích và supervisor.
- protos/BlindDrone.proto: thân primitive, bốn Propeller, GPS/IMU/gyro và 10 DistanceSensor, không camera.
- controllers/drone_controller/: entry point Robot không có quyền Supervisor.
- controllers/lab_supervisor/: quản lý/reset, nhãn hiển thị, fixture kiểm tra và kết quả.
- plugins/: chưa cần plugin riêng.

Dùng python3 tools/build_lab.py để cập nhật world/PROTO sau thay đổi cấu hình, rồi python3 tools/build_lab.py --check. Không sửa file generated bằng tay.

Bản này là điều khiển thủ công qua bộ ổn định. Kiểm tra smoke dùng chuỗi operator command để xác minh mô phỏng, không phải AI điều hướng.
