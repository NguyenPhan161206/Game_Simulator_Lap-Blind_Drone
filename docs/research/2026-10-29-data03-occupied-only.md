# DATA-03 — occupied-only persistent map (development)

Ngày 2026-10-29. Source runtime: `94f8e0b461c01aa18f269e75eb6662ce2d2283df`. Thiết kế [ADR 0008](../decisions/0008-data03-occupied-only.md), kế hoạch [0015](../plans/0015-data03-occupied-only.md). Đây là phép thử development trên các ca đã exposed, không phải validation/test mới.

## Cấu hình và phép đo

Candidate giữ occupied hits và inflation trong episode; các ô free cũ bị bỏ khi có acquisition mới. Cùng packet được đọc ở policy tick kế tiếp thì không làm free evidence hết hạn. Lệnh chỉ được phát khi target và đoạn lệnh được chứng minh free, đủ clearance bằng dữ liệu quan sát còn hiệu lực; nếu không có lối thì dừng/quét. Budget 16000 đếm số entry trong ba set free/occupied/blocked, gồm cả tọa độ bị lặp ở nhiều set.

So sánh frozen v3 mapped reference với candidate DATA-03, cadence range/pose 32 ms, điều khiển/vật lý 16 ms, cùng Webots R2025a, 88 case development của v4, hai repeat và cùng evaluator: 352 episode, 176 pair. Bộ case đã được dùng cho development v4; không xem đây là n mới hoặc unseen.

| Chỉ số trên mọi case khả thi | Reference | DATA-03 |
|---|---:|---:|
| Case success ở cả hai repeat | 62/74 (83.8%) | 67/74 (90.5%) |
| Episode success / timeout | 129 / 47 | 140 / 36 |
| Collision / out-of-bounds | 0 / 0 | 0 / 0 |
| Negative false success | 0 | 0 |
| Weighted mean decision CPU | 0.860 ms | 1.622 ms |
| Max decision CPU | 80.850 ms | 72.813 ms |
| Max per-episode p95 CPU | 1.993 ms | 3.539 ms |
| Sampled controller RSS peak | 29.457 MiB | 28.973 MiB |
| `RangeGrid` peak free+occupied cells | 5370 | 534 |

Candidate cải thiện 8 case và kém đi 3 case so với reference theo collapse bảo thủ hai repeat; 4 case còn lại đều không thành công ở ít nhất một arm. Trên 59 case cả hai arm cùng thành công, tỷ số candidate/reference là 1.625 cho thời gian và 1.241 cho quãng đường. Dùng failure penalty trên tất cả case khả thi, tỷ số thời gian 1.323 và quãng đường 0.912. Vì vậy tỷ lệ case success cao hơn trong development không đồng nghĩa đường đi nhanh hơn.

## Bằng chứng biểu diễn và integrity

- Độc lập replay **673885 candidate decisions**: target/command chỉ dùng free evidence còn hiệu lực; không đi qua unknown.
- Candidate peak: 271 persistent occupied cells, 313 ephemeral free cells, 2317 blocked/inflation cells, 2534 tọa độ hợp nhất, 2832 set entries; dưới budget 16000. Canonical JSON occupied-hit encoding tối đa 2255 B. Đây là encoding metric, không phải RAM.
- Năm gate engineering của DATA-03 đều đạt: không collision/bounds/negative false success, command replay đạt, không vượt map budget.
- RSS là process controller lấy mẫu ở decision ticks, không phải tổng RAM Webots; mức giảm khoảng 0.48 MiB nhỏ và không chứng minh giảm RAM đáng kể trên phần cứng.
- CPU tăng khoảng 88.5% theo weighted mean; max vẫn vượt tick 16 ms ở cả hai arm. Không có hard-realtime claim.
- Local reviewer tại Python workspace xác nhận đủ 88 case/352 episode, identity/source/inventory/raw hashes và summary **khớp chính xác** với collector output. Review JSON digest `95b60663f3b0f2c4635e698d854eedcc2a3a076dee840b92de60c79278b7b627`; raw result digest `bc188514e0d1a862fac548e8340fd8f6e85cc9897b0d08b063fd502f04f83fea`.

## Tình trạng CI và kết luận

[GitHub Actions run 40796152653](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40796152653) chạy simulator step thành công đủ 352 lượt và upload artifact `12866482176` (232909890 B; SHA-256 do GitHub khai báo `54698da35f4c1351d9ee39b56c466d72138ea3c3dfe616c172c97d83ad371e3a`). Tổng job hết budget 60 phút khi bắt đầu reviewer nên overall conclusion là cancelled; local raw reviewer sau đó hoàn tất và pass. Digest artifact là metadata GitHub, không được tính lại từ file zip.

DATA-03 đã hoàn tất **thử nghiệm development**; chưa có quality threshold đăng ký cho việc chọn cấu hình, nên không kết luận candidate được chọn. Nó cho thấy trade-off trong suite đã dùng: giảm mạnh high-water free+occupied cells và RSS giảm nhẹ; task success cao hơn reference trong development nhưng chậm hơn trên common successes, CPU tốn hơn. Chưa có held-out, validation, test, phần cứng, privacy hoặc mức dữ liệu tối thiểu tuyệt đối. V3 vẫn đóng với kết quả validation âm 87/100 và test chưa mở.
