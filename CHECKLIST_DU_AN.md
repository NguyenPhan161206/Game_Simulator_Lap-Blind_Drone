# Checklist tổng thể — Blind Drone Lab

**Cập nhật:** 2026-10-29, múi giờ Asia/Ho_Chi_Minh.

**Mốc repo được đối chiếu:** thiết kế v3 `761318df1293c195347f486b0d228f88af10fae1`; runtime cadence v3 `0c75ce28f14b8ea881e8c0c7c9335aa4319030c5`, validation `0c5f598c512a24db63b0fd19ca259a3b85382ee5`; nghiệm thu GUI/manual lịch sử vẫn là `39c34af`. Mốc checklist gốc `d7018cb` được giữ trong lịch sử.
**Audit bổ sung nhánh L/GitHub:** source collector `b32410595b26f8ef2d0f8d99dca469797278366b`; xem [cây phiên bản](docs/version-history.md) và evidence liên kết ở mục 8.
**Mục đích:** theo dõi từ ý tưởng ban đầu, các phần đã triển khai/kiểm chứng, phần còn mở và roadmap tương lai trong một file.

## Cách đọc và cập nhật

- `[x]`: hoàn thành đúng phạm vi câu đó; không tự suy rộng sang phần cứng, môi trường mới hoặc chất lượng sản phẩm.
- `[ ]`: chưa thực hiện, chưa có bằng chứng đủ, hoặc là bước tương lai.
- **Đã thống nhất** là quyết định về hướng đi; **đã triển khai** là đã có mã; **đã kiểm chứng CI** là đã chạy simulator thật trên CI. Ba trạng thái không đồng nhất.
- Mục tương lai là **roadmap đề xuất**, chưa phải mọi thông số/thuật toán đều đã được chấp nhận. Không mặc định phải làm tất cả nhánh.
- Mỗi khi đánh dấu xong: thêm nguồn bằng chứng, source commit/config/seed và giới hạn nếu liên quan. Không chỉ đánh dấu vì file hoặc thư mục đã tồn tại.
- Giữ kết quả xấu; không đổi tiêu chí sau khi thấy test để biến thất bại thành thành công.
- File này là sổ theo dõi thủ công; trạng thái không tự cập nhật theo CI. Các báo cáo/JSON và protocol lock là nguồn đối chiếu chi tiết.

## 1. Bản đồ giai đoạn

| Mốc | Nội dung | Trạng thái tại ngày cập nhật | Điều kiện để coi là hoàn thành |
|---|---|---|---|
| 0 | Làm rõ ý tưởng, phạm vi, nguyên tắc thông tin | Đã thống nhất và ghi lại | Có bản ghi quyết định, phân biệt yêu cầu với đề xuất |
| 1 | Kiến trúc, cây thư mục, cấu hình agent/Git | Đã triển khai | Repo có cấu trúc, hợp đồng, hướng dẫn và kiểm tra scaffold |
| 2 | World, drone thủ công, cảm biến, collision/reset | Đã kiểm chứng CI | Webots thật chạy chuỗi kiểm tra; GUI local báo riêng |
| 3 | Baseline navigation và evaluator | Đã kiểm chứng CI | Đến đích/dừng/dwell/failure được chấm đúng, có đối chứng |
| 4 | Môi trường theo seed và protocol v1 | Đã kiểm chứng CI | Case khả thi có witness, split/lock rõ, mọi outcome được giữ |
| 5 | Quan sát có bộ nhớ, guard, planner v2 | Đã kiểm chứng CI | Khóa trước fresh evaluation, đủ 108 lượt, có chi phí/giới hạn |
| L | Hoàn tất trải nghiệm local | Đã nghiệm thu LOC-01–09 | Mở GUI và chạy thật trên máy người dùng, lưu bằng chứng riêng |
| 6 | Khóa câu hỏi nghiên cứu và protocol tiếp theo | Thiết kế v3 giữ nguyên; runtime được bổ sung ở 7A | Có quyết định, ngưỡng chất lượng, dữ liệu và test mới |
| 7A | Khảo sát giảm dữ liệu/biểu diễn | V3 kết thúc âm (validation 87/100); DATA-03 occupied-only development 67/74 so với reference 62/74; test v3 chưa mở | Mỗi cấu hình cần study/source riêng và quality assessment; DATA-03 chưa held-out/chưa có quality-selection threshold |
| 7A-D | Chẩn đoán kẹt đoạn đầu trên development | Hoàn tất offline 5 trace, 141 unit tests; chưa sửa thuật toán | [Nguyên nhân origin/cell alignment](docs/research/2026-10-28-navigation-start-diagnostics.md); không là flight evaluation mới |
| 7A-N4 | GOAL-23: đường thay thế qua vùng đã quan sát | Hoàn tất development v4: 165 tests, 352 episode, 74/74 feasible case | [Nguồn `9503c2c`, raw audit/CI](docs/research/2026-10-28-observed-detour-v4.md); chưa held-out/hardware, CPU tăng |
| 7B | Huấn luyện model nếu phù hợp câu hỏi | Chưa làm, nhánh tùy chọn | Train/eval không rò rỉ, tái lập, so sánh với baseline |
| 8 | Độ vững, cảm biến không lý tưởng, điều hướng khó hơn | Chưa làm | Có protocol và đánh giá riêng cho từng mở rộng |
| 9 | Giao diện giải thích/replay như game | Có observer cơ bản; còn mở rộng | Phân biệt live/replay và dữ liệu drone/ground truth |
| 10 | Đánh giá bảo vệ thông tin | Mới có nguyên tắc và ranh giới code | Có threat model và phép đo, không suy từ việc bỏ camera |
| 11 | Một chuyến giao hàng hoàn chỉnh, mức D | Chưa làm | Hoàn thành state machine nhiệm vụ và failure handling |
| 12 | Điều phối logistics, mức E | Chưa làm | Có đơn hàng, baseline và KPI vận hành riêng |
| 13 | Xe, radar vật lý, Unity hoặc phần cứng | Hướng mở rộng có điều kiện | Có nhu cầu, nguồn lực, mô hình và kiểm chứng tương ứng |

**Điểm đứng hiện tại:** đã có reference navigation không học và một thử nghiệm DATA-03 trong mô phỏng lý tưởng. Occupied-only đạt 67/74 so với reference 62/74 trên development đã exposed, nhưng common-success time/path và CPU tăng; RSS chỉ giảm nhẹ. Chưa có held-out selection. Chưa ANN/RL, chưa chứng minh tối thiểu dữ liệu, riêng tư, an toàn tổng quát hoặc khả năng triển khai ngoài đời.

## 2. Mốc 0 — ý tưởng và các quyết định gốc

Nguồn: [bản ghi trao đổi](docs/01-y-tuong-va-quyet-dinh.md), [ADR nền tảng](docs/decisions/0001-foundation.md). Các mục dưới đây ghi quyết định, không phải năng lực đã thực nghiệm ngoài đời.

