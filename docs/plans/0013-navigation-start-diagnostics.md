# 0013 — Chẩn đoán đoạn đường đầu bị từ chối

Ngày: 2026-10-28. Phạm vi được người dùng yêu cầu: lập kế hoạch chi tiết rồi thực thi bước chẩn đoán đã đề xuất. Đây là công cụ phân tích offline trên development, chưa triển khai thuật toán v4.

## Điểm xuất phát và đích bàn giao

V3 đã đóng bằng validation âm: 87/100 case mỗi arm, dưới ngưỡng 95%; test không đủ điều kiện chạy. [Replay trước](../research/2026-10-28-v3-public-replay.json) có năm trace reference development: có path nhưng lệnh ngang luôn 0. Chưa biết chính xác ô/điều kiện từ chối. Không dùng validation để chọn bản sửa.

Đích của bước này: tái hiện quyết định từ quan sát công khai, chỉ ra ô đầu tiên vi phạm free-check, giải thích vai trò sensor origin/chia ô/pose; cung cấp lệnh tái lập, kiểm thử, báo cáo và đề xuất sửa có giới hạn bằng chứng.

## Các bước và tiêu chí hoàn thành

1. **Kiểm tra checkout và nguồn dữ liệu.** Kiểm tra Git sạch, local acceptance không giữ lock; ghi source, hash raw result, inventory và bốn lock v1/v2/v3. Dùng bộ hậu kiểm v3 hiện có xác minh toàn bộ development trước phân tích. Không sửa hoặc tạo lại lock.
2. **Khoanh mẫu rõ ràng.** Chọn đúng năm trace đã có trong replay trước (ba empty, hai narrow_gap). Đồng thời báo số reference timeout trong toàn development và số trace được phân tích, tránh hiểu năm trace là toàn bộ failure. Chỉ reference 32 ms có đủ pose 32 ms trong acquisition log để replay; candidate 64 ms thiếu pose trung gian nên không nội suy.
3. **Lập công cụ độc lập trong tools/.** Nạp mission bằng whitelist goal/policy; navigation chỉ nhận pose/range/timestamp đã ghi. Phát lại theo thứ tự decisions. Bọc lời gọi segment_ok bằng phép giải thích cùng quy tắc lấy mẫu, trả lại chính kết quả gốc; không đổi grid, lệnh hay target. Đối chiếu mọi counter điều hướng tất định với episode gốc, bỏ riêng số đo CPU vì máy phát lại khác.
4. **Ghi bằng chứng từ chối.** Với từng lời gọi: vị trí đầu/cuối, chỉ số mẫu đầu vi phạm, tọa độ/ô, unknown/blocked/outside, free-check khi không yêu cầu free, khoảng cách tới pose. Tổng hợp theo quyết định, thời điểm, cell; giữ ví dụ đầu/cuối và phân bố lý do. Phân biệt invalid/stale, không có path và vượt lookahead với segment rejection. Ghi acquisition/current pose và tuổi mẫu để tránh quy lỗi timestamp khi chưa có bằng chứng.
5. **Kiểm tra hình học và độ nhạy biểu diễn.** Đối chiếu ô bị từ chối với bán kính origin 0.33 m và grid 0.25 m; kiểm tra cell có được center-retain/ray chạm hay không. Chạy sweep tổng hợp các offset trong một cell với tia lý tưởng quay đủ vòng; thay riêng origin trong phép thử biểu diễn để phân biệt lỗ coverage với vật cản/độ mới dữ liệu. Đây không phải episode vật lý hoặc bản sửa được chấp nhận; không suy vùng chưa đo là an toàn.
6. **Kiểm thử và kiểm tra toàn dự án.** Test reason precedence, free/blocked/outside, ranh giới cell, hàm giải thích khớp frozen predicate và không sửa grid; từ chối thiếu pose/cadence sai và dữ liệu ngoài development. Chạy make check. Không thay runtime/navigation/lab nên không cần mở Webots mới; replay không chứng minh bản sửa bay thành công.
7. **Bàn giao.** Lưu raw diagnostic trong artifacts ignored; lưu JSON bằng chứng nhỏ và báo cáo ở docs/research. Cập nhật GOAL-22 theo phần thực sự giải thích được, checklist dự án và hướng dẫn công cụ. Kiểm tra diff/locks, commit và push nhánh theo standing authorization; báo trạng thái CI. Chỉ chuyển main nếu đủ điều kiện của repo.

## Điều kiện giữ nguyên

- Không đọc obstacle/witness vào navigator; không mở test hoặc chạy lại validation v3.
- Không sửa src/, config, runtime inventory, simulator world hoặc exposed protocol.
- Không giảm margin, bỏ require_free, tô free vùng chưa đo, tăng timeout hoặc hạ ngưỡng để tạo pass.
- Bản sửa điều hướng tiếp theo cần version riêng, giả định an toàn rõ và development trước protocol/evaluation mới. Chẩn đoán năm trace không giải thích mặc nhiên toàn bộ 13 case validation thất bại.

Kết quả thực thi sẽ được liên kết từ checklist sau khi có bằng chứng; kế hoạch này tự nó chưa chứng minh nguyên nhân hay cải thiện chất lượng.
