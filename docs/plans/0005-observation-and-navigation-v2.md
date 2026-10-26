# Kế hoạch 0005 — quan sát có bộ nhớ và điều hướng v2

Ngày: 2026-10-26. Yêu cầu: lập kế hoạch chi tiết rồi thực thi cẩn thận giai đoạn sau seeded v1.

## Mục tiêu và ranh giới

Phân tích ba U collision của reactive v1, triển khai quan sát có bộ nhớ hữu hạn và lọc lệnh xét hull, kiểm tra liệu lập đường từ dữ liệu tự đo có cải thiện nhiệm vụ. Không huấn luyện trong giai đoạn này. Không dùng layout/witness/ID/ảnh của supervisor làm input. V1 và protocol lock v1 giữ nguyên byte; v2 có adapter/world/launcher/protocol riêng.

Đối chứng gồm reactive v1, guarded (reactive + quét/range memory + lọc lệnh), mapped (cùng cảm biến/guard + lập đường trên grid tự cập nhật). Đây là so sánh gói thành phần, không tự coi mọi khác biệt là hiệu quả riêng của bộ nhớ. Bản đồ số có thể biểu diễn bố trí môi trường; không gọi nó là tối thiểu dữ liệu hoặc bảo vệ toàn bộ thông tin.

## Các bước và điều kiện qua bước

| Bước | Công việc | Điều kiện qua bước |
|---|---|---|
| 1 | Audit repo, dữ liệu lỗi và môi trường local | Git sạch tại 2568f07; đọc đúng evidence; xác minh simulator/dependencies |
| 2 | Ghi giả thuyết, hợp đồng và tiêu chí trước thử | Phân biệt lỗi hình học, ray thưa, mất lịch sử và điều khiển; không suy diễn nguyên nhân chỉ từ ba collision |
| 3 | Viết v2 độc lập | Quét yaw; chiếu range bằng pose đo; grid hữu hạn/free/occupied/unknown; guard xét hull + phanh; planner chỉ nhận grid tự đo |
| 4 | Test hành vi và ranh giới | Đổi frame RPY/ENU, stale/future/missing, at-limit, swept segment/unknown, budget, reset, reject privileged packets; v1 lock vẫn hợp lệ |
| 5 | Chạy development và chỉnh chỉ trên development | Dùng hai seed v1 development 21001/21002; giữ mọi lượt thử/lỗi. So sánh ba policy, đọc telemetry/trace U và khe; thêm logging lỗi nếu cần |
| 6 | Khóa protocol v2 sau chọn cấu hình | Baseline/config/runtime/generator có checksum; fresh validation 51001/51002, test 61001/61002; không overlap geometry với v1 hoặc dev. Mỗi split 12 case, ba policy, 36 lượt |
| 7 | Chạy validation rồi test không chỉnh xen giữa | 72 lượt fresh sau khóa, tổng bộ chính thức 108 lượt tính development; mọi outcome được giữ, negative controls tách riêng, đủ paired coverage/provenance |
| 8 | Báo cáo và bàn giao | Phân tích success/collision/time/path và scan/guard/map budget; ghi rõ test exposure, giới hạn lý tưởng/2D/điểm mù; tài liệu chạy local và commit/push theo AGENTS.md |

## Tiêu chí quyết định

- Gate hạ tầng: đủ lượt, dữ liệu/seed/protocol khớp, ca trống đạt, không chấm success ca âm, v1 không bị sửa. Thiếu simulator phải báo lỗi.
- Mục tiêu kỹ thuật trên development trước khi khóa: mapped hoàn thành ít nhất một trong hai U từng gây collision, đạt ít nhất 8/10 ca khả thi và không tăng collision so với reactive. Nếu chưa đạt, phân tích/sửa trên dev rồi ghi toàn bộ thử nghiệm; không nới tiêu chí sau khi xem validation/test.
- Sau khóa, giữ kết quả dù kém; chỉ kết luận cải thiện trên những điều kiện có bằng chứng, không coi một lượt không collision là bảo đảm an toàn.
- Giữ bán kính đích 0.5 m, stop 0.18 m/s, dwell 1 s; v2 deadline 90 s cho cả ba policy, warmup 2 s. Vật lý/cảm biến vẫn v1; không đổi số ray để làm đẹp kết quả.
- Memory budget ghi số cell free/occupied/peak, số cập nhật cảm biến, lần scan/guard/planning và thời gian xử lý. Các byte ước tính phải ghi encoding; không coi JSON/log hoặc số cell là privacy metric.
- Dữ liệu v1 đã exposed chỉ dùng regression/development. Validation/test v2 được chạy khi protocol đã khóa; không retune rồi gọi lại v2 là unseen. Không tạo nhãn train bằng toàn bản đồ trong bước này.

## Trạng thái

- [x] Bước 1: worktree sạch, remote main đúng 2568f07. Webots đã có local và ldd với thư viện bundled không còn thiếu dependency; chưa xác minh GUI/flight local trong giai đoạn này.
- [x] Bước 2: ghi kế hoạch trước triển khai.
- [x] Bước 3: triển khai v2 cạnh v1, không sửa file v1 đã khóa; grid tạo từ GPS/tư thế/range, unknown tách free, giữ ngân sách và lọc lệnh.
- [x] Bước 4: 63 test Python đạt sau bổ sung kiểm tra protocol, sampling và recovery; v1 lock hợp lệ. Local dev lần đầu không kết nối được display :0, không có result.json/không báo đã bay. Chọn CI/Xvfb cho bước bay thật.
- Development đầu: CI 40253447132 (source 5d1500b, có render) và 40254520825 (source f2b054b, numeric/no-render) đều đủ 36 lượt, guarded/mapped 10/10, reactive 8/10 ca khả thi; giữ mọi outcome trong [development evidence](../research/2026-10-26-v2-development.json). Sau đó thêm recovery cho trường hợp synthetic contract bị kẹt vì inflation; chưa chạy fresh split.
- [ ] Bước 5.
- [ ] Bước 6.
- [ ] Bước 7.
- [ ] Bước 8.
