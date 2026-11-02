# 7A — Trade-off hữu hạn trong từng nghiên cứu đã thử

Ngày: 2026-11-02. Bảng này tổng hợp các summary đã hậu kiểm trong repository; không chạy lại simulator hoặc chứng nhận lại raw artifact lịch sử. [JSON tái lập](2026-11-02-7a-tradeoffs.json) giữ SHA-256 các nguồn, mọi failure/outcome và cách tổng hợp.

| Nhóm / arm | Case khả thi đạt | Range payload B/s | CPU mean ms | RSS peak MiB | Pareto trong nhóm |
|---|---:|---:|---:|---:|---|
| cadence_v3_local_development / reference | 45/50 | 3000 | 0.553 | 24.547 | Có |
| cadence_v3_local_development / candidate | 46/50 | 1500 | 0.394 | 24.625 | Có |
| navigation_v4 / reference | 62/74 | 3000 | 0.652 | 29.219 | Có |
| navigation_v4 / candidate | 74/74 | 3000 | 1.132 | 30.426 | Có |
| occupied_only / reference | 62/74 | 3000 | 0.860 | 29.457 | Có |
| occupied_only / candidate | 67/74 | 3000 | 1.622 | 28.973 | Có |
| occupied_ttl_10s / reference | 67/74 | 3000 | 0.940 | 29.180 | Không |
| occupied_ttl_10s / candidate | 67/74 | 3000 | 0.874 | 28.805 | Có |

CPU lịch sử là mean theo decision; RSS lịch sử là peak mẫu đo của process. Mỗi nhóm paired có cùng điều kiện của chính run đó. Không so trực tiếp CPU/RSS giữa các hàng khác nhóm để chọn thuật toán. DATA-03 và v4 không có cách tính map budget giống nhau; A/A sau đó còn đo được khác biệt warm initialization. Vì vậy không dựng một đường biên toàn cục hay gọi chênh lệch giữa hai run là tác động riêng của retention.

Trong cadence local, 64 ms giảm range payload từ 3000 xuống 1500 B/s, CPU mean giảm và RSS tăng nhẹ; task 46/50 so với 45/50 vẫn dưới ngưỡng quality đã khóa. Trong DATA-03, candidate cải thiện outcome quan sát nhưng CPU tăng đáng kể; trong DATA-04, hai arm 67/74 với một case cải thiện/một kém đi dù CPU/RSS giảm. Pareto là tập điểm không bị trội trên các trục được báo, không phải lựa chọn cấu hình hoặc bằng chứng qua gate. Các collision/timeout/negative được giữ trong JSON; không chỉ đưa success-only path.

Đây là đường biên **rời rạc, quan sát được**, giới hạn ở các cấu hình và điều kiện đã thử; không nội suy thành đường liên tục hoặc tối ưu tuyệt đối. Với retention cold mới, mean free entries sẽ là trục dữ liệu riêng sau raw review; chưa có kết quả thì không thêm điểm giả.

Range packet canonical dùng `<dIHH10d` little-endian, 96 B/packet (timestamp, sequence, validity/limit masks và mười float64). Payload không gồm pose, metadata, log hoặc map. Set entries/cell count không thay cho RAM; RSS cũng là RSS process lấy mẫu, không phải peak phần cứng được bảo đảm.

**DATA-13 — Giới hạn kết luận:** ít float/byte/cell hơn không chứng minh tối thiểu thông tin tuyệt đối, riêng tư, tiết kiệm điện, radar thật, hard realtime hoặc an toàn phần cứng. Muốn kết luận riêng tư cần threat model và phép thử suy luận riêng (GOAL-18 vẫn mở). Không biến kết quả simulator development thành generalization. V3 kết thúc âm ở validation; test v3 không mở.

Tái lập: `python3 tools/build_7a_tradeoffs.py`; kiểm đồng bộ: `python3 tools/build_7a_tradeoffs.py --check`. Các nguồn: [cadence](2026-10-28-cadence-v3-development.md), [v4](2026-10-28-observed-detour-v4.md), [DATA-03](2026-10-29-data03-occupied-only.md), [DATA-04](2026-10-29-data04-hit-ttl.md).