- [x] IDEA-01 — Xác định phòng lab phục vụ mô phỏng phương tiện giao hàng và nghiên cứu sử dụng thông tin cảm biến tiết kiệm.
- [x] IDEA-02 — Làm rõ runtime không dùng ảnh camera/vision làm đầu vào điều hướng.
- [x] IDEA-03 — Phân biệt hình ảnh observer cho con người với camera input của drone.
- [x] IDEA-04 — Cho phép khảo sát camera hỗ trợ thu dữ liệu/huấn luyện ở nhánh riêng; chưa chọn phương pháp cụ thể.
- [x] IDEA-05 — Cho phép dùng các nguồn đo không camera và định vị được khai báo, ví dụ GPS.
- [x] IDEA-06 — Ưu tiên drone trước, xe sau; core phương tiện trước logistics.
- [x] IDEA-07 — Xác định giai đoạn hiện tại chỉ trong simulation; chưa thực nghiệm phần cứng.
- [x] IDEA-08 — Chọn mức B: một drone đến đích được cấp, tránh vật cản tĩnh trong môi trường chưa biết đầy đủ.
- [x] IDEA-09 — Phân biệt giảm số phép đo, giảm đầu vào model, giảm truyền/lưu và giảm thông tin nhạy cảm có thể suy ra.
- [x] IDEA-10 — Ghi nhận không camera không tự chứng minh bảo vệ mọi thông tin; grid/GPS vẫn có thể chứa thông tin bố trí/vị trí.
- [x] IDEA-11 — Chấp nhận khảo sát Webots trước; giữ Unity là phương án có thể xem lại, không tự chuyển engine.
- [x] IDEA-12 — Ghi lại phân tích Snake_ANN và bài học về quan sát cục bộ, A* và nguy cơ dùng toàn bản đồ.
- [x] IDEA-13 — Giữ giới hạn bằng chứng Snake_ANN: đó là kiểm tra nguồn/hành vi được ghi trong cuộc trao đổi, chưa tái huấn luyện hoặc tái lập hiệu năng model.
- [x] IDEA-14 — Không gọi cửa sổ game/range hình học là mô phỏng radar vật lý.

**Điều kiện duy trì:** thay đổi quan trọng phải ghi ADR hoặc cập nhật bản ghi; không biến ý tưởng tùy chọn thành quyết định đã thống nhất.

## 3. Mốc 1 — kiến trúc, repo và agent

Nguồn: [kiến trúc](docs/architecture/system.md), [hợp đồng dữ liệu](docs/architecture/data-contracts.md), [cây repo](docs/architecture/repository.md), [hướng dẫn agent](agents/README.md). Scaffold chính: `c319ec2`.

- [x] FND-01 — Tạo repo và cây thư mục theo các module: contracts, world, vehicle, sensors, observation, navigation, control, evaluation, experiments, visualization, adapter và training.
- [x] FND-02 — Tách Python core khỏi API Webots; simulator giữ thẩm quyền trạng thái vật lý.
- [x] FND-03 — Tách drone controller thường với supervisor tạo/reset/chấm/observer.
- [x] FND-04 — Khai báo đơn vị, hệ tọa độ, timestamp, validity và nguồn đo trong hợp đồng.
- [x] FND-05 — Quy định không đưa toàn scene, nhãn vật thể, witness hoặc đường oracle vào navigation runtime.
- [x] FND-06 — Tạo TOML cấu hình, README trách nhiệm module và ADR.
- [x] FND-07 — Giữ preset nghiên cứu chưa chốt ở trạng thái draft/non-runnable; tách preset kỹ thuật chạy được.
- [x] FND-08 — Tạo AGENTS.md chung và entry point cho Codex/Claude/Gemini/Copilot.
- [x] FND-09 — Tạo cấu hình Codex di động và launcher; không thay cấu hình/quyền toàn máy.
- [x] FND-10 — Tạo kiểm tra scaffold, TOML và link nội bộ.
- [x] FND-11 — Tạo cơ chế Git cho workspace managed qua tools/git.sh và metadata cục bộ khi cần.
- [x] FND-12 — Ghi nguồn/giấy phép thành phần ngoài, giữ credential/model/raw artifact lớn ngoài Git.
- [x] FND-13 — Ghi quyền thường trực tự commit/push theo milestone hợp lý trong AGENTS.md, commit `ec9a40f`.
- [x] FND-14 — Push các mốc đã hoàn thành lên repo được chỉ định, giữ source SHA của từng đợt kiểm chứng.

**Điều kiện duy trì:** thư mục tồn tại không đồng nghĩa module đã có runtime; đọc README/bằng chứng của từng module trước khi dùng.

## 4. Mốc 2 — bãi thử Webots tối thiểu

Nguồn: [kế hoạch 0002](docs/plans/0002-webots-minimal-lab.md), [hướng dẫn lab](docs/lab-v1.md), [báo cáo môi trường](docs/research/2026-10-25-webots-v1-smoke.md). Bản bàn giao: `686681f`.

- [x] LAB-01 — Ghim Webots R2025a và có installer trong .local/ của workspace.
- [x] LAB-02 — Tạo world primitive 20×20 m, mặt đất, tường, ba vật cản và vùng đích.
- [x] LAB-03 — Tạo thân drone, khối lượng/quán tính, bốn propeller và collision hull.
- [x] LAB-04 — Khai báo ENU cho world và FLU cho thân, sử dụng mét/giây/radian.
- [x] LAB-05 — Triển khai stabilizer và lệnh vận tốc thủ công có giới hạn.
- [x] LAB-06 — Có mapping bàn phím tiến/lùi, ngang, lên/xuống, yaw, dừng và reset.
- [x] LAB-07 — Gắn 8 ray ngang + 2 ray đứng, range tối đa 8 m; GPS/tư thế/gyro lý tưởng.
- [x] LAB-08 — Ghi chu kỳ vật lý/control 16 ms, range 32 ms và phân biệt at_limit với dữ liệu lỗi.
- [x] LAB-09 — Kiểm chứng hover, tiến, phanh, ngang, yaw, tăng độ cao trên Webots CI.
- [x] LAB-10 — Kiểm chứng số đo fixture, bề mặt gần nhất và vật cản bị che khuất.
- [x] LAB-11 — Kiểm chứng contact vật lý đúng vùng vật cản; reset xóa trạng thái/contact.
- [x] LAB-12 — Có telemetry, result/progress JSON, console và ảnh observer.
- [x] LAB-13 — Sửa dấu/authority actuator và hướng observer; đã xem ảnh CI đúng bãi thử.
- [x] LAB-14 — Chạy 12 mục smoke trên simulator thật, không dùng stub để báo đạt.
- [x] LAB-15 — Ghi rõ actuator chưa hiệu chỉnh theo motor thật, collision mới xét hộp thân, không phải rotor/khí động/pin đầy đủ.

**Gate đã qua:** môi trường và điều khiển cơ bản chạy được trên CI. Việc thao tác GUI/bàn phím local nằm ở mục 8, chưa đánh dấu hoàn thành.

## 5. Mốc 3 — baseline navigation và evaluator v1

Nguồn: [kế hoạch 0003](docs/plans/0003-navigation-baseline.md), [hướng dẫn](docs/navigation-v1.md), [báo cáo](docs/research/2026-10-26-navigation-v1.md). Bàn giao: `555f59f`.

- [x] NAV1-01 — Có VehicleState, MotionCommand, NavigationObservation, RangeReading và mission có whitelist.
- [x] NAV1-02 — Triển khai direct tới đích và reactive tiếp tuyến trái không học.
- [x] NAV1-03 — Chuyển hướng đích ENU sang lệnh FLU; kiểm tra dữ liệu thiếu/cũ/sai frame/không hữu hạn.
- [x] NAV1-04 — Tách mission do supervisor cấp với velocity command do drone tự tạo.
- [x] NAV1-05 — Chấm success bằng vùng đích + tốc độ thấp + dwell liên tục; bay xuyên vùng đích quá nhanh không được tính đạt.
- [x] NAV1-06 — Chấm collision/bounds/deadline với thứ tự ưu tiên rõ, giữ kết quả terminal.
- [x] NAV1-07 — Ghi thời gian, quãng đường 3D, khoảng cách cuối/gần nhất, tốc độ và contact kể cả lượt thất bại.
- [x] NAV1-08 — Có ca trống, một khối, hai khối lệch và goal trong solid làm đối chứng âm.
- [x] NAV1-09 — Chạy ghép cặp tám lượt Webots; direct 1/3 và reactive 3/3 ca khả thi trong bộ diagnostic đó.
- [x] NAV1-10 — Tách đối chứng âm khỏi tỷ lệ thành công của ca khả thi.
- [x] NAV1-11 — Kiểm chứng 29 unit test ở mốc này và giữ smoke môi trường đạt.
- [x] NAV1-12 — Ghi rõ diagnostic công khai không phải held-out test hoặc kết quả ML.

