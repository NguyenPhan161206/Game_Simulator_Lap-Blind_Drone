# Protocol v3 — giảm nhịp thu nhận range trên mapped cố định

Ngày đăng ký thiết kế: 2026-10-27. [ADR 0006](../decisions/0006-range-cadence-protocol-v3.md), [kế hoạch](../plans/0010-research-protocol-v3.md), [config số học](../../configs/experiments/range_cadence_v3.toml), [nguồn chính](../research/2026-10-27-range-cadence-related-work.md).

**Trạng thái:** thiết kế và case generation có thể kiểm chứng bằng Python; runtime v3 chưa triển khai và chưa được phép evaluation. Không có kết quả Webots v3, không có model đã train. Khóa thiết kế không thay khóa mã chạy.

## 1. Câu hỏi, giả thuyết và miền suy luận — EXP-01/03

Một drone bay ngang ở độ cao mục tiêu 1.5 m, tới goal được cấp trong scene tĩnh chưa biết bố trí, với range hình học lý tưởng và định vị lý tưởng. Hỗn hợp năm family: empty, single_block, staggered_blocks, narrow_gap, u_trap; blocked_goal là negative control riêng. Arena, body/physics/devices theo lab v1, planner/guard/map theo mapped v2. Không mở rộng sang obstacle động, nhiễu, radar vật lý, bay tránh 3D, giao hàng, fleet hoặc phần cứng.

Giả thuyết có thể bác bỏ: **đổi duy nhất acquisition period 32 → 64 ms giảm ít nhất 50% rate mẫu/payload range, đồng thời candidate đạt mọi gate chất lượng/tài nguyên đã đặt trước so với reference.** Nếu bất kỳ gate nào hỏng: không đạt thiết kế này. Nếu thiếu bằng chứng/infrastructure không khôi phục được: chưa kết luận. Không tiếp tục thử model để cứu giả thuyết trong cùng protocol.

## 2. Arms, controls và budget — EXP-05/06

| Thành phần | Reference | Candidate |
|---|---|---|
| Policy | mapped v2 và cùng config | như reference |
| 10 range: 8 ngang + lên/xuống, 8 m, noise/latency=0 | acquisition mỗi 32 ms | acquisition mỗi 64 ms |
| Pose GPS/IMU/Gyro | 32 ms | 32 ms |
| Physics/control tick; freshness range | 16 ms; 120 ms | như reference |
| Navigation speed / yaw scan | 0.4 m/s / 0.35 rad/s | như reference |
| Initial scan / replan | 2.5 s / 0.5 s | như reference |
| Actuation command limits | ngang 0.8 m/s, dọc 0.4 m/s, yaw 0.5 rad/s | như reference |
| Grid / search budget | 16000 cells / 20000 expansions mỗi plan | như reference |
| Process controller RSS | tối đa 512 MiB | như reference |

Giữ toàn bộ tham số grid/guard/điều khiển, sensor origins, geometry, start/goal/yaw, warmup 2 s, device order, phiên bản Webots R2025a và seeds bằng nhau theo cặp. Không đổi cadence của pose theo range. Reference mới vẫn phải đo chất lượng; kết quả v2 không bảo đảm reference đạt trên v3.

Khi triển khai, lấy mẫu trên thiết bị `enable(period)` và ghi `getSamplingPeriod()`, thời điểm acquisition đầu tiên và lịch thực tế. Không tạo dữ liệu giả bằng đọc ray mỗi 32 ms rồi bỏ một nửa. Cùng packet ở nhiều control tick không là mẫu sensor mới. Không gắn timestamp control mới cho phép đo cũ. State để chiếu ray lên world phải khớp thời điểm acquisition, không dùng pose mới cho ray cũ. Không đọc scene để điền khoảng trống; ground truth chỉ thuộc supervisor/evaluator/observer.

## 3. Đo dữ liệu, thời gian và đường đi — EXP-04/05

Báo bốn tầng riêng: (1) sensor acquisition, (2) observation/policy reads, (3) state map/history trong bộ nhớ, (4) payload/log lưu hoặc truyền thực tế. Không lấy cell count làm byte RAM; đo controller RSS, Webots RSS riêng, môi trường/CPU/OS/Python/Webots/version và hardware được ghi.

