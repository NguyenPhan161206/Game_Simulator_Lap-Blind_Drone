# Kết nối cây phiên bản, kiểm thử và tích hợp GitHub

Ngày: 2026-10-26. Yêu cầu: lập kế hoạch, thực hiện từng giai đoạn có test/thử nghiệm và commit/push. Phạm vi đang thực hiện: đồng bộ GitHub, kiểm chứng công cụ nhánh L và tích hợp bản đủ điều kiện; không tự biến roadmap nghiên cứu tương lai thành kết quả đã làm.

## Giai đoạn 1 — kiểm kê và checkpoint kế hoạch

- [x] GH-01 — Đọc quy tắc, kiểm tra worktree và lịch sử; không có thay đổi người dùng trước khi bắt đầu.
- [x] GH-02 — Xác nhận origin SSH đúng repo; connector đọc được branch và CI. SSH managed lỗi quyền của cấu hình hệ thống, không sửa quyền hoặc remote để né lỗi.
- [x] GH-03 — Đối chiếu main, feature và ancestry. Hai remote feature cũ đang dừng ở source kiểm thử, trong khi local có thêm commit tài liệu đã nằm trong main.
- [x] GH-04 — Đọc bằng chứng desktop mới: mapped có result/ảnh; manual có phiếu nhưng telemetry cần đối chiếu. Không ghi đè lượt hay phiếu cũ.
- [x] GH-05 — Scaffold/link check và diff review đạt; kế hoạch đã push ở 1bec854a924128ef004d5c98823ab04765a8e8cf trên feat/local-acceptance.

## Giai đoạn 2 — kiểm chứng công cụ và xử lý bằng chứng

- [x] GH-06 — Đã thêm CI riêng cho helper: unit/core checks, mapped dưới Xvfb và manual timeout/telemetry, lưu artifact. Kết quả chạy chờ gate GH-09; không gọi đây là GUI laptop hoặc nhấn phím thật.
- [x] GH-07 — Review chặn provenance sai, result thiếu, tiến trình lỗi và chênh outcome; đã bổ sung xử lý result malformed và cảnh báo phiếu manual không khớp sampled command. make check đạt 75 test; không sửa raw evidence/phiếu.
- [x] GH-08 — Đã kiểm tra telemetry/82 sample trajectory/ảnh laptop và ghi audit riêng; báo delta/trạng thái đầu/CPU, không tự suy nguyên nhân.
- [x] GH-09 — make check đạt 75 test; source b324105 đã push, CI collector 40284088405/job 121443592619 success; đã đọc log và artifact 12633900122. Mapped success và manual telemetry/timeout đạt, không có giả lập phím.

## Giai đoạn 3 — cây phiên bản và tích hợp

- [x] GH-10 — Có cây phiên bản và bảng source kiểm chứng/tài liệu/nhánh; remote seeded/v2 đã fast-forward lên 2568f07/d7018cb sau kiểm tra ancestry. Không xóa nhánh hoặc viết lại lịch sử.
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
