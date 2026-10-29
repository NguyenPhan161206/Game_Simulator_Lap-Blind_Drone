# Khởi tạo A/A v1 — kiểm chứng development

CI chạy ngày 2026-10-29; hậu kiểm local và bàn giao ngày 2026-10-30 (Asia/Ho_Chi_Minh). Thiết kế [plan 0019](../plans/0019-initialization-aa-development.md)/[ADR 0011](../decisions/0011-initialization-aa-development.md) được đăng ký ở `734996d` trước simulator. Source implementation kiểm chứng: **`97be9a0c6882dddd5e7ca58c17bf75ddd6182bf5`**.

## Kết quả và phạm vi

Đã hoàn tất A/A development: cùng ObservedDetourNavigator v4 full-history cho hai nhãn reference/candidate, so warm-sequential với cold-isolated. [CI 40911479243](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40911479243) qua 189 unit tests, legacy smoke/navigation Webots thật và đầy đủ **12 case × 2 mode × 2 arm × 2 repeat = 96 episode**, 72 process/72 attempt, không retry. Local raw reviewer chạy ở checkout riêng sạch đúng source và JSON khớp hoàn toàn với CI.

| Kết quả | Warm nối tiếp | Cold từng process mới |
|---|---:|---:|
| Episode | 48 | 48 |
| Feasible success / feasible episodes | 44 / 44 | 44 / 44 |
| Negative timeout / negative episodes | 4 / 4 | 4 / 4 |
| Collision / bounds / negative false success | 0 / 0 / 0 | 0 / 0 / 0 |
| So toàn trace giữa bốn episode cold cùng case | Không phải gate warm | 36/36 phép so đạt tolerance |

Cả năm gate A/A đều đạt: cold equivalence, zero observed collision/bounds/negative false success và raw audit đầy đủ. **Đây là gate khởi tạo, không phải gate chất lượng giảm dữ liệu.** Không đổi retention/cadence/thuật toán và chưa có held-out mới. Các case đã exposed; không cộng 96 episode thành 96 case độc lập hoặc nâng kết quả v4 74/74 thành một nghiên cứu xác nhận mới.

## Điều được đối chiếu

Cold: cả hai label và hai repeat được so với cold reference repeat 0 cho mỗi case. Flags/counts/status/outcome phải bằng nhau; initial state, measured acquisition/pose, command/target và scored physics dùng tolerance `1e-6` theo đơn vị tương ứng, timestamp chuẩn hóa `1e-9 s`. Elapsed/path có bound 0.016 s/1e-5 m. Không chọn episode đẹp nhất. CPU/wall/RSS được loại khỏi điều kiện tương đương; không kết luận chúng giống nhau hoặc cold tiết kiệm tài nguyên.

Reviewer xác minh source/inventory, case membership, toàn bộ hash file dùng, retry history, binary encoding 96 B/packet, sensor timing/read reuse, evaluator tại physics tick và **276546 command decisions** từ pose/range hợp lệ. Target/lệnh được kiểm bằng grid tự đo; ground truth chỉ vào scoring/clearance. Minimum scored-polyline surface clearance đo được là 0.984976 m; không là chứng minh chuyển động liên tục hoặc an toàn phần cứng.

## Khác biệt warm và cơ chế bootstrap quan sát được

Trên 24 warm pair, chênh lệch initial state lớn nhất giữa hai arm: vị trí **0.044904 m**, vận tốc **0.027907 m/s**, yaw **0.039232 rad**. Chênh lệch elapsed lớn nhất **1.392 s**, quãng đường **3.163967 m**, dù outcome các arm đều giống nhau trên suite này. Các maximum không nhất thiết thuộc cùng một case.

Log Robot tại thời điểm nhận reset cho thấy:

- Cold và slot đầu của warm: motor target velocity đều 0 rad/s trước reset controller.
- Slot thứ hai của warm: motor targets còn khoảng **489.998–500.477 rad/s**. Stabilizer targets được reset về None, nhưng lệnh motor chỉ được đặt zero khi khởi tạo Robot adapter, không trong reset handler kế tiếp.
- Trước mission, altitude target của stabilizer ở slot đầu khoảng **1.492466–1.492493 m**, slot thứ hai khoảng **1.500000 m**. Đây là state đo/điều khiển được ghi riêng, không cấp thêm cho navigation.

Như vậy warm không đưa hai arm về cùng bootstrap actuator/state tại thời điểm reset; cold khởi động lại process đã loại chênh lệch này tới precision gate trên 12 case. Đây là một cơ chế khác khởi tạo đo được và phù hợp luồng code. Chưa xác định riêng nó gây mọi khác biệt đường đi hoặc mọi DATA-03/04 failure; cold thay nhiều thành phần khởi tạo cùng lúc. Warm vẫn nằm trong tolerance protocol lịch sử, nên không sửa hoặc phủ nhận báo cáo cũ.

## Bằng chứng, integrity và tái hiện

[JSON evidence](2026-10-30-initialization-aa.json) giữ full summary, init ranges, source, raw hashes và giới hạn. Raw result SHA-256: `589a2abddd6c5822a6460425cc45a8f14cfb7814adfa0300f1c8e64b01899873`. Local review SHA-256: `890b081c3be390d2283831ff3bed37c1f500a8644db4e787079e62aa66a3d32f`; dữ liệu JSON và byte output khớp CI.

Runtime inventory A/A: **77 file**, digest `27455c9272b0956ece199612df2fbd34986d2f99a919f8a6ebd44c9b78c2be4d`. Inventory v3/v4/DATA-03/DATA-04 và bốn khóa cũ giữ nguyên. Artifact GitHub `12914948272`, 60419162 B, digest archive do GitHub cung cấp `162e1ab3b708b5e218b7fdab4f7474a0ecb8ac942d03ace640333beec9b6223f`; không tính lại digest ZIP tại local. Reviewer tính lại hash từng raw file theo manifest.

Checkout chính có thay đổi menu lệnh độc lập chưa commit. Để giữ chúng, local review dùng detached worktree riêng ở source `97be9a0`; không reset/stash/clean hoặc thay code để bỏ clean-source gate. Trên checkout sạch đúng source, materialize fixture rồi review artifact:

```bash
python3 tools/build_initialization_aa.py
python3 tools/review_initialization_aa.py artifacts/aa-ci-40911479243/initialization-aa \
  --expected-source 97be9a0c6882dddd5e7ca58c17bf75ddd6182bf5 \
  --output artifacts/aa-local-review-new.json
```

Không cần chạy lại Webots để review. CI dùng Python 3.12; local review dùng Python workspace và giữ log môi trường riêng. Đây không phải nghiệm thu GUI/manual trên laptop.

## Bước tiếp theo và giới hạn

Đã qua bước B khởi tạo của [0018](../plans/0018-retention-study-proposal.md). Nghiên cứu retention tiếp nên đăng ký cold-isolated cho cả hai arm, v4 full-history làm đối chứng trực tiếp, cùng accounting/budget map, rồi chốt một candidate/metric/ngưỡng trước implementation và đánh giá. Chưa chọn TTL/window hoặc hạ threshold từ kết quả đã xem. Chưa chạy C–F, train, radar, hardware hoặc v3 test; các phần đó không được đánh dấu hoàn thành vì A/A đạt.