## 6. Mốc 4 — generator, split và protocol v1

Nguồn: [kế hoạch 0004](docs/plans/0004-seeded-environments.md), [suite v1](docs/seeded-environments-v1.md), [báo cáo](docs/research/2026-10-26-seeded-environments.md). Bàn giao: `2568f07`.

- [x] SPL1-01 — Sinh case tái lập theo family/seed/tham số, có fingerprint geometry.
- [x] SPL1-02 — Có sáu family: empty, single_block, staggered_blocks, narrow_gap, u_trap, blocked_goal.
- [x] SPL1-03 — Thay start/goal, geometry, tịnh tiến/phản chiếu/quay world và yaw đầu.
- [x] SPL1-04 — Kiểm chứng ca khả thi bằng grid witness cho hull bảo thủ, kiểm tra cả đoạn chéo/cắt góc.
- [x] SPL1-05 — Không dùng grid search thất bại để tự kết luận vô nghiệm; ca âm có goal ball trong solid.
- [x] SPL1-06 — Giữ witness ở generator/evaluation, không cấp cho navigation.
- [x] SPL1-07 — Tạo 36 case: train_reserved 12, development 12, validation 6, test 6.
- [x] SPL1-08 — Kiểm tra seed/geometry không trùng và khóa code/config/manifest trước đánh giá.
- [x] SPL1-09 — Chạy đủ 48 lượt paired trên 24 case được đánh giá; 12 train_reserved chưa được dùng để train.
- [x] SPL1-10 — Kiểm tra thiếu/trùng case, source/protocol sai, pose đầu sai và summary bỏ failure.
- [x] SPL1-11 — Lưu 42 unit test đạt ở mốc này cùng regression Webots.
- [x] SPL1-12 — Ghi reactive development 8/10, validation 4/5, test 5/5; giữ ba U collision.
- [x] SPL1-13 — Đọc trace để phát hiện narrow-gap success có thể là đi vòng ngoài, không phải xuyên khe.
- [x] SPL1-14 — Đánh dấu v1 validation/test đã exposed sau khi đọc; không dùng lại như unseen khi tune.

## 7. Mốc 5 — quan sát có bộ nhớ và điều hướng v2

Nguồn: [kế hoạch 0005](docs/plans/0005-observation-and-navigation-v2.md), [hướng dẫn v2](docs/navigation-v2.md), [chẩn đoán](docs/research/2026-10-26-v2-diagnostics.md), [báo cáo chính thức](docs/research/2026-10-26-navigation-v2.md). Bàn giao: `d7018cb`; runtime kiểm chứng: `2f422e2`.

- [x] NAV2-01 — Phân tích U failure bằng snapshot có timestamp, command và contact; không gán nguyên nhân duy nhất từ vài ca.
- [x] NAV2-02 — Giữ nguyên v1 lock/runtime; tạo adapter/world/launcher/protocol v2 cạnh v1.
- [x] NAV2-03 — Chiếu ray bằng RPY và pose đo được, kể cả origin offset của sensor.
- [x] NAV2-04 — Tạo grid hữu hạn, tách free/occupied/unknown; at_limit không tạo vật cản giả.
- [x] NAV2-05 — Chỉ cập nhật map theo mẫu mới, kiểm tra stale/future/invalid trước tạo hành động.
- [x] NAV2-06 — Khai báo giới hạn vùng/budget và giữ trạng thái occupied trong mô hình static/ideal hiện tại.
- [x] NAV2-07 — Thêm quét yaw và lọc lệnh theo điểm đã đo, hull và khoảng đáp ứng phanh quy ước.
- [x] NAV2-08 — Thêm A* trên grid tự đo; unknown có cost riêng và không được thực thi như free.
- [x] NAV2-09 — Cache tìm kiếm đã duyệt hết grid; không coi hết budget search là chứng cứ vô nghiệm.
- [x] NAV2-10 — Thêm recovery khi ô hiện tại mới bị inflate; chỉ qua đoạn đã đo và kiểm tra swept disk, không vô hiệu guard.
- [x] NAV2-11 — Phân biệt unit/contract fixture vận tốc tức thời với Webots thật.
- [x] NAV2-12 — So sánh reactive, guarded và mapped; ghi rõ khác biệt tốc độ/quét/memory, không gọi là ablation đơn yếu tố.
- [x] NAV2-13 — Giữ ba pilot development, mỗi pilot 36 lượt, trước khóa; không cộng thành mẫu test độc lập.
- [x] NAV2-14 — Đạt tiêu chí development đã đặt trước rồi mới khóa v2; không sửa runtime sau fresh exposure.
- [x] NAV2-15 — Dùng validation mới 51001/51002 và test mới 61001/61002; không trùng geometry v1/development.
- [x] NAV2-16 — Chạy đủ 108 lượt chính thức, cùng source/lock/manifest; có 64 unit test đạt.
- [x] NAV2-17 — Ghi số range sample/value, map updates, primary/derived cells, guard/planning decisions và CPU.
- [x] NAV2-18 — Tách public observation khỏi ground truth trong failure snapshot; kiểm tra code path không dùng oracle.
- [x] NAV2-19 — Xem ảnh observer pilot có rendering; không giả ảnh đó là ảnh fresh evaluation không rendering hoặc GUI local.
- [x] NAV2-20 — Lưu đầy đủ outcome, trace review, artifact/CI link và source SHA; recheck integrity JSON trích xuất.
- [x] NAV2-21 — Đánh dấu v2 validation/test đã exposed; thay đổi thuật toán sau này cần protocol/test mới.

### 7.1. Kết quả v2 đã có bằng chứng

| Tập khả thi | Reactive | Guarded | Mapped |
|---|---:|---:|---:|
| Development | 8/10, 2 collision | 10/10, 0 collision | 10/10, 0 collision |
| Validation | 8/10, 2 collision | 10/10, 0 collision | 10/10, 0 collision |
| Test | 8/10, 2 collision | 10/10, 0 collision | 10/10, 0 collision |

- [x] EV-01 — Ghi nhận cả sáu U collision của reactive trong đợt chính thức, không chỉ trình diễn lượt thành công.
- [x] EV-02 — Tách sáu negative control mỗi policy: đều timeout, không false success; chưa có năng lực từ bỏ sớm.
- [x] EV-03 — So time/path guarded và mapped trên cùng 10 success test: 41.184 s/14.380 m và 37.619 s/13.340 m.
- [x] EV-04 — Không so mean reactive n=8 như cùng cohort/tốc độ với hai phương án n=10.
- [x] EV-05 — Ghi max primary cells mọi split: guarded 5277, mapped 5378; không gọi số cell là byte RAM.
- [x] EV-06 — Ghi CPU max mapped 55.957 ms trên toàn đợt, vượt 16 ms physics tick; chưa chứng minh deadline phần cứng.
- [x] EV-07 — Ghi không giảm số ray/cadence trong v2, không tự nhận đã giảm dữ liệu hoặc bảo vệ riêng tư.

**Gate đã qua:** reference navigation chạy trong miền static/ideal/horizontal được thử. Không phải chứng minh an toàn tổng quát, tránh 3D, qua đúng khe, cảm biến radar vật lý hoặc khả năng ngoài đời.

## 8. Nhánh L — hoàn tất chạy và thao tác local

Tách riêng phần này để không đánh đồng CI có simulator với GUI đã chạy trên laptop.

