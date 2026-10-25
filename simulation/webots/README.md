# Webots adapter workspace

Trạng thái: chưa có world hoặc controller thực thi. Webots là nền tảng khảo sát đầu tiên, chưa cài/chốt phiên bản trong scaffold.

- worlds/: các world .wbt của thí nghiệm.
- protos/: cấu hình robot và cảm biến; ghi license trước khi nhập asset.
- controllers/drone_controller/: entry point gắn với drone, chuyển dữ liệu thiết bị sang hợp đồng quan sát.
- controllers/lab_supervisor/: tạo/reset tình huống, chấm điểm và ghi log. Trạng thái thật không được chảy vào controller điều hướng.
- plugins/: phần mở rộng chỉ thêm khi thiết bị có sẵn không đáp ứng mô hình cần nghiên cứu.

Khởi đầu bằng world tối thiểu và điều khiển thủ công, kiểm tra cảm biến và va chạm trước huấn luyện. Hướng dẫn phát triển ở [docs/development.md](../../docs/development.md).
