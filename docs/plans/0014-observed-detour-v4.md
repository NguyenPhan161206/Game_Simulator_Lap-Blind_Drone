# 0014 — Thực thi GOAL-23: nhánh đi qua vùng đã quan sát

Ngày: 2026-10-28. Người dùng đã yêu cầu triển khai đề xuất GOAL-23. Quyết định: [ADR 0007](../decisions/0007-observed-detour-v4.md).

1. Đối chiếu source sạch, collector không giữ flock, bốn khóa hợp lệ. Tạo nhánh riêng; đặt package v4 ngoài src/ để v3 inventory nguyên vẹn.
2. Viết kiểm tra segment supercover và measured swept clearance. Không free unknown; unit test góc cell, pose lệch tâm, corridor thiếu dữ liệu, occupied gần thân, stale/invalid và no-route.
3. Viết planner free-only bounded, không cắt góc. Kết nối từ pose đo; tìm đường tới goal đã quan sát hoặc điểm tiến triển trong connected component. Cache route giữa các replan nhưng kiểm lại segment mỗi tick. Dừng nếu không có đoạn hợp lệ.
4. Tích hợp navigator v4 cùng cadence/speed/guard/margins cũ. Phát lại snapshot tại lần kẹt đầu của năm trace development: ghi có/không lối thay thế, target, swept clearance và lệnh mới. Replay chỉ kiểm tra quyết định; không coi là thoát kẹt vật lý.
5. Thêm world/adapter/controller/runner v4 tên riêng, inventory riêng; import lại evaluator/acquisition/audit đã khóa. Ghi command/status/target từng tick và đối chiếu audit với quan sát. Nguồn shared cũ không thay đổi.
6. Đăng ký manifest development: toàn bộ 60 v3 development case là regression đã exposed; thêm empty theo offset/yaw/biên cell, near-wall, narrow gap và negative controls. Hai arm cùng 32 ms, paired order và 2 repeats. Giữ timeout/collision/bounds/infra attempts, không retry lỗi thuật toán để tìm pass. Không sinh validation/test v4 tại bước này.
7. Chạy make check và check build v4. Commit source/config/manifest trước simulator. Push workflow CI/Xvfb: kiểm tra legacy navigation thực và paired v4 development, không mở GUI laptop. Mục tiêu kỹ thuật: v4 đến đích ở cả hai repeat của năm regression kẹt, không collision/bounds trên suite; negative không báo success. Báo cả success toàn suite, path/time/CPU/RSS và failure mới; nếu mục tiêu không đạt thì giữ nguyên kết luận đó.
8. Review raw acquisition/physics/command evidence độc lập, giữ hashes/source và bốn khóa. Cập nhật báo cáo/checklists theo bằng chứng thực, commit/push bàn giao. Không tuyên bố chất lượng held-out, hardware, hard realtime hoặc mức giảm dữ liệu mới.

Nếu cần sửa sau pilot development, giữ source/attempt cũ và phiên bản config/source mới; không sửa lịch sử outcome hoặc đánh dấu đạt vì unit tests. Kế hoạch là phạm vi kiểm chứng phát triển, chưa là protocol nghiên cứu xác nhận.
