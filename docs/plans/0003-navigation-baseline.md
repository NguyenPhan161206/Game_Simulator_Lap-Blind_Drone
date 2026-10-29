# Kế hoạch 0003 — điều hướng tham chiếu và đánh giá nhiệm vụ

**Trạng thái hiện tại:** Hoàn tất baseline/evaluator kỹ thuật trên CI. [Bằng chứng](../research/2026-10-26-navigation-v1.md). Các bước và giới hạn lúc thực thi bên dưới là lịch sử, không là việc đang chờ chạy lại.

Ngày: 2026-10-26. Phạm vi: baseline không học, chỉ cảm biến/đích hợp lệ, chạy trên Webots v1. Chưa huấn luyện, chưa giảm cảm biến, chưa logistics.

## Lựa chọn kỹ thuật cho mốc này

- Bay ở độ cao đích 1.5 m, giữ yaw ban đầu; đánh giá đi vòng theo mặt phẳng ngang trước. Không tuyên bố điều hướng 3D tổng quát.
- Hai baseline tự viết: `direct` đi tới đích không né; `reactive` kết hợp hướng đích, bám tiếp tuyến vật cản gần nhất và giới hạn tốc độ theo khoảng cách. Không dùng toàn bản đồ, không coi là Bug2 hoặc thuật toán có bảo đảm hội tụ.
- Quan sát có kiểu dữ liệu: GPS/vận tốc ước lượng, tư thế/gyro lý tưởng, 10 phép đo khoảng cách cùng timestamp/frame/validity. Mẫu lỗi hoặc cũ khiến yêu cầu chuyển động về zero.
- Supervisor chỉ tạo tình huống, reset và chấm điểm. Trong lượt tự hành không gửi lệnh vận tốc, waypoint trung gian, vật cản hoặc đường đi.
- Bán kính 0.5 m, tốc độ dừng 0.18 m/s, dwell 1 s và deadline 65 s là tham số kỹ thuật tạm thời, chưa phải ngưỡng chất lượng nghiên cứu đã khóa.
- Tập chẩn đoán công khai: đường trống, vật cản chắn thẳng, hai vật cản liên tiếp và trường hợp đích trong vật cản (đối chứng âm, báo riêng). Các tình huống đã dùng phát triển không được gọi là tập test chưa thấy.
- Thành công cần trong vùng đích và chậm liên tục đủ dwell; va chạm/vượt biên ưu tiên hơn thành công, rồi timeout. Đối chứng không khả thi không trộn tỷ lệ thành công của các ca khả thi.

## Thứ tự và điều kiện qua bước

| Bước | Công việc | Bằng chứng cần có |
|---|---|---|
| 1 | Kiểm tra repo, lịch sử quyết định, simulator và quyền truy cập | Worktree sạch, không thay đổi phần có trước; chọn CI nếu local chưa có Webots |
| 2 | Ghi kế hoạch, hợp đồng quan sát và giao thức nhiệm vụ | Không có trường đặc quyền; config tách navigation và evaluation |
| 3 | Viết hai baseline và kiểm tra hành vi | Đổi frame đúng, thiếu/cũ dữ liệu thì dừng, lệnh có giới hạn, phản ứng với vật cản |
| 4 | Viết evaluator độc lập simulator | Kiểm tra dwell liên tục, thứ tự ưu tiên, deadline, path length và kết quả trên cả lượt thất bại |
| 5 | Tích hợp drone + supervisor + runner | Manual/smoke cũ vẫn chạy; autonomous chỉ gửi mission lúc đầu lượt |
| 6 | Chạy kiểm tra core và Webots thực | So sánh ghép cặp; lưu từng lượt, telemetry, cấu hình, commit và kết quả thực tế |
| 7 | Phân tích thất bại và bàn giao | Báo số liệu không chọn lọc, giới hạn ray thưa/không nhiễu/2D và trạng thái local riêng |

## Tiến độ

- [x] Bước 1: main tại 686681f, worktree sạch; không có Webots local, shell không phân giải github.com. GitHub connector đọc được repo; dùng CI để chạy simulator thật.
- [x] Bước 2: ghi kế hoạch trước triển khai. Các bước còn lại chỉ đánh dấu sau khi kiểm tra tương ứng.
- [x] Bước 3: hai baseline, schema quan sát/mission và kiểm tra hành vi đã triển khai; dữ liệu thiếu/cũ/sai frame trả lệnh zero.
- [x] Bước 4: evaluator và test thứ tự ưu tiên, dwell, tốc độ, deadline, quãng đường/tổng hợp thất bại đạt.
- [x] Bước 5: tích hợp mode navigation, runner/CI, giữ manual mapping; smoke Webots cũ 12 mục vẫn đạt. Không bấm phím GUI local.
- [x] Bước 6: 29 unit test đạt; CI 40249783714 chạy đủ 8 lượt, 5 gate tích hợp đạt. Reactive 3/3 ca khả thi success; direct 1/3 success, 2 collision; đối chứng âm direct collision, reactive timeout.
- [x] Bước 7: đã xem ảnh CI và lưu [báo cáo/JSON/giới hạn](../research/2026-10-26-navigation-v1.md). Không chốt chất lượng nghiên cứu bằng ba fixture.

Kết luận: baseline/evaluator kỹ thuật đã được kiểm chứng trên simulator CI. Local chưa có Webots; không huấn luyện model. Cần bộ tình huống đa dạng và protocol chia tập trước mốc nghiên cứu tiếp theo.
