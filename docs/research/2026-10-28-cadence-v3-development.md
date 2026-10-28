# Mốc 7A — runtime cadence v3 và development

Ngày 2026-10-28. **Đã triển khai và kiểm chứng acquisition/accounting/evaluation v3; chưa chứng minh giả thuyết giữ chất lượng khi giảm dữ liệu.** Source runtime `0c75ce28f14b8ea881e8c0c7c9335aa4319030c5`. [JSON bằng chứng](2026-10-28-cadence-v3-development.json), [kế hoạch](../plans/0011-range-cadence-runtime.md), [hướng dẫn](../runtime-v3.md).

## Nguồn và phạm vi

- Local Webots R2025a trên laptop: `artifacts/v3-development-0c75ce2`, source sạch lúc bắt đầu, 60 case × 2 arm × 2 repeat = **240 lượt**, 120 pair/attempt hợp lệ, không retry. Từng pair qua independent raw replay; file result gốc có hash trong JSON.
- [CI 40615141669](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40615141669), job `122575752293`, success tại cùng source: **240 lượt development khác lần chạy local**, 112 unit tests, generation/design checks và raw replay đạt. Không cộng local+CI thành 120 case độc lập.
- Khóa thiết kế giữ nguyên `968c59e193336c49a015a62f87bf6f0ac834c6131bdb348105b5fcd950ad1474`. Khóa runtime bổ sung `bcc938bb18acd9bd829f43e6f0f722f204a5c7702e5fa3b20c82b6171a080c3d` ghim inventory của implementation commit trên và digest development. Hai khóa v1/v2 vẫn nguyên byte.
- **Chỉ development được thực thi/xem outcome.** Validation/test v3 chưa chạy. Train vẫn dự trữ; không ANN/RL, radar vật lý, hardware hoặc privacy claim.

## Runtime đã kiểm chứng

World/proto/controllers v3 sống cạnh v2. Mười DistanceSensor thực sự đặt `enable(32)` hoặc `enable(64)` và ghi sampling period hiệu lực. GPS/IMU/Gyro 32 ms; control/physics 16 ms ở cả hai arm. Packet giữ pose lúc acquisition, không dùng pose control mới để chiếu ray cũ. Navigator không nhận geometry, case IDs, witness hoặc ảnh; supervisor giữ việc bố trí và chấm.

`AcquisitionGrid.plan` có cùng thuật toán v2, thêm counters expansions; unit test so AST sau bỏ riêng các assignment counters. Không thay số ray, tốc độ, freshness, grid/guard/planner parameters để cải thiện outcome. Dữ liệu đo lý tưởng, vật cản tĩnh, tìm đường ngang; đây không phải thử localization hoặc sensing ngoài đời.

Bốn tầng được đo riêng: acquisition duy nhất; policy reads/reuse; map/search/RSS; canonical range payload và actual file bytes. Raw acquisition JSONL và binary được đối chiếu byte; CPU/read counts replay; evaluator được chạy lại từ toàn bộ physics trace 16 ms để đối chiếu outcome/path/deadline. Timestamp được suy ra từ epoch enable/lịch thiết bị, không giả là timestamp hardware độc lập.

CPU dùng process CPU time, thời gian wall decision báo riêng. RSS controller đọc tại decision ticks; Webots RSS báo riêng trong attempts. Instrumentation có chi phí ở cả hai arm; không coi cell count là byte hoặc canonical payload là lưu lượng mạng.

## Kết quả development

| Đơn vị và outcome | Reference 32 ms | Candidate 64 ms |
|---|---:|---:|
| Case khả thi thành công ở **cả hai** repeat | 45/50 (90%) | 46/50 (92%) |
| Lượt khả thi success / timeout | 92 / 8 trên 100 | 93 / 7 trên 100 |
| Lượt negative timeout / false success | 20 / 0 | 20 / 0 |
| Collision / out-of-bounds, mọi lượt | 0 / 0 | 0 / 0 |
| Range payload rate, mọi lượt, sai số số học ≤1e-9 tương đối | 3000 B/s | 1500 B/s |
| Acquisition packets, cả warmup và failure | 189807 | 94241 |
| Canonical range payload toàn đợt | 18221472 B | 9047136 B |

Đã đo được giảm 50% **rate range** trong miền development này. Tổng byte không nhất thiết giảm đúng 50% vì thời gian/outcome hai arm khác nhau. Không suy ra điện năng, dung lượng log toàn hệ thống, chi phí vận hành hoặc riêng tư giảm tương ứng.

Bảng paired sau collapse: 45 case cả hai success; 4 case cả hai failure; 1 case reference failure/candidate success; 0 case reference success/candidate failure. Các case feasible có timeout: `narrow_gap-s3200004`, `empty-s3200020`, `narrow_gap-s3200029`, `empty-s3200034`, `empty-s3200041` (đều thuộc development). Không bỏ chúng hoặc đổi nhãn sang negative.

Ở `narrow_gap-s3200004`, arm chạy đầu timeout trong cả hai repeat; arm chạy sau success. Pose đầu khác nhau trong tolerance reset và đã được lưu. Đây là liên hệ quan sát với thứ tự/khởi tạo, chưa xác định nguyên nhân. Quy tắc collapse vẫn tính cả hai arm failure tại case đó; không chọn repeat tốt. Không tăng warmup hoặc sửa planner sau quan sát để cứu điểm.

