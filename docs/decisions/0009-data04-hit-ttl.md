# ADR 0009 — DATA-04: giới hạn thời hạn occupied hit

Ngày: 2026-10-29. Trạng thái: giao thức development đã khóa; chưa có kết quả simulator.

## Câu hỏi và biến duy nhất

DATA-03 giữ occupied hit tới hết episode. DATA-04 kiểm tra một biến: mỗi occupied hit được giữ trong 10.0 giây kể từ lần quan sát gần nhất; quan sát lại hit sẽ làm mới thời hạn. Khi hit hết hạn, xóa hit và dựng lại vùng inflation chỉ từ các hit còn hạn.

Đối chứng là DATA-03 persistent occupied-hit trên cùng 88 case development đã lộ, hai repeat, tổng 352 episode và 176 cặp. Giữ Webots R2025a, cadence 32 ms, control/physics 16 ms, vehicle, sensor, free-cell retention tới acquisition tiếp theo, planner v4, evaluator, ngân sách map và mọi cấu hình khác cố định. Không có arm dùng ground truth trong navigation.

10 giây là một điểm engineering để khảo sát, không được suy ra từ yêu cầu an toàn hoặc dữ liệu ngoài đời. Không quét nhiều TTL rồi chọn cấu hình tốt nhất trên cùng suite. Thử TTL khác cần protocol/source version và kế hoạch đánh giá mới.

## Hợp đồng dữ liệu

- Hit hết hạn tại `sample_time - latest_hit_time >= 10.0 s`; xử lý ở acquisition timestamp mô phỏng, không theo wall clock.
- Khi có hit mới trên cùng ô, thời điểm quan sát gần nhất thay thế thời điểm cũ.
- Khi hit hết hạn, cập nhật `occupied`, dựng lại `blocked/inflation` từ các hit còn hạn và vô hiệu hóa cache đường đi.
- Free evidence cũ vẫn chỉ tồn tại tới acquisition kế tiếp như DATA-03; đọc lại cùng packet không làm nó hết hạn.
- Unknown luôn bị cấm khi xác nhận tuyến/lệnh. Hit hết hạn không đồng nghĩa vùng đó đã được chứng minh an toàn/trống.
- Đo outcome đầy đủ, paired case, CPU, process RSS và peak map entries; giữ collision, bounds, timeout và negative control.

## Phạm vi

Chỉ là development trên suite đã exposed, không validation/test mới, không quality-selection, không an toàn phần cứng, không riêng tư hoặc tối thiểu thông tin. V3 validation đã fail; test v3 vẫn đóng gate. Giữ nguyên DATA-03 report/raw và mọi v1/v2/v3/v4 locks.

## Bàn giao development — 2026-10-29

Thiết kế giữ nguyên. [CI và raw review](../research/2026-10-29-data04-hit-ttl.md) tại source `8b4e3be` hoàn tất 176 tests/352 episode. Hai arm cùng 67/74, một case cải thiện/một kém đi; năm gate riêng DATA-04 đạt, gate v4 deadlock kế thừa chưa đạt. Chưa chọn cấu hình hoặc mở held-out.
