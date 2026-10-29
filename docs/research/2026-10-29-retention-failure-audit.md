# Audit 0017 — củng cố và đối chiếu retention failure

Ngày: 2026-10-29. Phạm vi được cho phép: [kế hoạch 0017](../plans/0017-maintenance-and-retention-audit.md). Đây là phân tích mô tả offline trên development đã exposed; không chạy simulator, policy replay mới, validation/test hoặc huấn luyện.

## Kết quả chính

V4 full-history hoàn tất 74/74 case khả thi trong run lịch sử; DATA-03 và hai arm DATA-04 đạt 67/74 trong từng run. Timeout retention trong mẫu vẫn di chuyển 22.36–24.66 m, không giống năm lỗi đứng yên ở đầu lượt của GOAL-22. Cùng occupied-only đổi danh tính case thất bại giữa hai run. Trạng thái scoring ban đầu khác theo slot, nên chưa có căn cứ gán toàn bộ chênh lệch cho mất free-history hoặc TTL.

Ưu tiên tiếp theo là [dự thảo 0018](../plans/0018-retention-study-proposal.md): đối chứng trực tiếp v4, kiểm tra cùng policy ở hai slot/nhãn và kiểm soát khởi tạo trước nghiên cứu retention. Chưa chọn candidate hay ngưỡng chất lượng mới.

## Nguồn và phạm vi xác minh lần này

| Study | Source lịch sử | Raw manifest SHA-256 |
|---|---|---|
| V4 | `9503c2c2b483d677d7f0ff25f76d7dcca360bc08` | `e7840b636a2c67365a01e185c27214899bcf1328d43db3ee0e147ab82819bb83` |
| DATA-03 | `94f8e0b461c01aa18f269e75eb6662ce2d2283df` | `bc188514e0d1a862fac548e8340fd8f6e85cc9897b0d08b063fd502f04f83fea` |
| DATA-04 | `8b4e3bed8a9e86946ca1c7c2a47dcffdf646aca2` | `35186405fb35e0eb0584d5bf63c369da086c57a69bef198fc104c5da04323a5c` |

Các manifest khớp digest trong hồ sơ đã review trước đó, cùng development commitment, 88 case/352 episode mỗi run, 74 case khả thi. Lần này lấy hợp các case có ít nhất một repeat timeout ở DATA-03 candidate hoặc hai arm DATA-04: chín case. Đối chiếu hai repeat của bốn phương pháp/vị trí nghiên cứu: 72 episode sẵn có, không tăng cỡ mẫu nghiên cứu.

Tool [analyze_retention_failures.py](../../tools/analyze_retention_failures.py) xác minh hash 234 file case/result/decision/evaluation được dùng từ attempt manifest; case và episode khớp raw pair result, số decisions khớp counter. Nó không chạy lại toàn bộ auditor lịch sử và không xác minh lại mọi acquisition/range.bin trong ba artifact. Full raw replay vẫn là bằng chứng tại các báo cáo [v4](2026-10-28-observed-detour-v4.md), [DATA-03](2026-10-29-data03-occupied-only.md), [DATA-04](2026-10-29-data04-hit-ttl.md).

## Từng case sau collapse hai repeat

`S/T` theo thứ tự repeat 0/1; một timeout làm case không success. Negative controls không nằm trong bảng. Đây là so sánh outcome development khác run, không là confidence estimate hoặc ablation cost cùng host.

| Case | V4 full-history | DATA-03 gốc | DATA-03 reference trong DATA-04 | TTL 10 s |
|---|---|---|---|---|
| `development-narrow_gap-s3200004` | S/S | T/S | S/T | S/S |
| `development-narrow_gap-s3200017` | S/S | T/S | S/S | S/S |
| `development-narrow_gap-s3200027` | S/S | S/S | T/S | S/T |
| `development-narrow_gap-s3200029` | S/S | T/S | S/T | T/S |
| `development-narrow_gap-s3200039` | S/S | T/S | T/T | T/T |
| `development-u_trap-s3200019` | S/S | S/S | S/S | S/T |
| `development-u_trap-s3200046` | S/S | T/S | S/T | T/S |
| `development-u_trap-s3200048` | S/S | T/S | S/T | T/S |
| `development-v4-narrow_gap-20` | S/S | T/T | T/T | T/T |

DATA-03 gốc và reference DATA-04 cùng 67/74 nhưng đổi case `narrow_gap-s3200017` và `narrow_gap-s3200027`. Có 11 thay đổi outcome theo case/repeat; nhãn arm đổi vị trí trong thứ tự chạy. Khi đối chiếu cùng slot thứ nhất/thứ hai, còn ba thay đổi ở slot thứ hai: `narrow_gap-s3200017`, `s3200027`, `s3200039`. Không gọi tất cả 11 thay đổi là ngẫu nhiên độc lập hoặc hiệu ứng TTL.

## Dấu hiệu failure thực sự ghi được

