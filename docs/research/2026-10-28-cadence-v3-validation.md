# Validation v3 — kết quả không đạt; test giữ chưa mở

Ngày 2026-10-28. **Nghiên cứu cadence v3 không đạt thiết kế ở validation:** reference 32 ms và candidate 64 ms đều thành công 87/100 case khả thi, dưới ngưỡng 95%. Rate range/payload giảm 50% và các gate còn lại đạt, nhưng phải đạt đồng thời mọi gate. Theo protocol, dừng ở kết quả âm này, không mở test và không tune cấu hình bằng validation.

## Nguồn và toàn vẹn

- [CI duy nhất 40633617042](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40633617042), job `122635441422`, **job success**, source sạch `0c5f598c512a24db63b0fd19ca259a3b85382ee5`. Job success nghĩa pipeline hoàn tất và raw evidence hợp lệ; `study_outcome=not_met`, `test_qualified=false`.
- Runtime implementation vẫn `0c75ce28f14b8ea881e8c0c7c9335aa4319030c5`. Design digest `968c59e193336c49a015a62f87bf6f0ac834c6131bdb348105b5fcd950ad1474`; runtime digest `bcc938bb18acd9bd829f43e6f0f722f204a5c7702e5fa3b20c82b6171a080c3d`. Không đổi bốn lock hoặc file trong runtime inventory.
- [Kế hoạch 0012](../plans/0012-v3-validation-gate.md) có trước exposure; [protocol](../protocols/range-cadence-v3.md) và ngưỡng có trước implementation. Candidate 64 ms duy nhất được chọn trước outcome; không lựa chọn thay thế hoặc thêm ML.
- Đủ **120 case × 2 arm × 2 repeat = 480 lượt**, 240 pair/attempt hợp lệ, 0 retry. Một host CI Ubuntu 22.04, Python 3.12.15, Webots R2025a/Xvfb/software rendering, observer rendering tắt. Không chạy Webots validation trên laptop.
- Artifact `range-cadence-v3-validation`, ID `12794301003`, bản nén 220121298 B. Đã tải raw về thư mục ignored, kiểm từng file hash/case commitment/binary/sample-clock, rồi replay physics ticks, policy reads/CPU và aggregate qua các hàm đã khóa. **Review local khớp toàn bộ review CI**, không chỉ trường `met`.
- [JSON bằng chứng](2026-10-28-cadence-v3-validation.json) giữ nguồn, hash result/log/review/ledger, mọi gate, breakdown, mọi failure repeat và tài nguyên. Raw result SHA256 `8eac93a1697cd10ce2348cc66774080940069aeb8bf831e6b7e96705b0bbe4ee`. Tải về chỉ đổi attempt paths trong bản sao bộ nhớ, không sửa artifact/result gốc.

## Kết quả nhiệm vụ

| Đơn vị và outcome | Reference 32 ms | Candidate 64 ms |
|---|---:|---:|
| Case khả thi thành công cả hai repeat | **87/100 (87%)** | **87/100 (87%)** |
| Lượt khả thi success / timeout | 175 / 25 trên 200 | 175 / 25 trên 200 |
| Lượt negative timeout / false success | 40 / 0 | 40 / 0 |
| Collision / out-of-bounds, mọi lượt | 0 / 0 | 0 / 0 |

Mẫu số thống kê là 100 case khả thi, không phải 400 lượt khả thi hay hàng triệu ticks. Một case chỉ success nếu cả hai repeat đạt; mọi repeat vẫn được giữ. Negative có chứng chỉ goal trong solid từ generator, giữ riêng mẫu số, không đổi label của case feasible thất bại.

| Family feasible | Số case | Reference success | Candidate success |
|---|---:|---:|---:|
| empty | 27 | 25 | 25 |
| narrow_gap | 17 | 14 | 14 |
| single_block | 19 | 16 | 16 |
| staggered_blocks | 17 | 14 | 14 |
| u_trap | 20 | 18 | 18 |

Bảng paired sau collapse: 87 cả hai success, 13 cả hai failure, 0 chỉ reference success, 0 chỉ candidate success. Các baseline cùng gặp vấn đề chất lượng trong miền này; không có căn cứ quy việc không đạt 95% riêng cho cadence 64 ms. Cũng không được dùng sự tương đương tương đối để bỏ yêu cầu chất lượng tuyệt đối.

## Đối chiếu gate đã đăng ký

| Gate | Kết quả | Diễn giải |
|---|---|---|
| Cả hai arm ≥95% feasible case success | **Không đạt: 87% / 87%** | Đây là gate làm study không đạt |
| Không collision/bounds; negative không false success | Đạt trong 480 lượt | Không suy thành bảo đảm an toàn tổng quát |
| Adverse upper bound một phía 95% ≤5% | Đạt: 0/100, upper **2.9513%** | Adverse là reference success/candidate failure; giới hạn theo generator/giả định case độc lập |
| Rate range/payload giảm ≥50% trên mọi cặp | Đạt: 3000 →1500 B/s | Sai số số học trong 1e-9 tương đối; acquisitions/invalid/warmup được chấm riêng |
| Common-success path ratio ≤1.10 | Đạt: 0.999693 | 87 common-success case; không dùng nó thay số liệu failure |
| Penalized all-feasible time / path ratio ≤1.10 | Đạt: 0.998514 / 0.999832 | Penalty 90 s /72 m giữ đúng thiết kế |
| Tỷ số tổng p95 CPU theo case ≤1.10 | Đạt: 0.966929 | Cùng host, max repeat mỗi case, gồm negative |
| Map/search/RSS trong budget | Đạt | Không chứng nhận deadline phần cứng |

