# Blind Drone Lab — phòng lab mô phỏng tự hành không camera

Nghiên cứu cách sử dụng thông tin cảm biến tiết kiệm để phương tiện giao hàng tự di chuyển và tránh vật cản. Bắt đầu ở **mức B: một drone đến đích được cung cấp, tránh vật cản tĩnh trong môi trường chưa biết đầy đủ**. Webots là nền tảng khảo sát đầu tiên.

Camera có thể hỗ trợ tạo dữ liệu/huấn luyện ở nhánh nghiên cứu riêng; hệ thống điều hướng khi vận hành và đánh giá tự hành không nhận ảnh camera. Trạng thái thật của toàn môi trường dành cho tạo tình huống, chấm điểm và quan sát, không đưa trực tiếp vào điều hướng.

## Trạng thái hiện tại

Đã kiểm chứng Webots v1 và [điều hướng v2](docs/navigation-v2.md) không camera: reactive, guarded và mapped từ grid tự đo. [Báo cáo giai đoạn 0005](docs/research/2026-10-26-navigation-v2.md) có 64 unit test và 108 lượt chính thức, protocol khóa trước validation/test mới. Guarded/mapped đạt 10/10 ca khả thi mỗi split; reactive 8/10 với hai U collision.

Đây là kết quả mô phỏng lý tưởng, điều hướng ngang trong tập hữu hạn; chưa ANN/RL, chưa giảm dữ liệu hoặc bảo đảm an toàn/riêng tư. V2 dùng thêm bộ nhớ/CPU. [Nghiệm thu laptop](docs/research/2026-10-27-local-acceptance-complete.md) đã hoàn tất 9/9 mục nhánh L: đủ điều khiển manual gồm T/G, mapped success và phiếu quan sát khớp dữ liệu tại source 39c34af. CPU max vẫn vượt tick 16 ms; chưa chứng minh deadline realtime phần cứng.

V1 được giữ để tái lập: [môi trường](docs/research/2026-10-25-webots-v1-smoke.md), [baseline](docs/research/2026-10-26-navigation-v1.md), [seeded suite](docs/research/2026-10-26-seeded-environments.md). Test v1 và v2 đều đã exposed; thay thuật toán cần protocol/test mới.

Mốc 6 giữ nguyên [thiết kế nghiên cứu v3](docs/protocols/range-cadence-v3.md). [Mốc 7A](docs/research/2026-10-28-cadence-v3-development.md) triển khai và khóa runtime; local và CI mỗi nơi có 240 lượt development. Acquisition 32/64 ms thực cho payload rate 3000/1500 B/s; sau collapse reference đạt 45/50 case và candidate 46/50, chưa đạt 95%.

[Validation v3](docs/research/2026-10-28-cadence-v3-validation.md) đã hoàn tất đúng một lần với 480 lượt trên CI và hậu kiểm local khớp raw evidence: cả hai arm đạt **87/100 case khả thi**, dưới 95%, không collision/bounds. Rate range giảm 50%, nhưng giả thuyết kết hợp **không đạt**. Theo protocol, v3 dừng tại validation; test giữ chưa mở và CLI từ chối chạy test.

Validation v3 đã exposed, chưa ML; thay thuật toán/cảm biến cần version và đánh giá mới. Không suy ra tiết kiệm điện, riêng tư hoặc an toàn phần cứng. [Hướng dẫn runtime](docs/runtime-v3.md).

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

Nghiệm thu desktop bằng một lệnh: `python3 tools/local_session.py accept`. Công cụ chạy manual → phiếu → mapped → phiếu tuần tự, chặn chạy chồng và ghi phần thiếu. [Hướng dẫn](docs/local-acceptance.md), [82 test và CI collector](docs/research/2026-10-26-sequential-acceptance.md).

## Bản đồ tài liệu

- [Checklist tổng thể từ ý tưởng đến roadmap tương lai](CHECKLIST_DU_AN.md)
- [Checklist mục tiêu phát sinh trong quá trình hiện thực hóa](CHECKLIST_MUC_TIEU_NGHIEN_CUU.md)
- [Kế hoạch chi tiết mốc 6](docs/plans/0010-research-protocol-v3.md)
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

V3 đã dừng đúng protocol ở kết quả validation không đạt; giữ nguyên source, locks, raw evidence và test chưa mở. Bước phát triển thuật toán/cảm biến tiếp theo cần protocol/version và đánh giá mới; không tune bằng validation đã exposed. Ưu tiên khảo sát giảm dữ liệu trên baseline; ML là nhánh riêng khi có câu hỏi phù hợp. Sau core phương tiện mới mở rộng một chuyến giao hàng và điều phối logistics.

Các preset nghiên cứu level_b vẫn mang `status = "draft"`, `runtime_ready = false`. [lab_v1.toml](configs/lab_v1.toml) là preset kỹ thuật riêng cho môi trường và kiểm tra simulator, không phải cấu hình nghiên cứu đã hoàn thiện.