- DATA-03 gốc có tám timeout episode thuộc bảy case; reference DATA-04 và TTL mỗi arm có chín timeout episode thuộc bảy case. Tất cả là timeout, không collision/bounds trong các outcome này.
- Trong 10 giây cuối, tám timeout DATA-03 gốc vẫn có 516–626 lệnh ngang khác zero trên 626 decisions; timeout reference DATA-04 và TTL có 618–626. Bbox ngang của physics trace trong cửa sổ đó có đường chéo 1.88–2.95 m. Đây là chuyển động còn tiếp diễn, chưa chứng minh dao động, vòng lặp hoặc một nguyên nhân planner cụ thể.
- Trong 72 episode được mô tả, không có budget exhaustion hoặc invalid acquisition value được ghi. Điều đó loại hai dấu hiệu này khỏi mẫu, không loại mọi khả năng lỗi geometry, cache hoặc freshness ở các tình huống khác.
- Với TTL, `narrow_gap-s3200027` repeat 1 vào vùng đích ở 88.352 s, bắt đầu đạt điều kiện tốc độ ở 89.680 s; khoảng liên tục dài nhất 0.320 s trước deadline 90 s. `u_trap-s3200019` repeat 1 vào vùng ở 89.408 s nhưng chưa có tick tốc độ đạt ngưỡng. `v4-narrow_gap-20` repeat 0 vào vùng ở 88.016 s, nhưng khoảng chậm liên tục dài nhất chỉ 0.224 s. Không lượt nào đủ dwell 1 s; không sửa evaluator/deadline để biến chúng thành success.

Khoảng dwell ở đây chỉ mô tả điều kiện vị trí/tốc độ từ scored physics trace, không thay outcome hoặc tái chấm toàn evaluator.

## Khởi tạo và thứ tự cần được kiểm soát

Trong 148 pair khả thi của từng run, chênh lệch vị trí scoring ban đầu lớn nhất giữa hai arm là 0.04543 m ở v4 và 0.04668 m ở DATA-03/04; chênh lệch vận tốc lớn nhất là 0.02807/0.02844 m/s, yaw 0.03926/0.03928 rad. Các số này là từ manifest đã xác minh digest; không chứng minh tác động nhân quả của mỗi sai lệch.

Ví dụ `narrow_gap-s3200017`: DATA-03 gốc candidate ở slot thứ nhất success, slot thứ hai timeout; khi occupied-only là reference DATA-04 thì cả hai slot success. Slot thứ hai của hai run đi sau phương pháp khác nhau và có initial pose/velocity khác nhau. Cần nghiên cứu reset/khởi tạo và độ nhạy của policy trước khi diễn giải mức thay đổi nhỏ do retention.

Frozen adapter đặt pose/resetPhysics, reset stabilizer rồi warmup 2 s; gate cũ chấp nhận sai lệch position/speed/yaw trong tolerance. Các lượt trên không bị kết luận invalid theo protocol cũ. Tolerance đủ để chạy đúng protocol cũ vẫn có thể quá rộng cho câu hỏi ablation nhỏ hơn. Chưa chứng minh tồn dư controller, khác biệt số học hoặc slot là nguyên nhân duy nhất; không sửa adapter frozen trong đợt này.

## Củng cố tooling và kế hoạch

- `configs/navigation_v2.toml` được phục hồi đúng byte đã commit sau khi xác nhận diff chỉ thiếu newline cuối. Không thay thông số hoặc tái sinh bốn khóa.
- Scaffold checker loại nội dung sinh tại root artifacts/data/models và export hội thoại root theo mẫu rõ; vẫn kiểm ba README và source/tài liệu chưa tracked. File export và raw artifact được giữ nguyên.
- Checklist/README/development/agent có trạng thái sau DATA-04; kế hoạch cũ được gắn nhãn lịch sử. GOAL-13 ghi hoàn tất kiểm nghiệm với kết quả âm; phần test GOAL-15 không thực hiện vì gate fail, không phải việc chờ chạy bù.
- [ADR 0010](../decisions/0010-maintenance-and-retention-priorities.md) ghi phạm vi được chấp nhận và đề xuất còn mở. 0018 chưa cấp quyền sửa navigation hoặc chạy nghiên cứu mới.

Kiểm chứng source: `make check` đạt 181 unit tests cùng scaffold/assets/bốn khóa; năm test mới bảo vệ phạm vi source, repeat collapse, hash/time drift và phân biệt gần đích với dwell. So sánh inventory v3/v4/DATA-03/DATA-04 với manifest lịch sử khớp; bốn file khóa nguyên byte. Không chạy Webots mới trong 0017. Nhánh bàn giao `fix/checklist-retention-audit`; commit/CI được ghi ở Git và thông báo bàn giao, không dùng HEAD của tài liệu thay SHA runtime lịch sử.

## Tái hiện

Với raw artifacts đã có, chạy ở checkout chứa tool này và full v4 development spec khớp hash; output phải là file mới:

```bash
python3 tools/analyze_retention_failures.py \
  --v4-run artifacts/v4-ci-40684709433/v4-development \
  --data03-run artifacts/data03-final-ci \
  --data04-run artifacts/data04-ci-40816451698 \
  --output artifacts/retention-failures-new.json
```

[JSON evidence nhỏ](2026-10-29-retention-failure-audit.json) giữ outcome, timeout profiles, manifest/tool/output hashes và thống kê khởi tạo. Output đầy đủ local có danh sách 234 file SHA-256; không đưa raw logs vào Git. Chỉ dùng development đã exposed; chưa có held-out, cải thiện thuật toán, chứng minh riêng tư/tối thiểu dữ liệu hoặc phần cứng. V3 test tiếp tục đóng.
