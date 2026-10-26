# Chạy và nghiệm thu trên laptop — nhánh L

Các lệnh dưới chạy trong **terminal desktop của bạn**, tại thư mục dự án. Phiên managed chưa truy cập được desktop; CI không thay thế việc quan sát GUI và thao tác bàn phím. [Kế hoạch](plans/0006-local-acceptance.md) và [checklist LOC](../CHECKLIST_DU_AN.md) giữ phần đó riêng.

## Cách khuyến nghị: một lệnh, hai lượt tuần tự

Đóng các cửa sổ Webots cũ, rồi chạy:

```bash
python3 tools/local_session.py accept
```

1. Chọn vùng 3D của Webots, thử đủ phím trong bảng dưới, mỗi phím giữ khoảng 0.5–1 giây và quan sát phản ứng. Thử R sau khi drone đã di chuyển. Đóng cửa sổ Webots bằng nút đóng khi xong.
2. Trả lời phiếu manual trong terminal. Phần độ phản hồi và pause/đổi tốc độ dùng lựa chọn đánh số; Enter giữ trạng thái chưa quan sát/không rõ. Nếu phiếu không khớp telemetry hoặc còn thiếu, công cụ dừng và in PENDING; mapped chưa được mở.
3. Khi manual đủ bằng chứng, mapped tự mở. Quan sát tới lúc kết thúc, giữ nguyên tốc độ simulation và trả lời phiếu mapped.
4. Gửi đường dẫn `Acceptance batch:` để agent đọc cả hai lượt và `acceptance.json`. Trạng thái `ready_for_review=true` nghĩa là đã đủ dữ liệu/phiếu theo gate của công cụ để review; checklist dự án vẫn được đối chiếu riêng.

Thư mục cha là artifacts/local-acceptance-… với hai thư mục manual/ và mapped/. Khóa tại .local/local-session/active.lock ngăn các collector trong workspace chạy chồng nhau, kể cả lúc đang trả lời phiếu; OS giải phóng khóa khi tiến trình kết thúc. File khóa còn tồn tại là bình thường. Các cửa sổ mở ngoài local_session.py không thuộc khóa này.

Nếu cần giới hạn dài hơn, dùng `--manual-timeout 900 --mapped-timeout 360`. `accept` yêu cầu terminal tương tác. Đánh giá lại batch đã có bằng `python3 tools/local_session.py audit-batch /duong/dan/batch`; source dirty/khác nhau, các lượt chồng thời gian, thiếu xác nhận hoặc mapped bị pause/đổi speed sẽ yêu cầu review/chạy lại phù hợp. Trễ nhiều được ghi nhận như hạn chế hiệu năng, không bị đổi thành “mượt”. SPACE/thả phím/R vẫn cần xác nhận người thao tác; telemetry command không tự chứng minh từng phím vật lý.

Các lệnh chạy riêng bên dưới vẫn dùng được. [Kế hoạch cải thiện quy trình](plans/0008-sequential-local-acceptance.md) giữ tách test công cụ với bằng chứng desktop.

## 1. Manual: mở world và thử phím (LOC-04/05)

Đóng Webots đang mở để tránh nhầm cửa sổ/lượt. Chạy:

```bash
python3 tools/local_session.py manual
```

Lệnh in đường dẫn `Session: .../artifacts/local-manual-...`. World phải là `minimal_lab.wbt`; scene tree có `DRONE` dùng `drone_controller`, `LAB_SUPERVISOR` dùng `lab_supervisor`. Console phải có `BLIND_DRONE_READY` và `BLIND_DRONE_LAB_READY: mode=manual`. Đây là kiểm tra world/controller ở GUI kết hợp console, không chỉ xem tên file.

Chọn vùng 3D để nhận phím; tốc độ simulation là realtime. Chờ hover ổn định, rồi thử từng mục ngắn khoảng 0.5–1 giây, thả phím và đợi phanh. Có thể bấm R giữa các nhóm để tránh đi quá xa.

| Thao tác | Quan sát cần ghi |
|---|---|
| W, S | Tiến, lùi theo hướng thân |
| A, D | Sang trái, phải theo hướng thân |
| T, G | Tăng, giảm độ cao |
| Q, E | Quay trái, phải; hướng thân đổi theo |
| SPACE | Phanh, giữ độ cao/yaw mục tiêu |
| Thả phím di chuyển | Drone giảm vận tốc, có quãng phanh |
| R sau khi đã di chuyển | Về điểm ban đầu, controller được reset, hover lại |

Đóng Webots sau khi thử; quay lại terminal trả lời phiếu cho **đúng lượt vừa chạy**. `y` là đã thử và đúng, `n` là đã thử nhưng không đúng, Enter là chưa thử. Ghi rõ giật, trễ, việc đổi speed/pause, lỗi. Nếu console bị đóng trước phiếu, dùng `attest` bên dưới. Không có result.json trong manual bình thường; telemetry và phiếu người thao tác là bằng chứng riêng, không tạo result “passed” giả.

