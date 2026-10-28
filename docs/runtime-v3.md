# Runtime acquisition và đánh giá cadence v3

Giai đoạn 7A triển khai [kế hoạch 0011](plans/0011-range-cadence-runtime.md) theo [thiết kế đã khóa](protocols/range-cadence-v3.md). Không sửa v1/v2 hoặc design lock; `runtime_ready=false` trong hồ sơ thiết kế là trạng thái lịch sử của mốc 6. Quyền chạy held-out do artifact runtime lock riêng quyết định, không bằng cách đổi TOML đó.

## Runtime

- `drone_v3` chỉ dùng Robot/device API và mission goal; không import world/evaluation/experiments, không có camera. `lab_v3` là supervisor đặc quyền để bố trí/chấm; dữ liệu hình học/witness không gửi vào navigator.
- Mười DistanceSensor thực sự `enable(32)` hoặc `enable(64)`, kiểm lại `getSamplingPeriod()`. GPS/IMU/Gyro luôn 32 ms, physics/stabilizer/policy 16 ms. Timestamps suy ra từ epoch enable và lịch thiết bị; Webots API không cung cấp timestamp acquisition độc lập. Chuẩn hóa giây tới 9 chữ số thập phân để không gắn sample vào tương lai do round-off.
- Ray giữ pose đo đúng tick acquisition. `AcquisitionGrid` chiếu bằng pose đó; guard/planner/command dùng state đo gần nhất. Planner giống AST v2 sau bỏ counters expansions; không đổi tốc độ/grid/guard tham số.
- Pose giữ nguyên giữa hai tick đo, velocity là finite difference trên 32 ms rồi lọc cùng hệ số 0.35/0.65. Đây là nguồn đo lý tưởng trong simulator, chưa là localization phần cứng.

Nguồn API đối chiếu: [DistanceSensor R2025a](https://raw.githubusercontent.com/cyberbotics/webots/R2025a/docs/reference/distancesensor.md), [GPS R2025a](https://raw.githubusercontent.com/cyberbotics/webots/R2025a/docs/reference/gps.md). Không nhập mã/asset ngoài.

## Dữ liệu và đo tài nguyên

Mỗi pair có acquisition JSONL (timestamp/pose/readings/validity), range binary chuẩn 96 B/packet, decision JSONL (read/reuse/CPU/RSS), physics evaluation JSONL ở từng tick 16 ms và JSON kết quả. Sample ở đúng ranh giới bắt đầu scoring thuộc warmup; sample sau ranh giới mới thuộc cửa sổ chấm. Reads có thể dùng sample cuối warmup, nên unique samples read có thể lớn hơn số acquisition trong cửa sổ scoring một mẫu. Không nhập hai đại lượng này làm một.

Bốn tầng được báo riêng: sensor acquisition; observation reads/reuse; primary/derived map cells/search/RSS; canonical payload và byte file thực. RSS đọc `/proc/self/statm`, lấy đỉnh ở các decision tick; có thể bỏ lỡ spike ngắn giữa ticks. Webots RSS đọc riêng từ launcher, không gộp vào controller. Canonical payload không phải byte network. Log còn có overhead metadata/JSON/physics trace và không phải cấu hình lưu trữ tối thiểu.

`cpu` dùng process CPU time quanh construction/decision; `decision_wall` dùng timer wall của navigator v2. Báo p95 nearest-rank, max và số lần >16 ms riêng; không suy ra hard realtime. Chi phí instrumentation có mặt ở cả hai arms. Gate CPU chỉ so trong từng host/run, không gộp local và CI.

`cadence_audit.py` replay encoding binary/JSON, toàn bộ acquisition schedule, CPU/read counts và evaluator từ physics trace. File thiếu/sai, nguồn thay giữa collector hoặc pair unresolved đều chặn kết luận. Mọi attempt được giữ. Chỉ lỗi loader/display có thông báo cụ thể mới tự retry cả pair một lần; watchdog/crash chưa rõ nguyên nhân không được tự đổi thành infrastructure. Controller exception được giữ như lỗi thuật toán trong raw evidence; nếu làm thiếu arm/accounting, toàn nghiên cứu incomplete, không báo success rate trên phần còn lại.

## Lệnh

```bash
make check
python3 tools/build_research_v3.py
python3 tools/build_runtime_v3.py --check
python3 tools/run_research_v3.py --case development-empty-s3200006
python3 tools/run_research_v3.py --output artifacts/v3-development
```

Runner dùng cùng active.lock với collector laptop và từ chối chạy chồng. Giữ checkout trong lúc chạy. Mỗi case có hai repeat, mỗi repeat hai arm liền nhau theo hash case ID và đảo thứ tự ở repeat sau. Default không rendering; Linux cần display hoặc Xvfb. Không bỏ qua khi executable/display không hoạt động.

Trước/sau mỗi vòng, runner append ý định/kết quả vào exposure ledger; ledger thay đổi cần được review/commit trước lượt held-out tiếp theo. Fixture generation có automated geometry access nhưng không có navigation outcome; chỉ development mới được debug.

Sau source đã commit sạch và toàn bộ 60 ca development/240 lượt có integrity đầy đủ:

```bash
python3 tools/build_runtime_v3.py --freeze artifacts/v3-development/result.json
python3 tools/build_runtime_v3.py --check
```

Freeze replay raw evidence, đối chiếu hashes với implementation commit và tạo file mới `protocol_v3.runtime.lock.json`; từ chối overwrite. Inventory gồm toàn Python core, runner/builder, các config số học, generated proto/world và entrypoints/runtime.ini. Lock ghim source implementation; commit thêm lock/evidence sau đó vẫn phải có cùng inventory. Khóa runtime không khẳng định các gate chất lượng đã đạt.

Validation/test chỉ chạy sau hai lock hợp lệ; không thuộc bàn giao development 7A. Test còn cần complete validation với tất cả gate đạt trên đúng source/locks. Design builder cũ vẫn từ chối `--evaluate` vì nó không phải runner runtime. Train được giữ dự trữ, không runnable.


## Validation sau bàn giao 7A

[Kế hoạch 0012](plans/0012-v3-validation-gate.md) dùng workflow `research-v3-validation.yml`, chỉ `workflow_dispatch`, một host CI/Xvfb, 480 lượt. Không mở Webots local. Trước exposure phải khớp runtime digest đã review, source sạch, không có validation navigation trong ledger, không có dispatch khác và `GITHUB_RUN_ATTEMPT=1`. Không tự rerun job hoặc dispatch lần nữa khi kết quả xấu/thiếu.

`tools/review_research_v3.py` là hậu kiểm offline, không được runtime import và không thuộc thay đổi thuật toán. Nó kiểm identity, raw file hashes, case commitments, provenance, classification/retry và replay qua các hàm evaluator đã khóa. Download artifact được đổi đường dẫn **chỉ trong bản sao bộ nhớ**, giữ hash result gốc. Trường hợp development cũ chưa có runtime lock được ghi rõ và chỉ chấp nhận cho development; validation/test luôn cần digest execution runtime đúng.

Một study complete nhưng `study_outcome=not_met` vẫn là kết quả nghiên cứu hợp lệ, không là simulator job thất bại. `test_qualified` chỉ true nếu validation complete/raw audit và tất cả gate đạt. Workflow validation không thực thi test. Snapshot exposure sau chạy nằm trong artifact để review/đồng bộ về repo; raw logs/datasets không commit.
