# Blind Drone Lab — phòng lab mô phỏng tự hành không camera

Nghiên cứu cách sử dụng thông tin cảm biến tiết kiệm để phương tiện giao hàng tự di chuyển và tránh vật cản. Bắt đầu ở **mức B: một drone đến đích được cung cấp, tránh vật cản tĩnh trong môi trường chưa biết đầy đủ**. Webots là nền tảng khảo sát đầu tiên.

Camera có thể hỗ trợ tạo dữ liệu/huấn luyện ở nhánh nghiên cứu riêng; hệ thống điều hướng khi vận hành và đánh giá tự hành không nhận ảnh camera. Trạng thái thật của toàn môi trường dành cho tạo tình huống, chấm điểm và quan sát, không đưa trực tiếp vào điều hướng.

## Trạng thái hiện tại

Đã có bộ khung, world Webots v1 bằng primitive, drone không camera, controller bàn phím và bộ kiểm tra. Việc chạy Webots được kiểm chứng riêng với các kiểm tra Python; xem [kế hoạch và tiến độ](docs/plans/0002-webots-minimal-lab.md). Chưa có model học hoặc kết quả điều hướng tự động. Cấu hình v1 là prototype kỹ thuật; các ngưỡng nghiên cứu vẫn cần đặc tả.

## Bắt đầu

Python 3.11+; kiểm tra nền dùng thư viện chuẩn, không cần cài dependency:

```bash
python3 tools/check_scaffold.py
python3 tools/build_lab.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/run_codex.py --dry-run
```

Agent bắt đầu tại [AGENTS.md](AGENTS.md). Đọc [hướng dẫn phát triển](docs/development.md) để dùng Git và cấu hình Codex trong môi trường managed.

## Bản đồ tài liệu

- [Ý tưởng và quyết định từ cuộc trao đổi](docs/01-y-tuong-va-quyet-dinh.md)
- [Dự thảo thí nghiệm mức B](docs/02-du-thao-thi-nghiem-muc-b.md)
- [Kiến trúc hệ thống](docs/architecture/system.md)
- [Hợp đồng và ranh giới dữ liệu](docs/architecture/data-contracts.md)
- [Cây thư mục](docs/architecture/repository.md)
- [Quyết định nền tảng](docs/decisions/0001-foundation.md)
- [Cấu hình](configs/README.md) và [workflow agent](agents/README.md)
- [Chạy và điều khiển bãi thử Webots v1](docs/lab-v1.md)
- [Nguồn và giấy phép thành phần ngoài](THIRD_PARTY.md)

## Hướng phát triển

Đặc tả môi trường → world và điều khiển thủ công → xác minh cảm biến/va chạm → baseline và bộ đánh giá → huấn luyện → khảo sát giảm dữ liệu. Sau core phương tiện mới mở rộng một chuyến giao hàng và điều phối logistics.

Các preset nghiên cứu level_b vẫn mang `status = "draft"`, `runtime_ready = false`. [lab_v1.toml](configs/lab_v1.toml) là preset kỹ thuật riêng cho môi trường và kiểm tra simulator, không phải cấu hình nghiên cứu đã hoàn thiện.