- [x] LOC-01 — Có xác nhận installer tải/extract Webots R2025a vào workspace từ terminal người dùng.
- [x] LOC-02 — Chẩn đoán libGLU.so.1/libsndio.so.7; lần audit sau với bundled library path không còn thiếu dependency.
- [x] LOC-03 — Ghi lần chạy trong phiên managed không kết nối được display :0; không báo đó là chuyến bay local thành công.
- [x] LOC-04 — Mở Webots bằng terminal desktop; phiếu người thao tác xác nhận GUI/world/controller, console và source khớp ở lượt manual 064254.
- [x] LOC-05 — Lượt manual 20261027T020953 có đủ hai chiều của bốn trục, gồm T/G ±0.4 m/s; phiếu xác nhận SPACE/thả phím/R và GUI đúng, không còn warning thiếu phím.
- [x] LOC-06 — Lượt mapped 20261027T022316 trên development-u_trap-s21001 realtime có result success/0 contact; người thao tác xác nhận đã thấy di chuyển và kết thúc.
- [x] LOC-07 — Đã lưu console/result/source/telemetry/trajectory/phiếu và JPG đúng lượt mapped 022316; ảnh đã được xem, hash raw files trong evidence.
- [x] LOC-08 — Cùng protocol/manifest/geometry với CI; success/0 contact, 41.216 s, path +3.421 mm. Motion metrics khớp chính xác lượt laptop trước; giữ delta và giới hạn suy luận.
- [x] LOC-09 — Mapped 46.774846 s wall, CPU mean/max 1.057187/32.586333 ms; hai phiếu smooth/unchanged. Max CPU > tick 16 ms, chưa chứng minh deadline realtime hoặc FPS/input latency.

**Nhánh L hoàn tất 9/9:** [audit cuối và JSON bằng chứng](docs/research/2026-10-27-local-acceptance-complete.md) tại source runtime 39c34af. Hai lượt manual/mapped mới có source sạch, phiếu/telemetry phù hợp và kết thúc bình thường. [Kế hoạch nhánh L](docs/plans/0006-local-acceptance.md), [hướng dẫn nghiệm thu](docs/local-acceptance.md). Các lượt thiếu lệnh/timeout và [audit cũ](docs/research/2026-10-26-local-acceptance.md) được giữ nguyên; CI và desktop là các nguồn bằng chứng riêng.

**Mốc kết nối GitHub đã hoàn tất:** GH-01…14 trong kế hoạch tích hợp; source runtime 39c34af đã qua cả bốn workflow và 82 unit test. [Báo cáo tích hợp lịch sử](docs/research/2026-10-26-github-integration.md). Các nhánh lịch sử giữ nguyên; roadmap nghiên cứu dưới đây còn là các mốc tiếp theo.

**Công cụ tái lập:** lệnh accept vẫn chạy tuần tự và chặn thiếu bằng chứng; manual/mapped riêng đã được review cùng nhau ở mốc hoàn tất này. [Bằng chứng công cụ](docs/research/2026-10-26-sequential-acceptance.md), [audit lượt chưa đạt](docs/research/2026-10-27-local-acceptance-followup.md), [sửa launcher](docs/plans/0009-local-launcher-followup.md). Hai protocol giữ nguyên.

Chạy từ terminal desktop khi Webots đã cài:

```bash
python3 tools/local_session.py accept
```

**Gate đã qua:** có bằng chứng local riêng về GUI/phím/quan sát mapped và số đo; giới hạn mô phỏng/realtime vẫn được ghi trong audit cuối.

## 9. Mốc 6 — khóa câu hỏi nghiên cứu và protocol tiếp theo

Đây là bước chung trước khi sửa baseline, khảo sát giảm dữ liệu hoặc bắt đầu ML. Không tự chọn model/framework chỉ vì đã có thư mục training.

- [x] EXP-01 — Chọn câu hỏi chính có thể bác bỏ bằng thực nghiệm: giảm dữ liệu nào, giữ chất lượng nhiệm vụ ở mức nào, trong miền nào? **Bằng chứng:** [Protocol §1](docs/protocols/range-cadence-v3.md): giảm acquisition rate range ≥50%, margin success 5 điểm phần trăm, miền tĩnh cùng generator.
- [x] EXP-02 — Đối chiếu nghiên cứu liên quan bằng nguồn chính; phân biệt đóng góp ứng dụng, thuật toán, bộ dữ liệu và hạ tầng. **Bằng chứng:** [Đối chiếu sáu nguồn chính và định vị đóng góp](docs/research/2026-10-27-range-cadence-related-work.md); chưa tuyên bố thuật toán mới.
- [x] EXP-03 — Chọn nhánh ưu tiên: giảm thông tin trên baseline, huấn luyện policy, hoặc cả hai theo thí nghiệm tách biệt. **Bằng chứng:** [ADR 0006](docs/decisions/0006-range-cadence-protocol-v3.md): ưu tiên cadence trên mapped; ML nghiên cứu riêng.
- [x] EXP-04 — Khóa success/collision/deadline/path và mức suy giảm chấp nhận trước đánh giá cuối; không lấy 10/10 hiện tại làm bảo đảm chất lượng sản phẩm. **Bằng chứng:** [Config quality](configs/experiments/range_cadence_v3.toml), [protocol §3–4](docs/protocols/range-cadence-v3.md): deadline/dwell, zero observed collision/bounds, path/time penalty và confidence bound đã ghi trước outcome.
- [x] EXP-05 — Xác định cấu hình tham chiếu, budget cảm biến/bộ nhớ/xử lý và biến độc lập của từng ablation. **Bằng chứng:** [Config budget/controls](configs/experiments/range_cadence_v3.toml): 10 ray, 96 B packet, map/search/RSS/CPU budget; chỉ period 32/64 ms thay đổi.
- [x] EXP-06 — Làm bằng nhau các yếu tố cần kiểm soát: tốc độ, quét, sensor cadence, giới hạn actuation và tập case. **Bằng chứng:** [Protocol §2](docs/protocols/range-cadence-v3.md): cùng speed/scan/pose cadence/control/actuation/case; range cadence là biến độc lập có chủ đích.
- [x] EXP-07 — Tạo protocol version mới, giữ v1/v2 để hồi quy; không âm thầm sửa lock hoặc tái gọi test đã xem là unseen. **Bằng chứng:** [Khóa thiết kế v3](configs/scenarios/protocol_v3.design.lock.json) giữ v1/v2 nguyên vẹn. Khóa runtime bổ sung bắt buộc ở mốc 7A; design lock chưa cho phép evaluation.
- [x] EXP-08 — Sinh train/development/validation/test mới với provenance và kiểm tra không trùng geometry phù hợp mục tiêu. **Bằng chứng:** [Index commitments](configs/scenarios/range_cadence_v3.index.json): đã sinh 480 case/chứng chỉ vào artifacts ignored; đủ bốn split, không trùng raw/canonical task với v1/v2. [Audit](docs/research/2026-10-27-research-protocol-v3.md).
- [x] EXP-09 — Định nghĩa số case/seed, số lần lặp, cách tổng hợp và xử lý lượt lỗi infrastructure trước chạy. **Bằng chứng:** [Protocol §4–6](docs/protocols/range-cadence-v3.md): 60/60/120/240 case, 2 repeat/arm, case là đơn vị thống kê, CI một phía và retry đã định trước.
- [x] EXP-10 — Quy định khi nào một lượt hợp lệ, bất khả thi hoặc hỏng hạ tầng; không loại failure chỉ vì thuật toán làm kém. **Bằng chứng:** [Protocol §6](docs/protocols/range-cadence-v3.md): negative có chứng minh, timeout/collision/OOM thuật toán giữ trong mẫu số, infra không phục hồi chặn kết luận.
- [x] EXP-11 — Lập sổ exposure: ai/thuật toán nào đã dùng tập nào để thiết kế, tune, chọn cấu hình hoặc báo cáo. **Bằng chứng:** [Exposure ledger](configs/scenarios/exposure_v3.json) phân biệt người/agent/CI kiểm metadata/geometry tự động với xem outcome; nay đã ghi pilot/development và validation chính thức; validation đã exposed, test chưa chạy.
- [x] EXP-12 — Ghi lựa chọn kỹ thuật và ngưỡng mới vào ADR/config trước triển khai đánh giá. **Bằng chứng:** [ADR](docs/decisions/0006-range-cadence-protocol-v3.md) + [config](configs/experiments/range_cadence_v3.toml) + design lock có trước implementation/evaluation v3; 92 tests và CI đạt.

