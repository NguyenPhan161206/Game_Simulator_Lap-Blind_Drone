# Kết nối cây phiên bản, kiểm thử và tích hợp GitHub

Ngày: 2026-10-26. Yêu cầu: lập kế hoạch, thực hiện từng giai đoạn có test/thử nghiệm và commit/push. Phạm vi đang thực hiện: đồng bộ GitHub, kiểm chứng công cụ nhánh L và tích hợp bản đủ điều kiện; không tự biến roadmap nghiên cứu tương lai thành kết quả đã làm.

## Giai đoạn 1 — kiểm kê và checkpoint kế hoạch

- [x] GH-01 — Đọc quy tắc, kiểm tra worktree và lịch sử; không có thay đổi người dùng trước khi bắt đầu.
- [x] GH-02 — Xác nhận origin SSH đúng repo; connector đọc được branch và CI. SSH managed lỗi quyền của cấu hình hệ thống, không sửa quyền hoặc remote để né lỗi.
- [x] GH-03 — Đối chiếu main, feature và ancestry. Hai remote feature cũ đang dừng ở source kiểm thử, trong khi local có thêm commit tài liệu đã nằm trong main.
- [x] GH-04 — Đọc bằng chứng desktop mới: mapped có result/ảnh; manual có phiếu nhưng telemetry cần đối chiếu. Không ghi đè lượt hay phiếu cũ.
- [ ] GH-05 — Chạy scaffold/link check và diff review, commit/push kế hoạch trên feat/local-acceptance.

## Giai đoạn 2 — kiểm chứng công cụ và xử lý bằng chứng

- [ ] GH-06 — Thêm CI riêng cho helper: unit/core checks và một lượt Webots mapped thật dưới Xvfb, realtime/rendering bật; lưu artifact. Không gọi đây là GUI laptop hoặc nhấn phím thật.
- [ ] GH-07 — Kiểm tra review chặn provenance sai, result thiếu, tiến trình lỗi và chênh outcome; bổ sung kiểm tra việc đọc evidence/ghi file nếu phát hiện thiếu.
- [ ] GH-08 — Kiểm tra telemetry/trajectory/ảnh của lượt laptop; báo delta, trạng thái ban đầu và CPU, không tự suy nguyên nhân do GPU hoặc sai số số học.
- [ ] GH-09 — Chạy make check, review diff, commit/push công cụ/CI, đợi CI kết thúc và đọc log/artifact metadata của đúng SHA. Nếu lỗi thì sửa và kiểm tra lại trước tích hợp.

## Giai đoạn 3 — cây phiên bản và tích hợp

- [ ] GH-10 — Ghi cây phiên bản và bảng source kiểm chứng/tài liệu/nhánh. Chỉ đồng bộ remote feature cũ bằng fast-forward khi ancestry đã xác nhận; không xóa nhánh hoặc viết lại lịch sử.
- [ ] GH-11 — Đọc mới remote main và kiểm tra khả năng fast-forward, các check phù hợp đã đạt. Nếu protection yêu cầu PR thì dùng PR, không bypass.
- [ ] GH-12 — Tích hợp phần công cụ đã kiểm chứng vào main, đồng bộ local/remote bằng tree/commit hash; giữ trạng thái LOC chưa đủ bằng chứng.
- [ ] GH-13 — Kiểm tra CI sau tích hợp và bảo toàn hai protocol; ghi evidence của đúng source, không coi một test đã exposed là unseen.
- [ ] GH-14 — Kiểm tra tài liệu/checklist, commit/push bàn giao, xác nhận không đưa raw logs/downloads/credential vào Git và worktree sạch.

## Gate desktop còn độc lập

- LOC-04/07/08 có thể đóng theo log, provenance, ảnh và đối chiếu thực tế sau audit.
- LOC-05: phiếu all-yes của manual 064254 chưa khớp command telemetry toàn 0; cần xác nhận/thử lại, không tự đổi phiếu.
- LOC-06: kết quả mapped đạt nhưng còn thiếu xác nhận đã quan sát chuyển động/kết thúc của đúng lượt.
- LOC-09: đã có wall time và CPU; ghi chú độ phản hồi hiện chỉ là “y”, chưa đủ mô tả, cần người thao tác bổ sung.

Những mục phụ thuộc thao tác/quan sát chưa được cung cấp phải giữ mở. Test CI và đồng bộ GitHub vẫn có thể hoàn thành độc lập. Checklist tổng thể tiếp tục phân biệt việc đã làm, kiểm chứng CI, desktop và đề xuất tương lai.
