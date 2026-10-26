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

## Thông tin đặc quyền

Toàn bộ danh sách vật cản, ID/tag vật thể, vật cản ngoài tầm hoặc sau che khuất, đường chuẩn và ảnh camera không thuộc Observation runtime. GroundTruthSnapshot không được truyền vào điều hướng hay bộ lọc lệnh của phương tiện.

## Dữ liệu thiếu và thời gian

Không có phát hiện trong tầm đo không đồng nghĩa một hướng luôn trống. Phải phân biệt no-return, ngoài tầm, mẫu lỗi, dữ liệu cũ và vật thể ở khoảng cách tối đa. Kiểm tra timestamp và validity trước khi dùng; mô phỏng độ trễ theo thời gian mô phỏng.

## Đo lượng dữ liệu

Báo riêng đầu ra cảm biến, đầu vào mô hình và dữ liệu lưu. Số float/giây hoặc byte/giây cần kèm cách mã hóa, metadata và cửa sổ lịch sử; không tự coi chúng là mức riêng tư hoặc lượng thông tin ngữ nghĩa.
