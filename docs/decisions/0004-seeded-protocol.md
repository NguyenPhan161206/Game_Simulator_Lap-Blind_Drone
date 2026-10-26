# ADR 0004 — môi trường có seed, chứng cứ khả thi và protocol khóa

Ngày: 2026-10-26. Thực hiện giai đoạn môi trường/đánh giá trước huấn luyện theo yêu cầu người dùng.

- Giữ Webots v1 và baseline source 555f59f; chỉ mở rộng fixture, reset yaw, provenance và kiểm tra protocol. Không sửa thuật toán để hợp kết quả validation/test.
- Tạo sáu family và bốn split tách seed/geometry; train_reserved chưa huấn luyện. Development/validation/test có 24 case, chạy hai policy ghép cặp, tổng 48 lượt.
- Dùng chứng cứ đường ngang cho hull bảo thủ từ ground truth ở generator/evaluation. Nó không phải đường chuẩn tối ưu hoặc input của drone. Grid thất bại không chứng minh vô nghiệm; ca âm phải có goal trong Solid.
- Checksum runtime/config/manifest trước lần chạy seeded đầu; thay đổi file khóa cần version mới và ghi lại test exposure. Manifest công khai; không tuyên bố chống rò rỉ bằng việc giấu seed.
- Giữ mọi outcome và tách ca âm; pipeline có thể đạt trong khi baseline còn timeout/collision ở family khó. Đây là kết quả để chọn hướng nghiên cứu, không là lý do thay tiêu chí sau chạy.

Protocol này xác định các ngưỡng kỹ thuật và cách đánh giá của seeded v1. Nó không khóa chất lượng sản phẩm giao hàng hoặc tuyên bố mức an toàn phần cứng. Xem [đặc tả/tái hiện](../seeded-environments-v1.md) và [tiến độ](../plans/0004-seeded-environments.md).