## 2. Mapped realtime (LOC-06/07)

```bash
python3 tools/local_session.py mapped
```

World phải là `observed_v2.wbt`, controller `drone_v2` và `lab_v2`; ca duy nhất `development-u_trap-s21001`, policy mapped. Quan sát drone quét/di chuyển và kết thúc. Không bấm R, điều khiển bằng tay, pause hoặc thay tốc độ trong phép đo. Runner yêu cầu realtime, rendering bật; GUI chưa được xác nhận chỉ nhờ flag này.

CI tham chiếu của đúng ca: success, thời gian nhiệm vụ 41.216 s, đường đi 14.855334 m, khoảng cách cuối 0.046152 m, contact_count=0. Có warmup 2 s và thời gian khởi động/tắt ngoài thời gian nhiệm vụ. Webots tự đóng khi hoàn thành; đợi terminal in Review rồi điền phiếu. Mặc định timeout 180 s wall, không phải thay deadline nhiệm vụ 90 s. Máy chậm có thể dùng `--timeout 360` cho lượt mới và ghi điều đó.

Nếu lỗi driver/render, giữ nguyên lượt lỗi rồi thử lượt **mới** với `--software-rendering`; ghi cấu hình này trong so sánh. Nếu thiếu thư viện, xem console; không thay đổi quyền display. `--webots /duong/dan/webots` chỉ định wrapper R2025a ở nơi khác. Tất cả lệnh yêu cầu hai protocol vẫn hợp lệ.

## 3. Bằng chứng và so sánh (LOC-07/08/09)

Mỗi lượt tạo thư mục mới; mặc định trong artifacts đã bị Git ignore:

- `session.json`: source SHA/dirty state, protocol, world/controller dự kiến, cấu hình máy/hiển thị tối thiểu, lệnh, exit code và wall time. Đây là provenance của launcher, không tự chứng minh GUI đúng.
- `console.log`: stdout/stderr thật của Webots, kể cả lỗi khởi động.
- `run/telemetry.jsonl`: số đo thật của lượt; manual còn giữ dấu các command, không tự chứng minh đã nhấn từng phím hoặc R.
- `run/result.json`, `cases.json`, `manifest.json`, `trajectories.json` và ảnh JPG nếu controller mapped xuất thành công. Ảnh observer không được đưa vào policy. Manual không tự xuất ảnh; nếu cần lưu ảnh bằng Webots vào chính thư mục lượt đó rồi chạy review lại.
- `operator.json`: người thao tác tự xác nhận GUI/phím/chuyển động và ghi độ phản hồi. Công cụ không tự điền “yes”, không ghi đè phiếu cũ.
- `review.json`/`review.md`: hash các file, số telemetry, kiểm tra identity và delta mapped với [CI gốc](research/2026-10-26-navigation-v2.md). Giữ raw logs cùng review, không chỉ gửi một dòng PASS.

Thay `/duong/dan/session` bằng đường dẫn Session đã in:

```bash
python3 tools/local_session.py attest /duong/dan/session
python3 tools/local_session.py review /duong/dan/session
```

`attest` chỉ cần khi chưa có phiếu. `review` có thể chạy lại sau khi thêm ảnh. Dùng `--no-interview` để chỉ thu số liệu; cách đó vẫn thiếu xác nhận người quan sát. Exit code 0 của launcher không tự đóng LOC hoặc chứng minh phím đã được thử.

So sánh chỉ hợp lệ khi result/checks đạt, tiến trình hoàn tất bình thường, đúng protocol/manifest/Webots/geometry/case/policy và source/dirty của chính lượt. Source helper/docs mới có thể khác source CI, nhưng frozen file hashes phải giữ nguyên. Sai số ≤1e-6 chỉ được gắn nhãn chẩn đoán `numerically_close`; không phải ngưỡng chất lượng nghiên cứu mới. Outcome khác hoặc delta lớn phải giữ để điều tra; chưa có bằng chứng thì không quy lỗi cho GPU, driver hay sai số số học.

`sim_s_over_total_wall_s` gồm warmup và toàn bộ startup/shutdown, pause nếu có, nên chỉ giúp nhận ra một lượt chậm. Không đo FPS hay input latency bằng số này. Xem thêm cpu_mean_ms/cpu_max_ms trong comparison; max vượt tick 16 ms không đạt bằng chứng deadline thời gian thực. Phiếu ghi trải nghiệm phím/GUI, không thay phép đo độ trễ chính xác. Nếu máy chậm, LOC-09 vẫn có thể ghi nhận hiệu năng hạn chế; không tuyên bố đã đạt realtime.

Chỉ đóng từng LOC khi có bằng chứng đúng nghĩa: GUI/world-controller (04), toàn bộ phím/reset (05), mapped chuyển động/kết thúc (06), raw/source/ảnh nếu có (07), so sánh/điều tra khác biệt (08), ghi nhận hiệu năng và giới hạn (09). Tài liệu CI lịch sử không được sửa thành kết quả local.
