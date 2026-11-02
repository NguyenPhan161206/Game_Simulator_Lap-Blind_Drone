# ADR 0012 — Giảm free-history với đối chứng cold-isolated

Ngày: 2026-11-02. Người dùng yêu cầu tiến hành hoàn thiện nhánh 7A (DATA-01–13). Quyền này mở công việc mới theo từng gate; không mở test v3. Đây là lựa chọn kỹ thuật cho development mới, không thay yêu cầu hoặc outcome lịch sử.

Tiếp nối A/A 0019 đã đạt, triển khai một package riêng `versions/retention_cold_v1/`. Hai arm dùng v4; reference giữ free-history, candidate giữ free evidence 2 giây tính từ lần acquisition gần nhất đã đo ô. Occupied và inflation giữ nguyên suốt episode. Unknown/expired chặn thực thi. Không đổi planner, guard, tốc độ, physics, sensor hoặc scoring; mỗi episode một process Webots R2025a mới.

Cả hai arm dùng cùng grid wrapper và metadata last-seen để tính budget công bằng: tổng số entries của free set, occupied set, blocked set và last-seen dictionary không quá 16000. Đây là budget entry, không phải RAM; log RSS riêng. Dictionary last-seen chỉ chứa ô free đang giữ. Hết budget dừng chuyển động và giữ outcome, không evict occupied hoặc loại case.

Chọn 2 giây như một phép ablation hữu hạn (62–63 acquisition 32 ms), không gọi tối ưu. Không quét TTL sau outcome. Gate development ở [0020](../plans/0020-complete-7a.md) cố định trước simulator. Chưa đăng ký held-out: DATA-11 cần protocol/split/source lock mới sau readiness. Giữ nguyên mọi runtime và bốn lock lịch sử.