Encoding range chuẩn để so sánh: little-endian `<dIHH10d`: timestamp float64 8 B, sequence uint32 4 B, valid mask uint16 2 B, at-limit mask uint16 2 B, 10 distance float64 80 B = **96 B/packet**. Thứ tự ray cố định như NavigationObservation; metadata frame/units/sensor origins/version một lần phải ghi kích thước riêng. Đây là payload chuẩn hóa, không tự là byte network hoặc định dạng hardware. Byte JSON/file thực tế phải đo riêng; pose/mission/command không bị nhập vào tuyên bố giảm 50% range. Mẫu invalid vẫn tốn acquisition/byte, không được bỏ để làm đẹp số.

Rate theo mỗi lượt: `10*(N-1)/(last_acquisition_time-first_acquisition_time)` và `96*(N-1)/dt`, N là packet duy nhất trong cửa sổ chấm, N≥2; kiểm tra từng inter-arrival và đủ acquisition theo lịch, không chỉ timestamp hai đầu. Ref danh định 312.5 values/s và 3000 B/s; candidate 156.25 và 1500. Sai số so sánh số học 1e-9 tương đối. Cả hai lượt phải có rate và valid đủ để tính; thiếu dữ liệu không được coi là đạt. Count/byte toàn lượt và riêng warmup cũng được báo, kể cả failure. Không hứa tổng byte nhiệm vụ giảm đúng 50% nếu candidate bay lâu hơn.

Thời gian nhiệm vụ tính theo simulation time sau warmup, không theo wall clock. Path là tổng độ dài 3D giữa mọi pose đánh giá liên tiếp ở tick 16 ms từ lúc bắt đầu chấm đến outcome; không dùng trajectory đã downsample để tính lại path. Witness length chỉ là đường chứng chỉ khả thi, không là đường tối ưu, không đưa policy và không dùng làm mẫu số SPL tối ưu.

## 4. Gates chất lượng và cách chọn cấu hình — EXP-04/09

Một lượt success: cách goal ≤0.5 m, tốc độ 3D ≤0.18 m/s liên tục ≥1 s, hoàn tất trước hoặc đúng 90 s, không contact/out-of-bounds. Bounds ENU: x/y ±9.5 m, z 0.4..5 m. Thứ tự khi cùng tick: collision → bounds → success trong deadline → timeout. Thời hạn 90 s là simulation deadline, không là hard realtime CPU.

Mỗi case có 2 repeat/arm. Collapse case: success chỉ nếu cả 2 success; collision/bounds nếu bất kỳ repeat vi phạm; path/time/CPU/RSS lấy giá trị lớn hơn của hai repeat cho tính gate; giữ bảng từng repeat. Repeat để kiểm tra tái lập, không tăng n thống kê. Nếu outcome lặp khác nhau, giữ cả hai, dùng quy tắc bảo thủ trên và phân tích độ lệch.

Candidate chỉ đạt khi đồng thời:

1. Reference và candidate đều ≥95% case success trong tập feasible; không observed collision hoặc out-of-bounds ở bất kỳ repeat nào, kể cả negative controls. Negative không được success; timeout không collision là outcome chấp nhận cho negative, không là success nhiệm vụ.
2. Gọi adverse là case reference success nhưng candidate không success. Upper confidence bound một phía 95% Clopper–Pearson cho xác suất adverse ≤0.05. Vì `P(ref success)-P(candidate success) ≤ P(adverse)`, đây là gate bảo thủ cho margin 5 điểm phần trăm, không bù mất ca bằng các ca được thêm. Báo thêm bảng paired 2×2 và chênh lệch success quan sát.
3. Rate range và payload candidate ≤50% reference trên **mọi** case/repeat có cặp hợp lệ; không chỉ mean đẹp. Khi failure ngắn không đủ 2 mẫu, gate chưa được chứng minh và nghiên cứu không đạt, không loại case. Tổng acquisition/byte vẫn báo đầy đủ.
4. Trên common-success cases, tỷ số tổng path candidate/reference ≤1.10. Đồng thời tỷ số mean time và path có penalty trên **mọi feasible case** đều ≤1.10: fail nhận 90 s và 72 m; success dùng elapsed và `min(path,72)` m. Penalty 72=0.8×90 là quy ước điểm số, không là chứng minh giới hạn vật lý. Báo riêng common-success time/path và failure để tránh survival bias.
5. Map/search/RSS không vượt budget; p95 decision CPU candidate/reference ≤1.10 trên cùng host. Tính p95 nearest-rank trong từng repeat; lấy max repeat mỗi case, rồi tỷ số tổng các p95 case giữa arms, không dùng hai máy khác nhau để xét gate. Báo mean/p95/max, số tick vượt 16 ms và wall/sim riêng; vượt tick không bị gọi infrastructure, không được tuyên bố realtime từ gate tương đối.