**Gate:** có protocol, baseline, nguồn dữ liệu, ngưỡng và cách chọn cấu hình đủ rõ. Nếu thiếu quyết định, tiếp tục làm rõ thay vì train để có số đẹp.

**Đã qua gate thiết kế mốc 6:** [báo cáo/source/CI](docs/research/2026-10-27-research-protocol-v3.md). Mốc 7A nay đã có adapter/acquisition/accounting/evaluator, [240 lượt development local + 240 lượt CI và runtime lock](docs/research/2026-10-28-cadence-v3-development.md). Rate range giảm 50% trong development, nhưng success 45/50 và 46/50 chưa đạt 95%; [Validation tiếp theo](docs/research/2026-10-28-cadence-v3-validation.md) đủ 480 lượt nhưng 87/100 mỗi arm không đạt 95%, kết luận âm; test giữ chưa mở, chưa ML. [Checklist mục tiêu phát sinh khi hiện thực hóa](CHECKLIST_MUC_TIEU_NGHIEN_CUU.md) đánh dấu các phép đo/báo cáo đã có bằng chứng; phần phụ thuộc test và nghiên cứu tương lai giữ chưa thực hiện.

## 10. Nhánh 7A đề xuất — nghiên cứu giảm dữ liệu

Ưu tiên sát câu hỏi gốc; có thể làm với thuật toán không học trước. Từng cấu hình phải đánh giá lại chất lượng nhiệm vụ.

- [x] DATA-01 — Đo riêng đầu ra sensor, observation đưa vào policy, state giữ trong bộ nhớ và dữ liệu truyền/lưu. **Phạm vi đã kiểm chứng:** cadence 32/64 ms trên mapped cố định, development 7A tại `0c75ce2`; [bằng chứng](docs/research/2026-10-28-cadence-v3-development.md). Chưa là kết luận validation/test, hardware hoặc tối thiểu thông tin.
- [x] DATA-02 — Khai báo encoding/metadata khi báo byte; đo RSS/bộ nhớ thực nếu muốn nói về RAM, không thay bằng cell count. **Phạm vi đã kiểm chứng:** cadence 32/64 ms trên mapped cố định, development 7A tại `0c75ce2`; [bằng chứng](docs/research/2026-10-28-cadence-v3-development.md). Chưa là kết luận validation/test, hardware hoặc tối thiểu thông tin.
- [x] DATA-03 — Thử guarded chỉ lưu occupied hits thay vì cả free-grid; xác minh hành vi và budget. **Development:** [báo cáo](docs/research/2026-10-29-data03-occupied-only.md), [raw-review summary](docs/research/2026-10-29-data03-occupied-only.json), source `94f8e0b`; 88 case/352 episode, reference 62/74 và candidate 67/74. Local raw review khớp collector; không collision/bounds/negative false success, command replay đạt, budget 16000 entries không vượt. RSS giảm nhẹ 29.457→28.973 MiB; CPU mean tăng 0.860→1.622 ms. Chỉ case development đã lộ, không là validation/test, không chọn cấu hình hoặc tuyên bố tối thiểu.
- [ ] DATA-04 — Thử giới hạn lịch sử, vùng nhớ, thời hạn hit và nén/độ phân giải; ghi chi phí mất thông tin. **Đang thực hiện:** giao thức development riêng chỉ khảo sát TTL occupied-hit 10 s so với DATA-03; [ADR 0009](docs/decisions/0009-data04-hit-ttl.md), [kế hoạch 0016](docs/plans/0016-data04-hit-ttl.md). Chưa có Webots evidence; chưa đánh dấu hoàn thành.
- [x] DATA-05 — Giảm từng yếu tố một: số hướng ray, tần suất cập nhật hoặc độ chính xác số đo. **Phạm vi đã kiểm chứng:** cadence 32/64 ms trên mapped cố định, development 7A tại `0c75ce2`; [bằng chứng](docs/research/2026-10-28-cadence-v3-development.md). Chưa là kết luận validation/test, hardware hoặc tối thiểu thông tin.
- [ ] DATA-06 — Khảo sát quét/chọn phép đo theo tình huống thay vì lấy mọi phép đo cố định.
- [x] DATA-07 — Ghi số mẫu duy nhất theo timestamp, không đếm lại cùng sensor packet ở mỗi control tick. **Phạm vi đã kiểm chứng:** cadence 32/64 ms trên mapped cố định, development 7A tại `0c75ce2`; [bằng chứng](docs/research/2026-10-28-cadence-v3-development.md). Chưa là kết luận validation/test, hardware hoặc tối thiểu thông tin.
- [x] DATA-08 — Đánh giá trên cùng case paired, giữ đầy đủ collision/timeout và không chỉ báo đường đi của success. **Phạm vi đã kiểm chứng:** cadence 32/64 ms trên mapped cố định, development 7A tại `0c75ce2`; [bằng chứng](docs/research/2026-10-28-cadence-v3-development.md). Chưa là kết luận validation/test, hardware hoặc tối thiểu thông tin.
- [ ] DATA-09 — Tách thử bỏ sensor khi chạy với thử thiết kế/huấn luyện riêng cho cấu hình sensor ít hơn.
- [ ] DATA-10 — Đo đường biên trade-off chất lượng nhiệm vụ–dữ liệu–CPU/bộ nhớ theo các cấu hình đã thử.
- [ ] DATA-11 — Chọn cấu hình theo validation và ngưỡng đã khóa, chỉ dùng test mới cho báo cáo cuối. **V3:** candidate đã cố định trước outcome, không chọn bằng validation; validation không đạt nên test chưa mở. Phần đánh giá test của mục này chưa thực hiện và không được chạy trái gate.
- [x] DATA-12 — Nếu không cấu hình giảm dữ liệu nào đạt ngưỡng, kết luận chưa đạt và giữ nguyên bằng chứng. **V3:** candidate 64 ms duy nhất đã đăng ký không đạt gate success ở validation; [kết luận âm](docs/research/2026-10-28-cadence-v3-validation.md) giữ đủ 480 lượt, không chạy test.
- [ ] DATA-13 — Không tuyên bố tối thiểu tuyệt đối hoặc riêng tư chỉ từ số float, byte hay map cell ít hơn.

**Gate:** có cấu hình giảm chi phí cụ thể đạt ngưỡng nhiệm vụ trong miền thử; hoặc có kết luận âm được chứng minh. Không bắt buộc mọi thử nghiệm phải cải thiện.

## 11. Nhánh 7B đề xuất — huấn luyện model nếu cần

Chưa chọn ANN, imitation hay RL. Nhánh này chỉ triển khai khi phục vụ câu hỏi nghiên cứu; reference không học vẫn phải giữ để so sánh.

- [ ] ML-01 — Xác định đầu ra cần học: motion command, chọn hành động/cảm biến, representation hay phần khác của core.
- [ ] ML-02 — Khóa observation schema, lịch sử, normalization và action limits; ghi mọi thông tin được phép biết.
- [ ] ML-03 — Chọn supervised/imitation/RL theo dữ liệu, tiêu chí và chi phí; không mặc định một framework hoặc kiến trúc.
- [ ] ML-04 — Tạo dữ liệu train hoặc environment API từ đúng train split; không dùng v1/v2 test đã xem để chứng minh generalization mới.
- [ ] ML-05 — Đánh giá chất lượng teacher nếu dùng baseline làm nhãn; không coi đường teacher là tối ưu hoặc luôn đúng.
- [ ] ML-06 — Nếu reward/label dùng ground truth, giữ nó ở nhánh train/evaluation, không đưa thành observation runtime.
- [ ] ML-07 — Chỉ fit normalization/preprocessing bằng train; chọn tham số/checkpoint bằng validation, giữ test cho cuối.
- [ ] ML-08 — Ghi seed, source, dependencies, config, dataset split và môi trường chạy cho từng experiment.
- [ ] ML-09 — Có checkpoint/resume, ngân sách thời gian/tài nguyên và phát hiện training lỗi.
- [ ] ML-10 — Chạy nhiều seed huấn luyện độc lập theo số lượng đã khóa, tách khỏi seed hình học môi trường.
- [ ] ML-11 — Đánh giá model export/inference độc lập với trainer, cùng observation/action contract.
- [ ] ML-12 — So model với direct/reactive/guarded/mapped hoặc reference phù hợp trên cùng điều kiện thông tin/tốc độ/budget.
- [ ] ML-13 — Báo cả thất bại, phân phối kết quả và chi phí inference; không chỉ reward hoặc một video đẹp.
- [ ] ML-14 — Audit runtime không nhận camera, object IDs, full scene, route oracle hoặc metadata dùng để nhận dạng case.
- [ ] ML-15 — Khóa model/pipeline trước test mới; không chọn checkpoint theo test score.

