# DATA-06 — acquisition theo tình huống

Ngày: 2026-11-02. [0021](../plans/0021-sensor-development.md)/[ADR0013](../decisions/0013-situational-and-sparse-sensors.md), source `9d1e39031c4560b0889c43046f41e8481cb59457`; [CI41383159235](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/41383159235) và local raw review trên worktree sạch khớp byte-for-byte. ZIP digest đã tính lại khớp GitHub; JSON giữ source/runtime/design/raw hashes và mọi gate.

12 case development đã exposed (11 feasible/1 negative), hai repeat/cold process. 48 episode, đủ14 gate; không mở validation/test hoặc huấn luyện. Đây là phép thử trong tập pilot nhỏ, không suy generalization.

| Arm | Feasible case đạt cả hai repeat | Outcomes | Payload B/s | CPU episode-mean ms | Mean episode sampled RSS peak MiB |
|---|---:|---|---:|---:|---:|
| reference | 11/11 | {'success': 22, 'timeout': 2} | 2999.376927 | 1.999718 | 26.882324 |
| candidate | 11/11 | {'success': 22, 'timeout': 2} | 2300.402628 | 1.798247 | 25.852702 |

Ratios candidate/reference: `{"payload_rate_ratio": 0.7669601669403036, "cpu_mean_ratio": 0.8992501201653696, "rss_mean_peak_ratio": 0.9616989071534526, "elapsed_s_ratio": 1.0000869865052575, "path_length_m_ratio": 0.9999725565695002}`. Không collision/bounds/negative false success; không mất case reference đã đạt. RSS gồm recorder/accounting buffers; CPU/RSS chỉ so trong paired run trên cùng host. Không xếp hạng CPU/RSS giữa hai matrix job hoặc với runtime cũ. CPU max/p95/>16ms và toàn bộ failure được giữ trong JSON; không chứng nhận hard realtime/hardware/riêng tư hoặc tối thiểu tuyệt đối.

Candidate dùng hardware32/64ms theo public status và range của acquisition trước, mọi hướng vẫn cố định. Warmup32ms; chỉ chọn64ms khi follow observed route và mọi horizontal range hợp lệ>=2m. Reviewer kiểm sequence/timestamp, pose32ms độc lập, next-period reason và effective device periods. Payload giảm khoảng23.30%; không gọi đây là chọn hướng beam/radar vật lý.

Đường đi/thời gian common-success được tách khỏi outcomes và denominator đầy đủ. [Trade-off](2026-11-02-7a-tradeoffs.md) giữ nhóm riêng; lựa chọn candidate theo quy tắc [0022](../plans/0022-fresh-7a-evaluation.md), không theo validation.
