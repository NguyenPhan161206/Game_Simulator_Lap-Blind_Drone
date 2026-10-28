# Hợp đồng dữ liệu dự kiến

Trạng thái: runtime.py có VehicleState/MotionCommand; navigation.py có NavigationMission, NavigationObservation và RangeReading. EpisodeEvaluator xuất kết quả dưới dạng dict/JSON. Bảng bên dưới còn gồm các hợp đồng đích cho mốc sau, chưa phải toàn bộ class đã triển khai. V1 dùng ENU cho thế giới và FLU cho thân; mét, giây, radian. Các thiết bị được đặt theo cùng frame ở Webots, vận tốc thân được đổi từ GPS ENU theo yaw. Xem [schema runtime/tiêu chí cụ thể](../navigation-v1.md).

| Bản tin | Nội dung cần có | Bên nhận |
|---|---|---|
| MissionGoal | Vị trí đích, frame, ID nhiệm vụ và điều kiện nhiệm vụ được phép biết | Điều hướng, đánh giá |
| SensorPacket | Timestamp mô phỏng, sensor ID, frame, phép đo, validity/missing mask, cấu hình/provenance | Quan sát |
| Observation | Đích tương đối, trạng thái đo/ước lượng, phép đo cục bộ và lịch sử đã khai báo | Điều hướng |
| MotionCommand | Yêu cầu chuyển động, frame, timestamp, giới hạn và thời hạn hiệu lực | Điều khiển |
| ActuatorCommand | Lệnh hợp lệ cho mô hình phương tiện đã chọn | Adapter phương tiện |
| GroundTruthSnapshot | Trạng thái thật, hình học, va chạm và thông tin chấm điểm | Supervisor/đánh giá/hiển thị |
| EpisodeResult | ID tình huống, cấu hình, model/baseline version, kết quả, lý do kết thúc và chỉ số | Nhật ký/báo cáo |

## Quan sát được phép

Chỉ chứa thông tin có nguồn đo/ước lượng hoặc thông tin nhiệm vụ đã khai báo. Vị trí/vận tốc lý tưởng có thể dùng làm baseline mô phỏng nếu ghi rõ là nguồn đo lý tưởng. Không che việc đọc trạng thái thật bằng cách gọi nó là GPS/IMU.

V2 dùng cùng NavigationObservation, thêm MissionV2 với whitelist goal_m/policy. Grid là trạng thái suy ra từ ray/pose, không phải bản sao scene; free/occupied/unknown và counters được khai báo trong [v2](../navigation-v2.md). Whitelist và kiểm tra code là hợp đồng luồng dữ liệu, chưa phải sandbox quyền OS: controller kế thừa môi trường launcher, còn navigation class không đọc metadata thí nghiệm từ đó.

## Thông tin đặc quyền

Toàn bộ danh sách vật cản, ID/tag vật thể, vật cản ngoài tầm hoặc sau che khuất, đường chuẩn và ảnh camera không thuộc Observation runtime. GroundTruthSnapshot không được truyền vào điều hướng hay bộ lọc lệnh của phương tiện.

## Dữ liệu thiếu và thời gian

Không có phát hiện trong tầm đo không đồng nghĩa một hướng luôn trống. Phải phân biệt no-return, ngoài tầm, mẫu lỗi, dữ liệu cũ và vật thể ở khoảng cách tối đa. Kiểm tra timestamp và validity trước khi dùng; mô phỏng độ trễ theo thời gian mô phỏng.

## Đo lượng dữ liệu

Báo riêng đầu ra cảm biến, đầu vào mô hình và dữ liệu lưu. Số float/giây hoặc byte/giây cần kèm cách mã hóa, metadata và cửa sổ lịch sử; không tự coi chúng là mức riêng tư hoặc lượng thông tin ngữ nghĩa.

## V3 — pose tại acquisition

`SampledObservation` giữ current state và acquisition state riêng; range timestamp phải khớp acquisition pose. Grid cập nhật theo acquisition pose, guard/lệnh theo current measured state giữ giữa hai lần pose sampling. GPS/IMU/Gyro 32 ms, policy/stabilizer 16 ms; không nội suy bằng ground truth. [Runtime v3](../runtime-v3.md) và [bằng chứng development](../research/2026-10-28-cadence-v3-development.md) mô tả counters, payload 96 B, log bytes, CPU process/wall và RSS riêng. Khóa thiết kế giữ nguyên trạng thái lịch sử `runtime_ready=false`; artifact runtime lock mới quyết định quyền chạy held-out.