## Gate và chi phí

Chỉ số gate tính trên development mang tính chẩn đoán, không là validation/test cuối. Success 90%/92% thấp hơn ngưỡng đăng ký 95%. Với 0 adverse/50 case, upper bound một phía 95% là **5.8155%**, chưa ≤5%; ngay cả development hoàn hảo cũng chưa đủ số case cho gate thống kê này. Không tăng n hoặc thay confidence sau khi xem kết quả. Vì vậy `met=false` không được biến thành tuyên bố candidate đã kém reference ở test; held-out còn chưa được mở.

Trên local: common-success path ratio candidate/reference `1.000405`; common-success time ratio `1.001835`; penalized all-feasible time ratio `0.979907`, path ratio `0.940812`. Tỷ số tổng p95 CPU theo case, gồm negative, là `0.869860` local và `0.950772` CI; xét riêng từng host, không gộp hai máy.

| Tài nguyên local, gồm mọi outcome | Reference | Candidate |
|---|---:|---:|
| Decision CPU mean, trọng số theo số decisions | 0.5534 ms | 0.3938 ms |
| Decision CPU max | 48.6495 ms | 46.3166 ms |
| Decisions có CPU >16 ms | 1360 | 1209 |
| Controller RSS đỉnh được lấy mẫu | 24.5469 MiB | 24.6250 MiB |
| Primary map cells đỉnh | 5370 | 5362 |
| Search expansions đỉnh mỗi plan | 3320 | 3411 |

Candidate không giảm RSS đỉnh trong lần đo này. CPU max vẫn vượt tick; simulator chờ controller, nên không có kết luận hard realtime hoặc phần cứng. RSS lấy mẫu có thể bỏ lỡ spike giữa tick. Tổng wall của 120 pair local khoảng 806.289 s, gồm startup/shutdown. Source không rendering nhưng local dùng display laptop, nên cửa sổ Webots mở/đóng cho mỗi pair; CI dùng Xvfb và không mở cửa sổ trên laptop.

Local và CI khớp toàn bộ collapsed success, elapsed delta lớn nhất 0 s, path delta lớn nhất khoảng `3.32e-14` m. Đây là đối chiếu tái lập của cùng case/source, không là bằng chứng generalization hoặc tương đương từng physics tick.

## Lỗi đã giữ và kiểm tra

Pilot đầu ca trống có bốn lượt success nhưng source dirty. Pilot audit tiếp theo bị chặn vì pose age âm cỡ `1e-14` s do floating point; cùng sai số cũng khiến navigator từ chối một số mẫu mới. Đã chuẩn hóa timestamp tới 9 chữ số thập phân, thêm test hồi quy và giữ nguyên raw lượt lỗi. Pilot sửa lỗi gồm ca U/trống/negative có 12 lượt, raw audit đạt. Các pilot không cộng vào kết quả development chính thức.

Đã sửa launcher v3 để tái lập `WEBOTS_TMPDIR/TMPDIR=/tmp` như wrapper Webots; pilot sửa lỗi và full run không còn thông báo “Webots has not been started regularly”. Không sửa launcher v1/v2 đã khóa.

- `make check` trước source runtime: 112 tests đạt. Bàn giao bổ sung test fault-injection corruption/missing physics tick và retry orchestration; tổng **116 tests** đạt khi chạy lại.
- Smoke v1 local đạt 12 checks; navigation direct/reactive development local ghi đủ 8 lượt và 5 integration checks đạt. Direct collision/reactive negative timeout vẫn giữ nguyên, không gọi mọi baseline là success.
- Runner từ chối validation khi chưa có runtime lock; builder từ chối freeze từ pilot thiếu full split. Sau tạo runtime lock, `--check` xác minh inventory, commit implementation và ancestry. Design builder cũ vẫn không phải runtime evaluator.
- Unit fault injection: binary corruption, thiếu physics tick, thiếu/duplicate repeat, invalid/stale/future sample, deadline/contact priority, lock mismatch, algorithm failure không retry, infrastructure retry tối đa một lần rồi incomplete. Đây là unit tests; không giả là đã gây OOM hoặc crash Webots thật.

## Bàn giao và bước kế tiếp

Mốc 7A hoàn tất **hạ tầng runtime và kiểm chứng development**, không hoàn tất nghiên cứu chất lượng cuối. Khóa runtime chứng minh mã chạy/provenance, không chứng nhận các gate nghiên cứu đã đạt. Không đổi design lock hoặc v1/v2 locks.

Validation/test vẫn chưa exposed outcome và không được dùng để sửa reference. Bước tiếp theo cần giữ đúng protocol nếu thực hiện validation gate; test chỉ mở khi validation đạt. Nếu muốn sửa thuật toán hoặc thiết kế vì các failure development, phải lập version/thiết kế mới phù hợp, giữ nguyên kết quả này. Chưa có căn cứ mở ML hoặc tuyên bố sản phẩm giao hàng.
