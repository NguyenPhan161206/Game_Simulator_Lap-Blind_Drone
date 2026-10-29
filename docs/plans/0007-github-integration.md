# Kết nối cây phiên bản, kiểm thử và tích hợp GitHub

**Trạng thái hiện tại:** Hoàn tất tích hợp lịch sử; các gate desktop còn mở trong ghi chép dưới đã được đóng ở mốc local sau đó. [Bằng chứng](../research/2026-10-27-local-acceptance-complete.md). Các bước và giới hạn lúc thực thi bên dưới là lịch sử, không là việc đang chờ chạy lại.

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
- [x] GH-11 — Đọc mới remote main tại 1df11fd, ancestry cho phép fast-forward; helper b324105 đã qua CI thật, evidence/docs qua scaffold và kiểm tra hash. Sửa whitespace ở checklist trước tích hợp. Nếu server yêu cầu PR thì dùng PR, không bypass.
- [x] GH-12 — Đã fast-forward main từ 1df11fd lên 63298d7, khớp tree/commit local/remote; giữ LOC-05/06/09 mở.
- [x] GH-13 — Cả bốn workflow main tại 63298d7 đã success: 75 unit test, 12 smoke checks, 8 diagnostic, 48 seeded v1, 108 v2 và collector. Hai protocol giữ nguyên, có evidence đúng source; đây là regression trên tập exposed.
- [x] GH-14 — Tài liệu/checklist và evidence đã được kiểm tra scaffold/link/diff/hash; commit/push bàn giao là mốc chứa checklist này. Chỉ thêm source/docs/evidence nhỏ, không đưa raw logs/downloads/credential vào Git; kiểm tra refs/worktree sau push.

[Báo cáo bàn giao và CI evidence](../research/2026-10-26-github-integration.md) ghi source kiểm chứng, các workflow/artifact và phạm vi chưa hoàn thành. GH-01…14 hoàn tất không đồng nghĩa toàn bộ checklist nghiên cứu hoặc ba LOC còn lại đã đạt.

## Gate desktop còn độc lập

- LOC-04/07/08 có thể đóng theo log, provenance, ảnh và đối chiếu thực tế sau audit.
- LOC-05: phiếu all-yes của manual 064254 chưa khớp command telemetry toàn 0; cần xác nhận/thử lại, không tự đổi phiếu.
- LOC-06: kết quả mapped đạt nhưng còn thiếu xác nhận đã quan sát chuyển động/kết thúc của đúng lượt.
- LOC-09: đã có wall time và CPU; ghi chú độ phản hồi hiện chỉ là “y”, chưa đủ mô tả, cần người thao tác bổ sung.

Những mục phụ thuộc thao tác/quan sát chưa được cung cấp phải giữ mở. Test CI và đồng bộ GitHub vẫn có thể hoàn thành độc lập. Checklist tổng thể tiếp tục phân biệt việc đã làm, kiểm chứng CI, desktop và đề xuất tương lai.
