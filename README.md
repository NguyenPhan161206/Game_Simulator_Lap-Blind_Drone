# Blind Drone Lab — phòng lab mô phỏng tự hành không camera

Nghiên cứu cách sử dụng thông tin cảm biến tiết kiệm để phương tiện giao hàng tự di chuyển và tránh vật cản. Bắt đầu ở **mức B: một drone đến đích được cung cấp, tránh vật cản tĩnh trong môi trường chưa biết đầy đủ**. Webots là nền tảng khảo sát đầu tiên.

Camera có thể hỗ trợ tạo dữ liệu/huấn luyện ở nhánh nghiên cứu riêng; hệ thống điều hướng khi vận hành và đánh giá tự hành không nhận ảnh camera. Trạng thái thật của toàn môi trường dành cho tạo tình huống, chấm điểm và quan sát, không đưa trực tiếp vào điều hướng.

## Trạng thái hiện tại

Đã có world Webots v1, điều khiển thủ công, hai baseline không học và bộ đánh giá. Giai đoạn [môi trường có seed/protocol khóa](docs/seeded-environments-v1.md) đã hoàn tất kiểm chứng CI; [kế hoạch](docs/plans/0004-seeded-environments.md) ghi từng bước. Chưa có model học. Protocol v1 khóa các ngưỡng kỹ thuật của suite, chưa xác định chất lượng sản phẩm giao hàng.

[Báo cáo kiểm chứng](docs/research/2026-10-25-webots-v1-smoke.md): 13 kiểm tra Python và 12 mục smoke trên Webots thật trong CI đạt; đã xem ảnh observer. Cài/chạy GUI local chưa được xác nhận.

[Navigation v1 đã chạy trên Webots CI](docs/research/2026-10-26-navigation-v1.md): 29 unit test và 12 mục smoke đạt; tám lượt ghép cặp trên bốn fixture công khai. Reactive hoàn thành ba ca khả thi, direct hoàn thành một; đối chứng âm được báo riêng. Chưa có kết luận khái quát hóa hoặc model học.

[Giai đoạn môi trường có seed/đánh giá đã hoàn thành](docs/research/2026-10-26-seeded-environments.md): 36 case có chứng cứ hình học, split/protocol khóa, 42 unit test và 48 lượt Webots ghép cặp. Reactive dev 8/10, validation 4/5, test 5/5 ca khả thi; ba U collision vẫn được báo. [Cách chạy thử](docs/seeded-environments-v1.md). Chưa huấn luyện, chưa kết luận vững/an toàn hoặc bảo mật.

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
