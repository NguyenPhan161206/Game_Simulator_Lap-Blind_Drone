# Điều hướng tham chiếu v1

Mốc này thêm hai thuật toán không học và bộ chấm nhiệm vụ trên Webots v1. [Báo cáo kiểm chứng simulator](research/2026-10-26-navigation-v1.md): reactive đạt 3/3 ca khả thi trong tám lượt ghép cặp; xem giới hạn và mọi outcome trong báo cáo. [Kế hoạch](plans/0003-navigation-baseline.md) ghi trạng thái từng bước; kiểm tra Python không thay thế chạy simulator.

## Đường chạy

```bash
make check
python3 tools/run_webots.py --navigation
python3 tools/run_webots.py --navigation --policy reactive --case single_block
python3 tools/run_webots.py --navigation --policy reactive --case single_block --realtime
```

Cần Webots R2025a; xem [cài đặt lab](lab-v1.md). Headless dùng xvfb-run -a và --software-rendering. Mặc định chạy hai phương pháp trên bốn fixture, tám lượt độc lập. --policy direct hoặc reactive chỉ chọn một phương pháp. Không có Webots thì runner trả lỗi, không tạo kết quả giả.

Runner tự động mặc định chạy fast để kiểm tra; --realtime cho phép quan sát cùng chuyển động vật lý và nhãn trạng thái ở tốc độ thời gian thực. Bàn phím chuyển động không can thiệp lượt tự hành. Chạy không có --navigation để trở lại manual. Trong lượt đánh giá, reset ngoài giao thức làm lượt kiểm tra thất bại.

## Thuật toán và dữ liệu

- direct: vận tốc hướng tới đích, giảm theo khoảng cách; không né vật cản. Đây là đối chứng kiểm tra việc chấm va chạm.
- reactive: đi tới đích; khi các ray gần hướng đích bị chắn thì ghi khoảng cách tới đích lúc gặp vật cản và chuyển sang tiếp tuyến trái của bề mặt đo gần nhất. Chỉ thoát chế độ khi hướng đích đủ thoáng và đã tiến gần đích hơn. Lệnh bị giới hạn thêm theo khoảng cách phanh trên ray.

Đây là heuristic tự viết, không có bảo đảm hoàn thành hoặc tránh mọi va chạm. Tám ray ngang bỏ sót vật cản giữa các hướng; ray không chứng nhận cả hành lang theo kích thước thân. Không có bản đồ, A*, waypoint đặc quyền, nhãn vật thể hoặc ảnh. Lịch sử thuật toán chỉ gồm cờ bám tiếp tuyến và khoảng cách tới đích lúc vào chế độ; chưa có bản đồ tích lũy.

NavigationObservation chỉ chứa VehicleState từ GPS/IMU/gyro đã khai báo và 10 RangeReading. Frame body_FLU, khoảng cách m, timestamp theo thời gian mô phỏng. Tất cả ray phải có giá trị hữu hạn, hợp lệ, đúng schema và không cũ hơn 0.12 s; nếu không, navigation yêu cầu vận tốc zero. Trạng thái at_limit chỉ là không đo thấy trong tầm. Giữ yaw; điều chỉnh tới độ cao đích, tránh vật cản chủ yếu theo mặt phẳng ngang. Chưa thử lên/xuống để vượt vật cản.

Supervisor gửi đúng mission chứa goal_m và policy, không gửi danh sách vật cản hoặc vận tốc trong lượt. Nó thay geometry/sensing/collision đồng thời trước lượt, reset và dùng trạng thái vật lý/contact để chấm. Không dịch chuyển drone trong lượt tự hành.

## Chấm điểm và bằng chứng

[navigation_v1.toml](../configs/navigation_v1.toml) tách navigation params với evaluation/cases. Chỉ bảng navigation được whitelist sang drone. Tham số đều là lựa chọn kỹ thuật cho development_diagnostic; không khóa ngưỡng nghiên cứu.

Thành công: nằm trong cầu bán kính 0.5 m và tốc độ ≤0.18 m/s liên tục 1 s, trước hoặc đúng 65 s. Đánh giá ở mỗi bước vật lý 16 ms. Va chạm ưu tiên, tiếp đến vượt biên, thành công rồi timeout. Đến đích sau deadline không được tính đạt. Không cất/hạ cánh hoặc giao kiện hàng.

Mỗi lượt có outcome, thời gian, quãng đường 3D tích lũy, khoảng cách cuối/gần nhất, tốc độ cuối và contact. Kết quả báo mọi lượt; thống kê thời gian/quãng đường chỉ trên lượt thành công được ghi rõ. blocked_goal là đích nằm trong khối kín, báo nhóm đối chứng không khả thi riêng. Ba ca còn lại có lối ngang rộng bằng cấu trúc fixture; chưa dùng bộ sinh/kiểm định đường đi tổng quát.

artifacts/navigation-* chứa result.json, progress.json, manifest.json, telemetry.jsonl và ảnh cuối từng lượt. Ảnh là đầu ra observer. Telemetry JSONL được lấy thưa khoảng 64 ms để xem lại; chấm điểm dùng bước 16 ms, không dùng log lấy thưa. Nhật ký định vị chưa được tối ưu lượng dữ liệu hoặc đánh giá bảo mật.

CI phải giữ smoke v1 đạt, hoàn tất số lượt yêu cầu, kiểm tra đến đích/dwell ở ca trống, phát hiện direct đâm vật cản, reactive đi vòng một khối và không chấm thành công đối chứng âm. Ca nhiều vật cản được báo dù đạt hoặc thất bại. Tập fixture công khai đã dùng phát triển; không dùng số liệu để tuyên bố khả năng khái quát hóa.
