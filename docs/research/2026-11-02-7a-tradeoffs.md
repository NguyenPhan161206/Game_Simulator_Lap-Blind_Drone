# 7A — Trade-off hữu hạn trong từng nghiên cứu đã thử

Ngày: 2026-11-02. Bảng này tổng hợp các summary đã hậu kiểm trong repository; không chạy lại simulator hoặc chứng nhận lại raw artifact lịch sử. [JSON tái lập](2026-11-02-7a-tradeoffs.json) giữ SHA-256 các nguồn, mọi failure/outcome và cách tổng hợp.

| Nhóm / arm | Case khả thi đạt | Range payload B/s | CPU mean ms | RSS mẫu MiB | Pareto trong nhóm |
|---|---:|---:|---:|---:|---|
| cadence_v3_local_development / reference | 45/50 | 3000 | 0.553 | 24.547 | Có |
| cadence_v3_local_development / candidate | 46/50 | 1500 | 0.394 | 24.625 | Có |
| navigation_v4 / reference | 62/74 | 3000 | 0.652 | 29.219 | Có |
| navigation_v4 / candidate | 74/74 | 3000 | 1.132 | 30.426 | Có |
| occupied_only / reference | 62/74 | 3000 | 0.860 | 29.457 | Có |
| occupied_only / candidate | 67/74 | 3000 | 1.622 | 28.973 | Có |
| occupied_ttl_10s / reference | 67/74 | 3000 | 0.940 | 29.180 | Không |
| occupied_ttl_10s / candidate | 67/74 | 3000 | 0.874 | 28.805 | Có |
| retention_cold_2s / reference | 74/74 | 3000 | 1.559 | 21.685 | Có |
| retention_cold_2s / candidate | 74/74 | 3000 | 1.560 | 21.769 | Có |
| sensor_pilot_adaptive / reference | 11/11 | 2999 | 2.000 | 26.882 | Không |
| sensor_pilot_adaptive / candidate | 11/11 | 2300 | 1.798 | 25.853 | Có |
| sensor_pilot_sparse / reference | 11/11 | 2999 | 2.070 | 26.887 | Không |
| sensor_pilot_sparse / dropout | 0/11 | 2000 | 0.038 | 30.614 | Fault control |
| sensor_pilot_sparse / sparse | 11/11 | 1999 | 1.623 | 25.803 | Có |

CPU lịch sử là mean theo decision; RSS lịch sử là peak mẫu đo của process. Với retention cold, CPU là mean episode và RSS là mean của sampled peak từng episode; các cách tổng hợp không bị gộp để xếp hạng. Mỗi nhóm paired có cùng điều kiện của chính run đó. Không so trực tiếp CPU/RSS giữa các hàng khác nhóm để chọn thuật toán. DATA-03 và v4 không có cách tính map budget giống nhau; A/A sau đó còn đo được khác biệt warm initialization. Vì vậy không dựng một đường biên toàn cục hay gọi chênh lệch giữa hai run là tác động riêng của retention.

Trong cadence local, 64 ms giảm range payload từ 3000 xuống 1500 B/s, CPU mean giảm và RSS tăng nhẹ; task 46/50 so với 45/50 vẫn dưới ngưỡng quality đã khóa. Trong DATA-03, candidate cải thiện outcome quan sát nhưng CPU tăng đáng kể; trong DATA-04, hai arm 67/74 với một case cải thiện/một kém đi dù CPU/RSS giảm. Pareto là tập điểm không bị trội trên các trục được báo, không phải lựa chọn cấu hình hoặc bằng chứng qua gate. Các collision/timeout/negative được giữ trong JSON; không chỉ đưa success-only path.

Đây là đường biên **rời rạc, quan sát được**, giới hạn ở các cấu hình và điều kiện đã thử; không nội suy thành đường liên tục hoặc tối ưu tuyệt đối. Với [retention cold](2026-11-02-retention-cold.md), mean free entries là trục dữ liệu riêng sau CI raw review: 3602.318→2331.511 (−35.28%), trong khi acquisition vẫn3000B/s. RSS tăng nhẹ; hai arm74/74 trên development. Local raw replay được báo riêng khi hoàn tất.

Range packet canonical dùng `<dIHH10d` little-endian, 96 B/packet (timestamp, sequence, validity/limit masks và mười float64). Payload không gồm pose, metadata, log hoặc map. Set entries/cell count không thay cho RAM; RSS là process controller lấy mẫu, gồm cả recorder/accounting buffers và không phải RAM riêng của policy, RAM toàn Webots hoặc peak phần cứng được bảo đảm.

**DATA-13 — Giới hạn kết luận:** ít float/byte/cell hơn không chứng minh tối thiểu thông tin tuyệt đối, riêng tư, tiết kiệm điện, radar thật, hard realtime hoặc an toàn phần cứng. Muốn kết luận riêng tư cần threat model và phép thử suy luận riêng (GOAL-18 vẫn mở). Không biến kết quả simulator development thành generalization. V3 kết thúc âm ở validation; test v3 không mở.

Tái lập: `python3 tools/build_7a_tradeoffs.py`; kiểm đồng bộ: `python3 tools/build_7a_tradeoffs.py --check`. Các nguồn: [cadence](2026-10-28-cadence-v3-development.md), [v4](2026-10-28-observed-detour-v4.md), [DATA-03](2026-10-29-data03-occupied-only.md), [DATA-04](2026-10-29-data04-hit-ttl.md).
