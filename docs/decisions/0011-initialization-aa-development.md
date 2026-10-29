# ADR 0011 — Đối chứng khởi tạo v4 với chính nó

Ngày: 2026-10-29. Chấp nhận triển khai development theo yêu cầu mới của người dùng tiếp tục tiến trình. Thiết kế trước outcome ở [plan 0019](../plans/0019-initialization-aa-development.md); mở bước B của [0018](../plans/0018-retention-study-proposal.md), chưa chốt candidate retention hoặc mở held-out.

## Vấn đề và quyết định

Audit 0017 ghi timeout retention vẫn di chuyển và cùng occupied-only đổi outcome giữa run/slot; chưa biết tác động của initial/reset state. Thay vì thêm acquisition/retention ngay, dùng cùng ObservedDetourNavigator v4 full-history ở cả hai nhãn reference/candidate. So hai điều kiện: hai episode chung process như trước và mỗi episode một Webots process mới. World giữ randomSeed 11, physics/sensor/control và evaluator như v4.

12 case gồm chín case audit, empty `development-empty-s3200020`, offset `development-v4-empty_offset-06` và negative `development-blocked_goal-s3200051`; tất cả development đã exposed. Hai repeat đảo arm order, 96 episode. Khóa spec/index/inventory mới ở source implementation trước simulator; giữ nguyên bốn khóa và runtime cũ. Không dùng API Supervisor trong robot; supervisor chỉ bố trí, scoring và ghi khởi tạo.

Cold gate: đủ 48 cold episode; cùng case có cùng counts/flags/status/outcome, initial + public observation + command/target + scored physics khớp tolerance plan 0019. Bốn cold episode cùng case so với baseline đầu tiên; không lựa episode tốt nhất. Không collision/bounds/negative false success trong toàn bộ 96 episode. Báo task outcomes nhưng chưa đặt 95% hoặc generalization gate cho A/A. Warm differences được giữ như kết quả chẩn đoán.

Gate fail đóng kết luận preflight chưa đạt, không tiến sang retention, không sửa thresholds để cứu kết quả. Gate đạt chỉ cho phép hoàn thiện protocol retention, không chứng minh mức giảm dữ liệu hay hardware. Tolerance 1e-6/1e-9 là precision gate đã định trước cho cùng mô hình trên một host; nếu không đạt cần giải thích và version mới, không khẳng định simulator có bảo đảm tất định tuyệt đối.

## Giới hạn

Cold isolation là intervention trên khởi tạo/orchestration, không phải cải tiến navigation. Nó không xác định riêng yếu tố nào trong motor/device/controller/physics gây khác biệt warm; log các trạng thái để phân tích. Không đổi cảm biến, thêm ground truth vào policy, train, radar, hardware hoặc chạy v3 test. Các số case/repeat không là mẫu held-out hay độc lập thống kê mới.

## Bàn giao 2026-10-30

[Source `97be9a0`, CI 40911479243 và local raw review](../research/2026-10-30-initialization-aa.md) hoàn tất 96 episode; 36/36 cold comparisons và cả năm gate đạt. Không thay tolerance/quality sau outcome. Warm khác initial/time/path nhưng outcome không đổi; bootstrap motor targets khác nhau được ghi. Gate chỉ mở việc đăng ký protocol retention tiếp, không tự chứng nhận giảm dữ liệu hoặc mở held-out.