Chỉ có **một** candidate 64 ms được chọn trước dữ liệu. Development chỉ sửa implementation để khớp thiết kế. Validation áp dụng toàn bộ gate; nếu không đạt thì dừng, báo âm, giữ test chưa chạy. Nếu đạt thì khóa provenance/không chỉnh gì và chạy test một lần. Test lặp cùng protocol chỉ tái lập, không làm mới độ unseen. Mọi thay đổi thiết kế/candidate sau exposure cần version/test mới; không thử 96 ms rồi chọn bằng cùng test.

## 5. Số case, seeds, nguồn và provenance — EXP-07/08/09

| Split | Feasible | Negative | Cases | Lượt 2 arms × 2 repeats |
|---|---:|---:|---:|---:|
| train | 50 | 10 | 60 | 0: dự trữ, chưa train |
| development | 50 | 10 | 60 | tối đa 240 mỗi vòng debug, mọi vòng ghi ledger |
| validation | 100 | 20 | 120 | 480, chỉ sau runtime freeze |
| test | 200 | 40 | 240 | 960, chỉ nếu validation đạt |

Generator tái sử dụng hàm frozen `generate_case` v1, với seed mới riêng từng case, không chung seed giữa family/split. Feasible family được chọn từ hash namespace v3 (uniform modulo 5, sai lệch modulo 2^256 không đáng kể), không cưỡng ép cân bằng hoặc đổi seed để có ca dễ. Estimand là hỗn hợp năm family cùng trọng số theo cơ chế sinh; đây là pseudo-random sampling, không là mẫu drone/địa hình thật. Báo count/outcome từng family. Không gọi scene cùng generator là OOD.

Đơn vị phân tích độc lập là case seed mới, không là ray/tick/repeat. Confidence bound dựa trên giả định case là các draw độc lập của hỗn hợp đã khai báo; kết luận giới hạn trong generator này. Với n=200 và không adverse, upper bound ≈1.49%; đây là minh họa độ phân giải, không là power guarantee hoặc kết quả thực nghiệm. Cấu hình không đạt bound phải báo không đủ bằng chứng/không đạt, không tăng n sau khi xem số.

Mọi geometry (start/goal/obstacles) phải khác toàn bộ v1/v2 và mọi split v3. Kiểm thêm fingerprint bất biến tịnh tiến/quay bội 90°/đối xứng để tránh cùng nhiệm vụ chỉ đổi hướng/vị trí. Cùng family/topology vẫn có thể tương tự; test không kiểm nghiệm family mới. Chứng chỉ feasible là đường ngang có hull margin; negative có goal nằm trong solid. Không tìm được witness không là chứng minh bất khả thi: dừng generation audit, không tự bỏ/reseed case.

Công cụ sinh **tất cả** case/chứng chỉ vào artifacts ignored. Chỉ commit index gồm ID/split/seed/family/hash/certificate kind và hash nội dung toàn case; không commit witness/coordinates. Index và generator công khai để tái lập, không bí mật mật mã. Exposure phân biệt kiểm tra máy/hashes, xem geometry và xem outcome; công khai seed không được gọi là bảo mật held-out. Tập mới nghĩa là không trùng geometry, chưa dùng outcome để tune; không bảo đảm mọi người ngoài dự án chưa từng sinh/xem nó.

## 6. Hợp lệ, lỗi và lịch chạy — EXP-09/10

