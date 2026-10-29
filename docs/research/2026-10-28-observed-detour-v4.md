# GOAL-23 — Điều hướng v4 đi vòng qua vùng đã quan sát

Thí nghiệm CI ngày 2026-10-28; hậu kiểm và bàn giao ngày 2026-10-29 (Asia/Ho_Chi_Minh). Hoàn tất development theo [kế hoạch 0014](../plans/0014-observed-detour-v4.md), [ADR 0007](../decisions/0007-observed-detour-v4.md). Không có held-out evaluation hoặc kết quả phần cứng.

## Kết quả trên đúng source bàn giao

Runtime source **`9503c2c2b483d677d7f0ff25f76d7dcca360bc08`**, [CI 40684709433](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40684709433): **88 case × 2 arm × 2 repeat = 352 episode**, 176 attempts. Hai arm cùng range/pose **32 ms**, control 16 ms. Reference giữ CadenceNavigator v3; candidate dùng ObservedDetourNavigator v4. Source CI sạch, mọi raw pair được audit; kiểm lại artifact trên local Python 3.12 cho JSON review **khớp CI hoàn toàn**.

| Kết quả | Reference đã khóa | V4 |
|---|---:|---:|
| Case khả thi thành công, cả hai repeat | 62/74 | 74/74 |
| Episode success, trong 148 lượt khả thi | 129 | 148 |
| Episode khả thi thất bại | 19 | 0 |
| Collision / out_of_bounds, mọi lượt | 0 / 0 | 0 / 0 |
| False success, 28 lượt negative | 0 | 0 |

Năm case kẹt cũ đều đến đích trong **cả hai repeat** của v4; không chỉ phát lệnh tại snapshot. Có 12 case cải thiện và 0 case reference thành công nhưng v4 thất bại. Các engineering gates đều đạt trong suite này. 74/74 là kết quả development trên dữ liệu được dùng để phát triển, không phải ước lượng generalization hoặc chứng nhận đạt ngưỡng nghiên cứu trên held-out.

## Thay đổi thực thi