### Nhánh tùy chọn: camera hỗ trợ train

- [ ] CAM-01 — Chỉ mở nhánh này nếu có giả thuyết và dữ liệu phù hợp; không bắt buộc cho dự án.
- [ ] CAM-02 — Tách dữ liệu ảnh/teacher với observation của student; kiểm tra đồng bộ và provenance nếu thu đa cảm biến.
- [ ] CAM-03 — Định nghĩa nhãn/teacher supervision và cách tránh leakage giữa train/validation/test.
- [ ] CAM-04 — Train student theo cấu hình triển khai không camera; không chỉ bỏ camera khỏi một model phụ thuộc ảnh.
- [ ] CAM-05 — So sánh có/không hỗ trợ camera, cùng input/runtime budget lúc đánh giá và nhiều training seed.
- [ ] CAM-06 — Kiểm tra artifact inference không yêu cầu ảnh hoặc chứa đường fallback âm thầm dùng vision.

**Gate:** có model tái lập, chạy không camera bằng input được phép và kết quả so sánh công bằng; hoặc kết luận mô hình chưa có lợi thế. Chưa gọi đó là giải pháp ngoài đời.

## 12. Mốc 8 đề xuất — độ vững và môi trường khó hơn

Mỗi nhóm mở rộng cần protocol riêng; không suy từ static/ideal/horizontal sang toàn bộ 3D.

- [ ] ROB-01 — Thêm sensor noise có nguồn/giả định rõ, không đặt nhiễu tùy ý rồi gọi là phần cứng thật.
- [ ] ROB-02 — Thử latency, mất mẫu, timestamp lệch, sensor hỏng và phép đo ngoài miền hợp lệ.
- [ ] ROB-03 — Thử định vị/tư thế có bias, drift hoặc mất tạm thời; tách lỗi sensing với lỗi policy.
- [ ] ROB-04 — Thử góc/yaw, vật cản mảnh, góc khuất và tốc độ khác để khảo sát khoảng trống giữa ray.
- [ ] ROB-05 — Đo độ trễ điều khiển/tính toán, thiết kế xử lý quá hạn; không coi sim chờ controller là đủ deadline thật.
- [ ] ROB-06 — Bổ sung tiêu chí bắt buộc xuyên khe/cổng khi đó là nhiệm vụ, thay vì chỉ đến đích bằng đường vòng ngoài.
- [ ] ROB-07 — Thử vật cản động và cập nhật/xóa occupied hits; map giữ hit mãi của v2 chưa phù hợp giả định này.
- [ ] ROB-08 — Đặc tả phát hiện mắc kẹt, hồi phục, dừng hoặc từ bỏ; phân biệt unknown, search budget và vô nghiệm thật.
- [ ] ROB-09 — Mở rộng lựa chọn bay trên/dưới/đổi độ cao và scoring 3D nếu được chọn.
- [ ] ROB-10 — Đồng bộ terrain/geometry giữa render, sensor, collision và route-feasibility evaluation.
- [ ] ROB-11 — Bổ sung rotor collision/khí động/gió/pin hoặc actuator hiệu chỉnh nếu nghiên cứu cần các yếu tố đó.
- [ ] ROB-12 — Đánh giá ngoài phân phối theo family/terrain/tốc độ, không chỉ seed mới của cùng generator.
- [ ] ROB-13 — Giữ bộ case hồi quy cho lỗi đã phát hiện, đồng thời tách bộ test mới chưa dùng thiết kế.

**Gate:** kết luận theo từng miền/sai số đã đo; chưa đủ bằng chứng thì ghi chưa đạt, không mở rộng lời khẳng định an toàn.

## 13. Mốc 9 đề xuất — observer, replay và giao diện lab

- [x] UI-01 — Có world 3D và nhãn case/policy/trạng thái cho người quan sát trên Webots.
- [x] UI-02 — Có telemetry, trajectory và ảnh observer ở các lượt bật rendering, source được ghi rõ.
- [x] UI-03 — Có chế độ numeric không rendering và chế độ realtime; không xuất ảnh giả từ lượt tắt rendering.
- [ ] UI-04 — Thêm lựa chọn case/seed/policy thuận tiện và hướng dẫn thao tác trong giao diện nếu cần.
- [ ] UI-05 — Hiển thị trace, điểm hit, vùng unknown/free/occupied và lệnh trước/sau guard ở observer.
- [ ] UI-06 — Cho bật/tắt lớp ground truth và lớp drone thực nhận để kiểm tra ranh giới thông tin.
- [ ] UI-07 — Thêm timeline command–velocity–sensor timestamp–contact để giải thích phanh và lỗi.
- [ ] UI-08 — Replay từ log có source/config, ghi rõ phát lại và phân biệt với rerun mô phỏng.
- [ ] UI-09 — So sánh paired episodes và kết quả ngay trong công cụ quan sát, không chỉ trong console.
- [ ] UI-10 — Kiểm tra mọi overlay/replay chỉ dành observer, không làm giàu input của policy.

**Gate:** giao diện phản ánh đúng thuật toán/vật lý/log; không thay đường bay thật bằng animation dựng sẵn rồi gọi là tự hành.

## 14. Mốc 10 đề xuất — bảo vệ thông tin và quản trị dữ liệu

Đã có nguyên tắc và audit luồng code, chưa có nghiên cứu bảo mật/riêng tư hoàn chỉnh.

- [x] PRIV-01 — Không có camera trong robot runtime hiện tại; observer là đường riêng.
- [x] PRIV-02 — Ghi rõ navigation không nhận scene/witness qua observation/mission và có kiểm tra phụ thuộc code.
- [x] PRIV-03 — Ghi giới hạn: controller kế thừa environment launcher; whitelist code không phải sandbox quyền OS.
- [ ] PRIV-04 — Xác định threat model: cần bảo vệ ảnh/định danh/vị trí/bố trí không gian hay luồng nào, trước đối tượng nào?
- [ ] PRIV-05 — Phân loại raw sensor, pose, map, model state, telemetry và log theo mục đích/độ cần thiết.
- [ ] PRIV-06 — Đặt chính sách thu/lưu/xóa dữ liệu và metadata; đo thông tin thực giữ lại thay vì chỉ kích thước file.
- [ ] PRIV-07 — Tách môi trường/quyền process và quyền đọc file/network cho policy nếu chạy mã không đáng tin cậy.
- [ ] PRIV-08 — Hạn chế metadata thí nghiệm trong process policy; kiểm tra đường rò thông tin ngoài observation contract.
- [ ] PRIV-09 — Kiểm tra khả năng suy ra floorplan/vị trí/thông tin nhạy cảm từ range/map/log theo threat model.
- [ ] PRIV-10 — Đánh giá trade-off utility–information exposure bằng phép đo đã định nghĩa.
- [ ] PRIV-11 — Nếu dùng dữ liệu ngoài đời/ảnh train, có quy tắc truy cập và xử lý tương ứng; không trộn vào repo công khai mặc định.
- [ ] PRIV-12 — Chỉ đưa ra tuyên bố bảo vệ thông tin trong phạm vi có bằng chứng; không suy ra từ việc bỏ camera.

