# ADR 0008 — DATA-03: chỉ giữ occupied hits giữa các lần đo

Ngày: 2026-10-29. Đây là thiết kế development để thực thi mục DATA-03; chưa chấp nhận kết luận chất lượng.

## Giả thuyết và biến được giữ cố định

Thử biểu diễn có persistent occupied-hit map và các ô free chỉ trong bản quét acquisition mới nhất. Giữ nguyên cảm biến, số hướng, cadence range/pose 32 ms, policy tick 16 ms, thuật toán observed-detour v4, world/case, evaluator, repeats và budget `max_cells=16000`. Reference và candidate không học.

So sánh cùng từng case giữa reference mapped v3, v4 full free-grid đã biết và DATA-03 occupied-only. V4 là mốc dữ liệu/thuật toán trung gian, không đổi cách chấm cặp chính reference–candidate.

## Hợp đồng retention

- Khi có acquisition timestamp mới, xóa toàn bộ free cells cũ rồi dựng free cells từ đúng packet mới.
- Policy tick đọc lại cùng packet không xóa free evidence.
- Occupied hits và vùng inflation suy ra tiếp tục tồn tại tới reset episode; hit hiện tại không bị đảo thành free.
- Budget candidate đếm số entry trong ba set free hiện hành, occupied và blocked/inflation; cell có mặt ở nhiều set được tính riêng vì tốn chỗ trong mỗi set. Khi vượt 16000 entry thì ngừng tích lũy và ghi budget exhaustion.
- Planner, target, velocity guard và swept clearance chỉ dùng occupied map cùng free evidence còn hiệu lực. Unknown vẫn cấm đi.
- Không có tuyến được chứng minh thì dừng/quét; không cho controller “đoán trống” để lấy lại chất lượng.
- Đo process RSS tại policy decisions, peak map cells, số persistent occupied/ephemeral free, và byte JSON canonical của occupied coordinates. Byte canonical là metric encoding; RSS mới là phép đo RAM của process và cũng gồm overhead controller.

## Phạm vi bằng chứng

Chỉ dùng 88 case v4 development đã exposed để kiểm tra hành vi/cost; 352 episode paired, không phải validation/test, không là 88 case mới. Giữ mọi timeout/collision/bounds/negative. Không tạo held-out hoặc mở test v3. Nếu candidate kém chất lượng, kết luận trade-off âm trong development; không phục hồi free grid bằng cách biến unknown thành free.
