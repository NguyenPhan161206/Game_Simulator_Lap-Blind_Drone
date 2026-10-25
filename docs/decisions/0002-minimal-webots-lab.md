# ADR 0002 — bản thử môi trường Webots v1

Ngày: 2026-10-25. Trạng thái: lựa chọn kỹ thuật để thực hiện yêu cầu tạo môi trường; các ngưỡng nghiên cứu vẫn còn mở.

## Quyết định

- Pin Webots R2025a, bản phát hành chính thức được API trả về ở bước kiểm tra.
- Tạo robot và world từ primitive bằng mã gốc của dự án, không nhập model/mesh Mavic hoặc asset cần tải khi mở world.
- Frame thế giới ENU: x đông, y bắc, z lên. Frame thân: x trước, y trái, z lên. Góc dùng radian, độ dài mét, thời gian giây.
- Webots là nguồn trạng thái vật lý duy nhất. Drone có khối lượng, quán tính, bốn Propeller và lệnh tốc độ động cơ; không dùng supervisor để đẩy hoặc di chuyển drone trong quá trình điều khiển thường.
- Điều khiển thủ công đặt vận tốc thân, vận tốc đứng và tốc độ yaw; bộ điều khiển ổn định dùng GPS/IMU/gyro mô phỏng lý tưởng. Các số đo này chưa đại diện nhiễu hoặc trôi của thiết bị thật.
- Dùng 8 phép đo ngang và 2 phép đo đứng bằng DistanceSensor generic một ray, giới hạn 8 m. Bản đầu không nhiễu; bản này kiểm tra cơ chế trước khi mở rộng nhiễu. Không gọi đây là radar vật lý.
- Tạo bãi 20×20 m, biên cao 6 m, ba vật cản, điểm xuất phát và đích. Các con số trong configs/lab_v1.toml là preset prototype.
- Giữ các preset nghiên cứu level_b trước đây ở trạng thái draft; lab_v1 là preset kỹ thuật riêng.

## Ranh giới quyền và phép thử

Controller drone chỉ dùng Robot, thiết bị đo, bàn phím và gói lệnh operator. Supervisor nhận telemetry và chỉ dùng trạng thái thật để chấm, đặt fixture cảm biến/va chạm và reset có khai báo. Gói operator không chứa danh sách vật cản hay đường oracle.

Kịch bản smoke đưa lệnh thủ công có định thời, không phải điều hướng tự động. Việc supervisor đặt lại pose chỉ diễn ra ở fixture kiểm tra và reset, không được tính là năng lực bay của thuật toán.

## Đường chạy kiểm chứng

Local hiện thiếu Webots và không phân giải được github.com qua shell nên không tải được tarball. Có thể cài bản chính thức trong workspace khi đường mạng cho phép. Để không thay kiểm tra simulator bằng kiểm tra stub, dùng CI Ubuntu có Xvfb và tarball chính thức khi cần; báo riêng kết quả local, CI và GUI.

Nguồn API đã đọc tại tag R2025a: Propeller, DistanceSensor, InertialUnit, Supervisor và hướng dẫn cài/chạy của cyberbotics/webots. Controller và hình học bản thử được viết mới; không sao chép controller Mavic.