Kết luận chính xác: **đã đo được giảm acquisition rate 50% trong validation, nhưng baseline hiện tại không đạt yêu cầu nhiệm vụ nên giả thuyết kết hợp của protocol v3 không đạt.** Không kết luận mọi hệ thống ít dữ liệu đều không khả thi, không kết luận 64 ms làm kém chất lượng, và không kết luận đã tìm được lượng dữ liệu tối thiểu.

## Bốn tầng dữ liệu và tài nguyên

| Số đo toàn bộ 240 lượt/arm, gồm warmup/failure | Reference | Candidate |
|---|---:|---:|
| Unique acquisition packets | 397976 | 198900 |
| Canonical range payload tổng | 38205696 B | 19094400 B |
| Policy reads | 766353 | 766178 |
| Decision CPU mean, trọng số theo decisions | 0.875790 ms | 0.668939 ms |
| Decision CPU max | 76.386471 ms | 69.325767 ms |
| CPU decisions >16 ms | 6243 | 6181 |
| Controller RSS đỉnh được lấy mẫu | 23.468750 MiB | 23.5078125 MiB |
| Primary cells đỉnh | 5425 | 5413 |
| Search expansions đỉnh mỗi plan | 3483 | 3391 |

Payload chuẩn 96 B/packet không phải byte network hoặc định dạng hardware. Pose/mission/command/log JSON không được nhập vào tuyên bố range giảm 50%. Tổng byte phụ thuộc thời lượng/outcome, không nhất thiết giảm đúng 50% theo rate. Canonical payload, actual file bytes và cell/RSS được tách trong raw evidence. Candidate không giảm RSS đỉnh ở lần đo này.

CPU max vẫn vượt tick 16 ms; Webots chờ controller theo simulation time. RSS chỉ lấy mẫu tại decision ticks, có thể bỏ lỡ spike giữa tick. Không có kết quả điện năng/pin, sensor RF/radar, riêng tư hoặc hard realtime. Không gộp CPU từ các host hay cộng development/CI reproduction thành mẫu held-out mới.

## Kiểm tra thực sự đã chạy

1. `make check`: 127 tests cùng scaffold/lab/v1/v2/v3 design/runtime checks đạt local và CI tại source validation. Thêm 11 unit tests của review tool kiểm wrong source/lock/split, dirty/partial report, type/membership drift, train rejection, traversal/symlink, raw corruption, relocation không sửa input và classification/result mismatch. Không giả chúng là simulator smoke.
2. Trial review đủ 240 lượt development đã exposed tại đường dẫn gốc và một vị trí khác; không đổi raw result. Runtime digest vẫn khớp sau bổ sung workflow/tool ngoài đường thực thi.
3. Workflow validation chỉ dispatch thủ công, kiểm đúng digest/source sạch, không có dispatch trước hoặc run_attempt>1. Đã ghi ý định trước navigation. Thực thi chính thức 480 lượt trên một host, mọi pair qua raw audit; review độc lập sau tải về khớp CI.
4. Thử gate test bằng **CLI đã khóa** với result validation thật: exit 2, `Validation did not qualify this exact frozen runtime`. Không tạo output, ledger không đổi; từ chối trước executable lookup/launch. Không có lượt Webots/test nào được chạy bởi phép kiểm tra này.
5. CI exposure intent/result được nhập nguyên event sau review; thêm event local liên kết run ID/source/hash và kết luận âm. Không sửa hoặc xóa lịch sử development/pilot, không dispatch validation lần hai để tìm số đẹp.

## Trạng thái bàn giao

**V3 kết thúc đúng nhánh kết luận âm của protocol tại validation; test vẫn chưa mở.** Validation v3 đã exposed outcome và không được dùng như unseen sau này. Train vẫn dự trữ, chưa ML. Các thiết kế/runtime v1/v2/v3 giữ nguyên để tái lập; việc tái chạy đúng source/lock chỉ là reproduction, không tăng n hoặc làm mới unseen.

Nếu tiếp tục sửa coverage/free-grid/planner/cảm biến để khắc phục failure, phải lập version nghiên cứu phù hợp với đánh giá mới; không âm thầm sửa runtime v3 rồi dùng lại validation này. [GOAL-22](../../CHECKLIST_MUC_TIEU_NGHIEN_CUU.md) là đề xuất điều tra dựa trên development; chuyển radar và kiến trúc khác chưa được thực hiện trong mốc này. Phạm vi kết luận chỉ một drone, scene tĩnh, range/định vị lý tưởng và cùng generator; chưa là đánh giá ngoài đời hay bằng chứng sản phẩm giao hàng.
