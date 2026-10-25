# ADR 0001 — Nền tảng và ranh giới ban đầu

Ngày: 2026-10-25.

## Đã chấp nhận qua trao đổi
- Mức B là nhiệm vụ khởi đầu: một drone đến đích và tránh vật cản tĩnh.
- Runtime không vision; camera có thể hỗ trợ huấn luyện ở nhánh thử nghiệm riêng.
- Ưu tiên core phương tiện, sau đó một chuyến giao hàng và logistics.
- Phạm vi hiện tại là mô phỏng.
- Khảo sát Webots trước sau khi so sánh các nền mã nguồn mở.
- Tạo cấu trúc theo kiến trúc hệ thống và cấu hình agent, rồi commit/push lên repo được chỉ định.

## Lựa chọn tổ chức cho scaffold
- Python core và Webots adapter riêng; chưa thêm dependency simulator/ML.
- Root AGENTS.md là nguồn hướng dẫn agent chung.
- TOML cho cấu hình; preset thiếu quyết định vẫn mang status=draft, runtime_ready=false.
- Cấu hình Codex di động và launcher vì .codex có thể bị môi trường managed bảo vệ.
- Bộ kiểm tra scaffold chạy bằng Python 3.11+ và thư viện chuẩn.
- Không sao chép asset ngoài hoặc tự chọn license cho mã gốc của chủ dự án.

## Còn mở
Phiên bản Webots, world cụ thể, robot model, độ chi tiết động lực học, loại cảm biến, frame, thông số số học, điều kiện dừng, ngưỡng chất lượng và thuật toán.

Kiến trúc này không khẳng định nhiệm vụ, cảm biến hoặc controller đã chạy. Khi chốt hoặc thay đổi giả định nghiên cứu, thêm ADR mới và cập nhật preset tương ứng.
