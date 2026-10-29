# 0018 — Đề xuất nghiên cứu retention với đối chứng v4

Ngày: 2026-10-29. **Trạng thái: dự thảo để xem xét.** Người dùng đã cho phép củng cố/phân tích và soạn kế hoạch trong [0017](0017-maintenance-and-retention-audit.md); chưa chốt candidate, ngưỡng hoặc quyền triển khai/chạy nghiên cứu này. Không có runner/config nghiên cứu mới được tạo trong 0017.

## Câu hỏi và lý do ưu tiên

Câu hỏi đề xuất: có thể giảm lịch sử bản đồ được giữ lại mà vẫn duy trì chất lượng điều hướng so với v4 full-history trong cùng miền static/ideal/horizontal hay không?

[Audit development sẵn có](../research/2026-10-29-retention-failure-audit.md) cho thấy v4 đạt 74/74, DATA-03/04 đạt 67/74 trong các run riêng. Timeout retention vẫn có chuyển động đáng kể; cùng occupied-only có case đổi outcome giữa các run và slot thứ hai khác trạng thái khởi tạo. Vì vậy cần tách tác động retention khỏi reference cũ, khởi tạo, order và budget trước thêm adaptive acquisition DATA-06/09. Chưa được kết luận retention là nguyên nhân duy nhất.

## Các giai đoạn và điều kiện chuyển bước

| Bước | Việc cần làm khi kế hoạch được chấp nhận | Điều kiện chuyển bước |
|---|---|---|
| A — thiết kế | Chốt mục tiêu dữ liệu: retained map/history, miền nhiệm vụ, baseline, candidate và các budget/gates bên dưới; ghi ADR/protocol mới | Không còn trường bắt buộc chưa chốt; không hạ ngưỡng để khớp 67/74 đã biết |
| B — kiểm chứng khởi tạo development | So cùng policy với chính nó (A/A), đổi nhãn reference/candidate và thứ tự; ghi epoch, warmup, pose/velocity/yaw, sample đầu và trạng thái điều khiển trước scoring. Xem xét fresh process/cold start cho từng episode thay vì hai arm kế tiếp dùng chung tiến trình | Giải thích được chênh lệch slot/reset; protocol khai báo độ lệch ban đầu cho phép và cách xử lý. Không quy lỗi GUI/GPU/ngẫu nhiên khi chưa có bằng chứng |
| C — ablation development | V4 full-history là đối chứng trực tiếp; so với đúng một candidate retention đã định nghĩa. Giữ planner/guard/sensor/timing/speed/scoring giống nhau và kiểm config/source diff | Đủ paired cases, command replay và mọi failure; kết quả được ghi dù âm. Nếu baseline chưa đủ chất lượng thì dừng phát triển candidate, báo giới hạn |
| D — quyết định readiness | Đóng cấu hình trên development; giữ toàn bộ attempts và exposure; đăng ký fresh validation/test rồi khóa source/runtime | Không chọn cấu hình theo outcome validation; chưa đủ bằng chứng thì chưa mở held-out |
| E — validation | Chạy cấu hình duy nhất đã khóa trên fresh validation theo retry/gate đăng ký | Gate đạt mới đủ điều kiện test; fail thì đóng âm, không rerun tìm pass hoặc tune rồi dùng lại tập đó |
| F — test và bàn giao | Chỉ chạy test mới khi validation đạt; báo paired outcomes, bất định và chi phí | Giữ thất bại, source/locks/ledger/raw hashes; kết luận giới hạn trong miền đã thử |

A/A là kiểm tra cùng phương pháp ở hai nhãn/slot, không phải một thuật toán mới. Phép replay cùng log có thể kiểm tính tất định của policy, nhưng không thay thế kiểm chứng reset/physics của các episode độc lập. Khác biệt ban đầu nằm trong tolerance cũ không làm sai báo cáo cũ; tolerance đó vẫn có thể quá rộng để tách một tác động retention nhỏ.

