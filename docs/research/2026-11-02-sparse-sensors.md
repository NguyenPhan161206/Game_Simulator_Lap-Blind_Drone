# DATA-09 — dropout và interface sparse riêng

Ngày: 2026-11-02. [0021](../plans/0021-sensor-development.md)/[ADR0013](../decisions/0013-situational-and-sparse-sensors.md), source `9d1e39031c4560b0889c43046f41e8481cb59457`; [CI41383159235](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/41383159235) và local raw review trên worktree sạch khớp byte-for-byte. ZIP digest đã tính lại khớp GitHub; JSON giữ source/runtime/design/raw hashes và mọi gate.

12 case development đã exposed (11 feasible/1 negative), hai repeat/cold process. 72 episode, đủ14 gate; không mở validation/test hoặc huấn luyện. Đây là phép thử trong tập pilot nhỏ, không suy generalization.

| Arm | Feasible case đạt cả hai repeat | Outcomes | Payload B/s | CPU episode-mean ms | Mean episode sampled RSS peak MiB |
|---|---:|---|---:|---:|---:|
| reference | 11/11 | {'success': 22, 'timeout': 2} | 2999.376927 | 2.069943 | 26.887370 |
| dropout | 0/11 | {'timeout': 24} | 1999.644444 | 0.037556 | 30.613932 |
| sparse | 11/11 | {'success': 22, 'timeout': 2} | 1999.375148 | 1.623358 | 25.802897 |

Ratios candidate/reference: `{"payload_rate_ratio": 0.6665968288842168, "cpu_mean_ratio": 0.7842525506051505, "rss_mean_peak_ratio": 0.9596660936100148, "elapsed_s_ratio": 1.0085523472865243, "path_length_m_ratio": 1.0081783562014308}`. Không collision/bounds/negative false success; không mất case reference đã đạt. RSS gồm recorder/accounting buffers; CPU/RSS chỉ so trong paired run trên cùng host. Không xếp hạng CPU/RSS giữa hai matrix job hoặc với runtime cũ. CPU max/p95/>16ms và toàn bộ failure được giữ trong JSON; không chứng nhận hard realtime/hardware/riêng tư hoặc tối thiểu tuyệt đối.

Reference bật10 sensor; dropout chỉ bật6 nhưng giữ validator10 nên fail-closed (0/11 feasible,24 timeout). Sparse-designed dùng cùng6 sensor thật với schema riêng, không padding ray/no-return giả, và vẫn chặn unknown. Đây là thiết kế lại interface không học, không phải retraining. Payload `<dIHH6d`64B so với96B full; số value giảm40%, payload giảm khoảng1/3. Dropout là fault control, không candidate để chọn.

Đường đi/thời gian common-success được tách khỏi outcomes và denominator đầy đủ. [Trade-off](2026-11-02-7a-tradeoffs.md) giữ nhóm riêng; lựa chọn candidate theo quy tắc [0022](../plans/0022-fresh-7a-evaluation.md), không theo validation.
