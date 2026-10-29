# 0017 — Củng cố kiểm tra, trạng thái và chẩn đoán retention

Ngày: 2026-10-29. Phạm vi được người dùng cho phép bằng “Tiến hành” sau đợt rà soát checklist. Đây là bảo trì tooling/tài liệu và phân tích offline trên development đã exposed; không triển khai navigation, thay protocol hoặc chạy simulator mới.

## Các bước và bằng chứng cần có

1. Kiểm tra Git/diff và flock local collector. Lưu hash bốn khóa; phục hồi đúng byte `configs/navigation_v2.toml` sau khi xác nhận khác biệt duy nhất là ký tự xuống dòng cuối. Không tái sinh khóa hoặc sửa thông số.
2. Giới hạn scaffold checker vào source: bỏ phần sinh trong artifacts/data/models, vẫn kiểm README của ba thư mục; bỏ đúng mẫu export hội thoại `codex-session-*.md` tại root. Vẫn kiểm tài liệu/source mới chưa tracked và thư mục tên tương tự bên trong docs. Thêm kiểm thử để bảo đảm lỗi source thật tiếp tục bị phát hiện. Không xóa hoặc sửa bản export có sẵn.
3. Đối chiếu outcome trên manifest/log sẵn có của v4, DATA-03/04; xác minh hash file được dùng, tập case, repeat và source. Phân tích các ca khả thi candidate không success cả hai repeat, tách khỏi negative controls. Không gọi so sánh khác run/host là ablation nhân quả hoặc số đo CPU công bằng; không suy cơ chế chỉ từ timeout.
4. Cập nhật trạng thái mới nhất trong README, hai checklist, hướng dẫn agent/development và các kế hoạch còn dễ hiểu nhầm. Giữ nguyên nội dung báo cáo lịch sử, frozen locks và exposure. Phân biệt hoàn tất phép thử với đạt chất lượng; ghi mục test v3 không thực hiện do gate fail.
5. Viết [kế hoạch nghiên cứu retention tiếp theo](0018-retention-study-proposal.md) với v4 đầy đủ bộ nhớ làm đối chứng trực tiếp. Đây là đề xuất để xem xét, chưa là protocol chốt ngưỡng, triển khai hoặc quyền chạy evaluation.
6. Chạy `make check`, kiểm diff/hash/inventory; commit/push feature branch và đọc CI scaffold. Không chạy lại Webots, không dispatch validation/test, không tích hợp main trong đợt này.

## Điều kiện bàn giao

Kiểm tra source đạt; các byte khóa và runtime inventory không đổi; có báo cáo offline và kế hoạch tiếp đủ cụ thể, có nguồn/giới hạn. Nghiên cứu mới vẫn cần quyết định/protocol/source lock và fresh validation/test riêng. Kết quả âm v3 và việc test v3 giữ đóng không thay đổi.

## Bàn giao local

[Báo cáo/JSON](../research/2026-10-29-retention-failure-audit.md): chín case hợp, 72 episode sẵn có, 234 file dùng được xác minh hash; timeout retention vẫn có chuyển động và có khác biệt theo slot/khởi tạo cần kiểm soát. `make check` đạt 181 tests; inventory v3/v4/DATA-03/DATA-04 giữ nguyên lần lượt 44/61/77/78 file, bốn khóa nguyên byte. Đã soạn dự thảo 0018; không chạy simulator/held-out mới. Commit/push và CI được xác minh tại bàn giao Git, tách khỏi source runtime lịch sử.
