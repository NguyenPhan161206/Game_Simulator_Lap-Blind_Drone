# Blind Drone Lab — phòng lab mô phỏng tự hành không camera

Nghiên cứu cách sử dụng thông tin cảm biến tiết kiệm để phương tiện giao hàng tự di chuyển và tránh vật cản. Bắt đầu ở **mức B: một drone đến đích được cung cấp, tránh vật cản tĩnh trong môi trường chưa biết đầy đủ**. Webots là nền tảng khảo sát đầu tiên.

Camera có thể hỗ trợ tạo dữ liệu/huấn luyện ở nhánh nghiên cứu riêng; hệ thống điều hướng khi vận hành và đánh giá tự hành không nhận ảnh camera. Trạng thái thật của toàn môi trường dành cho tạo tình huống, chấm điểm và quan sát, không đưa trực tiếp vào điều hướng.

## Trạng thái hiện tại

Đã tạo kiến trúc thư mục, hướng dẫn agent, cấu hình dự thảo và công cụ kiểm tra nền. **Chưa có world Webots, controller thực thi, model đã huấn luyện hoặc kết quả đánh giá tự hành.** Các thông số cảm biến, động lực học và ngưỡng thành công còn cần đặc tả.

## Bắt đầu

Python 3.11+; kiểm tra nền dùng thư viện chuẩn, không cần cài dependency:

```bash
python3 tools/check_scaffold.py
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
- [Nguồn và giấy phép thành phần ngoài](THIRD_PARTY.md)

## Hướng phát triển

Đặc tả môi trường → world và điều khiển thủ công → xác minh cảm biến/va chạm → baseline và bộ đánh giá → huấn luyện → khảo sát giảm dữ liệu. Sau core phương tiện mới mở rộng một chuyến giao hàng và điều phối logistics.

Các config mô phỏng hiện mang `status = "draft"`, `runtime_ready = false`. Không dùng chúng như một preset thực nghiệm đã hoàn thiện.
