# Đối chiếu lượt nghiệm thu laptop mới — 27/10/2026

Audit tại source `c012ab85085d22b7bf4e6eaa3d5812633ec485bc`, trước thay đổi tài liệu này. [JSON bằng chứng](2026-10-27-local-acceptance-followup.json) lưu nguồn, số đếm, phiếu và hash raw files. Không sửa dữ liệu hoặc phiếu gốc.

## Lượt đã có và kết quả đối chiếu

Batch `artifacts/local-acceptance-20261026T224307533989Z` bắt đầu lúc 05:43:07 ngày 27/10 theo giờ Việt Nam. Manual chạy source c012ab8 sạch, Webots R2025a, đúng world/controller, exit 0, 82.338 s wall. Có 1.202 telemetry packet trong t=0.016…77.520 s mô phỏng. Operator xác nhận GUI/phím, chọn smooth và unchanged; các xác nhận là self-report, không phải agent đã thao tác GUI.

| Lệnh ghi trong telemetry | Mẫu dương | Mẫu âm | Mẫu zero |
|---|---:|---:|---:|
| forward_m_s | 500 | 136 | 566 |
| left_m_s | 117 | 106 | 979 |
| up_m_s | 0 | 0 | 1202 |
| yaw_rate_rad_s | 138 | 26 | 1038 |

Đã có bằng chứng chuyển động ngang và yaw tốt hơn lượt all-zero trước. Riêng T/G được đánh yes nhưng chưa có sampled up command tương ứng. Z chỉ trong khoảng 1.414458…1.503629 m; biên độ này không tự chứng minh đã thử tăng/giảm độ cao. Không kết luận do focus, thời gian giữ phím, input method, code hoặc driver khi chưa kiểm tra trực tiếp.

Collector dừng với PENDING, không mở mapped. Console có cảnh báo Webots không được khởi chạy từ launcher chính thức; controller vẫn khởi động, nhận telemetry và exit 0. Giữ cảnh báo trong evidence; chưa có bằng chứng liên hệ nó với T/G.

Đối chiếu [WbStandardPaths.cpp tại R2025a](https://github.com/cyberbotics/webots/blob/R2025a/src/webots/core/WbStandardPaths.cpp#L234-L242) xác định cảnh báo xuất hiện khi WEBOTS_TMPDIR trống/không tồn tại. Local collector được sửa để đặt temp base /tmp và giữ WEBOTS_ORIGINAL_LD_LIBRARY_PATH tương tự launcher; không gọi wrapper có thao tác desktop-file ngoài workspace. Console cũ được giữ nguyên. [Kế hoạch sửa](../plans/0009-local-launcher-followup.md) yêu cầu CI xác nhận console mới không còn cảnh báo.

Đã xác nhận bản sửa tại source b53f683f431bf5ba076099ebe8f33c9a2a70e5e9: [CI 40416478930](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40416478930) đạt 82 test, mapped success, manual telemetry/timeout và khóa chống chạy chồng. Bước verify kiểm tra cả hai console mới đều không còn chuỗi cảnh báo launcher; artifact 12696047038 và [JSON evidence](2026-10-27-launcher-fix-ci.json) giữ đúng source. Đây không phải lượt nhấn T/G trên desktop và không tự đóng LOC-05.

Trong nguồn R2025a đã kiểm tra, [3D key handler](https://github.com/cyberbotics/webots/blob/R2025a/src/webots/gui/WbView3D.cpp#L2183-L2214) chuyển key event cho robot; các shortcut T/G tìm thấy trong action manager đều có modifier. Chưa xác định được vì sao lượt này không nhận T/G. Mapping và stabilizer của dự án dùng up_m_s trực tiếp; không có thao tác xóa lệnh dọc trước telemetry.

## Kiểm tra hiện tại

- `make check`: scaffold, generated worlds/manifests, hai protocol và 82 unit test đều đạt. Đây là kiểm tra logic/source, không là lượt nhấn phím thực.
- Webots vẫn R2025a; ldd với bundled library path không có dependency not found.
- OS lock khả dụng; file active.lock tồn tại không có nghĩa collector đang chạy.
- JSON preflight ban đầu ghi xdpyinfo kết nối được :0. Lần probe phục vụ sửa launcher hiện trả exit 1, log riêng artifacts/20261027-display-probe.log. Giữ hai lần kiểm tra riêng; không coi agent đã điều khiển được GUI.
- Không thay runtime, world, protocol hoặc ngưỡng; không chạy lại test nghiên cứu và không huấn luyện model.

## Thực hiện tiếp theo

1. Có thể chạy `python3 tools/local_session.py manual` để kiểm tra riêng T/G còn thiếu: chọn vùng 3D; giữ T riêng khoảng 1–2 giây, thả và xem nhãn z tăng; sau đó giữ G riêng và xem z giảm. Không giữ SPACE hoặc T/G đồng thời. Với các phím không thử trong lượt bổ sung, để Enter/chưa thử trên phiếu. Mỗi phiếu vẫn gắn đúng lượt, không sao chép phiếu cũ.
2. Để bổ sung LOC-06 độc lập, chạy `python3 tools/local_session.py mapped`, quan sát quét/di chuyển/đến đích rồi điền phiếu. Giữ nguyên tốc độ và không pause trong phép đo.
3. Lệnh accept vẫn dùng khi muốn nghiệm thu lại cả hai bước trong một batch tự đủ. Nó chỉ mở mapped khi manual của batch đó qua gate.
4. Agent đối chiếu từng record/source/protocol và ghi rõ nguồn nếu dùng nhiều lượt cho từng mục checklist; chỉ đóng LOC-05 khi có T/G thực sự được nhận và xác nhận phản ứng phù hợp.

**LOC-09 đã hoàn thành việc ghi nhận hiệu năng và giới hạn.** Manual mới có 77.504 s telemetry cho 82.338 s wall và phiếu smooth/unchanged; phản hồi này áp dụng cho chuyển động ngang/yaw đã được nhận, T/G vẫn chưa xác minh. Lượt mapped laptop trước có 48.913 s wall và CPU max 48.679893 ms > tick 16 ms; được giữ dưới đúng source/lượt của [audit trước](2026-10-26-local-acceptance.md). Không coi số đo này là FPS/input latency hoặc chứng minh deadline thời gian thực.

**LOC-05/06 còn mở.** Thiếu bằng chứng T/G và xác nhận đã xem mapped chuyển động/kết thúc; không dùng CI hoặc phiếu khác để tự điền các xác nhận đó.
