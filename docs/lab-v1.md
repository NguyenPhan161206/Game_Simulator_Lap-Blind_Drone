# Bãi thử Webots v1

Trạng thái trước kiểm chứng: world, robot, controller bàn phím và smoke runner đã được triển khai; kết quả Webots/GUI sẽ được ghi riêng sau chạy. Bản này kiểm tra cơ chế mô phỏng, chưa có AI tự tránh vật cản.

## Cấu hình

[configs/lab_v1.toml](../configs/lab_v1.toml) là nguồn tạo world/PROTO. Bãi 20×20 m, ba khối vật cản, một drone và đích màu xanh. ENU: x đông, y bắc, z lên; thân drone x trước, y trái, z lên.

Drone có body va chạm dạng hộp 0.6×0.6×0.16 m, khối lượng 1 kg, quán tính khai báo và bốn Propeller. Đĩa cánh quạt và mũi chỉ hướng là hiển thị đơn giản; v1 chỉ xét va chạm của hộp thân, chưa mô phỏng va chạm cánh quạt, cản khí hoặc pin. Đây là giới hạn mô hình cần giữ rõ khi tạo lối hẹp.

Actuator là mô hình tốc độ phản hồi nhanh với acceleration/maxTorque rộng, chưa hiệu chỉnh theo motor thật. Webots dùng cả authority của motor trong bước điều khiển tốc độ kinematic của Propeller; giới hạn quá nhỏ có thể làm rotor tăng tốc rất chậm. Telemetry motor_target_rad_s ghi mục tiêu gửi vào motor, không giả làm tốc độ đã đo bằng encoder.

10 DistanceSensor một ray (8 ngang, 2 đứng), tối đa 8 m, chu kỳ 32 ms; vật lý/control 16 ms. Số đo khoảng cách lý tưởng không nhiễu; không mô phỏng RF/radar. GPS, gyro và InertialUnit cũng lý tưởng; InertialUnit trực tiếp phản ánh tư thế mô phỏng, không có bộ fusion hay sai số thực.

## Cài trong dự án

Linux x86_64, Python 3.11+ và đường mạng tới bản phát hành chính thức:

```bash
python3 tools/install_webots.py
python3 tools/build_lab.py --check
python3 tools/run_webots.py
```

Installer ghi vào .local/, không dùng sudo hay thay cấu hình máy. Nếu Webots đã cài ở nơi khác, truyền --webots /duong/dan/webots. Phụ thuộc hiển thị/driver cần phù hợp máy; tarball R2025a chưa được xác nhận trên Ubuntu 26.04 của workspace hiện tại.

Có thể mở trực tiếp [minimal_lab.wbt](../simulation/webots/worlds/minimal_lab.wbt) bằng Webots R2025a. Dùng launcher giúp đặt output và cache vào workspace.

## Điều khiển

Chọn cửa sổ 3D để Webots nhận phím, chạy simulation ở realtime:

| Phím | Tác dụng |
|---|---|
| W / S | Tiến / lùi theo hướng thân |
| A / D | Sang trái / phải theo hướng thân |
| T / G | Tăng / giảm độ cao mục tiêu |
| Q / E | Quay yaw trái / phải |
| SPACE | Yêu cầu vận tốc bằng không, giữ độ cao/yaw mục tiêu |
| Thả các phím chuyển động | Yêu cầu giảm vận tốc về không; vẫn có quãng phanh |
| R | Reset drone về vị trí ban đầu và xóa trạng thái controller |

Đây là điều khiển vận tốc qua bộ ổn định, không là thuật toán né vật cản. Người điều khiển có thể gây va chạm. Để nhìn tia khoảng cách, bật View → Optional Rendering → Show Distance Sensor Rays của Webots.

## Kiểm tra

```bash
python3 tools/check_scaffold.py
python3 tools/build_lab.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/run_webots.py --smoke
```

Máy headless cần display ảo, ví dụ xvfb-run -a python3 tools/run_webots.py --smoke --software-rendering. CI tạo display bằng Xvfb và dùng phần mềm render để kiểm chứng độc lập GPU local.

Smoke thực hiện hover, tiến, phanh, sang ngang, yaw, lên cao, fixture đo khoảng cách, vật cản bị che, va chạm vật lý rồi reset. Lệnh chuyển động được gửi như operator input; supervisor chỉ đặt pose ở fixture/reset được khai báo. Smoke không phải kết quả điều hướng tự động.

Mỗi lượt ghi console.log, telemetry.jsonl, scene.png nếu export thành công và result.json vào artifacts/. Telemetry là phép đo drone; supervisor chấm bằng trạng thái thật. Kết quả cũ không được dùng để báo một lượt mới đạt.

## Ranh giới dữ liệu

Controller drone chỉ nhận cấu hình phương tiện/cảm biến, gravity và tọa độ đích được phép biết. World layout và fixture không nằm trong customData của drone. Supervisor không gửi tọa độ vật cản, đường chuẩn hoặc hình ảnh cho drone.

Phép đo ở giới hạn 8 m có trạng thái at_limit; nó không chứng minh phía ngoài tầm luôn trống. Không có camera trên robot. Ảnh toàn cảnh do supervisor xuất chỉ phục vụ người quan sát.
