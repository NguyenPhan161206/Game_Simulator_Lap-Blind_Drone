# 0015 — Thử DATA-03: occupied-only persistent map

Mục tiêu: đo bằng runtime Webots xem có thể bỏ free-grid lịch sử mà vẫn giữ hành vi có kiểm chứng, đồng thời đo task outcome và budget thực.

1. Đóng nghĩa biến: free cells có hiệu lực tới acquisition mới; occupied hits và inflation tồn tại trong episode. Reuse một packet không làm free evidence hết hạn. Unknown luôn chặn.
2. Tạo package/protocol/world/controller riêng ngoài `src/` và `versions/navigation_v4/`; giữ v3/v4 runtime và bốn khóa nguyên byte.
3. Unit test expiry, packet reuse, persistent occupied/inflation, stop khi thiếu tuyến và ranh giới import policy.
4. Chạy cùng 88 exposed v4 development case, hai repeat, hai arm theo 32 ms; giữ toàn bộ outcome. V3 reference và v4 là comparators; DATA-03 là candidate.
5. Reviewer replay raw acquisition/decision/evaluation, kiểm hash/source, xác minh lệnh chỉ dùng free evidence còn hiệu lực, tính outcome/cost độc lập.
6. Báo RSS controller (sample tại tick), peak cells, occupied-only canonical bytes và CPU. Không coi canonical byte là RAM/network.
7. Chỉ kết luận development. Candidate không đạt chất lượng vẫn là kết quả âm; một protocol hoàn toàn mới cần fresh validation/test trước claim tổng quát.

Không đụng validation/test v3 đã exposed/đóng gate; không coi bộ 88 development là unseen hoặc dữ liệu độc lập mới.

## Bàn giao 2026-10-29

Implementation/runtime ở source `94f8e0b461c01aa18f269e75eb6662ce2d2283df`. [Báo cáo](../research/2026-10-29-data03-occupied-only.md), [JSON/raw-review summary](../research/2026-10-29-data03-occupied-only.json), CI 40796152653: simulator step complete 352 episodes; CI job bị hủy ở raw-review vì budget 60 phút. Reviewer chạy lại tại local và khớp chính xác toàn summary/hashes. 67/74 case candidate so với 62/74 reference; không collision/bounds/negative false success; map budget đạt, RSS giảm nhẹ 29.457→28.973 MiB nhưng CPU mean tăng 0.860→1.622 ms. Kết quả chỉ áp dụng cho development đã lộ; không chọn cấu hình hoặc mở validation/test.
