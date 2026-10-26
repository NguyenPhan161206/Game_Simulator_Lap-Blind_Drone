# Sửa launcher và làm rõ lượt manual thiếu T/G

Ngày 2026-10-27. Đầu vào: batch local-acceptance-20261026T224307533989Z tại c012ab8. Không thay runtime/controller/world hoặc hai protocol đã khóa.

1. Đối chiếu raw telemetry, phiếu, source và console: W/S/A/D/Q/E có command, một bước nhảy phù hợp reset, T/G chưa có up command. Giữ cảnh báo T/G; không tự coi phiếu yes là dữ liệu đầy đủ.
2. Đối chiếu nguồn Webots R2025a: cảnh báo launcher do WEBOTS_TMPDIR trống/không tồn tại. Khôi phục môi trường tương đương launcher: temp base /tmp ngắn cho Unix socket, giữ đường thư viện gốc; tạo thư mục trước chạy.
3. Gộp thông báo review lặp; batch chưa khởi chạy mapped được ghi not_started thay vì lỗi thiếu file. Không thay điều kiện nghiệm thu phím.
4. Chạy make check và lock checks; CI phải chạy mapped/manual thật và xác nhận cảnh báo launcher không còn trong hai console. Commit/push feature sau kiểm tra local, tích hợp khi CI đạt.
5. Bổ sung audit và checklist: LOC-09 ghi nhận hiệu năng/phiếu phản hồi với giới hạn; LOC-05/06 còn mở. Ghi rõ nguồn và từng lượt nếu người dùng thử bổ sung T/G hoặc chạy mapped riêng; không sao chép phiếu giữa các lượt.

Source cơ sở c012ab8; preflight 82 test đạt. Lần probe display của phiên sửa lỗi trả exit 1; không coi đây là lượt thao tác GUI. Sau sửa, 82 test local đạt; kết quả CI sẽ được ghi tại mốc bàn giao.
