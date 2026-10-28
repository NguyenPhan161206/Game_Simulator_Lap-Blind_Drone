# ADR 0007 — V4: đường thực thi qua vùng đã quan sát

Ngày: 2026-10-28. Chấp nhận trong phạm vi người dùng yêu cầu thực thi GOAL-23. Không mở ML/radar hoặc held-out evaluation.

## Vấn đề và lựa chọn

[Chẩn đoán 0013](../research/2026-10-28-navigation-start-diagnostics.md) chứng minh năm case development reference kẹt vì waypoint đầu xuyên ô unknown nằm trong vòng sensor origin. Quay tiếp không cập nhật được ô. Không có cơ sở tô ô này free.

Triển khai package `versions/navigation_v4/blind_drone_v4/` với namespace riêng. Package chỉ nhập các interface/thuật toán shared đã khóa từ `src/blind_drone`; không sửa hoặc thêm file vào src/. World/PROTO và controller v4 có tên riêng. Inventory v4 gồm inventory v3 hiện có cộng package/entrypoints/config/world v4; không thay inventory hoặc khóa v3. Cho phép cả hai runtime cùng được kiểm tra trong một checkout.

V4 giữ nguyên acquisition-pose projection, cadence range/pose 32 ms, control 16 ms, speed, scan, sensor origins, inflation/margins và evaluator. Cách dựng free/occupied không đổi. Khi đường optimistic hiện tại không có đoạn thực thi, tìm nhánh trong connected component của **free, inside, unblocked**; không cắt góc qua unknown. Kết nối từ pose thực đo, không dịch pose về tâm cell một cách ngầm định. Nếu không tới được goal thì chọn điểm tiến triển gần goal nhất trong component, nếu thực sự gần hơn vị trí hiện tại. Không có đường phù hợp thì dừng/quét.

Mọi target của v4 cần đoạn supercover free (kể cả cell chạm corner ở giữa đoạn hoặc dọc biên) và clearance giải tích với occupied-cell centers, ngưỡng hull + margin + half-cell diagonal hiện hành. Recovery ra khỏi vùng inflation giữ yêu cầu free và measured swept clearance; không dùng world geometry. Lệnh vẫn qua velocity guard. Đây chỉ là kiểm tra hình học với phép đo lý tưởng, chưa chứng nhận an toàn vật lý.

Giữ adapter v3 nguyên vẹn; adapter v4 dẫn xuất có provenance rõ, chọn policy từ nhãn reference/candidate công khai và ghi command/status/target từng tick. Supervisor/evaluator mới chỉ chạy development; obstacle/witness chỉ vào world/evaluation. Không truyền case/arm/world state vào navigator. Cadence hai arm đều 32 ms; reference dùng CadenceNavigator đã khóa, candidate dùng v4.

## Kiểm chứng và giới hạn

[Kế hoạch 0014](../plans/0014-observed-detour-v4.md) định nghĩa unit/replay/simulator development và các ca đối chứng trước chạy. Bộ phát triển có thể dùng để tìm/sửa lỗi và giữ mọi attempt; không gọi nó là validation mới. CLI v4 từ chối validation/test. Source/config/fixture hashes ghi trước simulator; source thay đổi trong collector phải làm run không hoàn tất.

Không đưa sensor origin về 0, bỏ require_free hoặc nới ngưỡng chấm điểm. Không sửa v3 validation âm, không chạy test v3. Sau development, câu hỏi/protocol/split và runtime lock mới là công việc riêng trước đánh giá held-out.

## Sửa biểu diễn endpoint trong development

Bản đầu `2cf9238` yêu cầu cả cell chỉ tiếp xúc đúng ở t=0/1. Snapshot tổng hợp start `(-4.875,0,1.5)` chứng minh điều này có thể chặn mọi kết nối dù có lối đi vào phía free, vì cell bên kia đường biên không được center-retain. Revision `v2_endpoints` giữ ô floor của hai endpoint, mọi cell có tiếp xúc với phần giữa đoạn và các corner nội bộ; loại riêng ô khác chỉ chạm ở t=0 hoặc t=1. Đoạn chạy dọc đường biên vẫn yêu cầu cả hai phía free. Không đánh dấu cell mới free hoặc cho đi qua unknown. Đây là sửa representation trong development chưa đóng băng, không tune bằng validation. Giữ source/snapshot/lượt CI bản đầu làm lịch sử, chạy kiểm chứng source mới riêng.
