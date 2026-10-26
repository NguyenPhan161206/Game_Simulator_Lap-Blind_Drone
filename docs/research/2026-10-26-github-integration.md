# Bàn giao cây phiên bản và kiểm chứng tích hợp GitHub

Ngày 2026-10-26. Source main đã kiểm chứng: **63298d7f93aa2371de6aee5ae7205ee64501a5dd**. [JSON evidence](2026-10-26-github-integration.json) giữ study/checks gốc trích từ đúng log CI, job/artifact IDs và SHA256 artifact. [Kế hoạch GH-01…14](../plans/0007-github-integration.md) và [cây phiên bản](../version-history.md) ghi các mốc. Các commit tài liệu bàn giao sau source này chỉ thay tài liệu/evidence, được kiểm tra scaffold/link/hash riêng.

## Các giai đoạn và commit

| Giai đoạn | Commit | Kiểm chứng trước/sau xuất bản |
|---|---|---|
| Bộ thu bằng chứng ban đầu | 534b83a | 73 unit test; lượt desktop thực do người dùng chạy được audit riêng |
| Kế hoạch tích hợp | 1bec854 | Scaffold/link và diff review |
| Collector CI, xử lý result malformed/phiếu mâu thuẫn | b324105 | 75 unit test; CI collector 40284088405 success, artifact 12633900122 |
| Audit laptop và nối cây phiên bản | 0dd9de9 | Đối chiếu hash raw evidence, commit references, ảnh và trajectory; whitespace được sửa ở mốc sau |
| Pre-integration và fast-forward main | 63298d7 | Scaffold/diff/ancestry và protocol hợp lệ, sau đó toàn bộ CI main đạt |
| Tài liệu bàn giao | Commit chứa báo cáo này | Scaffold/link, diff và kiểm tra JSON/source/hash; không thay runtime đã khóa |

SSH managed báo lỗi quyền của /etc/ssh/ssh_config.d/20-systemd-ssh-proxy.conf; không sửa file hệ thống hay remote. Xuất bản bằng connector GitHub được ủy quyền; tree/commit khớp local trước khi đồng bộ refs. Giữ remote git@github.com:NguyenPhan161206/Game_Simulator_Lap-Blind_Drone.git. Hai nhánh lịch sử seeded/v2 đã fast-forward lên 2568f07/d7018cb; không force-push, xóa nhánh hoặc sửa lịch sử. Main fast-forward từ 1df11fd lên 63298d7; mọi local branch có upstream đúng.

## CI sau tích hợp, đúng source 63298d7

| Workflow | Kết quả | Bằng chứng |
|---|---|---|
| Scaffold checks | success | [40284891197](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40284891197) |
| Local session collector | success: mapped tới đích, manual có telemetry/timeout cleanup, không có operator record giả | [40284891173](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40284891173), artifact 12633542554 |
| Navigation v2 | success: 108 lượt và integrity study | [40284891072](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40284891072), artifact 12634041546 |
| Webots minimal lab | success: 12 smoke checks, 8 diagnostic và 48 seeded episodes, integrity study | [40284891187](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40284891187), artifact 12634037529 |

Các simulator job đều chạy 75 unit test. V1 lock vẫn 96872282fc7df5029453ed684d0e73e9305137c3d6907736869b2e04bf64b90f; v2 vẫn 0825b3b219fbf6a7f939b3076b79b1c82888c02d71a8ffea36d2e7d5bde1e395. V2 guarded/mapped giữ 10/10 khả thi mỗi split, reactive 8/10 với hai U collision mỗi split; negative controls vẫn timeout. Giữ failure trong study, không biến CI success thành khẳng định mọi baseline đều tới đích.

Đây là regression/reproduction trên protocol đã exposed; không tăng số mẫu nghiên cứu độc lập, không có huấn luyện model hoặc xác nhận phần cứng. CI dùng Xvfb; không đóng thay gate quan sát laptop.

## Nhánh L và phần còn mở

[Audit laptop](2026-10-26-local-acceptance.md) đóng LOC-04/07/08 dựa trên source 534b83a, phiếu GUI, console, result, ảnh và so sánh CI. LOC-05 còn mâu thuẫn phiếu all-yes với command bằng 0; LOC-06 chưa có xác nhận đã thấy mapped chuyển động/kết thúc; LOC-09 thiếu mô tả độ phản hồi. CPU max laptop 48.68 ms vượt tick 16 ms; không khẳng định deadline realtime phần cứng.

Checklist GitHub có thể hoàn tất độc lập; ba LOC còn lại và roadmap nghiên cứu tương lai không được tự đánh dấu. Raw logs/downloads/credential và metadata .local/git không đưa vào repository. Các JSON nhỏ trong research là evidence được review, không thay raw artifact hoặc sửa kết quả lịch sử.