## Thiết kế ablation cần chốt

- Reference đề xuất: v4 giữ full measured free/occupied history; source package/guard/supercover hiện hành là nguồn tham chiếu, không sửa source đó.
- Candidate chưa chọn: latest-acquisition-only là mốc chẩn đoán đã biết; nếu khảo sát cửa sổ free-history hữu hạn thì phải định nghĩa chính xác thời hạn, timestamp, refresh, packet reuse, cache invalidation và reset. Không gộp thêm occupied TTL, giảm ray hoặc cadence vào cùng phép thử.
- Occupied retention của hai arm phải giống nhau khi khảo sát free-history. Occupied TTL 10 s là một biến khác, để nhánh riêng nếu cần.
- Chuẩn hóa accounting và budget map cho cả hai arm trong version mới: cùng cách đếm free/occupied/blocked và cùng xử lý budget exhaustion. V4 và DATA-03 lịch sử không đếm budget theo cùng cách; không gọi nguyên xi hai budget đó là một control đã bằng nhau.
- Giữ unknown chặn thực thi; expired không thành free. Mọi route/command được audit từ pose/range hợp lệ, không dùng scene, witness, object ID hoặc ảnh.
- World và mỗi episode giữ một nguồn vật lý có thẩm quyền là Webots; logic A/A/khởi tạo không tạo một simulator Python thứ hai.

## Những trường bắt buộc phải đăng ký trước evaluation

| Nhóm | Nội dung chưa chốt |
|---|---|
| Chất lượng | Success tối thiểu của reference/candidate; margin suy giảm; collision/bounds/negative false success; deadline, dwell, path/time penalties |
| Dữ liệu | Metric chính của retained history và mức giảm cần đạt; báo acquisition rate, policy reads và log bytes riêng. Retention không mặc định giảm sensor acquisition |
| Tài nguyên | Mean/percentiles/max CPU và tỷ lệ vượt budget, toàn bộ đường điều khiển so với navigator-only; sampled RSS/controller và map entries/encoding bytes riêng |
| Khởi tạo | Cold-start/reset method, warmup, trạng thái và sensor phase trước scoring, tolerance và gate A/A; quy tắc infrastructure/algorithm failure |
| Dataset | Development/validation/test mới với kiểm chống trùng; trường hợp cùng geometry khác yaw phải có grouping/thống kê phù hợp; exposure ledger |
| Thống kê | Số case theo family, repeats/order; case hoặc nhóm geometry là đơn vị phân tích, không coi tick/ray/repeat độc lập; bất định/margin và adverse bounds phù hợp mục tiêu |
| Vận hành | Một host cho so sánh cost, pinned versions/config/source, retry giới hạn, budget CI/artifact/reviewer, điều kiện dừng và kiểm raw evidence |

Ngưỡng 95% của v3 là lịch sử đã khóa; không tự chuyển thành ngưỡng được chấp nhận cho 0018 và không nới nó để phù hợp kết quả đã xem. Mọi con số mới phải có lý do theo mục tiêu và được ghi trước outcome mới. Validation dùng để kiểm cấu hình đã cố định; việc chọn/tune cấu hình ở development.

## Ranh giới triển khai tương lai

Chỉ sau quyết định mới triển khai package/world/runner/inventory riêng ngoài src/ và các version lịch sử. Giữ bốn khóa và toàn runtime cũ nguyên byte. Không dùng validation v3 đã exposed hoặc test v3 đang đóng làm fresh split. Không train, radar, dynamics/noise/3D/logistics/hardware trong nhánh này. Kết quả âm là đầu ra hợp lệ; kế hoạch không buộc tìm một candidate thắng.

Sản phẩm của bước A phải là ADR, protocol có đầy đủ trường trên và kế hoạch chạy có ngân sách; bản dự thảo này tự nó chưa là protocol có thể chạy.
