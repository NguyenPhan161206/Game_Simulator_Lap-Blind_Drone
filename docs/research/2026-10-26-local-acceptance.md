# Audit bằng chứng laptop — nhánh L

Ngày 2026-10-26. Source của các lượt: 534b83a20ae6f87ad3ce8aaa4a55aaed921338de, working_tree_dirty=false. Audit bằng tools/local_session.py tại b32410595b26f8ef2d0f8d99dca469797278366b. [JSON rút gọn](2026-10-26-local-acceptance.json) giữ source, số gốc, phiếu, delta và hash raw files. Agent đọc file/ảnh, không trực tiếp điều khiển desktop.

## Các lượt được đối chiếu

Manual: artifacts/local-manual-20261026T064254652516Z, Ubuntu 26.04.1 LTS, DISPLAY=:0, không yêu cầu software rendering. World minimal_lab.wbt, controller drone_controller/lab_supervisor; console có cả hai READY. Phiếu người thao tác xác nhận GUI mở và world/controller đúng. Exit 0, 2239 telemetry packet, không dòng lỗi, t=0.016…143.888 s mô phỏng, 152.067 s wall. Đây là bằng chứng LOC-04.

Phiếu manual đánh “yes” mọi phím, nhưng command telemetry có tất cả trục bằng 0; x/y không đổi, biên độ z chỉ 0.083637 m trong quá trình hover. Ghi chú độ phản hồi chỉ là “y”. Lượt manual 06:42:54 UTC kéo dài đến 06:45:26 UTC, trong khi mapped 06:43:28…06:44:17 UTC chạy chồng khoảng thời gian. Cần xác nhận cửa sổ/focus và thử lại nếu cần; không tự quy kết nguyên nhân hoặc sửa phiếu. **LOC-05 chưa đóng.** Những lượt manual khác có command ở một số trục nhưng không đủ bộ phím/reset và phiếu tương ứng để lấp thiếu cho lượt này.

Mapped: artifacts/local-mapped-20261026T064328483395Z, cùng source/máy, observed_v2.wbt, drone_v2/lab_v2, chỉ development-u_trap-s21001/mapped. Exit 0, result/checks passed, đúng protocol/manifest/geometry, có 668 telemetry packet, trajectory, cases, manifest và hai JPG. Đã mở xem ảnh đúng ca: drone ở gần đích; ảnh là observer và không đi vào policy. Đủ lưu bằng chứng LOC-07; ảnh tĩnh không thay xác nhận người xem đã thấy chuyển động/kết thúc, nên **LOC-06 còn chờ**.

Lượt managed riêng artifacts/local-managed-mapped-20261026 vẫn exit -6 vì không kết nối display :0; không có result hoặc telemetry. Lỗi này không phủ nhận lượt desktop thành công và không được gộp thành chuyến bay local khác.

## So sánh với CI cùng protocol

Tham chiếu [CI 40255492790](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40255492790), source 2f422e253376b589e478ac10f3eee8efa970dc74. Helper/docs mới nằm ngoài các file khóa. V1/v2 hash vẫn hợp lệ; việc chạy lại là reproduction, không phải tập test mới.

| Chỉ số đúng ca mapped U21001 | Laptop | CI |
|---|---:|---:|
| Outcome / contacts | success / 0 | success / 0 |
| Thời gian nhiệm vụ (s) | 41.216 | 41.216 |
| Đường đi 3D (m) | 14.858754976 | 14.855333972 |
| Khoảng cách cuối (m) | 0.046151670 | 0.046151666 |
| CPU policy mean / max (ms) | 1.466946 / 48.679893 | 0.858700 / 34.984393 |

Đường đi lệch +0.003421004 m; pose ban đầu lệch 0.002156186 m, pose cuối lệch khoảng 1.02e-8 m. 82 sample trajectory có cùng thời điểm; 4 sample lệch XY tối đa 0.0001 m, độ lệch XYZ tối đa 0.0022 m ở sample đầu. Ở sample đầu local z=1.4978, CI z=1.5; sample cuối trùng ở độ chính xác lưu bốn chữ số thập phân. Cùng 2575 decisions, 1288 range packets/map updates, 5178 peak cells, 76 plans. Không hết budget.

**LOC-08 hoàn tất đối chiếu:** cùng outcome và protocol; không phát hiện collision/regression nhiệm vụ trong ca này. Có khác biệt trạng thái đầu/dao động độ cao, nên không gọi toàn bộ delta là round-off hoặc lỗi driver. Chưa chứng minh nguyên nhân bằng thí nghiệm có kiểm soát, và chưa kết luận tương đương từng physics tick. Không tune lại runtime để ép hai log trùng số.

CI collector mới chạy **một ca riêng** dưới Xvfb/software rendering tại b324105 và [đạt](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40284088405). [Evidence](2026-10-26-local-collector-ci.json) ghi path=14.858754976240316 m, chỉ khác laptop khoảng 1e-14 m; initial pose delta với CI toàn suite trước vẫn 0.002156186 m. Việc khác biệt xuất hiện lại ngoài laptop không ủng hộ kết luận lỗi riêng GPU/driver laptop. Thứ tự ca và trạng thái động lực ban đầu là hướng cần kiểm tra nếu nghiên cứu nguyên nhân, chưa là nguyên nhân đã chứng minh. Hai lượt manual/mapped của CI này chỉ kiểm tra collector, không là thao tác bàn phím hoặc quan sát GUI laptop.

## Hiệu năng và gate còn lại

Mapped mất 48.913317 s wall cho nhiệm vụ 41.216 s và warmup 2 s; tỷ số sim/wall tổng khoảng 0.883522. Wall gồm startup/shutdown, nên không thay FPS hoặc đo input latency. CPU max 48.679893 ms lớn hơn tick 16 ms; chưa đạt bằng chứng deadline phần cứng. **LOC-09 còn chờ mô tả độ mượt/trễ/pause từ người thao tác**; giữ giới hạn realtime rõ ràng.

Raw console/result/source/ảnh vẫn nằm trong artifacts bị Git ignore; JSON rút gọn không thay thế archive raw. Chỉ LOC-04, LOC-07, LOC-08 được đóng từ audit này. LOC-05, LOC-06, LOC-09 cần bổ sung bằng chứng; công cụ CI không thay các xác nhận đó.
