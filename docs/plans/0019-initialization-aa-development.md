# 0019 — Thực thi kiểm chứng khởi tạo A/A trước nghiên cứu retention

Ngày: 2026-10-29. Người dùng yêu cầu lập kế hoạch từng bước rồi tiếp tục thực thi sau khi đã thống nhất ưu tiên 0018 → A/A → retention → DATA-10/11. Mốc thực thi đầu tiên là kiểm chứng khởi tạo, không mở held-out hoặc train. [ADR 0011](../decisions/0011-initialization-aa-development.md) đăng ký thiết kế trước simulator.

## Bước thực hiện và điều kiện chuyển bước

1. **Kiểm kê:** Git/diff sạch tại `7285f6d`, collector flock rảnh; lưu hash bốn khóa và inventory v3/v4/DATA-03/04. Không sửa src/ hoặc các version cũ.
2. **Đăng ký trước outcome:** ghi ADR/spec/index development và gates A/A; checkpoint kế hoạch. Dùng 12 case đã exposed: chín case hợp trong audit 0017, thêm empty `s3200020`, `v4-empty_offset-06`, negative `blocked_goal-s3200051`. Không chọn case theo kết quả A/A chưa chạy.
3. **Runtime riêng:** package `versions/initialization_aa_v1/`, PROTO/world/controller/runner/reviewer tên mới. Cả hai arm luôn dùng đúng ObservedDetourNavigator v4 full-history, acquisition/pose 32 ms, physics/control 16 ms, warmup 2 s, scoring cũ. Nhãn/slot chỉ dành orchestration, không vào observation policy.
4. **Hai chế độ:** warm-sequential chạy hai arm nối tiếp trong một Webots process theo order cũ; cold-isolated chạy mỗi arm trong một process/world mới, giữ thứ tự schedule để kiểm ảnh hưởng label. Hai repeat đảo order cho cả hai mode: 12 × 2 mode × 2 arm × 2 repeat = 96 episode, 72 process. Fresh output; không chồng collector.
5. **Bằng chứng khởi tạo:** ghi pose/velocity/yaw thật tại scoring (evaluator riêng), measured pose/acquisition timestamp, stabilizer targets và motor target velocities tại reset (Robot devices). Ground truth không đi vào navigation. Giữ mọi failure/negative và lỗi hạ tầng; chỉ một retry cho infrastructure có chứng cứ, không retry algorithm để lấy pass.
6. **Unit/integrity:** kiểm label không đổi policy, mode/split/case whitelist, membership/repeats, cold process schedule, byte inventory, normalized trace, threshold boundaries, retry/source/hash drift, geometry/observation boundary. Chạy make check; build A/A check tích hợp make. Kiểm diff rồi commit implementation trước simulator.
7. **Simulator CI/Xvfb:** push feature tại source đã ghi; workflow A/A chạy khi runtime paths thay đổi trên đúng nhánh `feat/initialization-aa-v1`, kèm dispatch cho trường hợp hạ tầng được ghi rõ. Docs-only không kích hoạt lại simulator. Chạy legacy smoke/navigation và đủ 96 episode trên một host. Không mở GUI laptop. Runner thiếu Webots R2025a phải fail; không dùng stub hoặc suy từ unit checks. Cơ chế trigger được chốt trước outcome để workflow mới có thể chạy từ feature branch.
8. **Review độc lập:** kiểm raw hashes, acquisition/range encoding/timing, physics evaluator, command/target từ public observations và aggregate A/A. Reviewer chỉ đọc output, không chạy physics; giữ local raw review riêng với nguồn CI. Báo warm differences và cold equivalence riêng; incomplete không được báo not_met hoặc met.
9. **Gate:** đủ dữ liệu, source sạch/hash khớp, không collision/bounds/negative false success; cold cùng case phải khớp initial/sensor phase/normalized non-resource traces và outcomes trong tolerance đăng ký. Warm differences là chẩn đoán, không bị xóa. Gate fail thì dừng nhánh retention để điều tra version mới, không nới tolerance hoặc rerun tìm pass.
10. **Bàn giao:** báo source/CI/raw hashes, kết quả âm hoặc đạt và giới hạn development. Cập nhật hai checklist/README/AGENTS, commit/push evidence; không fast-forward main trong mốc này. Nếu A/A đạt thì bước kế là chốt một candidate free-history, budget công bằng và protocol retention riêng trước implementation C; không tự coi A/A là chứng minh giữ chất lượng khi giảm dữ liệu.

## Định lượng đã đăng ký

Tolerance cold: position/velocity/attitude/angular-rate và giá trị range/command/target tối đa `1e-6` theo đơn vị tương ứng; timestamp sau chuẩn hóa tối đa `1e-9 s`. Cùng số tick/packet/decision, validity/reuse/status/recovery/target-presence/outcome phải bằng nhau; elapsed chênh tối đa một tick 0.016 s, path tối đa `1e-5 m`. So mọi cold episode cùng case, gồm hai label và hai repeat; không coi bốn episode là bốn case độc lập.

Đây là tolerance kỹ thuật cho việc chạy cùng runtime trên cùng host/seed, không ngưỡng chất lượng sản phẩm. CPU/wall/RSS là số đo tài nguyên được báo nhưng loại khỏi trace-equivalence vì chịu scheduling. Không thay margin/dwell/deadline hoặc v3 thresholds. Không đổi retained history trong A/A.

## Theo dõi tiến độ

- [x] Kiểm kê và ghi thiết kế trước simulator.
- [x] Triển khai/kiểm thử runtime A/A riêng; `make check` local đạt 189 tests, bốn khóa và inventory lịch sử nguyên vẹn. Chưa là bằng chứng simulator.
- [x] CI 40911479243 ở source `97be9a0` đủ 96 episode/72 process, legacy smoke/navigation và independent raw review; local replay trên worktree sạch khớp hoàn toàn.
- [x] [Bàn giao 30/10 và JSON](../research/2026-10-30-initialization-aa.md): năm gate đạt, 36/36 cold comparisons; warm differences được giữ. Chưa thực thi retention C–F, cần thiết kế mới trước triển khai.
