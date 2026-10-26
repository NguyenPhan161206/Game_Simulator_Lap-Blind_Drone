# Chẩn đoán development trước khóa v2

Đây là dữ liệu đã dùng phát triển, không phải kết quả validation/test mới. [Raw pilot evidence](2026-10-26-v2-development.json) giữ đủ các lượt và failure snapshot.

## Hai đợt Webots đầu

- [Pilot 1, CI 40253447132](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40253447132), source 5d1500bddeb257fdc9bcf7f96f6ff655b6953c46, có rendering: đủ 36 lượt.
- [Pilot 2, CI 40254520825](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40254520825), source f2b054bc97b28cb31b712fb8a823583a0a2ab555, không rendering, có cache tìm kiếm không có đường và counters rõ hơn: đủ 36 lượt.

Cả hai: reactive 8/10, guarded 10/10, mapped 10/10 ca khả thi. Reactive collision hai U; guarded/mapped không collision và hoàn thành cả hai U. Mỗi policy có hai negative control timeout, không false success. Đây đạt mục tiêu kỹ thuật đặt trước (mapped ≥8/10, ≥1/2 U và không tăng collision) cho hai bản ứng viên này.

Đã đối chiếu cả 36 episode giữa hai pilot: outcome, elapsed_s, path_length_m và final_position_m giống hệt; CPU metrics khác theo lần chạy. Điều này chỉ xác nhận hai đợt này, không chứng minh mọi lần chạy Webots đều deterministic. Pilot 1 gọi counter map_updates bằng tên sensor_updates; phải đọc nó là cập nhật grid, không phải số mẫu raw cảm biến của reactive bằng zero. Pilot 2 sửa tên và thêm range_samples/range_values.

## Một failure snapshot cụ thể

Chọn reactive, development-u_trap-s21001 ở pilot 2, contact_count=1. Contact tại simulation t=455.808 s; public pose/command gần nhất t=455.792 s, range sample t=455.776 s. Đây là timestamp toàn job, elapsed của episode là 13.824 s.

- Range_045 còn 0.108147 m từ origin cảm biến, các ray ngang khác xa hơn. Phép đo này có trước contact 32 ms.
- Đổi command từ FLU sang ENU bằng yaw đã đo cho vận tốc yêu cầu khoảng (-0.321, 0.447) m/s.
- Chênh lệch pose GPS trước đó với vị trí ground truth contact trong 16 ms tương ứng vận tốc đoạn trung bình khoảng (0.422, 0.491) m/s. GPS ở đây là lý tưởng, không có sensor noise; đây là sai phân hai vị trí, không giả làm encoder hoặc một sample vận tốc trực tiếp.

Nghĩa là command đã yêu cầu thành phần x đi ra xa nhưng chuyển động còn đi vào theo x. Guard v1 thay đổi yêu cầu vận tốc không tức thời xóa quán tính của plant. Bề mặt ở góc xuất hiện muộn trên một số ray và tuổi mẫu cũng cần xét. Snapshot hỗ trợ các giả thuyết về lịch sử quan sát/hull/khoảng đáp ứng phanh; chưa tách nguyên nhân từng yếu tố bằng ablation kiểm soát.

## Phần v2 được thử

Guard dùng điểm hit đã đo, hull sphere bao thân + margin + sai số lượng tử cell; giới hạn thành phần vận tốc đóng theo gap/1.4 s. Đây là khoảng đáp ứng quy ước, không phải chứng minh phanh thật hoặc control barrier được kiểm chứng hình thức. Guarded/mapped còn quét yaw và giảm giới hạn 0.55→0.4 m/s, nên không quy toàn bộ cải thiện cho riêng bộ nhớ/A*.

Mapped dùng A* trên grid tự đo. Unknown được phép lập kế hoạch với cost cao hơn, nhưng không được thực thi như free. Không có oracle waypoint/geometry trong input. Bản đồ dùng thêm bộ nhớ và có thể biểu diễn bố trí môi trường; không là kết quả tối thiểu dữ liệu/riêng tư.

## Lỗi bổ sung từ contract fixture

Một fixture có plant vận tốc tức thời (không phải Webots) làm robot đứng quét mãi khi phép đo mới inflate ô hiện tại. Planner có đường nhưng follower từ chối tất cả đoạn vì start cell bị chặn. Nhánh recovery chỉ ra ngoài qua ô đã đo free, kiểm tra swept disk trên điểm đo và giới hạn 0.2 m/s; vẫn qua guard. Fixture không được dùng thay bằng chứng bay hoặc để chấm success rate. Bản sửa được chạy lại trên development trước khóa/fresh evaluation.

[Pilot 3, CI 40255137469](https://github.com/NguyenPhan161206/Game_Simulator_Lap-Blind_Drone/actions/runs/40255137469), source 69d67124f6899a36cc5509ab74974fb265f2083a, kiểm chứng recovery trên đủ 36 lượt: guarded/mapped vẫn 10/10 ca khả thi, reactive 8/10 và hai U collision. Các outcome/time/path/pose cuối không đổi so với pilot 2 trong các fixture này; không suy ra recovery làm tăng success ở Webots từ chính các case đó. Recovery giải quyết contract fixture đã mô tả. Code/params của pilot 3 được chọn để khóa v2; mọi thay đổi sau đó chỉ là evidence/docs/tests/CI gate, không sửa file runtime đã khóa.
