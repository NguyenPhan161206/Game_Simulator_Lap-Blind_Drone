# ADR 0006 — nghiên cứu giảm thu nhận range trước ML

Ngày: 2026-10-27. Trạng thái: lựa chọn kỹ thuật được Codex xác lập trong phạm vi người dùng giao lập kế hoạch và hoàn thiện EXP-01–EXP-12; ngưỡng đăng ký trước kết quả, chưa là xác nhận chất lượng từ người dùng hoặc thực nghiệm. Hướng mặc định đã được nêu để người dùng điều chỉnh; không có yêu cầu chọn model/framework.

## Quyết định

1. Ưu tiên thí nghiệm giảm dữ liệu cảm biến trên baseline mapped. Câu hỏi: tăng chu kỳ thu nhận 10 range từ 32 lên 64 ms có giảm ít nhất 50% lưu lượng range, trong khi giữ chất lượng theo ngưỡng của [protocol v3](../protocols/range-cadence-v3.md), trong các scene tĩnh mới cùng generator không?
2. Chỉ có một candidate 64 ms, chọn trước mọi outcome. Validation là gate xác nhận đủ điều kiện mở test, không là nơi tìm candidate tốt nhất. Nếu không đạt, kết luận âm và không mở test để tìm số đẹp. ML, giảm số ray, nén, grid nhỏ hơn và sensing thích nghi thuộc protocol khác.
3. Giữ nguyên các file v1/v2 đã khóa; reference v3 tái sử dụng mapped v2 với cùng tham số, không kế thừa tuyên bố 10/10 trên case mới. Dùng adapter/evaluator version mới khi triển khai, không sửa module cũ để lách checksum.
4. Tạo 480 case mới: train dự trữ 60, development 60, validation 120, test 240. Mỗi case có seed riêng; feasible family được gán bằng hash từ cùng hỗn hợp năm family, negative tách riêng. Chứng chỉ chỉ dành generator/evaluator. Không có dataset camera/ML.
5. Khóa **thiết kế** tại mốc 6. Runtime còn thiếu adapter cadence/kế toán/runner: `runtime_ready=false` và tool từ chối yêu cầu chạy evaluation. Chỉ mở đánh giá ở mốc 7A sau kiểm chứng development và khóa source runtime bằng một artifact bổ sung, không thay design lock.
6. Các ngưỡng chất lượng, budget, thống kê, retry và exposure có một nguồn số học: [config](../../configs/experiments/range_cadence_v3.toml). [Nguồn chính/định vị](../research/2026-10-27-range-cadence-related-work.md) không chứng minh thuật toán mới hoặc riêng tư.

## Hệ quả và điều kiện sửa quyết định

Chu kỳ cảm biến là biến độc lập nên không giữ bằng nhau giữa hai arm; mọi yếu tố khác giữ bằng nhau, gồm pose cadence, control tick, yaw scan, tốc độ, guard freshness 120 ms, map/planner và case. Không tăng ngưỡng dữ liệu cũ riêng cho candidate. Cả 32 và 64 ms nằm trong freshness đã chọn; độ đúng timestamp vẫn phải kiểm chứng khi triển khai.

Đổi câu hỏi, candidate, ngưỡng hoặc generator sau khi khóa phải có ADR/protocol version mới và exposure mới. Lỗi implementation tìm trên development được sửa trước runtime freeze; không thay thiết kế hoặc chọn config bằng held-out. Không bảo đảm nghiên cứu đạt giả thuyết; cho phép kết luận không đạt hoặc thiếu bằng chứng.
