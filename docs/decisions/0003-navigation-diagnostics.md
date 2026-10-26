# ADR 0003 — baseline và đánh giá nhiệm vụ

Ngày: 2026-10-26. Đây là lựa chọn kỹ thuật để thực hiện mốc kế tiếp được người dùng yêu cầu; các con số không thay thế việc khóa protocol nghiên cứu cuối.

## Quyết định

- Giữ nguyên động lực học, cảm biến và ranh giới quyền của Webots v1. Core navigation/evaluation là Python độc lập simulator.
- Bắt đầu từ trạng thái bay, đến đích rồi giảm tốc và giữ tại đó. Chưa cất/hạ cánh, giao hàng hoặc điều phối.
- Triển khai direct và heuristic reactive tiếp tuyến trái tự viết. Bay vòng ở độ cao đích trước; không tuyên bố giải thuật có tính đầy đủ/hội tụ hoặc điều hướng 3D tổng quát.
- Drone nhận mission gồm tọa độ đích và tên baseline; không nhận ID tình huống, trạng thái khả thi, kích thước/vị trí vật cản hoặc route của supervisor. Quan sát chỉ được dựng từ device đã khai báo.
- Đánh giá privileged ở 16 ms: contact/vượt biên ưu tiên hơn thành công, deadline không được vượt. Thành công cần tốc độ thấp và dwell, không chỉ chạm vùng đích.
- Các fixture được công khai và dùng phát triển là development_diagnostic; tách riêng ca không khả thi. Chưa tạo tập train/validation/test cho học máy, và không tái gắn nhãn các fixture này thành held-out test.

## Hệ quả

Có thể kiểm tra nhiệm vụ, scoring và một năng lực đi vòng đơn giản trước khi thêm ML. Baseline reactive có thể mắc kẹt hoặc đâm vật cản giữa các ray; không tối ưu đường hoặc bảo đảm an toàn. Điều này phải được giữ trong báo cáo, không đổi tiêu chí sau khi thấy kết quả để làm đẹp tỷ lệ.

Thông số và cách chạy xem [navigation v1](../navigation-v1.md), quá trình kiểm chứng xem [kế hoạch 0003](../plans/0003-navigation-baseline.md).
