# Nghiệm thu local tuần tự và phiếu rõ nghĩa

Ngày 2026-10-26. Tiếp tục LOC-05/06/09 sau audit ở source 534b83a. Phiên agent không có surface desktop; hai lượt manual/mapped trước đây chạy chồng thời gian, phiếu manual all-yes không khớp telemetry và ghi chú chỉ là “y”. Cải thiện quy trình thu bằng chứng, giữ nguyên runtime/protocol đã khóa.

1. Khóa độc quyền các lượt do local_session.py khởi chạy trong workspace. Khóa phải được OS giải phóng khi tiến trình kết thúc; file khóa tồn tại không có nghĩa là đang bận. Không thay quyền display hoặc kiểm soát ứng dụng mở ngoài launcher.
2. Thêm lệnh accept chạy manual → phiếu/kiểm tra → mapped → phiếu/kiểm tra. Chỉ chuyển bước khi bằng chứng bước trước đủ; luôn lưu các lượt lỗi. Một thư mục cha giữ cả hai lượt và bản tổng hợp.
3. Phiếu hỏi riêng độ mượt và việc pause/đổi speed; lựa chọn “chưa quan sát” luôn được giữ. Không tự điền yes, không ghi đè phiếu cũ. Manual yêu cầu thử đủ phím và reset sau khi đã di chuyển; thiếu/mâu thuẫn với telemetry phải được báo cụ thể.
4. Thêm audit-batch để tổng hợp lại từ raw files. Không tự đánh dấu checklist dự án; “đủ bằng chứng để review” dựa cả telemetry và lời xác nhận, không là chứng nhận an toàn hoặc đo input latency.
5. Unit test cho khóa/chạy chồng, giải phóng khóa sau lỗi, thiếu phiếu, command mâu thuẫn, dirty/source khác, pause và outcome fail. Fixture unit không giả là thao tác GUI.
6. Chạy make check, kiểm tra locks/diff rồi commit/push feature. CI chạy Webots thật cho collector và kiểm tra khóa trong lúc manual đang chạy; giữ separate gate bàn phím/laptop.
7. Chỉ tích hợp khi check phù hợp đạt; cập nhật hướng dẫn một lệnh, source/evidence/checklist. LOC-05/06/09 giữ mở cho tới khi người dùng thực hiện lượt có bằng chứng nhất quán.

Trạng thái ban đầu: đã xác nhận repo sạch tại main 955378e và đồng bộ feat/local-acceptance bằng fast-forward. Chưa có operator record mới so với audit trước.

## Tiến độ triển khai

- Đã thêm khóa OS, accept tuần tự, audit-batch và lựa chọn độ phản hồi/pause rõ nghĩa; phiếu được tạo độc quyền để bảo toàn bản có sẵn.
- make check đạt 82 test, gồm fixture gate và kiểm tra khóa giữa hai process; hai protocol vẫn hợp lệ. Test fixture không phải thao tác GUI.
- CI 40290684935 tại source ea13295 đã success: mapped tới đích; manual có telemetry/timeout; launcher thứ hai bị khóa từ chối trước khi tạo output. Artifact 12636202161; xem [báo cáo và JSON evidence](../research/2026-10-26-sequential-acceptance.md).
- LOC-05/06/09 vẫn mở cho đến khi có dữ liệu người thao tác tương ứng.
