# Blind Drone Lab — phòng lab mô phỏng tự hành không camera

Nghiên cứu cách sử dụng thông tin cảm biến tiết kiệm để phương tiện giao hàng tự di chuyển và tránh vật cản. Bắt đầu ở **mức B: một drone đến đích được cung cấp, tránh vật cản tĩnh trong môi trường chưa biết đầy đủ**. Webots là nền tảng khảo sát đầu tiên.

Camera có thể hỗ trợ tạo dữ liệu/huấn luyện ở nhánh nghiên cứu riêng; hệ thống điều hướng khi vận hành và đánh giá tự hành không nhận ảnh camera. Trạng thái thật của toàn môi trường dành cho tạo tình huống, chấm điểm và quan sát, không đưa trực tiếp vào điều hướng.

## Trạng thái hiện tại

Đã kiểm chứng Webots v1 và [điều hướng v2](docs/navigation-v2.md) không camera: reactive, guarded và mapped từ grid tự đo. [Báo cáo giai đoạn 0005](docs/research/2026-10-26-navigation-v2.md) có 64 unit test và 108 lượt chính thức, protocol khóa trước validation/test mới. Guarded/mapped đạt 10/10 ca khả thi mỗi split; reactive 8/10 với hai U collision.

Đây là kết quả mô phỏng lý tưởng, điều hướng ngang trong tập hữu hạn; chưa ANN/RL, chưa giảm dữ liệu hoặc bảo đảm an toàn/riêng tư. V2 dùng thêm bộ nhớ/CPU. [Lượt laptop](docs/research/2026-10-26-local-acceptance.md) đã có GUI được người thao tác xác nhận và mapped success; phần thử đủ phím, quan sát mapped và mô tả độ phản hồi còn cần bổ sung. Phiên managed vẫn không kết nối được display.

V1 được giữ để tái lập: [môi trường](docs/research/2026-10-25-webots-v1-smoke.md), [baseline](docs/research/2026-10-26-navigation-v1.md), [seeded suite](docs/research/2026-10-26-seeded-environments.md). Test v1 và v2 đều đã exposed; thay thuật toán cần protocol/test mới.

## Bắt đầu

Python 3.11+; kiểm tra nền dùng thư viện chuẩn, không cần cài dependency:

```bash
python3 tools/check_scaffold.py
python3 tools/build_lab.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/run_codex.py --dry-run
```

Agent bắt đầu tại [AGENTS.md](AGENTS.md). Đọc [hướng dẫn phát triển](docs/development.md) để dùng Git và cấu hình Codex trong môi trường managed.

Chạy thử khi đã cài Webots: python3 tools/run_navigation_v2.py --policy mapped --case development-u_trap-s21001 --realtime. [Hướng dẫn cài/màn hình](docs/navigation-v2.md) và [kế hoạch từng bước](docs/plans/0005-observation-and-navigation-v2.md).

## Bản đồ tài liệu

- [Checklist tổng thể từ ý tưởng đến roadmap tương lai](CHECKLIST_DU_AN.md)
- [Cây phiên bản GitHub, source kiểm chứng và nhánh tích hợp](docs/version-history.md)
- [Nghiệm thu GUI local, bàn phím và so sánh CI — nhánh L](docs/local-acceptance.md)
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
