# 7A — Sparse6 qua fresh validation và final test

Bàn giao: 2026-11-03. Thu thập CI ngày 02/11. Source thực thi cố định `d51ada13b09b96037fc0e81d41ef978beaf1f387`, runtime hash `0e66cfbb50e8d0d3b7ec443d4a4c31f63e31a8a4e0b6fc1b5b828fc75780e949`. [CI 41399551997](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/41399551997) chạy đúng một validation, rồi một test sau khi validation đủ gate; 225 tests và legacy Webots smoke/navigation đạt.

Candidate sparse được chọn bằng quy tắc đăng ký trước outcome validation ở [0022](../plans/0022-fresh-7a-evaluation.md), binding/source lock sau [preflight 0023](2026-11-02-efficiency-preflight.md). Không chọn lại hoặc tune theo validation/test. [Validation JSON](2026-11-03-efficiency-validation.json) và [test JSON](2026-11-03-efficiency-test.json) giữ nguồn, raw/runtime/design/binding hashes, từng gate, mọi failure và artifact digest.

Mỗi split 72 case = 60 feasible (12/family trong năm family đã đăng ký) + 12 impossible negative; hai arm, hai repeat, 288 cold episode. Một case chỉ success nếu cả hai repeat success; repeat/tick/ray không phải mẫu độc lập. Hai tập mới đã kiểm raw/canonical task/seed disjoint với lịch sử và nhau trước chạy; v3 test chỉ dùng hash metadata chống trùng và vẫn chưa chạy.

| Split / arm | Case khả thi đạt | Success / timeout episode | Payload B/s | Nav CPU episode-mean ms | Mean episode sampled RSS peak MiB |
|---|---:|---:|---:|---:|---:|
| validation / reference | 60/60 | 120 / 24 | 2999.311183 | 1.627692 | 26.979329 |
| validation / sparse | 60/60 | 120 / 24 | 1999.527235 | 1.234826 | 25.867757 |
| test / reference | 60/60 | 120 / 24 | 2999.374640 | 1.853009 | 26.893148 |
| test / sparse | 60/60 | 120 / 24 | 1999.601287 | 1.410026 | 25.786431 |

**Kết quả đã kiểm chứng:** reference và sparse đều 60/60 feasible ở cả validation lẫn test; mỗi arm/split có 120 success và 24 negative timeout. Không collision, bounds violation hoặc negative false success. Mọi gate đã khóa đạt; one-sided 95% exact binomial lower bound là **0.9512970867**, tính theo 60 case dưới mô hình generator đã đăng ký. Không diễn giải thành bảo đảm ngoài miền/hardware.

| Ratio sparse/reference | Validation | Test |
|---|---:|---:|
| payload_rate_ratio | 0.666662148 | 0.666672733 |
| cpu_mean_ratio | 0.758636029 | 0.760938365 |
| rss_mean_peak_ratio | 0.958799114 | 0.958847637 |
| elapsed_s_ratio | 1.011329896 | 1.007060354 |
| path_length_m_ratio | 1.013180586 | 1.007609138 |

Test cho range payload giảm khoảng 33.33%, navigator CPU mean giảm 23.91%, mean sampled RSS peak giảm 4.12%; common-success time/path tăng 0.71%/0.76%. Các ratios đều trong ngưỡng. Đây là paired comparisons trong từng split/host, không gộp CPU/RSS của hai split hoặc các nghiên cứu cũ thành ranking toàn cục.

Codec baseline `<dIHH10d` 96 B/packet, sparse `<dIHH6d` 64 B/packet; active sampling 32 ms cả hai. Sparse bật 000/090/180/270/up/down, bốn diagonal sensor có effective period 0; không padding/no-return giả. Số value giảm 40%, payload giảm 1/3 vì vẫn có 16 B header; pose/metadata/log bytes được báo riêng trong raw evidence, không bị gọi chung là sensor payload.

Grid giữ full measured history trong cả hai arm và cùng budget 16000 entries (free/occupied/blocked/last-seen). Không ghép kết quả TTL 2 s development với sparse để tuyên bố một cấu hình kết hợp đã kiểm. RSS là process controller lấy mẫu, gồm recorder/accounting buffers; không là RAM riêng policy hay RAM toàn Webots. Test sparse CPU max 67.304134 ms, 6302 decisions vượt 16 ms; simulator chờ controller nên không chứng nhận hard realtime.

Hậu kiểm local chạy code đúng source trên worktree sạch, đọc lại binary packet encoding, actual device periods, pose/acquisition timeline, reused reads, raw file hashes, retained map/unknown support cho target và final command, physics 16 ms scoring, case matrix/retry/lock identity. Cả hai local review JSON khớp CI **byte-for-byte**; cả hai ZIP SHA-256 tự tính lại khớp GitHub. Đây là local raw replay, không phải một lượt bay simulator local mới hoặc GUI/hardware acceptance.

Giới hạn: simulator Webots R2025a/static/ideal/horizontal, năm family của generator hữu hạn; không camera trong runtime, không ML/training, không radar thật, điện năng hoặc privacy guarantee. Kết quả chứng minh một sparse configuration đạt ngưỡng đã đăng ký trong miền thử, không chứng minh tối thiểu thông tin tuyệt đối hoặc tốt nhất mọi cấu hình. Các split mới nay đã exposed; nghiên cứu/tune tiếp cần version/protocol/fresh split mới. Kết luận âm v3 vẫn giữ 87/100 mỗi arm, test v3 đóng.

Bước 0022 E/F và DATA-11 hoàn tất trong đúng phạm vi trên; [trade-off](2026-11-02-7a-tradeoffs.md) và hai checklist được cập nhật khi bàn giao.
