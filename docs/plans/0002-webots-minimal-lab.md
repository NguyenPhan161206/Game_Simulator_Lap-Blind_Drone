# Kế hoạch 0002 — môi trường Webots tối thiểu

**Trạng thái hiện tại:** Hoàn tất môi trường trên CI. [Bằng chứng](../research/2026-10-25-webots-v1-smoke.md). Các bước và giới hạn lúc thực thi bên dưới là lịch sử, không là việc đang chờ chạy lại.

Ngày bắt đầu: 2026-10-25. Yêu cầu: lập kế hoạch chi tiết rồi thực hiện từng bước để có môi trường, drone điều khiển thủ công, va chạm, cảm biến không camera và reset.

## Phạm vi và cách ra quyết định

Các con số của bản thử là lựa chọn kỹ thuật có thể sửa, không phải ngưỡng nghiên cứu đã được người dùng xác nhận. Không huấn luyện AI, không tuyên bố đã giải quyết điều hướng tự động mức B. Dữ liệu thật của thế giới chỉ dành cho tạo/reset và kiểm tra, không làm đầu vào controller drone.

Mỗi bước chỉ được đánh dấu đạt khi có bằng chứng tương ứng. Kiểm tra Python không thay thế chạy Webots. Nếu máy local chưa thể cài/chạy, tiếp tục hoàn thiện world và kiểm tra trên CI có Webots; báo riêng khả năng chạy local và CI.

## Các bước thực hiện

| Bước | Công việc | Sản phẩm | Điều kiện qua bước |
|---|---|---|---|
| 1 | Kiểm tra OS, RAM, đồ họa, Python, Webots và khả năng tải/cài trong workspace | Báo cáo môi trường | Biết điều kiện local và chọn đường chạy kiểm chứng |
| 2 | Đặc tả bãi thử, frame, phương tiện, phép đo, điều khiển và giới hạn | ADR + cấu hình v1 | Có đơn vị và nguồn dữ liệu rõ, tham số không mâu thuẫn |
| 3 | Dựng world và robot bằng primitive, không phụ thuộc tải asset lúc mở | World/PROTO tạo lại được | Kiểm tra cấu trúc; Webots load không báo lỗi world/device |
| 4 | Tạo controller giữ ổn định và điều khiển bằng bàn phím | Controller + hướng dẫn phím | Bay ổn định; lệnh di chuyển/đổi hướng/dừng tạo đáp ứng có đo |
| 5 | Gắn cảm biến khoảng cách, GPS/IMU/gyro mô phỏng lý tưởng | Quan sát có frame/đơn vị/validity | Số đo khớp bố trí kiểm tra; không có camera hoặc supervisor trong controller drone |
| 6 | Thêm supervisor kiểm tra, nhật ký và reset | Runner smoke + kết quả JSON | Kiểm tra hover, di chuyển, khoảng cách, va chạm, reset thực sự trên Webots |
| 7 | Rà soát hình ảnh hiển thị, hướng dẫn mở world và thao tác | Ảnh/replay khi công cụ cho phép, tài liệu chạy | Người dùng có cách mở và thao tác; ghi rõ phần GUI đã/chưa quan sát |
| 8 | Chạy toàn bộ kiểm tra liên quan, cập nhật trạng thái và bàn giao | Báo cáo bằng chứng, thay đổi Git | Không có bước nào được tuyên bố đạt chỉ dựa trên stub hoặc log giả |

## Trạng thái ban đầu

- Git worktree sạch tại c319ec2 trước thay đổi.
- Local: Ubuntu 26.04.1 x86_64, Python 3.14.4; khoảng 15 GB RAM tổng, khoảng 2.4 GB khả dụng tại thời điểm kiểm tra.
- Chưa tìm thấy Webots, Xvfb hoặc glxinfo qua PATH và các vị trí thông thường.
- DISPLAY/Wayland hiện có; công cụ UI không liệt kê app/browser có thể điều khiển trong phiên này.
- Bản phát hành chính thức mới nhất được GitHub API trả về: R2025a, có tarball Linux khoảng 150 MB.

## Nhật ký tiến độ

- [x] Ghi kế hoạch trước khi triển khai.
- [x] Bước 1: xác định đường chạy Webots và ghi giới hạn local. Shell không phân giải github.com nên tarball chưa tải được local; chọn kiểm chứng bổ sung trên CI Ubuntu/Xvfb.
- [x] Bước 2: đặc tả v1, ghi ADR 0002 và configs/lab_v1.toml.
- [x] Bước 3: world và robot đã load trên Webots R2025a trong CI.
- [x] Bước 4: mapping phím được kiểm tra bằng Python; đáp ứng tiến/phanh/sang ngang/yaw/lên cao đã đo qua operator command trong simulator. Chưa bấm phím GUI local.
- [x] Bước 5: phép đo 1.37 m phía trước, 1.38 m phía dưới khớp fixture; không có Camera và không cấp layout cho drone. 13 kiểm tra Python đạt.
- [x] Bước 6: 12 mục smoke đạt, gồm che khuất, contact vật lý đúng vị trí và reset xóa contact.
- [x] Bước 7: đã xem ảnh observer đúng world, sửa hướng nhìn; có docs/lab-v1.md hướng dẫn. GUI local chưa được mở/thao tác trong phiên.
- [x] Bước 8: bằng chứng và giới hạn được lưu ở docs/research/2026-10-25-webots-v1-smoke.md cùng JSON.

Kết luận mốc: bản thử môi trường đã được triển khai và kiểm chứng qua CI có simulator thật. Việc cài/chạy GUI local còn phụ thuộc môi trường máy; không báo nó là đã hoàn thành. Không huấn luyện AI trong mốc này.

Nguồn bản phát hành: https://github.com/cyberbotics/webots/releases/tag/R2025a
