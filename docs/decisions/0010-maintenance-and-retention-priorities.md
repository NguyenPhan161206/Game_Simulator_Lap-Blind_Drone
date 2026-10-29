# ADR 0010 — Củng cố trạng thái và ưu tiên chẩn đoán retention

Ngày: 2026-10-29. Chấp nhận trong phạm vi người dùng yêu cầu “Tiến hành” đợt củng cố sau audit checklist. Đây là quyết định bảo trì/workflow; không thay kiến trúc hoặc protocol nghiên cứu đã khóa.

## Quyết định được thực hiện

- Khôi phục đúng byte cấu hình v2 khi khác biệt duy nhất là newline cuối. Giữ nguyên bốn khóa và toàn runtime v1/v2/v3/v4/DATA-03/04.
- Scaffold kiểm source và README của thư mục output, không diễn giải bản xuất hội thoại hoặc nội dung sinh trong artifacts/data/models là tài liệu source. Vẫn kiểm source mới chưa tracked; không xóa file có sẵn.
- Đồng bộ trạng thái sau DATA-04; tách hoàn tất phép thử với đạt chất lượng, đóng v3 bằng kết quả âm và ghi phần test không đủ điều kiện thực hiện.
- Phân tích offline log development hiện có và soạn kế hoạch tiếp. Bằng chứng ở [báo cáo 0017](../research/2026-10-29-retention-failure-audit.md); không chạy simulator hoặc mở evaluation mới.

## Lý do và tác động tới roadmap

Checklist/hướng dẫn cũ dừng ở các mốc khác nhau, trong khi DATA-04 đã có bằng chứng. Checkout còn lỗi byte config và link trong các bản export; chúng không phải lý do tái sinh lock hoặc thay kết quả nghiên cứu cũ.

Log cho thấy timeout retention vẫn di chuyển và cùng occupied-only đổi outcome theo case/repeat/slot giữa run. Vì vậy [dự thảo 0018](../plans/0018-retention-study-proposal.md) đề xuất ưu tiên đối chứng v4 full-history, kiểm soát khởi tạo/order, rồi mới thêm biến acquisition DATA-06/09. Chưa xác định nguyên nhân duy nhất, candidate hoặc TTL tối ưu.

## Ranh giới chưa được chấp nhận để thực thi

0018 là đề xuất cần chốt câu hỏi, tolerance khởi tạo, candidate, budget/ngưỡng, thống kê, source lock và fresh evaluation. Không tự chuyển đề xuất thành triển khai, ML, radar, hardware, validation/test hoặc quyền chạy lại thí nghiệm lịch sử. Không nới ngưỡng v3, sửa nguồn frozen, tái gọi exposed cases là unseen hoặc tích hợp main trong đợt bảo trì này.