## 15. Mốc 11 đề xuất — một chuyến giao hàng, mức D

Chỉ mở sau core phương tiện và giao thức nhiệm vụ đủ rõ. Hover tại goal hiện tại chưa phải giao kiện hàng.

- [ ] DEL-01 — Định nghĩa state machine: chuẩn bị, xuất phát/cất cánh nếu cần, tới điểm giao, dừng/hạ cánh, xác nhận giao, quay về.
- [ ] DEL-02 — Định nghĩa tọa độ/vùng giao được cấp và phương thức xác nhận; không giả định tìm người nhận bằng khả năng chưa có.
- [ ] DEL-03 — Mô phỏng payload và giới hạn tải; cập nhật động lực học nếu khối lượng thay đổi.
- [ ] DEL-04 — Chọn mô hình pin/năng lượng/sạc hoặc ghi rõ chỉ dùng proxy, không gọi quãng đường là năng lượng thật.
- [ ] DEL-05 — Tích hợp thời hạn, vùng cấm/giới hạn hoạt động và failure recovery của một nhiệm vụ.
- [ ] DEL-06 — Phân biệt tới goal, giao thành công, giao đúng giờ và hoàn tất quay về.
- [ ] DEL-07 — Kiểm tra nhiệm vụ thất bại, điểm giao bị chặn, năng lượng không đủ và mất xác nhận.
- [ ] DEL-08 — Báo end-to-end KPIs trên cùng bộ nhiệm vụ, giữ ranh giới thông tin giữa nhiệm vụ và sensing.

## 16. Mốc 12 đề xuất — logistics, mức E

- [ ] LOG-01 — Sinh đơn hàng, đích, thời điểm đến và deadline có seed/provenance.
- [ ] LOG-02 — Định nghĩa hàng chờ, thời gian phục vụ, tải, pin/sạc và giới hạn phương tiện.
- [ ] LOG-03 — Tạo dispatch baselines phù hợp, ví dụ FIFO/ưu tiên deadline, trước khi thêm thuật toán học.
- [ ] LOG-04 — Kết nối thời gian/khả năng chuyến bay với mô hình logistics; không dùng oracle route mà không ghi lợi thế thông tin.
- [ ] LOG-05 — Đánh giá on-time rate cùng throughput, trễ, đơn bỏ/mất và chi phí; không làm đẹp tỷ lệ bằng loại đơn khó.
- [ ] LOG-06 — Tách chất lượng điều hướng khỏi chất lượng dispatch để biết nguyên nhân cải thiện/thất bại.
- [ ] LOG-07 — Chỉ thêm nhiều phương tiện/phối hợp/sạc khi bài toán một phương tiện đã đủ bằng chứng.
- [ ] LOG-08 — Khóa tập đơn và nhiều seed so sánh, không coi một heuristic luôn tốt hơn trong mọi tải hệ thống.

## 17. Mốc 13 — các nhánh mở rộng có điều kiện

### Xe, ưu tiên sau drone

- [ ] EXT-01 — Chọn xe mô hình hay loại phương tiện mục tiêu theo mục tiêu nghiên cứu/luận tốt nghiệp và nguồn lực thực tế.
- [ ] EXT-02 — Chọn mô hình steering/kinematics phù hợp; xe không mặc định có chuyển động ngang như drone.
- [ ] EXT-03 — Tái dùng observation/evaluation khi phù hợp, có adapter/actuation riêng và kiểm chứng lại.
- [ ] EXT-04 — Khảo sát thực tế chi phí/định vị/cảm biến, không tự khẳng định khả năng thử ngoài đời rẻ hoặc sẵn sàng.

### Radar vật lý hoặc sensor khác

- [ ] EXT-05 — Chốt nghiên cứu range hình học hay radar/LiDAR/ultrasonic cụ thể trước khi đặt tên năng lực.
- [ ] EXT-06 — Nếu nghiên cứu radar: bổ sung mô hình tín hiệu/đặc tính cần thiết và dữ liệu hiệu chỉnh phù hợp câu hỏi.
- [ ] EXT-07 — Đánh giá mô hình sensor với nguồn thật hoặc reference có provenance; không coi raycast là radar đã được xác thực.

### Unity hoặc engine khác

- [ ] EXT-08 — Chỉ xem lại engine khi có nhu cầu/kết quả chứng minh lợi ích; không bắt buộc chuyển khỏi Webots.
- [ ] EXT-09 — Nếu chuyển, xác định nguồn vật lý có thẩm quyền và kiểm chứng lại sensing/collision/control/scoring, không chỉ thay render.

### Thực nghiệm phần cứng, chưa thuộc phạm vi đã triển khai

- [ ] EXT-10 — Xác định mục tiêu, ngân sách, phần cứng và môi trường thử có kiểm soát trước triển khai.
- [ ] EXT-11 — Đối chiếu quy định hiện hành theo địa điểm/thời điểm và điều kiện thử; không suy ngoại lệ từ việc không có camera.
- [ ] EXT-12 — Hiệu chỉnh sensor/actuator/định vị, đánh giá sim-to-real và giới hạn an toàn phù hợp thiết bị.
- [ ] EXT-13 — Có cơ chế dừng/can thiệp và quy trình thử tăng dần; báo kết quả hardware riêng với simulation.

## 18. Hồ sơ nghiên cứu và sản phẩm bàn giao tương lai

- [x] RES-01 — Đã có ADR, kế hoạch từng mốc và báo cáo/JSON/CI/source cho các mốc hiện tại.
- [ ] RES-02 — Hoàn thiện literature review và phát biểu đóng góp có đối chiếu, không chỉ dựa vào tên công nghệ.
- [ ] RES-03 — Viết experiment registry cho các nhánh tiếp theo: giả thuyết, biến, dữ liệu, ngưỡng, baseline, cách chọn model.
- [ ] RES-04 — Bổ sung thống kê/bất định phù hợp thiết kế, phân biệt seed môi trường và seed train.
- [ ] RES-05 — Viết kết quả âm, giới hạn và threat to validity, không chỉ báo cấu hình tốt nhất.
- [ ] RES-06 — Chuẩn bị gói tái hiện: phiên bản, dependencies, config/seed/lock, lệnh và evidence nhỏ có thể kiểm tra.
- [ ] RES-07 — Xác định license/phạm vi phát hành mã và dữ liệu phù hợp trước các đợt công bố mới.
- [ ] RES-08 — Nếu chọn luận tốt nghiệp/bài báo/demo giáo dục: chốt yêu cầu cụ thể và chuyển kết quả thành tài liệu tương ứng.

## 19. Checklist lặp lại cho mỗi milestone từ nay

Các ô trống ở phần này là **mẫu cho lượt công việc tiếp theo**, không nói rằng các mốc trước chưa làm các việc đó.

- [ ] OPS-01 — Đọc AGENTS.md và quyết định/kiến trúc liên quan; xác định phạm vi được giao.
- [ ] OPS-02 — Kiểm tra Git status, diff và remote hiện tại; bảo toàn thay đổi của người dùng.
- [ ] OPS-03 — Ghi mục tiêu, giả thuyết, kế hoạch và tiêu chí qua bước trước khi chạy thí nghiệm.
- [ ] OPS-04 — Chọn development data phù hợp; kiểm tra exposure và protocol trước khi sửa code/config.
- [ ] OPS-05 — Triển khai theo module; audit không đưa dữ liệu đặc quyền vào policy.
- [ ] OPS-06 — Chạy kiểm tra phù hợp thay đổi; tài liệu thì kiểm tra link/scaffold, runtime thì cần simulator thật và checks tương ứng.
- [ ] OPS-07 — Stage đúng phần việc, không đưa credential/download/raw artifact/model lớn vào Git.
- [ ] OPS-08 — Commit mạch lạc ở mốc hợp lý, push feature branch để CI/lưu tiến độ theo standing authorization.
- [ ] OPS-09 — Đọc CI và failure; không báo pass khi còn lỗi, thiếu executable/result hoặc chưa chạy simulator.
- [ ] OPS-10 — Chỉ đưa lên main khi đủ kiểm chứng và remote cho phép fast-forward an toàn; tôn trọng branch protection.
- [ ] OPS-11 — Không force-push/reset/clean/stash công việc khác để làm sạch trạng thái.
- [ ] OPS-12 — Bàn giao source SHA, branch/push/CI status, lệnh tái hiện, kết quả và giới hạn.
- [ ] OPS-13 — Cập nhật ngày, trạng thái và bằng chứng trong checklist này sau milestone.

