# Retention cold v1 — free-history hữu hạn trên development

Ngày: 2026-11-02. [Plan 0020](../plans/0020-complete-7a.md), [ADR 0012](../decisions/0012-retention-cold-development.md). Thiết kế `651034e` có trước implementation/source `4c8bdee331c623bd6a40b7bac99c1ff2ea207905`; không thay ngưỡng sau outcome. [CI 41372012516](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/41372012516) đạt 198 tests, Webots R2025a smoke/navigation cũ và đủ 352 cold episode/352 process. [JSON raw review](2026-11-02-retention-cold.json) giữ source/runtime/design/raw hashes và từng gate.

CI standalone reviewer đọc lại raw files, kiểm hash, binary encoding, packet timing/reuse, free/occupied/blocked/last-seen replay, target/final command và scoring từ physics ticks. 955890 command decisions được kiểm; cả 264 so sánh khởi tạo cold đạt precision gate. Toàn bộ 14 gate đã đăng ký đạt. Pipeline thành công và study_outcome=met là hai kết luận riêng, đều có bằng chứng trong đợt này.

| Chỉ số | Reference full-history | Candidate free-history 2 s |
|---|---:|---:|
| Case khả thi success cả hai repeat | 74/74 | 74/74 |
| Episode success / timeout | 148 / 28 | 148 / 28 |
| Collision / bounds / negative false success | 0 / 0 / 0 | 0 / 0 / 0 |
| Mean retained free entries | 3602.318 | 2331.511 |
| Mean total map entries | 8224.601 | 5683.717 |
| Peak total map entries | 12646 | 7187 |
| Navigator CPU episode-mean, ms | 1.558632 | 1.560412 |
| Navigator CPU max, ms | 68.839770 | 64.146635 |
| Control CPU episode-mean, ms | 1.722484 | 1.727702 |
| Mean episode sampled RSS peak, MiB | 21.684726 | 21.769198 |
| Scored range payload B/s | 3000 | 3000 |
| Recorded raw log bytes | 592093244 | 595220287 |

Mean free-history giảm **35.28%**, total-entry mean giảm khoảng 30.89%; cả hai arm dùng cùng budget 16000 gồm cả last-seen metadata. RSS không giảm: tăng khoảng 0.0845 MiB; CPU mean gần bằng nhau (+0.114%). Common-success mean paired time/path ratios 1.004678/1.004049. Không mất case reference đã đạt; mọi negative-control episode giữ timeout, không bị loại khỏi mẫu số.

Acquisition vẫn 32 ms và payload `<dIHH10d` 96 B/packet; không gọi giảm history là giảm sensor acquisition. RSS là process controller lấy mẫu, gồm recorder/accounting buffers; entry count không phải RAM. Log volume tăng nhẹ. CPU max vẫn vượt control tick 16 ms; không chứng nhận realtime, phần cứng, riêng tư hoặc tối thiểu thông tin.

Đây là 88 case development đã exposed, không validation/test, không phải cấu hình tối ưu. Unknown/expired vẫn chặn thực thi; occupied hits giữ suốt episode. Kết quả mở bước nghiên cứu sensor riêng của [0021](../plans/0021-sensor-development.md); readiness/fresh evaluation vẫn theo [0022](../plans/0022-fresh-7a-evaluation.md), không tự mở test v3.

Artifact ID13111389470, ZIP 205132765 B, GitHub digest `822c064f97133c65cef551af8212606e02d06c02f9113438c7459bf742e00898`. Review JSON đã lấy bằng ZIP byte ranges và kiểm CRC/size từ central directory. **Đang tải raw bundle và chờ replay local** trên worktree sạch đúng source; chưa tuyên bố local replay khớp CI hoặc đã tự tính lại ZIP digest. CI raw review đã hoàn tất và là bằng chứng đủ cho gate baseline/khởi tạo của sensor pilots.
