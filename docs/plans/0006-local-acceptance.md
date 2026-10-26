# Nhánh L — nghiệm thu chạy và thao tác local

Ngày lập: 2026-10-26. Phạm vi: LOC-04 đến LOC-09 trong [checklist](../../CHECKLIST_DU_AN.md). Không thay thuật toán, world hoặc protocol v1/v2 đã khóa.

1. Kiểm tra khả năng truy cập desktop, Webots và dependency. Không lấy DISPLAY được khai báo làm bằng chứng đã kết nối; không thay quyền truy cập display.
2. Thêm launcher độc lập lưu provenance, console và thời gian thực. Manual dùng minimal_lab/drone_controller/lab_supervisor; mapped dùng observed_v2/drone_v2/lab_v2, development-u_trap-s21001, realtime, rendering bật.
3. Thu manual telemetry và xác nhận riêng của người thao tác cho từng phím, thả phím, SPACE, R. Không suy việc đã nhấn R từ mapping test hoặc bước nhảy vị trí.
4. Thu mapped result, telemetry, trajectory và ảnh observer nếu Webots xuất được. Giữ lỗi khởi động/timeout, không biến chúng thành lượt đạt.
5. Kiểm tra protocol/manifest/geometry/source/checks trước so sánh CI. Báo delta số học; outcome khác cần điều tra, không tự gán nguyên nhân cho GPU hoặc sai số.
6. Đo wall time của cả tiến trình và ghi CPU policy từ result; hỏi người quan sát về giật/độ phản hồi/pause. Không suy FPS hoặc deadline phần cứng từ tốc độ mô phỏng.
7. Kiểm tra helper bằng unit test có trường hợp sai provenance, result thiếu và outcome lệch; chạy toàn bộ check hiện có, xác nhận hai lock giữ nguyên. Unit test không phải nghiệm thu GUI.
8. Chỉ cập nhật LOC-04…09 khi có lượt desktop thật và bằng chứng tương ứng. Commit/push công cụ đã kiểm tra ở mốc riêng; nếu desktop chưa truy cập được, bàn giao lệnh thực hiện và giữ gate local mở.

Trạng thái ban đầu: công cụ computer-use báo không có app/browser; phiên trước Webots không kết nối display :0. Cần người dùng mở từ terminal desktop để thực hiện quan sát và bàn phím thật. Công cụ mới không tự đánh dấu checklist dự án.

## Tiến độ chuẩn bị

- Đã thêm tools/local_session.py và hướng dẫn nghiệm thu; không thay file khóa.
- make check đạt, gồm 73 unit test (9 kiểm tra mới cho bằng chứng/environment). CLI help hoạt động; ldd với bundled library path không còn dòng not found trong lần kiểm tra này.
- Chưa thực hiện được bước tương tác desktop 3–6 trong phiên managed. Đã yêu cầu người dùng chạy manual/mapped từ terminal desktop và trả đường dẫn Session. LOC-04…09 giữ mở cho đến khi đọc bằng chứng thật.
- Công cụ được bàn giao trên nhánh riêng feat/local-acceptance; kiểm tra helper không thay cho nghiệm thu local.

## Cập nhật sau khi người dùng chạy desktop

[Audit lượt mới](../research/2026-10-26-local-acceptance.md) đã đóng LOC-04/07/08. LOC-05 còn mâu thuẫn giữa phiếu và command; LOC-06 thiếu xác nhận đã xem chuyển động/kết thúc; LOC-09 thiếu mô tả độ phản hồi. [Kế hoạch tích hợp GitHub](0007-github-integration.md) đã thêm collector CI thực tại source b324105, 75 test và Webots mapped/manual-timeout đều đạt; không dùng CI để đóng ba gate desktop còn lại.