Package `versions/navigation_v4/blind_drone_v4/` và world/PROTO/controllers tên v4 riêng; **không thay hoặc thêm Python trong src/**. V4 inventory cộng shared v3 với source/config/entrypoints mới, không tái sinh khóa cũ.

Giữ cách chiếu ray theo acquisition pose, dựng free/occupied, origin 0.33 m, grid 0.25 m, scan/speed/margins và velocity guard. Khi đường optimistic không có đoạn thực thi, search trong connected component free/inside/unblocked, không cắt góc qua unknown. Kết nối từ pose thực đo; kiểm supercover và measured swept clearance cho target, rồi kiểm lại hướng lệnh sau guard. Không tự tô lỗ coverage thành free; không dùng obstacle/witness hoặc ảnh làm đầu vào navigation. Nếu chưa có lối phù hợp thì dừng/quét.

Revision endpoint giữ ô floor chứa hai endpoint và mọi cell tiếp xúc phần giữa đoạn, kể cả corner; chỉ bỏ cell khác tiếp xúc riêng đúng đầu/cuối. Đoạn chạy dọc đường biên vẫn yêu cầu cả hai phía free. Test bổ sung chứng minh departure vào phía đã quan sát mà không đánh dấu free phía chưa biết.

## Case, phép đo và clearance

Suite gồm 60 case v3 development đã exposed (50 feasible + 10 negative), thêm 16 empty offset/yaw, 4 near-wall, 4 narrow-gap, 4 negative. Tổng 74 feasible và 14 negative; case là đơn vị collapse, không coi repeat/tick là mẫu độc lập. Một số empty giữ cùng geometry và thay yaw: 74 là số task-config case, không phải 74 geometry độc lập. Không tính confidence bound từ suite kiểm soát này. Index hashes có trước simulator; fixture/world thật chỉ vào supervisor/evaluation. Mọi failure reference vẫn nằm trong [JSON bằng chứng](2026-10-28-observed-detour-v4.json), không bị loại khỏi mẫu số.

| Family | Reference case success | V4 case success |
|---|---:|---:|
| empty | 12/15 | 15/15 |
| empty_offset | 12/16 | 16/16 |
| narrow_gap | 8/12 | 12/12 |
| near_wall | 3/4 | 4/4 |
| single_block | 12/12 | 12/12 |
| staggered_blocks | 8/8 | 8/8 |
| u_trap | 7/7 | 7/7 |

Hậu kiểm **477042 quyết định candidate** bằng grid tái dựng chỉ từ pose/range ghi được; kiểm target và đoạn lệnh sau guard, không có vi phạm. Có 58404 quyết định đi theo detour. Raw log giữ command/status/target/recovery từng tick. Audit dùng cùng predicate hình học đã unit-test, không là một implementation hình học độc lập thứ hai.

Evaluator đặc quyền tính clearance riêng từ obstacle AABB và polyline vị trí thật ở tick 16 ms, gồm cả failure/negative. Khoảng cách nhỏ nhất từ tâm đến bề mặt vật cản/tường là **0.863025884 m**; mức kiểm tra sphere hull + margin là **0.551740663 m**. Dữ liệu này không đi vào controller. Đây là khoảng hở của polyline được chấm trong mô phỏng, chưa phải chứng minh chuyển động liên tục hoặc an toàn thiết bị thật.

## Chi phí và hiệu quả nhiệm vụ

| Chỉ số controller, mọi episode | Reference | V4 |
|---|---:|---:|
| CPU mean có trọng số theo số quyết định (ms) | 0.651574 | 1.132001 |
| p95 lớn nhất của một episode (ms) | 1.501016 | 6.430564 |
| CPU max (ms) | 57.826339 | 58.844088 |
| Số quyết định CPU >16 ms | 2323 | 6315 |
| Peak controller RSS (MiB) | 29.218750 | 30.425781 |
| Peak map cells / search expansions | 5370 / 3320 | 5378 / 4293 |

CPU đo quanh navigator.step, chưa gồm toàn adapter/stabilizer/I/O; RSS là process controller, không phải toàn Webots. Trong 62 case cả hai cùng thành công, tỷ số v4/reference time = 1.001208255, path = 1.001236426 (mỗi case lấy repeat xấu hơn). Khi giữ failure bằng penalty 90 s/72 m, time ratio = 0.796727273, path ratio = 0.558641608. Không so hai mean success-only khác mẫu để suy ra bay nhanh hơn. Lợi ích chính trong suite là tránh timeout; controller có thêm chi phí. CPU max vẫn vượt tick 16 ms, không chứng minh hard realtime. Hai arm đều 32 ms nên **không có kết quả giảm acquisition rate mới**.

## Kiểm tra, provenance và tái lập

- `make check`: **165 unit tests**, gồm 24 test v4, generated v4 assets và bốn legacy locks đều đạt local/CI.
- Webots R2025a thực trên CI/Xvfb: legacy `tools/run_webots.py --navigation` đạt; paired v4 đủ 352 episode và independent raw review đạt. Không mở GUI laptop.
- Source đầu `2cf9238`, [CI 40674654512](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40674654512), cũng đủ 352 lượt: reference 62/74, v4 74/74; [summary riêng](2026-10-28-v4-initial-ci-summary.json). Sửa endpoint xuất phát từ kiểm tra tổng hợp, không từ held-out. Không cộng hai lượt suite lặp thành 148 case độc lập.
- [Snapshot đầu](2026-10-28-v4-snapshot-decisions.json) và [snapshot revision endpoint](2026-10-28-v4-endpoint-snapshot-decisions.json) giữ riêng hash/source; chỉ là quyết định offline, không thay thế flight evidence.
- V4 runtime inventory digest: `e5c893081bb698d29a1ef853b510db4622b637c0a021bb66320752d8b620b795`.
- Development index/spec digest: `5ff85509e850c0d02ad8e1f0bc8a1af75d7d67f2f695d49c6e4a0148b4219662`.
- Shared v3 runtime digest giữ nguyên: `bcc938bb18acd9bd829f43e6f0f722f204a5c7702e5fa3b20c82b6171a080c3d`.
- Raw result SHA-256: `e7840b636a2c67365a01e185c27214899bcf1328d43db3ee0e147ab82819bb83`. Bốn hash byte file lock và source/CI được giữ trong JSON bằng chứng.
- Raw artifact local: `artifacts/v4-ci-40684709433/v4-development/`; CI review `artifacts/v4-ci-40684709433/v4-review.json`; independent local review `artifacts/v4-ci-40684709433/local-review.json`.

Dùng checkout riêng tại source `9503c2c2b483d677d7f0ff25f76d7dcca360bc08` để tái lập đúng bản đã chạy trước các lệnh dưới. Nếu chạy commit khác, reviewer phải nhận SHA thực của run đó từ manifest và vẫn kiểm inventory; không nhận source lịch sử thay cho source thực.

```bash
python3 tools/build_navigation_v4.py
make check
# Trên Xvfb/CI, fresh output; giữ checkout trong lúc collector giữ flock:
xvfb-run -a python3 tools/run_navigation_v4.py --output artifacts/v4-development-new
python3.12 tools/review_navigation_v4.py artifacts/v4-development-new \
  --expected-source 9503c2c2b483d677d7f0ff25f76d7dcca360bc08 --output artifacts/v4-review-new.json
```

## Trạng thái bàn giao

GOAL-23 hoàn tất **implementation và kiểm chứng development**: có phiên bản riêng, lối thay thế qua free-grid, đo clearance và thoát kẹt vật lý trong simulator ở năm regression. Chưa có protocol/validation/test v4; CLI chỉ nhận development. V3 vẫn đóng bằng kết quả âm 87/100, test chưa mở; v1/v2 và cả hai khóa v3 giữ nguyên.

Bước nghiên cứu sau cần câu hỏi/ngưỡng/source lock và validation/test mới trước exposure. Không dùng suite development này hoặc validation v3 đã exposed làm held-out. Chưa huấn luyện, radar, privacy/energy claim hoặc tích hợp hardware.