## 20. Thứ tự ưu tiên đề xuất sau bản checklist này

| Ưu tiên | Việc tiếp theo | Phụ thuộc / lý do |
|---|---|---|
| P0 | Hoàn tất development DATA-04/06/09 theo version riêng rồi thiết kế validation mới | DATA-03 cho thấy trade-off nhưng chưa có selection threshold; không dùng lại exposed cases làm held-out |
| P0 | Đăng ký câu hỏi/ngưỡng, source lock và fresh validation/test cho phiên bản được chọn | V3 validation exposed và test v3 vẫn đóng; test mới chỉ sau validation gate đạt |
| P1 | Xác định budget phản hồi và khảo sát chi phí CPU/RAM trước yêu cầu realtime | V4/DATA-03 có chi phí CPU cao hơn; CPU max vẫn >16 ms, simulator có thể chờ controller |
| P1 | Mở rộng Pareto DATA-10 trên các config cùng protocol/host và paired cases | DATA-03 là một điểm development; không trộn tùy tiện với cadence v3/v4 khác host/source |
| P2 | Mở rộng độ vững/UI theo nhu cầu nghiên cứu | Không suy rộng current success sang noise/dynamic/3D |
| Sau core | Một chuyến giao hàng, rồi logistics | Giữ ưu tiên phương tiện trước điều phối |
| Có điều kiện | Xe, sensor vật lý, engine khác, hardware | Cần quyết định/mô hình/nguồn lực và bằng chứng riêng |

## 21. Chỉ mục bằng chứng để tiếp tục công việc

| Nội dung | Nguồn |
|---|---|
| Ý tưởng, Snake_ANN, mức B và phạm vi | [Bản ghi gốc](docs/01-y-tuong-va-quyet-dinh.md) |
| Dự thảo câu hỏi/thí nghiệm mức B | [Dự thảo](docs/02-du-thao-thi-nghiem-muc-b.md) — không tự coi mọi số/chi tiết là đã chấp nhận |
| Module và ranh giới | [System](docs/architecture/system.md), [data contracts](docs/architecture/data-contracts.md) |
| Quy tắc agent/Git | [AGENTS.md](AGENTS.md), [agents](agents/README.md), [development](docs/development.md) |
| Lab Webots | [Kế hoạch 0002](docs/plans/0002-webots-minimal-lab.md), [bằng chứng](docs/research/2026-10-25-webots-v1-smoke.md) |
| Navigation/evaluator v1 | [Kế hoạch 0003](docs/plans/0003-navigation-baseline.md), [bằng chứng](docs/research/2026-10-26-navigation-v1.md) |
| Seeded v1 | [Kế hoạch 0004](docs/plans/0004-seeded-environments.md), [bằng chứng](docs/research/2026-10-26-seeded-environments.md) |
| Observed navigation v2 | [Kế hoạch 0005](docs/plans/0005-observation-and-navigation-v2.md), [bằng chứng](docs/research/2026-10-26-navigation-v2.md) |
| Runtime v1 khóa | [Protocol v1](configs/scenarios/protocol_v1.lock.json) |
| Runtime v2 khóa | [Protocol v2](configs/scenarios/protocol_v2.lock.json) |
| Runtime v3 development | [Source/CI/số đo](docs/research/2026-10-28-cadence-v3-development.md), [runtime lock](configs/scenarios/protocol_v3.runtime.lock.json) |
| Validation v3 âm | [Báo cáo/source/CI 480 lượt](docs/research/2026-10-28-cadence-v3-validation.md), 87/100 mỗi arm; test chưa mở |
| Chẩn đoán kẹt đoạn đầu | [Kế hoạch 0013](docs/plans/0013-navigation-start-diagnostics.md), [báo cáo](docs/research/2026-10-28-navigation-start-diagnostics.md), [JSON](docs/research/2026-10-28-navigation-start-diagnostics.json); offline development, không sửa runtime |
| V4 observed detour — GOAL-23 | [Kế hoạch 0014](docs/plans/0014-observed-detour-v4.md), [báo cáo](docs/research/2026-10-28-observed-detour-v4.md), [JSON](docs/research/2026-10-28-observed-detour-v4.json); source `9503c2c`, CI 40684709433, 352 episode development |
| CI chính thức v2 | [Run 40255492790](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40255492790), runtime source `2f422e2` |

## 22. Nhật ký cập nhật checklist

| Ngày | Nội dung | Mốc đối chiếu |
|---|---|---|
| 2026-10-26 | Tạo checklist tổng thể theo yêu cầu người dùng; đối chiếu lịch sử, plan, ADR và evidence, tách roadmap đề xuất khỏi phần đã kiểm chứng | Runtime/bàn giao trước checklist: `d7018cb`; v2 tested source: `2f422e2` |
| 2026-10-27 | Audit batch mới: thiếu lệnh T/G, mapped chưa mở; đóng LOC-09 theo số đo và phiếu smooth/unchanged. Preflight 82 test/locks/dependencies đạt; probe display của phiên sửa lỗi exit 1, được ghi riêng | Source audit `c012ab8`; [evidence](docs/research/2026-10-27-local-acceptance-followup.md) |
| 2026-10-27 | Manual 020953 và mapped 022316 đủ bằng chứng; hoàn tất LOC-01…09, giữ raw hashes/ảnh/phiếu và các giới hạn | Source runtime `39c34af`; [nghiệm thu cuối](docs/research/2026-10-27-local-acceptance-complete.md) |

| 2026-10-28 | Hoàn tất runtime 7A, local/CI mỗi nơi 240 lượt development, khóa runtime; giữ kết quả chất lượng chưa đạt và held-out chưa mở | Source `0c75ce2`; [báo cáo](docs/research/2026-10-28-cadence-v3-development.md) |

| 2026-10-28 | Validation v3 duy nhất hoàn tất 480 lượt/127 tests và independent raw audit; 87/100 mỗi arm dưới 95%, đóng kết luận âm, giữ test chưa mở | Source `0c5f598`; [báo cáo](docs/research/2026-10-28-cadence-v3-validation.md) |

| 2026-10-28 | Hoàn tất chẩn đoán GOAL-22: 5 trace development, 27340 unknown rejection, ô nằm trong vòng origin; sweep offset và 141 tests đạt. Bốn khóa nguyên vẹn, bản sửa version mới còn là đề xuất GOAL-23 | Runtime được replay `0c75ce2`; [báo cáo 0013](docs/research/2026-10-28-navigation-start-diagnostics.md) |

| 2026-10-29 | Bàn giao GOAL-23 sau CI 28/10: v4 riêng ngoài src/, 165 tests và 352 episode; reference 62/74, candidate 74/74, năm regression thoát kẹt cả hai repeat. Giữ CPU cost, bốn khóa và v3 test chưa mở; nghiên cứu v4 held-out còn là đề xuất | Source `9503c2c`; [bằng chứng](docs/research/2026-10-28-observed-detour-v4.md) |

Khi cập nhật tiếp, thêm dòng nhật ký, điều chỉnh checkbox và dẫn bằng chứng. Không sửa ngược báo cáo lịch sử hoặc đánh dấu hàng loạt tương lai chỉ vì đã có roadmap này.
