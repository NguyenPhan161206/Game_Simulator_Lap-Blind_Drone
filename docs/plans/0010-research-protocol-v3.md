# Kế hoạch 0010 — khóa nghiên cứu giảm thu nhận range, protocol v3

**Trạng thái hiện tại:** Hoàn tất thiết kế v3; thiết kế vẫn đóng băng. [Bằng chứng](../research/2026-10-27-research-protocol-v3.md). Các bước và giới hạn lúc thực thi bên dưới là lịch sử, không là việc đang chờ chạy lại.

Ngày: 2026-10-27. Phạm vi được giao: hoàn thiện EXP-01–EXP-12 trước triển khai đánh giá hoặc ML. Các ngưỡng mới là lựa chọn nghiên cứu được ghi trước kết quả, không phải ngưỡng chất lượng sản phẩm đã được chứng minh.

## Trình tự và điều kiện chuyển bước

1. **Rà soát nền tảng:** kiểm tra Git, tài liệu intent/kiến trúc, hợp đồng quan sát, generator, evaluator và khóa v1/v2. Không sửa các file đã khóa. Xác nhận bài toán còn là một drone, vật cản tĩnh, range hình học lý tưởng, bay ngang.
2. **Đối chiếu nguồn chính:** đọc nghiên cứu về grid/điều khiển cảm nhận, cảm biến ít dữ liệu và thiết kế thực nghiệm. Ghi rõ phần đã có và đóng góp dự kiến; không tuyên bố thuật toán mới hoặc bảo vệ riêng tư.
3. **Chốt câu hỏi và thiết kế:** ưu tiên giảm thu nhận range trên mapped; giữ ML thành nghiên cứu khác. Ghi cấu hình tham chiếu, một biến độc lập, định nghĩa byte/mẫu, tiêu chí nhiệm vụ, suy giảm cho phép, cách chọn cấu hình và trường hợp kết luận âm trong ADR + TOML + protocol.
4. **Tạo dữ liệu mới:** cấp seed riêng từng case và từng split; tạo train dự trữ/development/validation/test bằng generator có provenance. Chương trình kiểm tra geometry trùng nhau và trùng v1/v2, chứng chỉ khả thi/âm. Không xem trajectory/outcome held-out; không tự lọc case khó.
5. **Khóa và exposure:** đóng dấu hash thiết kế, nguồn sinh dữ liệu, commitments và sổ exposure. Phân biệt khóa thiết kế với khóa runtime còn phải thực hiện trước đánh giá. Tool phải từ chối đánh giá khi chưa có triển khai được khóa; không cung cấp runner giả.
6. **Kiểm chứng:** test tính tái lập, chống trùng/sai split, toàn vẹn khóa, phân loại failure, thống kê và gate; chạy scaffold, lab/scenario/v2 checks và toàn bộ unit tests. Các test này kiểm chứng đặc tả/công cụ, không là kết quả Webots giảm dữ liệu.
7. **Bàn giao:** cập nhật checklist từng EXP bằng đường dẫn bằng chứng, README và hướng dẫn agent. Commit/push theo nhóm kế hoạch → protocol/công cụ → bằng chứng. Chạy CI và xác minh commit/tree; chỉ fast-forward main khi các kiểm tra liên quan đạt.

## Ranh giới hoàn thành

Mốc này hoàn tất khi có thiết kế đóng băng, tập case đã sinh/kiểm chứng, sổ exposure và công cụ bảo vệ thiết kế. Không huấn luyện, không sửa navigation, không chạy validation/test chính thức. Mốc tiếp theo mới triển khai adapter v3 lấy mẫu thật, kế toán dữ liệu và evaluator theo thiết kế, rồi khóa source runtime trước mở held-out.

Nếu lựa chọn hướng nghiên cứu được người dùng điều chỉnh trong lúc thực hiện, cập nhật kế hoạch trước khi khóa; không chỉnh ngưỡng để hợp với kết quả đã xem.