- **Algorithm outcome hợp lệ:** success/collision/bounds/timeout với provenance đúng, đủ log/acquisition/evaluator. Timeout, stale stop, grid/search budget hết hoặc không tìm ra đường là failure thuật toán; không được loại vì khó. Controller exception/OOM từ code hoặc vượt tài nguyên của arm cũng là algorithm failure, giữ trong mẫu số; ghi nguyên nhân, không retry để tìm lượt tốt.
- **Negative:** chỉ case được generator chứng minh goal trong solid; giữ riêng mẫu số. Không đổi label feasible thành negative vì baseline thất bại.
- **Infrastructure:** sai executable/world/source, loader/display failure, process Webots hỏng do host, mất log do filesystem/transport, can thiệp pause/reset, watchdog do gián đoạn host có bằng chứng. Ghi raw evidence và lý do reviewer, không tự coi mọi crash/watchdog là infra. Không rõ nguyên nhân: unresolved, chặn kết luận chứ không loại.
- **Retry:** tối đa 1 lần cho cả pair của repeat bị infra, cùng seed/source/config và order; lưu mọi attempt. Nếu không khôi phục được đủ pair, báo nghiên cứu incomplete, không thay case hoặc tính success trên phần còn lại. Việc lặp debug development không được xóa lịch sử exposure.
- **Lịch:** một Webots mỗi lần. Hai arm liền nhau, thứ tự repeat đầu theo parity SHA256(case ID); repeat hai đảo thứ tự. Không chạy telemetry GUI/movement/reset hoặc đổi simulation speed giữa pair. Cùng CPU affinity/profile khi có; lưu host load và mọi khác biệt. Warmup/evaluator/collector phải giống nhau. Simulation rate có thể fast, chưa phải chứng minh phản hồi desktop hoặc deadline thiết bị.
- **Báo cáo:** mọi case/repeat/attempt với source SHA, design/runtime lock hashes, arm, seed, Webots/binary/config/environment hashes, acquisition counts, outcome, time/path, resource và lý do loại infra. Bảng feasible, negative, lỗi, retries riêng; raw output ở artifacts, nghiên cứu nhỏ được review trong docs/research. Không chỉ báo ca thành công.

## 7. Khóa, exposure và điều kiện triển khai — EXP-07/11/12

[Design lock](../../configs/scenarios/protocol_v3.design.lock.json) ghim config/protocol/ADR/generator/checker/statistics và index; kiểm v1/v2 lock trước. [Exposure ledger](../../configs/scenarios/exposure_v3.json) ban đầu ghi nguồn cũ đã exposed; agent/generator đã đọc spec và metadata/kiểm geometry bằng chương trình; không có navigation v3 chạy, không có outcome mới. Ledger append-only qua commit, không là hash thiết kế bất biến vì cần ghi exposure mới. Mỗi event ghi actor, source, split, nội dung đã xem, mục đích, thời gian và kết quả lựa chọn. Không copy nhãn unseen từ v1/v2.

Trước mỗi vòng debug/validation/test: ghi event ý định; sau chạy ghi đúng run path/source/outcome exposure, kể cả thất bại. Validation/test không dùng để tune. Nếu con người/agent xem geometry hoặc outcome ngoài kế hoạch, ghi ngay, đánh giá contamination và dùng version/test mới khi cần. Hash/metadata check tự động không là outcome exposure, nhưng phải ghi là automated geometry access.

Gate để sang **triển khai mốc 7A**, chưa sang test: đủ EXP-01–12 và kiểm tra thiết kế đạt. Việc còn bắt buộc trước evaluation: adapter v3 thật với timestamp acquisition/pose đúng, accounting các tầng, evaluator/aggregator và retry runner theo protocol; test hành vi và Webots development xác minh chỉ một biến thay đổi; kiểm kê dependency toàn bộ code/config/world/entrypoint và khóa runtime nguồn chính xác. Runtime lock là artifact mới tham chiếu design lock, không ghi đè file khóa thiết kế. Mọi held-out runner phải từ chối nếu thiếu/sai một trong hai khóa. Tool mốc 6 luôn từ chối `--evaluate` vì chưa có runtime; đây là guard, không là evaluator đã triển khai.
